import json
import queue
from pathlib import Path

import click
import mysql.connector
import pandas as pd
from dotenv import load_dotenv

from algos import binary_search, merge_sort
import db as db_utils
from db_init import initialize_schema
from profiler import profile_dataset
from transformers import TRANSFORMERS


def _get_pipeline_id(name: str) -> int | None:
    connection = db_utils.get_db_connection()
    try:
        cursor = connection.cursor()
        try:
            cursor.execute("SELECT pipeline_id FROM pipelines WHERE name = %s", (name,))
            row = cursor.fetchone()
        finally:
            cursor.close()
    finally:
        connection.close()
    return row[0] if row else None


def _fetch_pipeline_steps(pipeline_id: int) -> list[tuple]:
    connection = db_utils.get_db_connection()
    try:
        cursor = connection.cursor()
        try:
            cursor.execute(
                "SELECT step_id, step_order, operation, params FROM pipeline_steps WHERE pipeline_id = %s ORDER BY step_order",
                (pipeline_id,),
            )
            steps = cursor.fetchall()
        finally:
            cursor.close()
    finally:
        connection.close()
    return steps


def _insert_dataset(name: str, row_count: int, column_count: int) -> None:
    connection = db_utils.get_db_connection()
    try:
        cursor = connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO datasets (name, row_count, column_count) VALUES (%s, %s, %s)",
                (name, row_count, column_count),
            )
        finally:
            cursor.close()
        connection.commit()
    finally:
        connection.close()


def _require_pipeline(name: str) -> int:
    pipeline_id = _get_pipeline_id(name)
    if pipeline_id is None:
        raise click.ClickException(f"Pipeline '{name}' not found.")
    return pipeline_id


def _run_pipeline_batch(steps: list[tuple], input_file: str, output_file: str) -> None:
    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError as exc:
        raise click.ClickException(f"Input file not found: {input_file}") from exc

    task_queue: queue.Queue = queue.Queue()
    for step in steps:
        task_queue.put(step)

    while not task_queue.empty():
        step_id, _step_order, op_name, params_json = task_queue.get()
        params = json.loads(params_json) if params_json else {}
        op_function = TRANSFORMERS.get(op_name)
        if op_function is None:
            raise click.ClickException(f"Unknown operation '{op_name}' in step {step_id}.")
        df = op_function(df, params)

    df.to_csv(output_file, index=False)


def _run_pipeline_interactive(steps: list[tuple], input_file: str, output_file: str) -> None:
    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError as exc:
        raise click.ClickException(f"Input file not found: {input_file}") from exc

    undo_stack: list[pd.DataFrame] = []
    index = 0

    while index < len(steps):
        step_id, _step_order, op_name, params_json = steps[index]
        click.echo(f"Next step: {op_name} with params {params_json}")
        choice = click.prompt("[A]pply, [S]kip, [U]ndo, [Q]uit", default="A").strip().upper()

        if choice == "A":
            undo_stack.append(df.copy())
            op_function = TRANSFORMERS.get(op_name)
            if op_function is None:
                undo_stack.pop()
                raise click.ClickException(f"Unknown operation '{op_name}' in step {step_id}.")
            params = json.loads(params_json) if params_json else {}
            df = op_function(df, params)
            click.echo("Step applied.")
            index += 1
        elif choice == "S":
            click.echo("Step skipped.")
            index += 1
        elif choice == "U":
            if not undo_stack:
                click.echo("No steps to undo.")
            else:
                df = undo_stack.pop()
                click.echo("Last step undone.")
                if index > 0:
                    index -= 1
        elif choice == "Q":
            break
        else:
            click.echo("Invalid option. Please choose again.")

    click.echo("Interactive session finished.")
    if click.confirm(f"Save result to {output_file}?", default=True):
        df.to_csv(output_file, index=False)
        click.echo(f"Output saved to {output_file}.")
    else:
        click.echo("Output not saved.")


@click.group()
def cli() -> None:
    """DataForge: A CLI for reproducible data cleaning pipelines."""


@cli.command()
@click.argument("filepath", type=click.Path(exists=True, dir_okay=False, path_type=str))
def profile(filepath: str) -> None:
    """Generate a comprehensive profile of a CSV file."""

    click.echo(f"Profiling {filepath}...")
    row_count, column_count = profile_dataset(filepath)
    dataset_name = Path(filepath).name
    _insert_dataset(dataset_name, row_count, column_count)
    click.echo(
        f"Profile stored for '{dataset_name}' with {row_count} rows and {column_count} columns."
    )


@cli.group()
def pipeline() -> None:
    """Manage cleaning pipelines."""


@pipeline.command(name="create")
@click.argument("name")
def create_pipeline(name: str) -> None:
    """Create a new pipeline."""

    connection = db_utils.get_db_connection()
    try:
        cursor = connection.cursor()
        try:
            try:
                cursor.execute("INSERT INTO pipelines (name) VALUES (%s)", (name,))
            except mysql.connector.errors.IntegrityError as exc:
                click.echo(f"Error: Pipeline '{name}' already exists.")
                raise SystemExit(1) from exc
            connection.commit()
        finally:
            cursor.close()
    finally:
        connection.close()
    click.echo(f"Pipeline '{name}' created.")


@pipeline.command(name="add")
@click.argument("name")
@click.option("--operation", "-op", "operation", required=True, help="Operation to perform.")
@click.option("--params", "-p", "params_json", required=True, help="JSON string of parameters.")
@click.option("--order", "-o", "step_order", type=int, required=True, help="Step order.")
def add_step(name: str, operation: str, params_json: str, step_order: int) -> None:
    """Add a new step to a pipeline."""

    if operation not in TRANSFORMERS:
        raise click.ClickException(f"Unknown operation '{operation}'.")

    try:
        params = json.loads(params_json)
    except json.JSONDecodeError as exc:
        raise click.ClickException("Invalid JSON for params.") from exc

    pipeline_id = _require_pipeline(name)

    connection = db_utils.get_db_connection()
    try:
        cursor = connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO pipeline_steps (pipeline_id, step_order, operation, params) VALUES (%s, %s, %s, %s)",
                (pipeline_id, step_order, operation, json.dumps(params)),
            )
        finally:
            cursor.close()
        connection.commit()
    finally:
        connection.close()
    click.echo(f"Step {step_order} added to '{name}'.")


@pipeline.command(name="show")
@click.argument("name")
def show_pipeline(name: str) -> None:
    """Show the steps in a pipeline."""

    pipeline_id = _require_pipeline(name)
    steps = _fetch_pipeline_steps(pipeline_id)
    if not steps:
        click.echo("No steps configured for this pipeline.")
        return
    for step in steps:
        click.echo(step)


@pipeline.command(name="delete")
@click.argument("name")
def delete_pipeline(name: str) -> None:
    """Delete a pipeline."""

    pipeline_id = _require_pipeline(name)
    connection = db_utils.get_db_connection()
    try:
        cursor = connection.cursor()
        try:
            cursor.execute("DELETE FROM pipelines WHERE pipeline_id = %s", (pipeline_id,))
        finally:
            cursor.close()
        connection.commit()
    finally:
        connection.close()
    click.echo(f"Pipeline '{name}' deleted.")


@pipeline.command(name="rename")
@click.argument("name")
@click.argument("new_name")
def rename_pipeline(name: str, new_name: str) -> None:
    """Rename an existing pipeline."""

    pipeline_id = _require_pipeline(name)
    connection = db_utils.get_db_connection()
    try:
        cursor = connection.cursor()
        try:
            cursor.execute(
                "UPDATE pipelines SET name = %s WHERE pipeline_id = %s",
                (new_name, pipeline_id),
            )
        finally:
            cursor.close()
        connection.commit()
    finally:
        connection.close()
    click.echo(f"Pipeline '{name}' renamed to '{new_name}'.")


@cli.command()
@click.argument("name")
@click.option("--input", "-i", "input_file", type=click.Path(exists=True, dir_okay=False, path_type=str), required=True)
@click.option("--output", "-o", "output_file", type=click.Path(dir_okay=False, path_type=str), required=True)
@click.option("--interactive", is_flag=True, help="Run in interactive mode with undo support.")
def run(name: str, input_file: str, output_file: str, interactive: bool) -> None:
    """Run a pipeline on an input file."""

    pipeline_id = _require_pipeline(name)
    steps = _fetch_pipeline_steps(pipeline_id)
    if not steps:
        raise click.ClickException("No steps configured for this pipeline.")

    if interactive:
        _run_pipeline_interactive(steps, input_file, output_file)
    else:
        _run_pipeline_batch(steps, input_file, output_file)
        click.echo(f"Output saved to {output_file}.")

    click.echo(f"Pipeline '{name}' ran.")


@cli.group()
def datasets() -> None:
    """Manage profiled datasets."""


@cli.group()
def db() -> None:
    """Database utilities."""


@db.command(name="init")
def initialize_db() -> None:
    """Create or refresh the DataForge database schema."""

    click.echo("Initializing DataForge database schema...")
    try:
        initialize_schema()
    except mysql.connector.Error as exc:
        raise click.ClickException(f"Database initialization failed: {exc}") from exc
    click.echo("Database schema initialized successfully.")


@cli.command()
def init() -> None:
    """Run the interactive setup wizard."""

    config_path = Path.home() / ".dataforge.env"

    if config_path.exists():
        click.echo(f"Config file already exists at {config_path}.")
        if not click.confirm("Overwrite existing config?", default=False):
            click.echo("Setup aborted. Existing configuration preserved.")
            return

    db_host = click.prompt("DB Host", default="localhost")
    db_user = click.prompt("DB User", default="dataforge_user")
    db_pass = click.prompt(
        "DB Password", hide_input=True, confirmation_prompt=True
    )
    db_name = click.prompt("DB Name", default="dataforge")

    config_content = (
        f"DB_HOST={db_host}\n"
        f"DB_USER={db_user}\n"
        f"DB_PASSWORD={db_pass}\n"
        f"DB_NAME={db_name}\n"
    )
    config_path.write_text(config_content, encoding="utf-8")
    click.echo(f"Config file created at {config_path}.")

    load_dotenv(dotenv_path=config_path, override=True)

    click.echo("Now, attempting to initialize the database...")

    schema_sql = f"""
CREATE DATABASE IF NOT EXISTS `{db_name}`;
USE `{db_name}`;

CREATE TABLE IF NOT EXISTS pipelines (
    pipeline_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS pipeline_steps (
    step_id INT AUTO_INCREMENT PRIMARY KEY,
    pipeline_id INT NOT NULL,
    step_order INT NOT NULL,
    operation VARCHAR(100) NOT NULL,
    params JSON,
    FOREIGN KEY (pipeline_id) REFERENCES pipelines(pipeline_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS datasets (
    dataset_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    profiled_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    row_count INT,
    column_count INT
);
"""
    try:
        config = db_utils.get_db_config(include_database=False)
        connection = mysql.connector.connect(**config)
        try:
            cursor = connection.cursor()
            try:
                # Execute each SQL statement separately to avoid multi-statement driver bugs.
                for statement in schema_sql.split(";"):
                    if statement.strip():
                        cursor.execute(statement)
            finally:
                cursor.close()
            connection.commit()
        finally:
            connection.close()
    except mysql.connector.Error as exc:
        click.echo(f"Database initialization failed: {exc}")
        raise SystemExit(1) from exc

    click.echo(
        f"Database '{db_name}' and tables created successfully. You're all set!"
    )


@datasets.command(name="list")
@click.option("--sort-by", default="name", help="Column to sort by (name, row_count, column_count, profiled_on).")
def list_datasets(sort_by: str) -> None:
    """List all profiled datasets."""

    connection = db_utils.get_db_connection()
    try:
        cursor = connection.cursor()
        try:
            cursor.execute(
                "SELECT dataset_id, name, profiled_on, row_count, column_count FROM datasets"
            )
            datasets = cursor.fetchall()
        finally:
            cursor.close()
    finally:
        connection.close()

    if not datasets:
        click.echo("No datasets found.")
        return

    column_map = {
        "name": 1,
        "profiled_on": 2,
        "row_count": 3,
        "column_count": 4,
    }

    key_index = column_map.get(sort_by)
    if key_index is None:
        raise click.ClickException(
            "Invalid sort column. Choose from name, profiled_on, row_count, column_count."
        )

    sorted_data = merge_sort(datasets, key_index=key_index)
    for row in sorted_data:
        click.echo(row)


@datasets.command(name="find")
@click.argument("name")
def find_dataset(name: str) -> None:
    """Find a dataset by exact name."""

    connection = db_utils.get_db_connection()
    try:
        cursor = connection.cursor()
        try:
            cursor.execute(
                "SELECT dataset_id, name, profiled_on, row_count, column_count FROM datasets ORDER BY name"
            )
            datasets = cursor.fetchall()
        finally:
            cursor.close()
    finally:
        connection.close()

    if not datasets:
        click.echo("No datasets found.")
        return

    index = binary_search(datasets, name, key_index=1)
    if index == -1:
        click.echo("Dataset not found.")
    else:
        click.echo(datasets[index])


if __name__ == "__main__":
    cli()

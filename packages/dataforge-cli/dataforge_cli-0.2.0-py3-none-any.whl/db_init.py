from pathlib import Path

import mysql.connector

from db import get_db_config, get_db_connection


def _execute_sql_script(cursor: mysql.connector.cursor.MySQLCursor, sql: str) -> None:
	"""Execute each statement in the provided SQL script sequentially."""

	statements = [statement.strip() for statement in sql.split(";")]
	for statement in statements:
		if statement:
			cursor.execute(statement)


def initialize_schema() -> None:
	schema_path = Path(__file__).with_name("schema.sql")
	schema_sql = schema_path.read_text(encoding="utf-8")

	config = get_db_config(include_database=False)
	connection = mysql.connector.connect(**config)
	try:
		cursor = connection.cursor()
		try:
			# Execute schema statements sequentially to set up the database.
			_execute_sql_script(cursor, schema_sql)
		finally:
			cursor.close()
		connection.commit()
	finally:
		connection.close()

	# Sanity check: ensure the new database is reachable.
	connection = get_db_connection()
	try:
		connection.ping(reconnect=True, attempts=1, delay=0)
	finally:
		connection.close()


if __name__ == "__main__":
	initialize_schema()

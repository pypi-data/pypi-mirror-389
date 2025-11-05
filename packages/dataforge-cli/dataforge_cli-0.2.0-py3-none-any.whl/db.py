import os
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path.home() / ".dataforge.env")


def _env_value(*keys: str, default: str | None = None) -> str | None:
	"""Return the first non-empty environment variable from the provided keys."""

	for key in keys:
		value = os.environ.get(key)
		if value:
			return value
	return default


def get_db_config(include_database: bool = True) -> dict:
	"""Build the connection parameters from environment variables."""

	config = {
		"host": _env_value("DATAFORGE_DB_HOST", "DB_HOST", default="localhost"),
		"user": _env_value("DATAFORGE_DB_USER", "DB_USER", default="root"),
		"password": _env_value("DATAFORGE_DB_PASSWORD", "DB_PASSWORD", default=""),
	}
	if include_database:
		config["database"] = _env_value("DATAFORGE_DB_NAME", "DB_NAME", default="dataforge")
	return config


def get_db_connection() -> mysql.connector.MySQLConnection:
	"""Return a connection to the dataforge database."""

	return mysql.connector.connect(**get_db_config(include_database=True))

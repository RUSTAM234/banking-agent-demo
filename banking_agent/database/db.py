import sqlite3
import logging
from contextlib import contextmanager

from banking_agent.config import DATABASE_PATH

LOGGER = logging.getLogger(__name__)


@contextmanager
def get_connection():
    LOGGER.info("Database connection opened | path=%s", DATABASE_PATH)
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except sqlite3.Error:
        connection.rollback()
        raise
    finally:
        connection.close()
        LOGGER.info("Database connection closed")


def initialize_database() -> None:
    LOGGER.info("DATABASE initialize | schema=database/schema.sql")
    schema = (DATABASE_PATH.parent.parent / "database" / "schema.sql").read_text(
        encoding="utf-8"
    )
    with get_connection() as connection:
        connection.executescript(schema)


def database_is_empty() -> bool:
    initialize_database()
    with get_connection() as connection:
        row = connection.execute("SELECT COUNT(*) AS count FROM customers").fetchone()
        is_empty = row["count"] == 0
        LOGGER.info("DATABASE customer count=%s | empty=%s", row["count"], is_empty)
        return is_empty

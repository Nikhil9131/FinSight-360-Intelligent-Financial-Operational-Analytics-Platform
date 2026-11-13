"""
FinSight 360 - Database Connector & Query Execution Engine
===========================================================
Provides unified connection interfaces for analytics:
  - PostgreSQL (via psycopg2 / SQLAlchemy when available in production)
  - SQLite (built-in standard library fallback for zero-dependency local environments)
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any
import pandas as pd

from config.settings import get_settings
from src.utils.logger import get_logger

logger = get_logger("db_connector")


def get_sqlite_path() -> Path:
    """Return path to local analytical database."""
    settings = get_settings()
    db_path = settings.DATA_PROCESSED_DIR / "finsight360.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


@contextmanager
def get_connection(autocommit: bool = False):
    """
    Yields an active database connection.
    Attempts PostgreSQL if configured, otherwise falls back smoothly to SQLite.
    """
    settings = get_settings()
    conn = None
    use_sqlite = True

    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        conn = psycopg2.connect(**settings.DSN)
        conn.autocommit = autocommit
        use_sqlite = False
        logger.debug("Connected to PostgreSQL")
    except Exception as e:
        logger.debug("PostgreSQL not active ({}); falling back to local SQLite engine", e)
        use_sqlite = True

    if use_sqlite:
        conn = sqlite3.connect(get_sqlite_path())
        conn.row_factory = sqlite3.Row

    try:
        yield conn
        if not autocommit:
            conn.commit()
    except Exception as err:
        if conn and not autocommit:
            conn.rollback()
        logger.error("DB Transaction error: {}", err)
        raise
    finally:
        if conn:
            conn.close()


def execute_query(query: str, params: tuple | None = None, fetch: bool = True) -> list[dict[str, Any]]:
    """Execute SQL query and return results as list of dictionaries."""
    with get_connection() as conn:
        cur = conn.cursor()
        if params:
            cur.execute(query, params)
        else:
            cur.execute(query)

        if fetch and cur.description:
            cols = [col[0] for col in cur.description]
            rows = cur.fetchall()
            return [dict(zip(cols, row)) for row in rows]
        return []


def query_to_dataframe(query: str, params: tuple | None = None) -> pd.DataFrame:
    """Execute query and return clean Pandas DataFrame."""
    with get_connection() as conn:
        return pd.read_sql_query(query, conn, params=params)


def test_connection() -> bool:
    """Validate database connectivity."""
    try:
        res = execute_query("SELECT 1 AS status")
        return len(res) > 0 and res[0]["status"] == 1
    except Exception as e:
        logger.warning("Connection test failed: {}", e)
        return False

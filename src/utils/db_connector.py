"""
FinSight 360 - Database Connector
====================================
Provides reusable functions to connect to PostgreSQL using both:
  - psycopg2  (for raw SQL execution, stored procedures)
  - SQLAlchemy (for Pandas integration, ORM-style operations)

Usage:
    from src.utils.db_connector import get_engine, get_connection, execute_query

    # Pandas integration
    engine = get_engine()
    df = pd.read_sql("SELECT * FROM sales", engine)

    # Raw SQL
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM sales")
            count = cur.fetchone()[0]
"""

from contextlib import contextmanager
from typing import Any

import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from config.settings import get_settings
from src.utils.logger import get_logger

logger = get_logger("db_connector")


# ─── SQLAlchemy Engine (singleton) ────────────────────────────

_engine: Engine | None = None


def get_engine(echo: bool = False) -> Engine:
    """
    Create or return a cached SQLAlchemy engine.

    Args:
        echo: If True, log all SQL statements (useful for debugging).

    Returns:
        SQLAlchemy Engine connected to the configured PostgreSQL database.
    """
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(
            settings.DATABASE_URL,
            echo=echo,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,  # verify connections before use
        )
        logger.info("SQLAlchemy engine created for {}", settings.DB_NAME)
    return _engine


def dispose_engine() -> None:
    """Close all pooled connections and reset the engine singleton."""
    global _engine
    if _engine is not None:
        _engine.dispose()
        _engine = None
        logger.info("SQLAlchemy engine disposed")


# ─── psycopg2 Connection ─────────────────────────────────────

@contextmanager
def get_connection(autocommit: bool = False):
    """
    Context manager that yields a psycopg2 connection.
    Automatically commits on success, rolls back on exception, and closes.

    Args:
        autocommit: Set True for DDL statements (CREATE TABLE, etc.)

    Yields:
        psycopg2 connection object.

    Example:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO ...")
    """
    settings = get_settings()
    conn = None
    try:
        conn = psycopg2.connect(**settings.DSN)
        conn.autocommit = autocommit
        logger.debug("Database connection opened (autocommit={})", autocommit)
        yield conn
        if not autocommit:
            conn.commit()
    except Exception as e:
        if conn and not autocommit:
            conn.rollback()
        logger.error("Database error: {}", e)
        raise
    finally:
        if conn:
            conn.close()
            logger.debug("Database connection closed")


# ─── Convenience Helpers ──────────────────────────────────────

def execute_query(query: str, params: tuple | None = None, fetch: bool = True) -> list[dict[str, Any]]:
    """
    Execute a SQL query and optionally return results as a list of dicts.

    Args:
        query:  SQL query string (can use %s placeholders).
        params: Tuple of parameters for parameterized queries.
        fetch:  If True, return results. If False, return empty list (for INSERT/UPDATE).

    Returns:
        List of dictionaries (column_name → value) for SELECT queries,
        or empty list for INSERT/UPDATE/DELETE.
    """
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            if fetch and cur.description:
                results = [dict(row) for row in cur.fetchall()]
                logger.debug("Query returned {} rows", len(results))
                return results
            return []


def execute_script(filepath: str) -> None:
    """
    Execute an entire SQL script file against the database.

    Args:
        filepath: Path to the .sql file to execute.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        sql = f.read()

    with get_connection(autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
    logger.info("Executed SQL script: {}", filepath)


def test_connection() -> bool:
    """
    Test if the database connection is working.

    Returns:
        True if connection succeeds, False otherwise.
    """
    try:
        result = execute_query("SELECT version();")
        version = result[0]["version"] if result else "unknown"
        logger.info("Connection successful — PostgreSQL {}", version)
        return True
    except Exception as e:
        logger.error("Connection failed: {}", e)
        return False


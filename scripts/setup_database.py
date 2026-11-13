"""
FinSight 360 - Database Setup Script
=====================================
Initializes the PostgreSQL database by executing the schema SQL files
in order. Run this once after setting up PostgreSQL.

Usage:
    python scripts/setup_database.py
    python scripts/setup_database.py --reset   (drops and recreates all tables)
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import get_settings
from src.utils.logger import get_logger
from src.utils.db_connector import get_connection, execute_script, test_connection

logger = get_logger("setup_database")


# SQL files to execute in order
SCHEMA_DIR = PROJECT_ROOT / "database" / "schema"
SCHEMA_FILES = [
    "001_create_tables.sql",
    "002_create_dim_date.sql",
    "003_create_analytical_views.sql",
]


def drop_all_tables():
    """Drop all tables (for --reset mode). USE WITH CAUTION."""
    drop_sql = """
    DROP VIEW IF EXISTS
        vw_budget_variance,
        vw_monthly_financial_summary,
        fact_operations,
        fact_budget,
        fact_expenses,
        fact_sales,
        dim_product,
        dim_customer,
        dim_employee,
        dim_department
    CASCADE;

    DROP TABLE IF EXISTS
        data_quality_results,
        pipeline_logs,
        operational_performance,
        transactions,
        budgets,
        expenses,
        sales,
        products,
        customers,
        employees,
        departments,
        dim_date
    CASCADE;
    """
    with get_connection(autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(drop_sql)
    logger.warning("All tables and views dropped")


def setup_database(reset: bool = False):
    """
    Run all schema SQL files to set up the database.

    Args:
        reset: If True, drops everything first, then recreates.
    """
    settings = get_settings()
    logger.info("=" * 60)
    logger.info("FinSight 360 - Database Setup")
    logger.info("=" * 60)
    logger.info("Database: {} @ {}:{}", settings.DB_NAME, settings.DB_HOST, settings.DB_PORT)

    # Step 1: Test connection
    logger.info("Testing database connection...")
    if not test_connection():
        logger.error("Cannot connect to database. Check your .env configuration.")
        logger.error("Make sure PostgreSQL is running and the database '{}' exists.", settings.DB_NAME)
        sys.exit(1)

    # Step 2: Optionally reset
    if reset:
        logger.warning("RESET mode: dropping all existing tables and views...")
        drop_all_tables()

    # Step 3: Execute schema files in order
    for filename in SCHEMA_FILES:
        filepath = SCHEMA_DIR / filename
        if not filepath.exists():
            logger.error("Schema file not found: {}", filepath)
            sys.exit(1)

        logger.info("Executing: {}", filename)
        try:
            execute_script(str(filepath))
            logger.info("  ✓ {} completed successfully", filename)
        except Exception as e:
            logger.error("  ✗ {} failed: {}", filename, e)
            sys.exit(1)

    # Step 4: Verify tables created
    logger.info("Verifying table creation...")
    verify_sql = """
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
    ORDER BY table_name;
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(verify_sql)
            tables = [row[0] for row in cur.fetchall()]

    logger.info("Tables and views in database:")
    for t in tables:
        logger.info("  → {}", t)

    expected_tables = [
        "departments", "employees", "customers", "products",
        "sales", "expenses", "budgets", "transactions",
        "operational_performance", "pipeline_logs",
        "data_quality_results", "dim_date",
    ]
    missing = [t for t in expected_tables if t not in tables]
    if missing:
        logger.error("Missing tables: {}", missing)
        sys.exit(1)

    # Step 5: Verify dim_date populated
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM dim_date;")
            date_count = cur.fetchone()[0]
    logger.info("dim_date rows: {} (expected ~2192)", date_count)

    logger.info("=" * 60)
    logger.info("Database setup completed successfully! ✓")
    logger.info("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FinSight 360 - Database Setup")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop all tables and recreate from scratch"
    )
    args = parser.parse_args()
    setup_database(reset=args.reset)


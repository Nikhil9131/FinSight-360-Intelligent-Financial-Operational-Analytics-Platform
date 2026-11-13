"""
FinSight 360 - Master ETL Pipeline Orchestrator
===============================================
Coordinates the complete lifecycle:
  1. Ingestion: Reads CSV/JSON datasets from synthetic or raw directories
  2. Cleaning: Deduplicates, standardizes dates, imputes missing fields
  3. Validation: Runs 6-dimensional Data Quality assertions
  4. Transformation: Computes fact & dimension derivations
  5. Loading: Loads cleaned records into analytical database (PostgreSQL / SQLite)
  6. Audit: Writes execution logs to `pipeline_logs` and `data_quality_results`

Usage:
    python src/transformation/etl_pipeline.py
"""

import sys
import uuid
import time
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import get_settings
from src.utils.logger import get_logger
from src.utils.db_connector import get_sqlite_path
from src.ingestion.file_reader import DataIngestionEngine
from src.cleaning.cleaner import DataCleaner
from src.validation.validator import DataQualityValidator

logger = get_logger("etl_pipeline")


class FinSightETLPipeline:
    """End-to-End Enterprise ETL Pipeline for NovaTech Solutions."""

    def __init__(self, data_source_dir: Path | None = None):
        self.settings = get_settings()
        self.data_dir = data_source_dir or self.settings.DATA_SYNTHETIC_DIR
        self.run_id = f"RUN-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
        self.ingestion = DataIngestionEngine()
        self.validator = DataQualityValidator(run_id=self.run_id)
        self.cleaned_datasets: dict[str, pd.DataFrame] = {}

    def run_pipeline(self) -> dict[str, Any]:
        """Execute the complete end-to-end ETL process."""
        start_time = time.time()
        logger.info("=" * 60)
        logger.info("FINSIGHT 360 - STARTING ETL PIPELINE EXECUTION")
        logger.info("Run ID: {}", self.run_id)
        logger.info("Source Directory: {}", self.data_dir)
        logger.info("=" * 60)

        pipeline_summary = {
            "run_id": self.run_id,
            "status": "started",
            "start_time": datetime.now().isoformat(),
            "tables_processed": 0,
            "records_loaded": 0,
            "dq_checks_count": 0,
            "dq_passed_count": 0,
        }

        try:
            # ──────────────── STEP 1: INGESTION ────────────────
            logger.info(">>> STEP 1: INGESTION")
            raw_datasets = self._ingest_all()

            # ──────────────── STEP 2: CLEANING ────────────────
            logger.info(">>> STEP 2: DATA CLEANING & STANDARDIZATION")
            self._clean_all(raw_datasets)

            # ──────────────── STEP 3: VALIDATION ────────────────
            logger.info(">>> STEP 3: DATA QUALITY VALIDATION")
            dq_df = self._validate_all()
            pipeline_summary["dq_checks_count"] = len(dq_df)
            pipeline_summary["dq_passed_count"] = int(dq_df["passed"].sum())

            # ──────────────── STEP 4: DATABASE LOADING ────────────────
            logger.info(">>> STEP 4: DATABASE LOADING & STAGING")
            records_loaded = self._load_to_database()
            pipeline_summary["records_loaded"] = records_loaded
            pipeline_summary["tables_processed"] = len(self.cleaned_datasets)

            # ──────────────── STEP 5: AUDIT LOGGING ────────────────
            elapsed = time.time() - start_time
            pipeline_summary["status"] = "success"
            pipeline_summary["end_time"] = datetime.now().isoformat()
            pipeline_summary["duration_seconds"] = round(elapsed, 2)

            self._save_pipeline_audit(pipeline_summary, dq_df)

            logger.info("=" * 60)
            logger.info("ETL PIPELINE COMPLETED SUCCESSFULLY IN {:.2f}s", elapsed)
            logger.info("Records loaded: {:,} across {} tables", records_loaded, len(self.cleaned_datasets))
            logger.info("Data Quality Score: {}/{} passed ({:.1%})",
                        pipeline_summary["dq_passed_count"],
                        pipeline_summary["dq_checks_count"],
                        pipeline_summary["dq_passed_count"] / max(1, pipeline_summary["dq_checks_count"]))
            logger.info("=" * 60)
            return pipeline_summary

        except Exception as e:
            logger.error("ETL PIPELINE FAILED: {}", e, exc_info=True)
            pipeline_summary["status"] = "failed"
            pipeline_summary["error_message"] = str(e)
            pipeline_summary["end_time"] = datetime.now().isoformat()
            pipeline_summary["duration_seconds"] = round(time.time() - start_time, 2)
            return pipeline_summary

    def _ingest_all(self) -> dict[str, pd.DataFrame]:
        """Ingest all synthetic/raw files."""
        tables = [
            "departments", "employees", "customers", "products",
            "sales", "expenses", "budgets", "transactions", "operational_performance"
        ]
        raw = {}
        for tbl in tables:
            csv_path = self.data_dir / f"{tbl}.csv"
            if not csv_path.exists():
                raise FileNotFoundError(f"Missing required dataset: {csv_path}")
            raw[tbl] = self.ingestion.ingest_csv(csv_path)
            logger.info("  Ingested {}: {:,} rows", tbl, len(raw[tbl]))
        return raw

    def _clean_all(self, raw: dict[str, pd.DataFrame]) -> None:
        """Execute cleaning rules for each dataset."""
        # 1. Clean Reference Tables
        depts_df, _ = DataCleaner.deduplicate(raw["departments"], subset=["department_id"])
        self.cleaned_datasets["departments"] = depts_df

        emps_df, _ = DataCleaner.deduplicate(raw["employees"], subset=["employee_id"])
        emps_df = DataCleaner.standardize_dates(emps_df, ["hire_date", "termination_date"])
        self.cleaned_datasets["employees"] = emps_df

        cust_df, _ = DataCleaner.deduplicate(raw["customers"], subset=["customer_id"])
        cust_df = DataCleaner.standardize_dates(cust_df, ["registration_date"])
        cust_df = DataCleaner.handle_missing_values(cust_df, {
            "city": "Unknown", "phone": "N/A", "email": "info@customer.com"
        })
        self.cleaned_datasets["customers"] = cust_df

        prods_df, _ = DataCleaner.deduplicate(raw["products"], subset=["product_id"])
        self.cleaned_datasets["products"] = prods_df

        # 2. Clean Fact Tables
        sales_clean, _ = DataCleaner.clean_sales(raw["sales"])
        self.cleaned_datasets["sales"] = sales_clean

        expenses_clean, _ = DataCleaner.clean_expenses(raw["expenses"])
        self.cleaned_datasets["expenses"] = expenses_clean

        budgets_clean, _ = DataCleaner.deduplicate(raw["budgets"], subset=["budget_id"])
        budgets_clean = DataCleaner.standardize_dates(budgets_clean, ["approved_date"])
        self.cleaned_datasets["budgets"] = budgets_clean

        txns_clean, _ = DataCleaner.deduplicate(raw["transactions"], subset=["transaction_id"])
        txns_clean = DataCleaner.standardize_dates(txns_clean, ["transaction_date"])
        self.cleaned_datasets["transactions"] = txns_clean

        ops_clean, _ = DataCleaner.deduplicate(raw["operational_performance"], subset=["record_id"])
        self.cleaned_datasets["operational_performance"] = ops_clean

        # Save cleaned versions to data/processed
        processed_dir = self.settings.DATA_PROCESSED_DIR
        processed_dir.mkdir(parents=True, exist_ok=True)
        for tbl, df in self.cleaned_datasets.items():
            df.to_csv(processed_dir / f"{tbl}_cleaned.csv", index=False)

    def _validate_all(self) -> pd.DataFrame:
        """Run enterprise data quality checks across cleaned datasets."""
        v = self.validator
        depts = self.cleaned_datasets["departments"]
        emps = self.cleaned_datasets["employees"]
        cust = self.cleaned_datasets["customers"]
        prods = self.cleaned_datasets["products"]
        sales = self.cleaned_datasets["sales"]
        expenses = self.cleaned_datasets["expenses"]
        budgets = self.cleaned_datasets["budgets"]

        # Completeness Checks
        v.check_completeness(sales, "sales", "total_amount", max_null_pct=0.0)
        v.check_completeness(expenses, "expenses", "amount", max_null_pct=0.0)
        v.check_completeness(emps, "employees", "salary", max_null_pct=0.0)

        # Uniqueness Checks
        v.check_uniqueness(sales, "sales", "sale_id")
        v.check_uniqueness(expenses, "expenses", "expense_id")
        v.check_uniqueness(cust, "customers", "customer_id")
        v.check_uniqueness(emps, "employees", "employee_id")

        # Range Checks
        v.check_range(sales, "sales", "quantity", min_val=1)
        v.check_range(sales, "sales", "discount_pct", min_val=0.0, max_val=100.0)
        v.check_range(expenses, "expenses", "amount", min_val=0.01)

        # Referential Integrity Checks
        v.check_foreign_key(sales, cust, "sales", "customer_id", "customer_id")
        v.check_foreign_key(sales, emps, "sales", "employee_id", "employee_id")
        v.check_foreign_key(sales, prods, "sales", "product_id", "product_id")
        v.check_foreign_key(expenses, depts, "expenses", "department_id", "department_id")
        v.check_foreign_key(budgets, depts, "budgets", "department_id", "department_id")

        # Statistical Outliers (Informational)
        v.detect_outliers_zscore(sales, "sales", "total_amount", z_threshold=4.0)
        v.detect_outliers_zscore(expenses, "expenses", "amount", z_threshold=4.0)

        return v.get_results_dataframe()

    def _load_to_database(self) -> int:
        """Load datasets into local SQLite database for maximum portability and zero-lock execution."""
        total_rows = 0
        sqlite_path = get_sqlite_path()
        logger.info("Loading cleaned tables into database: {}", sqlite_path)

        with sqlite3.connect(sqlite_path) as conn:
            load_order = [
                "departments", "employees", "customers", "products",
                "sales", "expenses", "budgets", "transactions", "operational_performance"
            ]

            for tbl in load_order:
                df = self.cleaned_datasets[tbl]
                df.to_sql(tbl, con=conn, if_exists="replace", index=False)
                total_rows += len(df)
                logger.info("  Loaded {}: {:,} rows into table", tbl, len(df))

        return total_rows

    def _save_pipeline_audit(self, summary: dict[str, Any], dq_df: pd.DataFrame) -> None:
        """Save execution summaries and quality metrics."""
        summary_path = self.settings.LOG_DIR / f"pipeline_run_{self.run_id}.json"
        import json
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        dq_path = self.settings.DATA_PROCESSED_DIR / f"data_quality_report_{self.run_id}.csv"
        dq_df.to_csv(dq_path, index=False)
        logger.info("Saved pipeline run metadata to: {}", summary_path.name)
        logger.info("Saved data quality report to: {}", dq_path.name)


if __name__ == "__main__":
    pipeline = FinSightETLPipeline()
    result = pipeline.run_pipeline()
    print(f"\nETL Execution Result: {result['status'].upper()} (Loaded {result.get('records_loaded', 0):,} records)")

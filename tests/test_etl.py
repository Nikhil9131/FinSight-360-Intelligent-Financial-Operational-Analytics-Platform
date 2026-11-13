"""
FinSight 360 - Tests for ETL Components
=======================================
Validates the file reader, data cleaning steps, and quality validator.
"""

import sys
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion.file_reader import DataIngestionEngine
from src.cleaning.cleaner import DataCleaner
from src.validation.validator import DataQualityValidator


def test_ingestion_engine(tmp_path):
    csv_file = tmp_path / "sample.csv"
    pd.DataFrame({"id": [1, 2], "val": ["A", "B"]}).to_csv(csv_file, index=False)

    engine = DataIngestionEngine()
    df = engine.ingest_csv(csv_file)
    assert len(df) == 2
    assert "id" in df.columns

    summary = engine.get_audit_summary()
    assert len(summary) == 1
    assert summary.iloc[0]["source"] == "sample.csv"


def test_cleaner_deduplicate():
    df = pd.DataFrame({"id": [1, 1, 2], "val": ["A", "A", "B"]})
    clean_df, dropped = DataCleaner.deduplicate(df, subset=["id"])
    assert len(clean_df) == 2
    assert dropped == 1


def test_cleaner_standardize_dates():
    df = pd.DataFrame({"date_col": ["2024/01/15", "15-02-2024", "invalid"]})
    res = DataCleaner.standardize_dates(df, ["date_col"])
    assert res["date_col"].iloc[0] == "2024-01-15"


def test_validator_completeness_and_uniqueness():
    val = DataQualityValidator(run_id="TEST-RUN")
    df = pd.DataFrame({"id": [1, 2, 3], "amount": [10.0, None, 30.0]})

    pass_comp = val.check_completeness(df, "tbl", "amount", max_null_pct=0.50)
    fail_comp = val.check_completeness(df, "tbl", "amount", max_null_pct=0.10)
    assert pass_comp is True
    assert fail_comp is False

    pass_unique = val.check_uniqueness(df, "tbl", "id")
    assert pass_unique is True


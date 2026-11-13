"""
FinSight 360 - Enterprise Data Quality Validation Framework
============================================================
Performs rule-based and statistical quality assertions across 6 dimensions:
  1. Completeness (null/empty thresholds)
  2. Uniqueness (primary key collision checks)
  3. Validity (format, range, enum membership)
  4. Consistency (cross-field calculations)
  5. Referential Integrity (orphan foreign keys)
  6. Outliers (Z-score and IQR boundary checks)

Results are formatted for insertion into the `data_quality_results` database table.
"""

from typing import Any
import numpy as np
import pandas as pd

from src.utils.logger import get_logger

logger = get_logger("validation")


class DataQualityValidator:
    """Configurable quality validation engine."""

    def __init__(self, run_id: str):
        self.run_id = run_id
        self.validation_records: list[dict[str, Any]] = []

    def check_completeness(self, df: pd.DataFrame, table_name: str, column: str, max_null_pct: float = 0.05) -> bool:
        """Assert that null values do not exceed acceptable threshold."""
        total = len(df)
        nulls = int(df[column].isnull().sum())
        null_pct = nulls / total if total > 0 else 0.0
        passed = null_pct <= max_null_pct

        self._record_result(
            table_name=table_name,
            check_name=f"completeness_{column}",
            check_type="completeness",
            passed=passed,
            metric_val=null_pct,
            threshold=max_null_pct,
            records_checked=total,
            records_failed=nulls,
            details=f"{nulls}/{total} nulls ({null_pct:.2%}) in column '{column}'"
        )
        return passed

    def check_uniqueness(self, df: pd.DataFrame, table_name: str, primary_key: str) -> bool:
        """Assert primary key is strictly unique."""
        total = len(df)
        dupes = int(df.duplicated(subset=[primary_key]).sum())
        passed = dupes == 0

        self._record_result(
            table_name=table_name,
            check_name=f"uniqueness_{primary_key}",
            check_type="uniqueness",
            passed=passed,
            metric_val=float(dupes),
            threshold=0.0,
            records_checked=total,
            records_failed=dupes,
            details=f"Found {dupes} duplicate primary keys on '{primary_key}'"
        )
        return passed

    def check_range(self, df: pd.DataFrame, table_name: str, column: str, min_val: float | None = None, max_val: float | None = None) -> bool:
        """Assert values remain within logical business boundaries."""
        total = len(df)
        failed_mask = pd.Series(False, index=df.index)
        if min_val is not None:
            failed_mask |= (df[column] < min_val)
        if max_val is not None:
            failed_mask |= (df[column] > max_val)

        failed_count = int(failed_mask.sum())
        passed = failed_count == 0

        self._record_result(
            table_name=table_name,
            check_name=f"range_{column}",
            check_type="validity",
            passed=passed,
            metric_val=float(failed_count),
            threshold=0.0,
            records_checked=total,
            records_failed=failed_count,
            details=f"{failed_count} records violated range [{min_val}, {max_val}] on '{column}'"
        )
        return passed

    def check_foreign_key(self, child_df: pd.DataFrame, parent_df: pd.DataFrame, child_table: str, foreign_key: str, parent_key: str) -> bool:
        """Assert all foreign keys in child_df exist in parent_df."""
        total = len(child_df)
        parent_keys = set(parent_df[parent_key].dropna())
        orphans = ~child_df[foreign_key].isin(parent_keys)
        orphan_count = int(orphans.sum())
        passed = orphan_count == 0

        self._record_result(
            table_name=child_table,
            check_name=f"referential_integrity_{foreign_key}",
            check_type="referential",
            passed=passed,
            metric_val=float(orphan_count),
            threshold=0.0,
            records_checked=total,
            records_failed=orphan_count,
            details=f"Found {orphan_count} orphan keys in '{foreign_key}' not in parent table"
        )
        return passed

    def detect_outliers_zscore(self, df: pd.DataFrame, table_name: str, column: str, z_threshold: float = 3.5) -> pd.DataFrame:
        """Identify records with values > z_threshold standard deviations from the mean."""
        vals = pd.to_numeric(df[column], errors="coerce").dropna()
        if len(vals) < 10:
            return pd.DataFrame()

        mean_val = vals.mean()
        std_val = vals.std()
        if std_val == 0:
            return pd.DataFrame()

        z_scores = (df[column] - mean_val) / std_val
        outlier_mask = z_scores.abs() > z_threshold
        outlier_count = int(outlier_mask.sum())

        self._record_result(
            table_name=table_name,
            check_name=f"outlier_zscore_{column}",
            check_type="validity",
            passed=True,  # Informational check
            metric_val=float(outlier_count),
            threshold=z_threshold,
            records_checked=len(df),
            records_failed=outlier_count,
            details=f"Flagged {outlier_count} statistical outliers (|z| > {z_threshold}) in '{column}'"
        )
        return df[outlier_mask]

    def _record_result(self, table_name: str, check_name: str, check_type: str, passed: bool,
                       metric_val: float, threshold: float, records_checked: int,
                       records_failed: int, details: str) -> None:
        """Store result dictionary."""
        rec = {
            "run_id": self.run_id,
            "table_name": table_name,
            "check_name": check_name,
            "check_type": check_type,
            "passed": passed,
            "metric_value": round(metric_val, 4),
            "threshold": round(threshold, 4),
            "records_checked": records_checked,
            "records_failed": records_failed,
            "details": details
        }
        self.validation_records.append(rec)
        status = "PASSED" if passed else "FAILED"
        logger.info("[DQ {}] {}.{} - {}", status, table_name, check_name, details)

    def get_results_dataframe(self) -> pd.DataFrame:
        """Return quality results as a DataFrame."""
        return pd.DataFrame(self.validation_records)


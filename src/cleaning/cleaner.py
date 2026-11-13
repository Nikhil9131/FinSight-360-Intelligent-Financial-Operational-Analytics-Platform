"""
FinSight 360 - Data Cleaning Engine
====================================
Cleans and standardizes raw business data:
  1. Deduplication (exact and primary key based)
  2. Missing value handling (imputation and smart defaults)
  3. Date format standardization to ISO 8601 (YYYY-MM-DD)
  4. Categorical normalization (case trimming, known vocabulary mapping)
  5. Numeric parsing and monetary boundary validation
"""

from typing import Any
import numpy as np
import pandas as pd

from src.utils.logger import get_logger

logger = get_logger("cleaning")


class DataCleaner:
    """Enterprise-grade data cleaning transformation pipeline."""

    @staticmethod
    def deduplicate(df: pd.DataFrame, subset: list[str] | None = None, keep: str = "first") -> tuple[pd.DataFrame, int]:
        """Remove duplicate records and report count of pruned rows."""
        initial_count = len(df)
        cleaned_df = df.drop_duplicates(subset=subset, keep=keep)
        dropped_count = initial_count - len(cleaned_df)
        if dropped_count > 0:
            logger.info("Removed {} duplicate records (subset: {})", dropped_count, subset)
        return cleaned_df.reset_index(drop=True), dropped_count

    @staticmethod
    def standardize_dates(df: pd.DataFrame, date_columns: list[str]) -> pd.DataFrame:
        """Parse various date string formats and cast to standard ISO 8601 YYYY-MM-DD."""
        df = df.copy()
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%d")
                logger.debug("Standardized date column '{}'", col)
        return df

    @staticmethod
    def normalize_categories(df: pd.DataFrame, column_mappings: dict[str, dict[str, str]]) -> pd.DataFrame:
        """
        Normalize text categories (trim whitespace, title-case, and map synonyms).
        Example mapping: {'region': {'NA': 'North America', 'US': 'North America'}}
        """
        df = df.copy()
        for col, mapping in column_mappings.items():
            if col in df.columns:
                # Strip and clean
                df[col] = df[col].astype(str).str.strip()
                df[col] = df[col].replace(mapping)
                logger.debug("Normalized categories in column '{}'", col)
        return df

    @staticmethod
    def handle_missing_values(df: pd.DataFrame, fill_rules: dict[str, Any]) -> pd.DataFrame:
        """
        Impute missing values using domain-specific fallback rules.
        Example fill_rules: {'payment_method': 'Bank Transfer', 'discount_pct': 0.0}
        """
        df = df.copy()
        for col, default_val in fill_rules.items():
            if col in df.columns:
                null_count = df[col].isnull().sum()
                if null_count > 0:
                    df[col] = df[col].fillna(default_val)
                    logger.info("Imputed {} missing values in '{}' with '{}'", null_count, col, default_val)
        return df

    @classmethod
    def clean_sales(cls, df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
        """Domain-specific cleaning pipeline for Sales dataset."""
        logger.info("Executing Sales cleaning workflow...")
        stats = {}
        
        # 1. Deduplication on sale_id
        df, dupes = cls.deduplicate(df, subset=["sale_id"])
        stats["sales_duplicates_removed"] = dupes

        # 2. Date standardization
        df = cls.standardize_dates(df, ["sale_date"])

        # 3. Impute missing values
        df = cls.handle_missing_values(df, {
            "payment_method": "Bank Transfer",
            "discount_pct": 0.0,
            "region": "North America"
        })

        # 4. Numeric integrity checks
        df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(1).astype(int)
        df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce").fillna(0.0)
        df["discount_pct"] = pd.to_numeric(df["discount_pct"], errors="coerce").clip(0.0, 100.0)
        
        # Recalculate total_amount for mathematical consistency
        computed_total = np.round(df["quantity"] * df["unit_price"] * (1 - df["discount_pct"] / 100.0), 2)
        discrepancies = (df["total_amount"] - computed_total).abs() > 0.05
        if discrepancies.sum() > 0:
            logger.warning("Corrected {} inconsistent calculated total_amount records in sales", discrepancies.sum())
            df.loc[discrepancies, "total_amount"] = computed_total[discrepancies]
        stats["sales_recalculated"] = int(discrepancies.sum())

        return df, stats

    @classmethod
    def clean_expenses(cls, df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
        """Domain-specific cleaning pipeline for Expenses dataset."""
        logger.info("Executing Expenses cleaning workflow...")
        stats = {}

        # 1. Deduplication
        df, dupes = cls.deduplicate(df, subset=["expense_id"])
        stats["expenses_duplicates_removed"] = dupes

        # 2. Date standardization
        df = cls.standardize_dates(df, ["expense_date"])

        # 3. Impute missing values
        df = cls.handle_missing_values(df, {
            "vendor": "Generic Vendor",
            "payment_method": "Credit Card",
            "approval_status": "approved",
            "receipt_number": "N/A"
        })

        # 4. Enforce positive amount
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0).abs()
        df["amount"] = df["amount"].round(2)

        return df, stats


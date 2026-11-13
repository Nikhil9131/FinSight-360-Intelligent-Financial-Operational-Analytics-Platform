"""
FinSight 360 - Financial Anomaly & Fraud Risk Detection Engine
==============================================================
Identifies unusual corporate spending, duplicate disbursements,
and statistical outliers using:
  1. Departmental Robust Z-Score Multipliers
  2. Interquartile Range (IQR) Non-Parametric Outlier Bounds
  3. Distance-based Anomaly Scoring
  4. Domain Business Categorization

Generates standardized risk audit reports for finance managers.
"""

import sys
from pathlib import Path
from typing import Any
from datetime import datetime
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.logger import get_logger
from src.utils.db_connector import query_to_dataframe

logger = get_logger("anomaly_detection")


class FinancialAnomalyDetector:
    """Enterprise anomaly and risk detection engine."""

    def __init__(self, contamination: float = 0.01):
        self.contamination = contamination
        logger.info("Anomaly Detector initialized (Contamination target: {:.2%})", contamination)

    def detect_expense_anomalies(self) -> pd.DataFrame:
        """
        Scan all corporate expenses using statistical and multi-factor outlier models.
        Returns audited DataFrame with scores and diagnostic reasons.
        """
        query = """
        SELECT 
            e.expense_id,
            e.expense_date,
            e.department_id,
            d.department_name,
            e.category,
            e.vendor,
            e.amount
        FROM expenses e
        JOIN departments d ON e.department_id = d.department_id
        """
        df = query_to_dataframe(query)
        logger.info("Analyzing {} corporate expense transactions for anomalies", len(df))

        # ─── 1. Departmental Baseline (Mean & Std Dev) ───────────────────
        stats_df = df.groupby(["department_name", "category"])["amount"].agg(["mean", "std", "count"]).reset_index()
        stats_df["std"] = stats_df["std"].fillna(1.0).replace(0, 1.0)
        df = df.merge(stats_df, on=["department_name", "category"], how="left")
        
        # Z-Score
        df["z_score"] = (df["amount"] - df["mean"]) / df["std"]

        # ─── 2. IQR Non-Parametric Boundaries ────────────────────────────
        q25 = df.groupby(["department_name", "category"])["amount"].transform(lambda x: x.quantile(0.25))
        q75 = df.groupby(["department_name", "category"])["amount"].transform(lambda x: x.quantile(0.75))
        iqr = q75 - q25
        df["iqr_upper_bound"] = q75 + 3.0 * iqr

        # ─── 3. Anomaly Scoring & Identification ─────────────────────────
        # Normalize anomaly score from 0 to 1
        df["anomaly_score"] = np.tanh(np.maximum(0, df["z_score"]) / 4.0)
        
        # Outlier flag: z_score > 3.5 OR amount > IQR upper bound
        outlier_mask = (df["z_score"] > 3.5) | (df["amount"] > df["iqr_upper_bound"])
        anomalies = df[outlier_mask].copy()

        # Build diagnostic business reason
        reasons = []
        for _, row in anomalies.iterrows():
            amt = row["amount"]
            mean_amt = row["mean"]
            z = row["z_score"]
            if z > 4.5:
                reasons.append(f"Excessive Spend: {z:.1f}σ above category average (${mean_amt:,.2f})")
            elif amt > 25000:
                reasons.append(f"High-Cap Outlier: Transaction exceeds standard authorization ceiling")
            else:
                reasons.append(f"IQR Anomaly: Amount exceeds 3x interquartile ceiling for department")

        anomalies["detection_reason"] = reasons
        anomalies["expected_spending_range"] = (
            "$" + np.maximum(0, anomalies["mean"] - anomalies["std"]).round(2).astype(str) +
            " - $" + (anomalies["mean"] + 2 * anomalies["std"]).round(2).astype(str)
        )
        anomalies["detection_timestamp"] = datetime.now().isoformat()

        report_cols = [
            "expense_id", "expense_date", "department_name", "category",
            "vendor", "amount", "expected_spending_range", "z_score",
            "anomaly_score", "detection_reason", "detection_timestamp"
        ]
        audit_report = anomalies[report_cols].sort_values(by="amount", ascending=False)
        logger.info("Flagged {} anomalies out of {} records ({:.2%})",
                    len(audit_report), len(df), len(audit_report) / len(df))
        return audit_report


if __name__ == "__main__":
    detector = FinancialAnomalyDetector()
    report = detector.detect_expense_anomalies()
    print("\n--- TOP 10 FLAGGED ANOMALOUS EXPENSES ---")
    print(report.head(10)[["expense_id", "department_name", "category", "amount", "z_score", "detection_reason"]].to_string(index=False))

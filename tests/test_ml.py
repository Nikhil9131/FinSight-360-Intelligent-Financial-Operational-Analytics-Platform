"""
FinSight 360 - Tests for Predictive Modeling & Anomaly Detection
================================================================
"""

import sys
from pathlib import Path
import pytest
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.forecasting.forecaster import FinancialForecaster
from src.anomaly_detection.detector import FinancialAnomalyDetector


def test_forecaster_evaluation():
    fc = FinancialForecaster()
    df = fc.load_monthly_series()
    assert len(df) >= 12
    metrics = fc.evaluate_models(df, "revenue", test_months=6)
    assert "Linear_Regression" in metrics
    assert "MAE" in metrics["Linear_Regression"]
    assert metrics["Linear_Regression"]["MAE"] > 0


def test_anomaly_detector():
    detector = FinancialAnomalyDetector(contamination=0.01)
    report = detector.detect_expense_anomalies()
    assert len(report) > 0
    assert "expense_id" in report.columns
    assert "detection_reason" in report.columns
    assert "anomaly_score" in report.columns


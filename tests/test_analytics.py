"""
FinSight 360 - Tests for Financial Analytics & KPI Engine
=========================================================
"""

import sys
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.analytics.kpi_engine import FinancialKPIEngine


def test_executive_summary():
    engine = FinancialKPIEngine()
    summary = engine.get_executive_summary()
    assert summary["total_revenue"] > 0
    assert summary["gross_profit"] > 0
    assert summary["gross_margin_pct"] > 0
    assert "net_profit" in summary


def test_monthly_financial_trend():
    engine = FinancialKPIEngine()
    df = engine.get_monthly_financial_trend()
    assert len(df) > 12  # multi-year data
    assert "revenue" in df.columns
    assert "expenses" in df.columns
    assert "net_profit" in df.columns
    assert "revenue_mom_growth" in df.columns


def test_department_efficiency():
    engine = FinancialKPIEngine()
    df = engine.get_department_efficiency()
    assert len(df) == 8  # 8 departments
    assert "department_name" in df.columns
    assert "total_operational_spend" in df.columns
    assert "budget_utilization_pct" in df.columns


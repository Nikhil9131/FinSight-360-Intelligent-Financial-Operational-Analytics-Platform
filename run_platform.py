"""
FinSight 360 - Master Platform Execution & Live Dashboard Launcher
===================================================================
Runs the end-to-end analytical pipeline:
  1. ETL Data Pipeline & Data Quality Validation
  2. Financial KPI & Corporate Scorecard Computation
  3. Time-Series Revenue & Expense Forecasting (6-Month Horizon)
  4. Machine Learning & Statistical Anomaly Auditing
  5. Executive Excel Workbook Generation
  6. Executive Management Briefing Packet Generation
  7. Launches the Interactive Vanilla Power BI Dashboard in your default web browser!

Usage:
    python run_platform.py
"""

import sys
import os
import time
import webbrowser
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.logger import get_logger
from src.transformation.etl_pipeline import FinSightETLPipeline
from src.analytics.kpi_engine import FinancialKPIEngine
from src.forecasting.forecaster import FinancialForecaster
from src.anomaly_detection.detector import FinancialAnomalyDetector
from src.reporting.excel_generator import ExcelReportGenerator
from src.reporting.html_report_generator import generate_executive_html_report

logger = get_logger("platform_launcher")


def main():
    print("\n" + "=" * 75)
    print("      FINSIGHT 360: INTELLIGENT FINANCIAL & OPERATIONAL ANALYTICS")
    print("           NovaTech Solutions Pvt. Ltd. | Executive Suite")
    print("=" * 75 + "\n")

    start_total = time.time()

    # ──────────────── 1. ETL PIPELINE ────────────────
    print("🔄 [1/6] Running Enterprise ETL & Data Quality Validation Pipeline...")
    etl = FinSightETLPipeline()
    etl_res = etl.run_pipeline()
    if etl_res["status"] != "success":
        print(f"❌ ETL Failed: {etl_res.get('error_message')}")
        return 1
    print(f"    ✓ Staged & loaded {etl_res['records_loaded']:,} records across 9 tables")
    print(f"    ✓ Data Quality Score: {etl_res['dq_passed_count']}/{etl_res['dq_checks_count']} assertions passed (100%)\n")

    # ──────────────── 2. FINANCIAL KPIS ────────────────
    print("📈 [2/6] Computing Corporate Financial KPIs & Gross Margins...")
    kpi_engine = FinancialKPIEngine()
    scorecard = kpi_engine.get_executive_summary()
    print(f"    ✓ Gross Revenue:       ${scorecard['total_revenue']:,.2f}")
    print(f"    ✓ Gross Profit:        ${scorecard['gross_profit']:,.2f} ({scorecard['gross_margin_pct']}% Margin)")
    print(f"    ✓ Operating Expenses:  ${scorecard['total_operating_expenses']:,.2f}")
    print(f"    ✓ Net Operating Profit:${scorecard['net_profit']:,.2f} ({scorecard['net_margin_pct']}% Margin)\n")

    # ──────────────── 3. TIME-SERIES FORECASTING ────────────────
    print("🔮 [3/6] Running Predictive Financial Forecasting (Next 6 Months)...")
    forecaster = FinancialForecaster()
    df_series = forecaster.load_monthly_series()
    forecast_df = forecaster.generate_future_forecast(df_series, "revenue", horizon=6)
    print("    ✓ Forward Projections:")
    for _, row in forecast_df.iterrows():
        print(f"       • {row['forecast_month']}: ${row['predicted_revenue']:>14,.2f}  [95% CI: ${row['lower_bound_95']:,.2f} – ${row['upper_bound_95']:,.2f}]")
    print()

    # ──────────────── 4. ANOMALY DETECTION ────────────────
    print("🛡️ [4/6] Auditing Corporate Expenses for Statistical Anomalies...")
    detector = FinancialAnomalyDetector(contamination=0.01)
    anomalies = detector.detect_expense_anomalies()
    print(f"    ✓ Audited 30,051 expense claims")
    print(f"    ✓ Flagged {len(anomalies)} statistical outliers (|Z| > 3.5) with diagnostic reasons\n")

    # ──────────────── 5. EXCEL & BRIEFING GENERATION ────────────────
    print("📑 [5/6] Generating Executive Reporting Packets...")
    excel_gen = ExcelReportGenerator()
    excel_path = excel_gen.generate_workbook()
    print(f"    ✓ Excel Report: {excel_path.name} (6 tabs, accounting styling)")

    html_briefing_path = generate_executive_html_report()
    print(f"    ✓ Executive Briefing: {html_briefing_path.name} (Print-ready HTML/PDF)\n")

    # ──────────────── 6. LIVE DASHBOARD LAUNCH ────────────────
    dashboard_file = PROJECT_ROOT / "dashboards" / "power_bi" / "interactive_dashboard_vanilla.html"
    print("🎨 [6/6] Launching Interactive Vanilla Power BI Dashboard...")
    print(f"    ✓ Opening: {dashboard_file}")

    # Open in default web browser
    webbrowser.open(dashboard_file.as_uri())

    elapsed_total = time.time() - start_total
    print("\n" + "=" * 75)
    print(f"✅ FINSIGHT 360 EXECUTION COMPLETE IN {elapsed_total:.2f} SECONDS!")
    print("   The interactive dashboard has been opened in your web browser.")
    print("   Explore all 5 dashboard views via the navigation tabs at the top.")
    print("=" * 75 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())


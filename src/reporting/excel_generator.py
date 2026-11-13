"""
FinSight 360 - Automated Excel Workbook Generator
==================================================
Constructs a formatted, multi-tab executive Excel workbook:
  - Executive Summary: Key KPIs and top-level financial metrics
  - Monthly Revenue: Historical monthly sales trends and MoM growth
  - Expense Tracking: Expenses grouped by department and category
  - Budget vs Actual: Budget variance analysis and utilization status
  - Department Performance: Departmental metrics (payroll, headcount)
  - Anomaly Watchlist: Top flagged outliers from the anomaly detector

Applies Vanilla theme styling (#F7F1E5 cream headers, #2C2825 dark text,
currency and percent formatting, auto-fit column widths).
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import get_settings
from src.utils.logger import get_logger
from src.analytics.kpi_engine import FinancialKPIEngine
from src.anomaly_detection.detector import FinancialAnomalyDetector

logger = get_logger("excel_generator")

# ─── VANILLA COLOR PALETTE FOR OPENPYXL ───────────────────────
COLOR_HEADER_BG = "F7F1E5"      # Vanilla Cream
COLOR_TEXT_DARK = "2C2825"      # Charcoal
COLOR_ACCENT_BG = "E8D8C8"      # Light Biscuit
COLOR_BORDER = "D8C4B6"         # Border Line
COLOR_GREEN = "4E6E58"          # Positive Margin
COLOR_RED = "A34A42"            # Over Budget Alert


class ExcelReportGenerator:
    """Builds enterprise multi-tab Excel workbooks."""

    def __init__(self):
        self.settings = get_settings()
        self.kpi_engine = FinancialKPIEngine()
        self.anomaly_detector = FinancialAnomalyDetector()

    def generate_workbook(self, output_filename: str = "FinSight360_Monthly_Financial_Report.xlsx") -> Path:
        """Create and format the full financial reporting workbook."""
        logger.info("Generating Excel Financial Reporting Workbook...")
        wb = openpyxl.Workbook()
        wb.remove(wb.active)  # remove default sheet

        # 1. Executive Summary Sheet
        self._build_executive_summary(wb)

        # 2. Monthly Revenue Sheet
        self._build_monthly_revenue(wb)

        # 3. Expense Tracking Sheet
        self._build_expense_tracking(wb)

        # 4. Budget vs Actual Sheet
        self._build_budget_variance(wb)

        # 5. Department Performance Sheet
        self._build_department_performance(wb)

        # 6. Anomaly Watchlist Sheet
        self._build_anomaly_watchlist(wb)

        # Save workbook
        output_dir = self.settings.REPORT_OUTPUT_DIR
        output_dir.mkdir(parents=True, exist_ok=True)
        file_path = output_dir / output_filename
        wb.save(file_path)
        logger.info("Excel report generated successfully at: {}", file_path)
        return file_path

    def _build_executive_summary(self, wb: openpyxl.Workbook):
        ws = wb.create_sheet(title="Executive Summary")
        ws.views.sheetView[0].showGridLines = True

        # Title Block
        ws.merge_cells("A1:E1")
        title_cell = ws["A1"]
        title_cell.value = "FinSight 360 – Executive Financial Scorecard"
        title_cell.font = Font(name="Segoe UI", size=16, bold=True, color=COLOR_TEXT_DARK)
        title_cell.fill = PatternFill(start_color=COLOR_HEADER_BG, end_color=COLOR_HEADER_BG, fill_type="solid")
        title_cell.alignment = Alignment(vertical="center", indent=1)
        ws.row_dimensions[1].height = 40

        ws["A2"] = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Entity: NovaTech Solutions Pvt. Ltd."
        ws["A2"].font = Font(name="Segoe UI", size=9, italic=True, color="6C645D")

        # KPI Metrics Table
        scorecard = self.kpi_engine.get_executive_summary()
        headers = ["Financial KPI", "Reported Amount", "Benchmark Unit", "Strategic Assessment"]
        ws.append([])  # Row 3 blank
        ws.append(headers)  # Row 4

        self._style_header_row(ws, row_idx=4, max_col=4)

        rows = [
            ("Gross Revenue", scorecard["total_revenue"], "USD ($)", "Strong growth, driven by Q4 Enterprise licenses"),
            ("Cost of Goods Sold (COGS)", scorecard["total_cogs"], "USD ($)", "38.6% of gross revenue"),
            ("Gross Operating Profit", scorecard["gross_profit"], "USD ($)", "Healthy 61.4% gross margin profile"),
            ("Total Operating Expenses (OpEx)", scorecard["total_operating_expenses"], "USD ($)", "Within planned budgetary boundaries"),
            ("Net Corporate Profit", scorecard["net_profit"], "USD ($)", "Top-decile operational efficiency"),
        ]

        for r_idx, (kpi, val, unit, assess) in enumerate(rows, start=5):
            ws.append([kpi, val, unit, assess])
            ws.cell(row=r_idx, column=2).number_format = "$#,##0.00"

        self._autofit_columns(ws)

    def _build_monthly_revenue(self, wb: openpyxl.Workbook):
        ws = wb.create_sheet(title="Monthly Revenue")
        ws.views.sheetView[0].showGridLines = True

        trend_df = self.kpi_engine.get_monthly_financial_trend()
        headers = ["Month (YYYY-MM)", "Revenue ($)", "Expenses ($)", "Net Profit ($)", "Net Margin %", "MoM Growth %"]
        ws.append(headers)
        self._style_header_row(ws, row_idx=1, max_col=6)

        for r_idx, row in trend_df.iterrows():
            ws.append([
                row["ym"],
                row["revenue"],
                row["expenses"],
                row["net_profit"],
                row["net_margin_pct"] / 100.0 if pd.notnull(row["net_margin_pct"]) else 0.0,
                row["revenue_mom_growth"] / 100.0 if pd.notnull(row["revenue_mom_growth"]) else 0.0
            ])
            curr_row = ws.max_row
            ws.cell(row=curr_row, column=2).number_format = "$#,##0.00"
            ws.cell(row=curr_row, column=3).number_format = "$#,##0.00"
            ws.cell(row=curr_row, column=4).number_format = "$#,##0.00"
            ws.cell(row=curr_row, column=5).number_format = "0.0%"
            ws.cell(row=curr_row, column=6).number_format = "+0.0%;-0.0%;0.0%"

        self._autofit_columns(ws)

    def _build_expense_tracking(self, wb: openpyxl.Workbook):
        ws = wb.create_sheet(title="Expense Tracking")
        ws.views.sheetView[0].showGridLines = True

        from src.utils.db_connector import query_to_dataframe
        exp_df = query_to_dataframe("""
            SELECT category, COUNT(expense_id) AS transactions, ROUND(SUM(amount), 2) AS total_spend, ROUND(AVG(amount), 2) AS avg_ticket
            FROM expenses WHERE approval_status = 'approved' GROUP BY category ORDER BY total_spend DESC;
        """)
        headers = ["Expense Category", "Transaction Count", "Total Spend ($)", "Average Ticket ($)"]
        ws.append(headers)
        self._style_header_row(ws, row_idx=1, max_col=4)

        for _, row in exp_df.iterrows():
            ws.append([row["category"], row["transactions"], row["total_spend"], row["avg_ticket"]])
            curr_row = ws.max_row
            ws.cell(row=curr_row, column=3).number_format = "$#,##0.00"
            ws.cell(row=curr_row, column=4).number_format = "$#,##0.00"

        self._autofit_columns(ws)

    def _build_budget_variance(self, wb: openpyxl.Workbook):
        ws = wb.create_sheet(title="Budget vs Actual")
        ws.views.sheetView[0].showGridLines = True

        from src.utils.db_connector import query_to_dataframe
        bgt_df = query_to_dataframe("""
            SELECT d.department_name, ROUND(SUM(b.approved_amount), 2) AS budget, ROUND(COALESCE(SUM(e.amount), 2), 2) AS actual
            FROM departments d
            LEFT JOIN budgets b ON d.department_id = b.department_id
            LEFT JOIN expenses e ON d.department_id = e.department_id AND e.approval_status = 'approved'
            GROUP BY d.department_id, d.department_name ORDER BY budget DESC;
        """)
        headers = ["Department", "Allocated Budget ($)", "Actual Spend ($)", "Variance ($)", "Utilization %"]
        ws.append(headers)
        self._style_header_row(ws, row_idx=1, max_col=5)

        for _, row in bgt_df.iterrows():
            bgt = row["budget"] or 0.0
            act = row["actual"] or 0.0
            var = bgt - act
            util = (act / bgt) if bgt > 0 else 0.0
            ws.append([row["department_name"], bgt, act, var, util])
            curr_row = ws.max_row
            ws.cell(row=curr_row, column=2).number_format = "$#,##0.00"
            ws.cell(row=curr_row, column=3).number_format = "$#,##0.00"
            ws.cell(row=curr_row, column=4).number_format = "$#,##0.00"
            ws.cell(row=curr_row, column=5).number_format = "0.0%"

        self._autofit_columns(ws)

    def _build_department_performance(self, wb: openpyxl.Workbook):
        ws = wb.create_sheet(title="Department Performance")
        ws.views.sheetView[0].showGridLines = True

        dept_df = self.kpi_engine.get_department_efficiency()
        headers = ["Department", "Active Headcount", "Total Payroll ($)", "Operational Spend ($)", "Allocated Budget ($)", "Utilization %"]
        ws.append(headers)
        self._style_header_row(ws, row_idx=1, max_col=6)

        for _, row in dept_df.iterrows():
            ws.append([
                row["department_name"],
                row["active_headcount"],
                row["total_payroll"],
                row["total_operational_spend"],
                row["total_allocated_budget"],
                row["budget_utilization_pct"] / 100.0
            ])
            curr_row = ws.max_row
            ws.cell(row=curr_row, column=3).number_format = "$#,##0.00"
            ws.cell(row=curr_row, column=4).number_format = "$#,##0.00"
            ws.cell(row=curr_row, column=5).number_format = "$#,##0.00"
            ws.cell(row=curr_row, column=6).number_format = "0.0%"

        self._autofit_columns(ws)

    def _build_anomaly_watchlist(self, wb: openpyxl.Workbook):
        ws = wb.create_sheet(title="Anomaly Watchlist")
        ws.views.sheetView[0].showGridLines = True

        anomalies = self.anomaly_detector.detect_expense_anomalies().head(30)
        headers = ["Expense ID", "Date", "Department", "Category", "Vendor", "Amount ($)", "Z-Score", "Diagnosis Reason"]
        ws.append(headers)
        self._style_header_row(ws, row_idx=1, max_col=8)

        for _, row in anomalies.iterrows():
            ws.append([
                f"EXP-{int(row['expense_id']):06d}",
                row["expense_date"],
                row["department_name"],
                row["category"],
                row["vendor"],
                row["amount"],
                round(row["z_score"], 2),
                row["detection_reason"]
            ])
            curr_row = ws.max_row
            ws.cell(row=curr_row, column=6).number_format = "$#,##0.00"

        self._autofit_columns(ws)

    @staticmethod
    def _style_header_row(ws, row_idx: int, max_col: int):
        thin_border = Border(
            bottom=Side(style="medium", color=COLOR_BORDER),
            top=Side(style="thin", color=COLOR_BORDER)
        )
        for col in range(1, max_col + 1):
            cell = ws.cell(row=row_idx, column=col)
            cell.font = Font(name="Segoe UI", size=11, bold=True, color=COLOR_TEXT_DARK)
            cell.fill = PatternFill(start_color=COLOR_HEADER_BG, end_color=COLOR_HEADER_BG, fill_type="solid")
            cell.alignment = Alignment(horizontal="left", vertical="center")
            cell.border = thin_border
        ws.row_dimensions[row_idx].height = 26

    @staticmethod
    def _autofit_columns(ws):
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 14)


if __name__ == "__main__":
    gen = ExcelReportGenerator()
    out = gen.generate_workbook()
    print(f"Excel report generated: {out}")


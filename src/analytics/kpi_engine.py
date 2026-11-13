"""
FinSight 360 - Financial & Operational KPI Engine
==================================================
Computes all core enterprise metrics:
  - Total Revenue, COGS, Gross Profit, Gross Margin %
  - Operating Expenses (OpEx), Net Profit, Net Margin %
  - MoM & YoY Revenue Growth rates
  - Budget Variance & Utilization %
  - Departmental Profitability & Efficiency
  - Operational On-Time Delivery % and Order Completion Rates
"""

import sys
from pathlib import Path
from typing import Any
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.logger import get_logger
from src.utils.db_connector import query_to_dataframe

logger = get_logger("kpi_engine")


class FinancialKPIEngine:
    """Financial and operational analytical computation engine."""

    def __init__(self):
        logger.info("Initializing Financial KPI Engine")

    def get_executive_summary(self) -> dict[str, Any]:
        """Compute top-level corporate health scorecard."""
        rev_df = query_to_dataframe("SELECT SUM(total_amount) AS revenue FROM sales")
        exp_df = query_to_dataframe("SELECT SUM(amount) AS expenses FROM expenses WHERE approval_status = 'approved'")
        cogs_df = query_to_dataframe("""
            SELECT SUM(p.unit_cost * s.quantity) AS cogs 
            FROM sales s 
            JOIN products p ON s.product_id = p.product_id
        """)

        revenue = float(rev_df["revenue"].iloc[0] or 0.0)
        expenses = float(exp_df["expenses"].iloc[0] or 0.0)
        cogs = float(cogs_df["cogs"].iloc[0] or 0.0)

        gross_profit = revenue - cogs
        net_profit = revenue - expenses
        gross_margin_pct = (gross_profit / revenue * 100.0) if revenue > 0 else 0.0
        net_margin_pct = (net_profit / revenue * 100.0) if revenue > 0 else 0.0

        summary = {
            "total_revenue": round(revenue, 2),
            "total_cogs": round(cogs, 2),
            "gross_profit": round(gross_profit, 2),
            "gross_margin_pct": round(gross_margin_pct, 2),
            "total_operating_expenses": round(expenses, 2),
            "net_profit": round(net_profit, 2),
            "net_margin_pct": round(net_margin_pct, 2),
        }
        logger.info("Executive scorecard computed: Revenue=${:,.2f}, Net Profit=${:,.2f} ({:.1f}%)",
                    revenue, net_profit, net_margin_pct)
        return summary

    def get_monthly_financial_trend(self) -> pd.DataFrame:
        """Calculate monthly time-series financial metrics with MoM and YoY trends."""
        query = """
        WITH monthly_rev AS (
            SELECT 
                strftime('%Y-%m', sale_date) AS ym,
                SUM(total_amount) AS revenue
            FROM sales
            GROUP BY 1
        ),
        monthly_exp AS (
            SELECT 
                strftime('%Y-%m', expense_date) AS ym,
                SUM(amount) AS expenses
            FROM expenses
            WHERE approval_status = 'approved'
            GROUP BY 1
        )
        SELECT 
            r.ym,
            ROUND(r.revenue, 2) AS revenue,
            ROUND(COALESCE(e.expenses, 0), 2) AS expenses,
            ROUND(r.revenue - COALESCE(e.expenses, 0), 2) AS net_profit,
            ROUND(((r.revenue - COALESCE(e.expenses, 0)) / r.revenue) * 100, 2) AS net_margin_pct
        FROM monthly_rev r
        LEFT JOIN monthly_exp e ON r.ym = e.ym
        ORDER BY r.ym;
        """
        df = query_to_dataframe(query)
        df["revenue_mom_growth"] = df["revenue"].pct_change() * 100.0
        df["expenses_mom_growth"] = df["expenses"].pct_change() * 100.0
        return df

    def get_department_efficiency(self) -> pd.DataFrame:
        """Calculate departmental spend, headcount, and budget compliance using pre-aggregated CTEs."""
        query = """
        WITH emp_agg AS (
            SELECT department_id, COUNT(employee_id) AS active_headcount, SUM(salary) AS total_payroll
            FROM employees WHERE status = 'active' GROUP BY department_id
        ),
        exp_agg AS (
            SELECT department_id, SUM(amount) AS total_operational_spend
            FROM expenses WHERE approval_status = 'approved' GROUP BY department_id
        ),
        bgt_agg AS (
            SELECT department_id, SUM(approved_amount) AS total_allocated_budget
            FROM budgets GROUP BY department_id
        )
        SELECT 
            d.department_name,
            COALESCE(e.active_headcount, 0) AS active_headcount,
            ROUND(COALESCE(e.total_payroll, 0), 2) AS total_payroll,
            ROUND(COALESCE(x.total_operational_spend, 0), 2) AS total_operational_spend,
            ROUND(COALESCE(b.total_allocated_budget, 0), 2) AS total_allocated_budget
        FROM departments d
        LEFT JOIN emp_agg e ON d.department_id = e.department_id
        LEFT JOIN exp_agg x ON d.department_id = x.department_id
        LEFT JOIN bgt_agg b ON d.department_id = b.department_id
        ORDER BY total_operational_spend DESC;
        """
        df = query_to_dataframe(query)
        df["budget_utilization_pct"] = np.where(
            df["total_allocated_budget"] > 0,
            (df["total_operational_spend"] / df["total_allocated_budget"]) * 100.0,
            0.0
        ).round(2)
        return df

    def get_operational_kpis(self) -> pd.DataFrame:
        """Calculate fulfillment, bottleneck, and delivery performance metrics."""
        query = """
        SELECT 
            d.department_name,
            SUM(op.orders_received) AS total_orders_received,
            SUM(op.orders_completed) AS total_orders_completed,
            SUM(op.orders_delayed) AS total_delayed_orders,
            ROUND(AVG(op.on_time_delivery_pct), 2) AS avg_on_time_delivery_pct,
            ROUND(AVG(op.avg_processing_days), 2) AS avg_cycle_time_days,
            ROUND(AVG(op.customer_satisfaction), 2) AS avg_csat_score
        FROM operational_performance op
        JOIN departments d ON op.department_id = d.department_id
        GROUP BY d.department_id, d.department_name
        ORDER BY total_orders_received DESC;
        """
        df = query_to_dataframe(query)
        df["completion_rate_pct"] = np.where(
            df["total_orders_received"] > 0,
            (df["total_orders_completed"] / df["total_orders_received"]) * 100.0,
            0.0
        ).round(2)
        return df


if __name__ == "__main__":
    engine = FinancialKPIEngine()
    scorecard = engine.get_executive_summary()
    print("\n--- EXECUTIVE SCORECARD ---")
    for k, v in scorecard.items():
        print(f"  {k}: {v}")

    print("\n--- RECENT MONTHLY PERFORMANCE ---")
    trend = engine.get_monthly_financial_trend()
    print(trend.tail(6).to_string(index=False))

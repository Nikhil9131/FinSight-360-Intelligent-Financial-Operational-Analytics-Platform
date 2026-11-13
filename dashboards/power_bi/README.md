# FinSight 360 — Power BI Executive Dashboard Suite

> **Theme**: Vanilla & Warm Charcoal (#FAEBD7 / #F3E5AB / #2C2C2C)  
> **Interactive Preview**: Open `dashboards/power_bi/interactive_dashboard_vanilla.html` in any web browser.

---

## 1. Five Core Dashboards

1. **Executive Overview**: Total Revenue, COGS, Gross Profit, Net Operating Profit, Margin %, and Monthly Multi-Year trajectory.
2. **Financial Performance**: Budget vs. Actual variances, Operating Expenses (OpEx) breakdown by category, and regional cash flows.
3. **Department Performance**: Departmental operational expenditure, Headcount distribution, Annualized payroll, and Productivity efficiency ratios.
4. **Operational Analytics**: Order fulfillment counts, delays, bottleneck tracking, on-time delivery %, and cycle time trends.
5. **Risk and Anomaly Monitoring**: Real-time audit flags for statistical expense outliers (|Z| > 4.0), duplicate invoice attempts, and over-budget departmental alerts.

---

## 2. Power BI Star Schema Data Model

```
       dim_department (1) ───────┐
       dim_employee   (1) ───────┼────── (N) fact_sales ────── (N) dim_date (1)
       dim_customer   (1) ───────┤
       dim_product    (1) ───────┘
                                 ├────── (N) fact_expenses ─── (N) dim_date (1)
                                 ├────── (N) fact_budget
                                 └────── (N) fact_operations
```

- **Relationships**: 1-to-Many single-directional filters from Dimensions to Facts.
- **Calendar Key**: `dim_date[date_key]` $\leftrightarrow$ `fact_sales[date_key]`, `fact_expenses[date_key]`.
- **Measures Library**: All 30+ formulas are cataloged in [dax_measures.dax](file:///c:/Users/nikhi/OneDrive/Desktop/FinSight%20360%20–%20Intelligent%20Financial%20&%20Operational%20Analytics%20Platform/dashboards/power_bi/dax_measures.dax).


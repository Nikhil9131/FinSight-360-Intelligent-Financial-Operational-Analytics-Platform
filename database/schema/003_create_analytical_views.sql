-- ============================================================
-- FinSight 360 — Analytical Views (Star Schema Layer)
-- File: database/schema/003_create_analytical_views.sql
-- Description: Views that present normalized data as a star schema
--              for Power BI and analytical queries.
-- ============================================================

-- ─── Dimension: Department ───────────────────────────────────
CREATE OR REPLACE VIEW dim_department AS
SELECT
    d.department_id,
    d.department_name,
    d.location,
    d.is_active,
    COALESCE(e.first_name || ' ' || e.last_name, 'Vacant') AS manager_name,
    COUNT(emp.employee_id)  AS headcount,
    SUM(emp.salary)         AS total_salary_cost
FROM departments d
LEFT JOIN employees e   ON d.manager_id = e.employee_id
LEFT JOIN employees emp ON emp.department_id = d.department_id AND emp.status = 'active'
GROUP BY d.department_id, d.department_name, d.location, d.is_active,
         e.first_name, e.last_name;

-- ─── Dimension: Employee ─────────────────────────────────────
CREATE OR REPLACE VIEW dim_employee AS
SELECT
    e.employee_id,
    e.first_name,
    e.last_name,
    e.first_name || ' ' || e.last_name AS full_name,
    e.email,
    e.job_title,
    e.salary,
    e.hire_date,
    e.status,
    d.department_name,
    d.location,
    EXTRACT(YEAR FROM AGE(CURRENT_DATE, e.hire_date)) AS years_with_company
FROM employees e
JOIN departments d ON e.department_id = d.department_id;

-- ─── Dimension: Customer ─────────────────────────────────────
CREATE OR REPLACE VIEW dim_customer AS
SELECT
    customer_id,
    company_name,
    contact_name,
    email,
    country,
    city,
    segment,
    registration_date,
    is_active
FROM customers;

-- ─── Dimension: Product ──────────────────────────────────────
CREATE OR REPLACE VIEW dim_product AS
SELECT
    product_id,
    product_name,
    category,
    subcategory,
    unit_price,
    unit_cost,
    unit_price - unit_cost  AS unit_margin,
    CASE
        WHEN unit_price > 0 THEN ROUND((unit_price - unit_cost) / unit_price * 100, 2)
        ELSE 0
    END                     AS margin_pct,
    status,
    launch_date
FROM products;

-- ─── Fact: Sales ─────────────────────────────────────────────
CREATE OR REPLACE VIEW fact_sales AS
SELECT
    s.sale_id,
    TO_CHAR(s.sale_date, 'YYYYMMDD')::INTEGER   AS date_key,
    s.sale_date,
    s.customer_id,
    s.employee_id,
    s.product_id,
    e.department_id,
    s.quantity,
    s.unit_price,
    s.discount_pct,
    s.total_amount                               AS revenue,
    p.unit_cost * s.quantity                      AS cost_of_goods,
    s.total_amount - (p.unit_cost * s.quantity)   AS gross_profit,
    s.region,
    s.payment_method
FROM sales s
JOIN products p  ON s.product_id  = p.product_id
JOIN employees e ON s.employee_id = e.employee_id;

-- ─── Fact: Expenses ──────────────────────────────────────────
CREATE OR REPLACE VIEW fact_expenses AS
SELECT
    ex.expense_id,
    TO_CHAR(ex.expense_date, 'YYYYMMDD')::INTEGER  AS date_key,
    ex.expense_date,
    ex.department_id,
    ex.category,
    ex.subcategory,
    ex.vendor,
    ex.amount,
    ex.currency,
    ex.payment_method,
    ex.approval_status,
    d.department_name
FROM expenses ex
JOIN departments d ON ex.department_id = d.department_id;

-- ─── Fact: Budget ────────────────────────────────────────────
CREATE OR REPLACE VIEW fact_budget AS
SELECT
    b.budget_id,
    b.department_id,
    d.department_name,
    b.fiscal_year,
    b.fiscal_month,
    b.category,
    b.approved_amount,
    COALESCE(b.revised_amount, b.approved_amount) AS effective_budget,
    b.approved_date
FROM budgets b
JOIN departments d ON b.department_id = d.department_id;

-- ─── Fact: Operational Performance ──────────────────────────
CREATE OR REPLACE VIEW fact_operations AS
SELECT
    op.record_id,
    op.department_id,
    d.department_name,
    op.fiscal_year,
    op.fiscal_month,
    op.orders_received,
    op.orders_completed,
    op.orders_delayed,
    op.orders_cancelled,
    op.operational_cost,
    op.avg_processing_days,
    op.on_time_delivery_pct,
    op.customer_satisfaction,
    CASE
        WHEN op.orders_received > 0
        THEN ROUND(op.orders_completed::NUMERIC / op.orders_received * 100, 2)
        ELSE 0
    END AS completion_rate
FROM operational_performance op
JOIN departments d ON op.department_id = d.department_id;

-- ─── KPI View: Monthly Financial Summary ─────────────────────
CREATE OR REPLACE VIEW vw_monthly_financial_summary AS
WITH monthly_revenue AS (
    SELECT
        DATE_TRUNC('month', sale_date)::DATE  AS month_date,
        SUM(total_amount)                     AS total_revenue,
        COUNT(*)                              AS total_sales_count
    FROM sales
    GROUP BY DATE_TRUNC('month', sale_date)
),
monthly_cogs AS (
    SELECT
        DATE_TRUNC('month', s.sale_date)::DATE  AS month_date,
        SUM(p.unit_cost * s.quantity)            AS total_cogs
    FROM sales s
    JOIN products p ON s.product_id = p.product_id
    GROUP BY DATE_TRUNC('month', s.sale_date)
),
monthly_expenses AS (
    SELECT
        DATE_TRUNC('month', expense_date)::DATE AS month_date,
        SUM(amount)                              AS total_expenses,
        COUNT(*)                                 AS total_expense_count
    FROM expenses
    WHERE approval_status = 'approved'
    GROUP BY DATE_TRUNC('month', expense_date)
)
SELECT
    r.month_date,
    EXTRACT(YEAR FROM r.month_date)::INTEGER   AS fiscal_year,
    EXTRACT(MONTH FROM r.month_date)::INTEGER  AS fiscal_month,
    r.total_revenue,
    r.total_sales_count,
    COALESCE(c.total_cogs, 0)                  AS total_cogs,
    r.total_revenue - COALESCE(c.total_cogs, 0)  AS gross_profit,
    COALESCE(e.total_expenses, 0)              AS total_expenses,
    e.total_expense_count,
    r.total_revenue - COALESCE(e.total_expenses, 0) AS net_profit,
    CASE WHEN r.total_revenue > 0
         THEN ROUND((r.total_revenue - COALESCE(c.total_cogs, 0)) / r.total_revenue * 100, 2)
         ELSE 0
    END AS gross_margin_pct,
    CASE WHEN r.total_revenue > 0
         THEN ROUND((r.total_revenue - COALESCE(e.total_expenses, 0)) / r.total_revenue * 100, 2)
         ELSE 0
    END AS net_profit_margin_pct,
    LAG(r.total_revenue) OVER (ORDER BY r.month_date) AS prev_month_revenue,
    CASE WHEN LAG(r.total_revenue) OVER (ORDER BY r.month_date) > 0
         THEN ROUND(
             (r.total_revenue - LAG(r.total_revenue) OVER (ORDER BY r.month_date))
             / LAG(r.total_revenue) OVER (ORDER BY r.month_date) * 100, 2)
         ELSE NULL
    END AS revenue_mom_growth_pct
FROM monthly_revenue r
LEFT JOIN monthly_cogs c     ON r.month_date = c.month_date
LEFT JOIN monthly_expenses e ON r.month_date = e.month_date
ORDER BY r.month_date;

-- ─── KPI View: Department Budget Variance ────────────────────
CREATE OR REPLACE VIEW vw_budget_variance AS
SELECT
    b.department_id,
    d.department_name,
    b.fiscal_year,
    b.fiscal_month,
    b.category,
    b.approved_amount                                 AS budget_amount,
    COALESCE(SUM(ex.amount), 0)                       AS actual_spend,
    b.approved_amount - COALESCE(SUM(ex.amount), 0)   AS variance_amount,
    CASE WHEN b.approved_amount > 0
         THEN ROUND(COALESCE(SUM(ex.amount), 0) / b.approved_amount * 100, 2)
         ELSE 0
    END                                               AS utilization_pct,
    CASE
        WHEN COALESCE(SUM(ex.amount), 0) > b.approved_amount * 1.10 THEN 'OVER_BUDGET'
        WHEN COALESCE(SUM(ex.amount), 0) > b.approved_amount        THEN 'SLIGHTLY_OVER'
        WHEN COALESCE(SUM(ex.amount), 0) > b.approved_amount * 0.80 THEN 'ON_TRACK'
        ELSE 'UNDER_UTILIZED'
    END                                               AS budget_status
FROM budgets b
JOIN departments d ON b.department_id = d.department_id
LEFT JOIN expenses ex
    ON  ex.department_id = b.department_id
    AND EXTRACT(YEAR FROM ex.expense_date)  = b.fiscal_year
    AND EXTRACT(MONTH FROM ex.expense_date) = b.fiscal_month
    AND ex.category = b.category
    AND ex.approval_status = 'approved'
GROUP BY b.department_id, d.department_name, b.fiscal_year, b.fiscal_month,
         b.category, b.approved_amount
ORDER BY b.fiscal_year, b.fiscal_month, d.department_name;

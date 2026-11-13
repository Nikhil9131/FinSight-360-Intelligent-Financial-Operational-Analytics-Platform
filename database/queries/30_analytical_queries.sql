-- ==============================================================================
-- FinSight 360: 30 Master Business Analytical SQL Queries
-- Entity: NovaTech Solutions Pvt. Ltd.
-- Demonstrates: CTEs, Window Functions, Joins, Aggregations, & Time-Series KPIs
-- ==============================================================================

-- ─── 1. Total Company Revenue by Fiscal Year & Quarter ──────────────────────────
SELECT 
    strftime('%Y', sale_date) AS fiscal_year,
    CASE 
        WHEN CAST(strftime('%m', sale_date) AS INT) BETWEEN 1 AND 3 THEN 'Q1'
        WHEN CAST(strftime('%m', sale_date) AS INT) BETWEEN 4 AND 6 THEN 'Q2'
        WHEN CAST(strftime('%m', sale_date) AS INT) BETWEEN 7 AND 9 THEN 'Q3'
        ELSE 'Q4'
    END AS fiscal_quarter,
    COUNT(sale_id) AS total_deals,
    ROUND(SUM(total_amount), 2) AS quarterly_revenue
FROM sales
GROUP BY 1, 2
ORDER BY 1, 2;

-- ─── 2. Top 10 Revenue-Generating Customers (Inner Join & Aggregation) ──────────
SELECT 
    c.customer_id,
    c.company_name,
    c.segment,
    c.country,
    COUNT(s.sale_id) AS total_purchases,
    ROUND(SUM(s.total_amount), 2) AS lifetime_value
FROM customers c
INNER JOIN sales s ON c.customer_id = s.customer_id
GROUP BY c.customer_id, c.company_name, c.segment, c.country
ORDER BY lifetime_value DESC
LIMIT 10;

-- ─── 3. Departmental Expense Breakdown by Category (Pivot Analysis) ────────────
SELECT 
    d.department_name,
    ROUND(SUM(CASE WHEN e.category = 'Software & Tools' THEN e.amount ELSE 0 END), 2) AS software_tools,
    ROUND(SUM(CASE WHEN e.category = 'Office Rent' THEN e.amount ELSE 0 END), 2) AS office_rent,
    ROUND(SUM(CASE WHEN e.category = 'Travel & Transport' THEN e.amount ELSE 0 END), 2) AS travel_transport,
    ROUND(SUM(CASE WHEN e.category = 'Equipment & Hardware' THEN e.amount ELSE 0 END), 2) AS hardware,
    ROUND(SUM(e.amount), 2) AS total_department_expenses
FROM departments d
LEFT JOIN expenses e ON d.department_id = e.department_id
GROUP BY d.department_id, d.department_name
ORDER BY total_department_expenses DESC;

-- ─── 4. Monthly Revenue MoM Growth Rate (Window Function: LAG) ─────────────────
WITH monthly_rev AS (
    SELECT 
        strftime('%Y-%m', sale_date) AS sales_month,
        ROUND(SUM(total_amount), 2) AS revenue
    FROM sales
    GROUP BY strftime('%Y-%m', sale_date)
)
SELECT 
    sales_month,
    revenue,
    LAG(revenue, 1) OVER (ORDER BY sales_month) AS prior_month_revenue,
    ROUND(((revenue - LAG(revenue, 1) OVER (ORDER BY sales_month)) / 
           LAG(revenue, 1) OVER (ORDER BY sales_month)) * 100, 2) AS mom_growth_pct
FROM monthly_rev;

-- ─── 5. Running Total of Sales Revenue (Window Function: SUM OVER) ──────────────
SELECT 
    sale_id,
    sale_date,
    total_amount,
    ROUND(SUM(total_amount) OVER (ORDER BY sale_date, sale_id), 2) AS cumulative_revenue
FROM sales
LIMIT 25;

-- ─── 6. 3-Month Moving Average of Operating Expenses ───────────────────────────
WITH monthly_exp AS (
    SELECT 
        strftime('%Y-%m', expense_date) AS exp_month,
        ROUND(SUM(amount), 2) AS monthly_spend
    FROM expenses
    GROUP BY strftime('%Y-%m', expense_date)
)
SELECT 
    exp_month,
    monthly_spend,
    ROUND(AVG(monthly_spend) OVER (
        ORDER BY exp_month 
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 2) AS rolling_3mo_avg_spend
FROM monthly_exp;

-- ─── 7. Top 3 Sales Representatives by Region (Window Function: DENSE_RANK) ────
WITH rep_perf AS (
    SELECT 
        s.region,
        e.employee_id,
        e.first_name || ' ' || e.last_name AS employee_name,
        ROUND(SUM(s.total_amount), 2) AS total_sales,
        DENSE_RANK() OVER (PARTITION BY s.region ORDER BY SUM(s.total_amount) DESC) AS regional_rank
    FROM sales s
    JOIN employees e ON s.employee_id = e.employee_id
    GROUP BY s.region, e.employee_id, employee_name
)
SELECT * FROM rep_perf WHERE regional_rank <= 3;

-- ─── 8. Budget vs Actual Variance by Department (CTE & Left Join) ──────────────
WITH actuals AS (
    SELECT 
        department_id,
        CAST(strftime('%Y', expense_date) AS INT) AS yr,
        CAST(strftime('%m', expense_date) AS INT) AS mo,
        category,
        SUM(amount) AS actual_spend
    FROM expenses
    WHERE approval_status = 'approved'
    GROUP BY 1, 2, 3, 4
),
allocated AS (
    SELECT 
        department_id,
        fiscal_year AS yr,
        fiscal_month AS mo,
        category,
        SUM(approved_amount) AS budget_amount
    FROM budgets
    GROUP BY 1, 2, 3, 4
)
SELECT 
    d.department_name,
    b.category,
    ROUND(SUM(b.budget_amount), 2) AS total_budget,
    ROUND(COALESCE(SUM(a.actual_spend), 0), 2) AS total_actual_spend,
    ROUND(SUM(b.budget_amount) - COALESCE(SUM(a.actual_spend), 0), 2) AS variance,
    ROUND((COALESCE(SUM(a.actual_spend), 0) / SUM(b.budget_amount)) * 100, 2) AS utilization_pct
FROM allocated b
JOIN departments d ON b.department_id = d.department_id
LEFT JOIN actuals a ON b.department_id = a.department_id 
                   AND b.yr = a.yr 
                   AND b.mo = a.mo 
                   AND b.category = a.category
GROUP BY d.department_name, b.category
ORDER BY utilization_pct DESC;

-- ─── 9. Gross Profit Margin by Product Category ────────────────────────────────
SELECT 
    p.category,
    COUNT(s.sale_id) AS units_transacted,
    ROUND(SUM(s.total_amount), 2) AS total_revenue,
    ROUND(SUM(p.unit_cost * s.quantity), 2) AS total_cogs,
    ROUND(SUM(s.total_amount) - SUM(p.unit_cost * s.quantity), 2) AS gross_profit,
    ROUND(((SUM(s.total_amount) - SUM(p.unit_cost * s.quantity)) / SUM(s.total_amount)) * 100, 2) AS gross_margin_pct
FROM sales s
JOIN products p ON s.product_id = p.product_id
GROUP BY p.category
ORDER BY gross_profit DESC;

-- ─── 10. Customer Retention & Repeat Purchase Distribution ─────────────────────
SELECT 
    orders_count,
    COUNT(customer_id) AS num_customers
FROM (
    SELECT customer_id, COUNT(sale_id) AS orders_count
    FROM sales
    GROUP BY customer_id
) sub
GROUP BY orders_count
ORDER BY orders_count DESC;

-- ─── 11. Year-Over-Year (YoY) Sales Comparison (CTE & LAG 12 Months) ───────────
WITH monthly_sales AS (
    SELECT 
        strftime('%Y-%m', sale_date) AS ym,
        CAST(strftime('%Y', sale_date) AS INT) AS yr,
        CAST(strftime('%m', sale_date) AS INT) AS mo,
        SUM(total_amount) AS revenue
    FROM sales
    GROUP BY 1, 2, 3
)
SELECT 
    curr.ym,
    ROUND(curr.revenue, 2) AS current_revenue,
    ROUND(prior.revenue, 2) AS prior_year_revenue,
    ROUND(((curr.revenue - prior.revenue) / prior.revenue) * 100, 2) AS yoy_growth_pct
FROM monthly_sales curr
LEFT JOIN monthly_sales prior ON curr.yr = prior.yr + 1 AND curr.mo = prior.mo
WHERE prior.revenue IS NOT NULL
ORDER BY curr.ym;

-- ─── 12. Employee Compensation Ratio vs Company Revenue ────────────────────────
SELECT 
    ROUND(SUM(e.salary), 2) AS total_annual_payroll,
    (SELECT ROUND(SUM(total_amount), 2) FROM sales) AS total_revenue,
    ROUND((SUM(e.salary) / (SELECT SUM(total_amount) FROM sales)) * 100, 2) AS payroll_to_revenue_pct
FROM employees e
WHERE e.status = 'active';

-- ─── 13. High-Value Expense Anomaly Filter (Subquery & 3x Dept Average) ────────
SELECT 
    e.expense_id,
    e.expense_date,
    d.department_name,
    e.category,
    e.vendor,
    e.amount,
    dept_avg.avg_dept_amount
FROM expenses e
JOIN departments d ON e.department_id = d.department_id
JOIN (
    SELECT department_id, ROUND(AVG(amount), 2) AS avg_dept_amount
    FROM expenses
    GROUP BY department_id
) dept_avg ON e.department_id = dept_avg.department_id
WHERE e.amount > (dept_avg.avg_dept_amount * 3.5)
ORDER BY e.amount DESC;

-- ─── 14. Monthly Net Profit Summary (Revenue - Expenses) ────────────────────────
WITH rev AS (
    SELECT strftime('%Y-%m', sale_date) AS ym, SUM(total_amount) AS monthly_revenue
    FROM sales
    GROUP BY 1
),
exp AS (
    SELECT strftime('%Y-%m', expense_date) AS ym, SUM(amount) AS monthly_expenses
    FROM expenses
    WHERE approval_status = 'approved'
    GROUP BY 1
)
SELECT 
    rev.ym,
    ROUND(rev.monthly_revenue, 2) AS revenue,
    ROUND(COALESCE(exp.monthly_expenses, 0), 2) AS expenses,
    ROUND(rev.monthly_revenue - COALESCE(exp.monthly_expenses, 0), 2) AS net_profit,
    ROUND(((rev.monthly_revenue - COALESCE(exp.monthly_expenses, 0)) / rev.monthly_revenue) * 100, 2) AS net_margin_pct
FROM rev
LEFT JOIN exp ON rev.ym = exp.ym
ORDER BY rev.ym;

-- ─── 15. Orders Processing Bottlenecks (Delayed vs Total Orders) ────────────────
SELECT 
    d.department_name,
    SUM(op.orders_received) AS total_orders_received,
    SUM(op.orders_completed) AS total_orders_completed,
    SUM(op.orders_delayed) AS total_delayed_orders,
    ROUND(AVG(op.on_time_delivery_pct), 2) AS avg_on_time_rate,
    ROUND(AVG(op.avg_processing_days), 2) AS avg_processing_days
FROM operational_performance op
JOIN departments d ON op.department_id = d.department_id
GROUP BY d.department_id, d.department_name
ORDER BY total_delayed_orders DESC;

-- ─── 16. Revenue Concentration: Top 5% Customers (Percentile Ranking) ─────────
WITH ranked_cust AS (
    SELECT 
        c.customer_id,
        c.company_name,
        SUM(s.total_amount) AS revenue,
        PERCENT_RANK() OVER (ORDER BY SUM(s.total_amount) DESC) AS p_rank
    FROM customers c
    JOIN sales s ON c.customer_id = s.customer_id
    GROUP BY c.customer_id, c.company_name
)
SELECT 
    COUNT(customer_id) AS top_tier_customers,
    ROUND(SUM(revenue), 2) AS revenue_contribution
FROM ranked_cust
WHERE p_rank <= 0.05;

-- ─── 17. Average Discount Offered by Customer Segment ─────────────────────────
SELECT 
    c.segment,
    COUNT(s.sale_id) AS total_sales,
    ROUND(AVG(s.discount_pct), 2) AS avg_discount_pct,
    ROUND(MAX(s.discount_pct), 2) AS max_discount_pct,
    ROUND(SUM(s.total_amount), 2) AS total_segment_revenue
FROM sales s
JOIN customers c ON s.customer_id = c.customer_id
GROUP BY c.segment
ORDER BY avg_discount_pct DESC;

-- ─── 18. Department Headcount & Average Tenured Salaries ───────────────────────
SELECT 
    d.department_name,
    COUNT(e.employee_id) AS active_headcount,
    ROUND(AVG(e.salary), 2) AS avg_salary,
    ROUND(MIN(e.salary), 2) AS min_salary,
    ROUND(MAX(e.salary), 2) AS max_salary
FROM employees e
JOIN departments d ON e.department_id = d.department_id
WHERE e.status = 'active'
GROUP BY d.department_name
ORDER BY avg_salary DESC;

-- ─── 19. Unapproved / Pending Expense Backlog by Department ───────────────────
SELECT 
    d.department_name,
    COUNT(e.expense_id) AS pending_expenses_count,
    ROUND(SUM(e.amount), 2) AS pending_exposure_usd
FROM expenses e
JOIN departments d ON e.department_id = d.department_id
WHERE e.approval_status IN ('pending', 'under_review')
GROUP BY d.department_name
ORDER BY pending_exposure_usd DESC;

-- ─── 20. Lead and Lag Days Between Successive Departmental Orders ──────────────
SELECT 
    record_id,
    department_id,
    fiscal_year || '-' || fiscal_month AS period,
    orders_completed,
    LAG(orders_completed, 1) OVER (PARTITION BY department_id ORDER BY fiscal_year, fiscal_month) AS prior_month_orders,
    LEAD(orders_completed, 1) OVER (PARTITION BY department_id ORDER BY fiscal_year, fiscal_month) AS next_month_orders
FROM operational_performance
LIMIT 20;

-- ─── 21. Sales Distribution by Regional Geo-Zones ─────────────────────────────
SELECT 
    region,
    COUNT(sale_id) AS deal_count,
    ROUND(SUM(total_amount), 2) AS regional_revenue,
    ROUND((SUM(total_amount) / (SELECT SUM(total_amount) FROM sales)) * 100, 2) AS revenue_share_pct
FROM sales
GROUP BY region
ORDER BY regional_revenue DESC;

-- ─── 22. Top 5 Vendors by Total Spend ─────────────────────────────────────────
SELECT 
    vendor,
    COUNT(expense_id) AS transaction_count,
    ROUND(SUM(amount), 2) AS total_paid
FROM expenses
WHERE approval_status = 'approved'
GROUP BY vendor
ORDER BY total_paid DESC
LIMIT 5;

-- ─── 23. Average Cost Per Completed Operational Order ─────────────────────────
SELECT 
    d.department_name,
    ROUND(SUM(op.operational_cost) / NULLIF(SUM(op.orders_completed), 0), 2) AS avg_unit_cost_per_order
FROM operational_performance op
JOIN departments d ON op.department_id = d.department_id
GROUP BY d.department_name
ORDER BY avg_unit_cost_per_order DESC;

-- ─── 24. Quarterly Employee Attrition / Termination Rate ──────────────────────
SELECT 
    strftime('%Y', termination_date) AS term_year,
    COUNT(employee_id) AS terminations_count
FROM employees
WHERE status = 'terminated'
GROUP BY 1
ORDER BY 1 DESC;

-- ─── 25. High Quantity Enterprise Sales (Having Clause Filter) ────────────────
SELECT 
    c.company_name,
    p.product_name,
    s.quantity,
    s.unit_price,
    s.total_amount
FROM sales s
JOIN customers c ON s.customer_id = c.customer_id
JOIN products p ON s.product_id = p.product_id
WHERE c.segment = 'Enterprise'
GROUP BY s.sale_id
HAVING s.quantity >= 15
ORDER BY s.total_amount DESC
LIMIT 15;

-- ─── 26. Unified Financial Ledger Daily Reconciliation ────────────────────────
SELECT 
    transaction_date,
    SUM(CASE WHEN transaction_type = 'credit' THEN amount ELSE 0 END) AS total_credits,
    SUM(CASE WHEN transaction_type = 'debit' THEN amount ELSE 0 END) AS total_debits,
    ROUND(SUM(CASE WHEN transaction_type = 'credit' THEN amount ELSE -amount END), 2) AS net_cashflow
FROM transactions
GROUP BY transaction_date
ORDER BY transaction_date DESC
LIMIT 30;

-- ─── 27. Product Portfolio Price Elasticity & Profit Contribution ──────────────
SELECT 
    p.product_id,
    p.product_name,
    p.category,
    p.unit_price,
    p.unit_cost,
    ROUND(p.unit_price - p.unit_cost, 2) AS unit_margin,
    ROUND(((p.unit_price - p.unit_cost) / p.unit_price) * 100, 2) AS unit_margin_pct,
    COUNT(s.sale_id) AS sales_volume,
    ROUND(SUM(s.total_amount), 2) AS total_sales_volume
FROM products p
LEFT JOIN sales s ON p.product_id = s.product_id
GROUP BY p.product_id, p.product_name, p.category, p.unit_price, p.unit_cost
ORDER BY total_sales_volume DESC;

-- ─── 28. Departments Exceeding Budget Threshold by >10% ────────────────────────
WITH monthly_audit AS (
    SELECT 
        d.department_name,
        b.fiscal_year,
        b.fiscal_month,
        b.approved_amount AS budget,
        COALESCE(SUM(e.amount), 0) AS actual
    FROM budgets b
    JOIN departments d ON b.department_id = d.department_id
    LEFT JOIN expenses e ON b.department_id = e.department_id 
        AND b.fiscal_year = CAST(strftime('%Y', e.expense_date) AS INT)
        AND b.fiscal_month = CAST(strftime('%m', e.expense_date) AS INT)
        AND b.category = e.category
    GROUP BY d.department_name, b.fiscal_year, b.fiscal_month, b.approved_amount
)
SELECT 
    department_name,
    fiscal_year,
    fiscal_month,
    ROUND(budget, 2) AS budget,
    ROUND(actual, 2) AS actual,
    ROUND(((actual - budget) / budget) * 100, 2) AS overrun_pct
FROM monthly_audit
WHERE actual > budget * 1.10
ORDER BY overrun_pct DESC
LIMIT 20;

-- ─── 29. Payment Method Usage & Share of Volume ────────────────────────────────
SELECT 
    payment_method,
    COUNT(sale_id) AS transactions_count,
    ROUND(SUM(total_amount), 2) AS total_settled_amount,
    ROUND((SUM(total_amount) / (SELECT SUM(total_amount) FROM sales)) * 100, 2) AS share_pct
FROM sales
GROUP BY payment_method
ORDER BY total_settled_amount DESC;

-- ─── 30. Executive Multi-Year Company Financial Scorecard ──────────────────────
SELECT 
    strftime('%Y', s.sale_date) AS fiscal_year,
    ROUND(SUM(s.total_amount), 2) AS gross_revenue,
    (SELECT ROUND(SUM(amount), 2) FROM expenses WHERE strftime('%Y', expense_date) = strftime('%Y', s.sale_date) AND approval_status = 'approved') AS operating_expenses,
    ROUND(SUM(s.total_amount) - (SELECT SUM(amount) FROM expenses WHERE strftime('%Y', expense_date) = strftime('%Y', s.sale_date) AND approval_status = 'approved'), 2) AS operating_profit
FROM sales s
GROUP BY strftime('%Y', s.sale_date)
ORDER BY fiscal_year;


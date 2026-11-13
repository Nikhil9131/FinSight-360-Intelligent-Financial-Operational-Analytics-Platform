-- ============================================================
-- FinSight 360 — Master Database Schema
-- File: database/schema/001_create_tables.sql
-- Description: Creates the normalized OLTP schema for
--              NovaTech Solutions' financial & operational data.
-- ============================================================

-- ─── DEPARTMENTS ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS departments (
    department_id   SERIAL PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL UNIQUE,
    location        VARCHAR(100) NOT NULL,
    manager_id      INTEGER,                         -- FK added after employees table
    created_date    DATE NOT NULL DEFAULT CURRENT_DATE,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE
);

COMMENT ON TABLE departments IS 'Company departments across all office locations';

-- ─── EMPLOYEES ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS employees (
    employee_id     SERIAL PRIMARY KEY,
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    email           VARCHAR(255) NOT NULL UNIQUE,
    department_id   INTEGER NOT NULL REFERENCES departments(department_id),
    job_title       VARCHAR(150) NOT NULL,
    salary          NUMERIC(12, 2) NOT NULL CHECK (salary > 0),
    hire_date       DATE NOT NULL,
    termination_date DATE,
    status          VARCHAR(20) NOT NULL DEFAULT 'active'
                    CHECK (status IN ('active', 'inactive', 'on_leave', 'terminated')),
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_employees_department ON employees(department_id);
CREATE INDEX idx_employees_status ON employees(status);

COMMENT ON TABLE employees IS 'All company employees with department assignment and compensation';

-- Now add the FK from departments.manager_id → employees
ALTER TABLE departments
    ADD CONSTRAINT fk_departments_manager
    FOREIGN KEY (manager_id) REFERENCES employees(employee_id);

-- ─── CUSTOMERS ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS customers (
    customer_id       SERIAL PRIMARY KEY,
    company_name      VARCHAR(200) NOT NULL,
    contact_name      VARCHAR(150),
    email             VARCHAR(255),
    phone             VARCHAR(50),
    country           VARCHAR(100) NOT NULL,
    city              VARCHAR(100),
    segment           VARCHAR(50) NOT NULL
                      CHECK (segment IN ('Enterprise', 'Mid-Market', 'SMB', 'Startup')),
    registration_date DATE NOT NULL,
    is_active         BOOLEAN NOT NULL DEFAULT TRUE,
    created_at        TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_customers_segment ON customers(segment);
CREATE INDEX idx_customers_country ON customers(country);

COMMENT ON TABLE customers IS 'B2B customer accounts segmented by size';

-- ─── PRODUCTS ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS products (
    product_id    SERIAL PRIMARY KEY,
    product_name  VARCHAR(200) NOT NULL,
    category      VARCHAR(100) NOT NULL,
    subcategory   VARCHAR(100),
    unit_price    NUMERIC(12, 2) NOT NULL CHECK (unit_price >= 0),
    unit_cost     NUMERIC(12, 2) NOT NULL CHECK (unit_cost >= 0),
    launch_date   DATE,
    status        VARCHAR(20) NOT NULL DEFAULT 'active'
                  CHECK (status IN ('active', 'discontinued', 'planned')),
    created_at    TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_products_category ON products(category);

COMMENT ON TABLE products IS 'Products and services offered by NovaTech Solutions';

-- ─── SALES ───────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sales (
    sale_id       SERIAL PRIMARY KEY,
    sale_date     DATE NOT NULL,
    customer_id   INTEGER NOT NULL REFERENCES customers(customer_id),
    employee_id   INTEGER NOT NULL REFERENCES employees(employee_id),
    product_id    INTEGER NOT NULL REFERENCES products(product_id),
    quantity      INTEGER NOT NULL CHECK (quantity > 0),
    unit_price    NUMERIC(12, 2) NOT NULL CHECK (unit_price >= 0),
    discount_pct  NUMERIC(5, 2) NOT NULL DEFAULT 0
                  CHECK (discount_pct >= 0 AND discount_pct <= 100),
    total_amount  NUMERIC(14, 2) NOT NULL CHECK (total_amount >= 0),
    region        VARCHAR(50) NOT NULL,
    payment_method VARCHAR(50),
    created_at    TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_sales_date ON sales(sale_date);
CREATE INDEX idx_sales_customer ON sales(customer_id);
CREATE INDEX idx_sales_employee ON sales(employee_id);
CREATE INDEX idx_sales_product ON sales(product_id);
CREATE INDEX idx_sales_region ON sales(region);

COMMENT ON TABLE sales IS 'Revenue-generating sales transactions (one row per line item)';

-- ─── EXPENSES ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS expenses (
    expense_id      SERIAL PRIMARY KEY,
    expense_date    DATE NOT NULL,
    department_id   INTEGER NOT NULL REFERENCES departments(department_id),
    category        VARCHAR(100) NOT NULL,
    subcategory     VARCHAR(100),
    vendor          VARCHAR(200),
    description     TEXT,
    amount          NUMERIC(14, 2) NOT NULL CHECK (amount > 0),
    currency        VARCHAR(3) NOT NULL DEFAULT 'USD',
    payment_method  VARCHAR(50),
    approval_status VARCHAR(20) NOT NULL DEFAULT 'approved'
                    CHECK (approval_status IN ('pending', 'approved', 'rejected', 'under_review')),
    approved_by     INTEGER REFERENCES employees(employee_id),
    receipt_number  VARCHAR(100),
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_expenses_date ON expenses(expense_date);
CREATE INDEX idx_expenses_department ON expenses(department_id);
CREATE INDEX idx_expenses_category ON expenses(category);
CREATE INDEX idx_expenses_status ON expenses(approval_status);

COMMENT ON TABLE expenses IS 'All company expenditures tracked by department and category';

-- ─── BUDGETS ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS budgets (
    budget_id       SERIAL PRIMARY KEY,
    department_id   INTEGER NOT NULL REFERENCES departments(department_id),
    fiscal_year     INTEGER NOT NULL CHECK (fiscal_year >= 2020 AND fiscal_year <= 2030),
    fiscal_month    INTEGER NOT NULL CHECK (fiscal_month >= 1 AND fiscal_month <= 12),
    category        VARCHAR(100) NOT NULL,
    approved_amount NUMERIC(14, 2) NOT NULL CHECK (approved_amount >= 0),
    revised_amount  NUMERIC(14, 2),
    approved_date   DATE NOT NULL,
    approved_by     INTEGER REFERENCES employees(employee_id),
    notes           TEXT,
    created_at      TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (department_id, fiscal_year, fiscal_month, category)
);

CREATE INDEX idx_budgets_dept_year ON budgets(department_id, fiscal_year);

COMMENT ON TABLE budgets IS 'Monthly budget allocations per department per expense category';

-- ─── TRANSACTIONS (unified ledger) ──────────────────────────
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id    SERIAL PRIMARY KEY,
    reference_id      INTEGER NOT NULL,
    reference_type    VARCHAR(20) NOT NULL
                      CHECK (reference_type IN ('sale', 'expense', 'refund', 'adjustment')),
    transaction_date  DATE NOT NULL,
    amount            NUMERIC(14, 2) NOT NULL,
    transaction_type  VARCHAR(10) NOT NULL
                      CHECK (transaction_type IN ('credit', 'debit')),
    description       TEXT,
    status            VARCHAR(20) NOT NULL DEFAULT 'completed'
                      CHECK (status IN ('completed', 'pending', 'failed', 'reversed')),
    created_at        TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_transactions_date ON transactions(transaction_date);
CREATE INDEX idx_transactions_ref ON transactions(reference_type, reference_id);
CREATE INDEX idx_transactions_status ON transactions(status);

COMMENT ON TABLE transactions IS 'Unified financial ledger linking sales and expenses';

-- ─── OPERATIONAL PERFORMANCE ─────────────────────────────────
CREATE TABLE IF NOT EXISTS operational_performance (
    record_id            SERIAL PRIMARY KEY,
    department_id        INTEGER NOT NULL REFERENCES departments(department_id),
    fiscal_year          INTEGER NOT NULL,
    fiscal_month         INTEGER NOT NULL,
    orders_received      INTEGER NOT NULL DEFAULT 0,
    orders_completed     INTEGER NOT NULL DEFAULT 0,
    orders_delayed       INTEGER NOT NULL DEFAULT 0,
    orders_cancelled     INTEGER NOT NULL DEFAULT 0,
    operational_cost     NUMERIC(14, 2) NOT NULL DEFAULT 0,
    avg_processing_days  NUMERIC(6, 2),
    on_time_delivery_pct NUMERIC(5, 2),
    customer_satisfaction NUMERIC(3, 1),
    notes                TEXT,
    created_at           TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (department_id, fiscal_year, fiscal_month)
);

COMMENT ON TABLE operational_performance IS 'Monthly operational metrics per department';

-- ─── PIPELINE LOGS ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS pipeline_logs (
    log_id             SERIAL PRIMARY KEY,
    run_id             VARCHAR(50) NOT NULL,
    pipeline_name      VARCHAR(100) NOT NULL,
    step_name          VARCHAR(100),
    status             VARCHAR(20) NOT NULL
                       CHECK (status IN ('started', 'running', 'success', 'failed', 'warning')),
    records_processed  INTEGER DEFAULT 0,
    records_accepted   INTEGER DEFAULT 0,
    records_rejected   INTEGER DEFAULT 0,
    error_message      TEXT,
    start_time         TIMESTAMP NOT NULL DEFAULT NOW(),
    end_time           TIMESTAMP,
    duration_seconds   NUMERIC(10, 2),
    metadata           JSONB,
    created_at         TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_pipeline_logs_run ON pipeline_logs(run_id);
CREATE INDEX idx_pipeline_logs_name ON pipeline_logs(pipeline_name);
CREATE INDEX idx_pipeline_logs_status ON pipeline_logs(status);

COMMENT ON TABLE pipeline_logs IS 'ETL pipeline execution history for auditing and debugging';

-- ─── DATA QUALITY RESULTS ───────────────────────────────────
CREATE TABLE IF NOT EXISTS data_quality_results (
    result_id          SERIAL PRIMARY KEY,
    run_id             VARCHAR(50) NOT NULL,
    table_name         VARCHAR(100) NOT NULL,
    check_name         VARCHAR(200) NOT NULL,
    check_type         VARCHAR(50) NOT NULL
                       CHECK (check_type IN ('completeness', 'uniqueness', 'validity',
                                             'consistency', 'timeliness', 'referential')),
    passed             BOOLEAN NOT NULL,
    metric_value       NUMERIC(10, 4),
    threshold          NUMERIC(10, 4),
    records_checked    INTEGER,
    records_failed     INTEGER,
    details            TEXT,
    created_at         TIMESTAMP NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE data_quality_results IS 'Data quality check results from validation pipeline';

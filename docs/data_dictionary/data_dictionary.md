# FinSight 360 — Data Dictionary

## Simulated Company: NovaTech Solutions Pvt. Ltd.

| Attribute | Value |
|---|---|
| Industry | Technology Services & Consulting |
| Employees | ~350 |
| Annual Revenue | ~$120M |
| Departments | 8 |
| Offices | New York, London, Bangalore |
| Data Period | January 2022 – October 2026 (58 months) |

---

## Table: `departments`

Company organizational units.

| Column | Type | Nullable | Description |
|---|---|---|---|
| department_id | INTEGER (PK) | No | Auto-incrementing primary key |
| department_name | VARCHAR(100) | No | Unique department name |
| location | VARCHAR(100) | No | Office city (New York / London / Bangalore) |
| manager_id | INTEGER (FK → employees) | Yes | Employee ID of the department head |
| created_date | DATE | No | When the department was established |
| is_active | BOOLEAN | No | Whether the department is currently active |

**Row count:** 8

---

## Table: `employees`

All company employees with role, compensation, and status.

| Column | Type | Nullable | Description |
|---|---|---|---|
| employee_id | INTEGER (PK) | No | Auto-incrementing primary key |
| first_name | VARCHAR(100) | No | Employee's first name |
| last_name | VARCHAR(100) | No | Employee's last name |
| email | VARCHAR(255) | No | Unique company email address |
| department_id | INTEGER (FK → departments) | No | Department the employee belongs to |
| job_title | VARCHAR(150) | No | Job title / role |
| salary | NUMERIC(12,2) | No | Annual salary in USD (must be > 0) |
| hire_date | DATE | No | Date the employee was hired |
| termination_date | DATE | Yes | Date of termination (NULL if still employed) |
| status | VARCHAR(20) | No | active / inactive / on_leave / terminated |

**Row count:** ~352  
**Intentional noise:** ~1% missing `termination_date` values for testing

---

## Table: `customers`

B2B customer accounts.

| Column | Type | Nullable | Description |
|---|---|---|---|
| customer_id | INTEGER (PK) | No | Auto-incrementing primary key |
| company_name | VARCHAR(200) | No | Customer company name |
| contact_name | VARCHAR(150) | Yes | Primary contact person |
| email | VARCHAR(255) | Yes | Contact email address |
| phone | VARCHAR(50) | Yes | Contact phone number |
| country | VARCHAR(100) | No | Customer's country |
| city | VARCHAR(100) | Yes | Customer's city |
| segment | VARCHAR(50) | No | Enterprise / Mid-Market / SMB / Startup |
| registration_date | DATE | No | When the customer registered |
| is_active | BOOLEAN | No | Whether the customer account is active |

**Row count:** 500  
**Segment distribution:** 15% Enterprise, 30% Mid-Market, 35% SMB, 20% Startup  
**Intentional noise:** ~2% missing phone/email/city values

---

## Table: `products`

Product and service catalog.

| Column | Type | Nullable | Description |
|---|---|---|---|
| product_id | INTEGER (PK) | No | Auto-incrementing primary key |
| product_name | VARCHAR(200) | No | Product or service name |
| category | VARCHAR(100) | No | Software Licenses / Consulting / Cloud / Training / Support |
| subcategory | VARCHAR(100) | Yes | Detailed sub-classification |
| unit_price | NUMERIC(12,2) | No | List price per unit in USD |
| unit_cost | NUMERIC(12,2) | No | Cost to NovaTech per unit in USD |
| launch_date | DATE | Yes | Product launch date |
| status | VARCHAR(20) | No | active / discontinued / planned |

**Row count:** 22

---

## Table: `sales`

Revenue-generating sales transactions (one row per line item).

| Column | Type | Nullable | Description |
|---|---|---|---|
| sale_id | INTEGER (PK) | No | Auto-incrementing primary key |
| sale_date | DATE | No | Date of the sale |
| customer_id | INTEGER (FK → customers) | No | Purchasing customer |
| employee_id | INTEGER (FK → employees) | No | Sales representative |
| product_id | INTEGER (FK → products) | No | Product sold |
| quantity | INTEGER | No | Number of units sold (must be > 0) |
| unit_price | NUMERIC(12,2) | No | Actual unit price charged |
| discount_pct | NUMERIC(5,2) | Yes | Discount percentage (0–25%) |
| total_amount | NUMERIC(14,2) | No | quantity × unit_price × (1 − discount%) |
| region | VARCHAR(50) | No | North America / Europe / Asia Pacific / Middle East |
| payment_method | VARCHAR(50) | Yes | Credit Card / Bank Transfer / Wire / ACH / Check |

**Row count:** ~50,400 (50K base + ~400 injected duplicates)  
**Seasonal patterns:** Q4 +30%, Q1 −15%  
**Growth:** ~12% year-over-year  
**Intentional noise:** ~2% missing payment_method/discount, ~0.8% duplicates, ~0.5% anomalous amounts

---

## Table: `expenses`

All company expenditures tracked by department and category.

| Column | Type | Nullable | Description |
|---|---|---|---|
| expense_id | INTEGER (PK) | No | Auto-incrementing primary key |
| expense_date | DATE | No | Date the expense was incurred |
| department_id | INTEGER (FK → departments) | No | Department that incurred the expense |
| category | VARCHAR(100) | No | Expense category (Rent, Software, Travel, etc.) |
| subcategory | VARCHAR(100) | Yes | Detailed sub-classification |
| vendor | VARCHAR(200) | Yes | Vendor / supplier name |
| description | TEXT | Yes | Expense description |
| amount | NUMERIC(14,2) | No | Expense amount in USD (must be > 0) |
| currency | VARCHAR(3) | No | Currency code (always USD) |
| payment_method | VARCHAR(50) | Yes | Payment method used |
| approval_status | VARCHAR(20) | No | pending / approved / rejected / under_review |
| approved_by | INTEGER (FK → employees) | Yes | Employee who approved |
| receipt_number | VARCHAR(100) | Yes | Receipt reference number |

**Row count:** ~30,300 (30K base + ~300 injected duplicates)  
**Approval distribution:** ~95% approved, ~3% pending, ~2% rejected  
**Intentional noise:** ~3% missing vendor/subcategory/receipt, ~1% duplicates, ~0.5% anomalous amounts

---

## Table: `budgets`

Monthly budget allocations per department per expense category.

| Column | Type | Nullable | Description |
|---|---|---|---|
| budget_id | INTEGER (PK) | No | Auto-incrementing primary key |
| department_id | INTEGER (FK → departments) | No | Department |
| fiscal_year | INTEGER | No | Budget year (2022–2026) |
| fiscal_month | INTEGER | No | Budget month (1–12) |
| category | VARCHAR(100) | No | Budget category (matches expense categories) |
| approved_amount | NUMERIC(14,2) | No | Originally approved budget |
| revised_amount | NUMERIC(14,2) | Yes | Revised amount (if budget was adjusted) |
| approved_date | DATE | No | Date budget was approved |
| approved_by | INTEGER (FK → employees) | Yes | Approver |
| notes | TEXT | Yes | Additional notes |

**Row count:** ~4,176  
**Budget formula:** Average actual spend × 1.10–1.25 buffer  
**Revisions:** ~15% of records have revised amounts

---

## Table: `transactions`

Unified financial ledger linking all sales and expenses.

| Column | Type | Nullable | Description |
|---|---|---|---|
| transaction_id | INTEGER (PK) | No | Auto-incrementing primary key |
| reference_id | INTEGER | No | Points to sale_id or expense_id |
| reference_type | VARCHAR(20) | No | sale / expense / refund / adjustment |
| transaction_date | DATE | No | Date of the transaction |
| amount | NUMERIC(14,2) | No | Transaction amount |
| transaction_type | VARCHAR(10) | No | credit (revenue) / debit (expense) |
| description | TEXT | Yes | Human-readable description |
| status | VARCHAR(20) | No | completed / pending / failed / reversed |

**Row count:** ~79,000 (one per sale + one per approved expense)

---

## Table: `operational_performance`

Monthly operational metrics per department.

| Column | Type | Nullable | Description |
|---|---|---|---|
| record_id | INTEGER (PK) | No | Auto-incrementing primary key |
| department_id | INTEGER (FK → departments) | No | Department |
| fiscal_year | INTEGER | No | Year |
| fiscal_month | INTEGER | No | Month |
| orders_received | INTEGER | No | Total orders received that month |
| orders_completed | INTEGER | No | Orders successfully completed |
| orders_delayed | INTEGER | No | Orders delivered late |
| orders_cancelled | INTEGER | No | Orders cancelled |
| operational_cost | NUMERIC(14,2) | No | Total operational cost for the month |
| avg_processing_days | NUMERIC(6,2) | Yes | Average days to process an order |
| on_time_delivery_pct | NUMERIC(5,2) | Yes | Percentage of on-time deliveries |
| customer_satisfaction | NUMERIC(3,1) | Yes | Average CSAT score (1.0–5.0) |
| notes | TEXT | Yes | Additional context |

**Row count:** ~464 (8 departments × 58 months)  
**Trends:** Completion rate improves over time (process maturity), Q4 volume spikes

---

## Data Quality Issues (Intentional — For Testing)

| Issue | Table | Column(s) | Approximate Rate |
|---|---|---|---|
| Missing values | sales | payment_method, discount_pct | ~2% |
| Missing values | expenses | vendor, subcategory, receipt_number | ~3% |
| Missing values | customers | phone, email, city | ~2% |
| Duplicate rows | sales | all columns | ~0.8% |
| Duplicate rows | expenses | all columns | ~1.0% |
| Anomalous amounts | sales | total_amount | ~0.5% |
| Anomalous amounts | expenses | amount | ~0.5% |

These issues are intentional to test the data cleaning pipeline in Phase 4.

---

## Relationships

```
departments ──1:N──→ employees
departments ──1:N──→ expenses
departments ──1:N──→ budgets
departments ──1:N──→ operational_performance
employees   ──1:N──→ sales
customers   ──1:N──→ sales
products    ──1:N──→ sales
sales       ──1:1──→ transactions (reference_type = 'sale')
expenses    ──1:1──→ transactions (reference_type = 'expense')
```


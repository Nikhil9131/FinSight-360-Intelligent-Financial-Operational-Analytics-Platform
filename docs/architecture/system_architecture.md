# FinSight 360 — End-to-End System Architecture

## Architecture Overview

```
[ Data Sources ]
├── CSV Files (Departments, Employees, Customers, Products, Sales, Expenses)
├── JSON Files (Budgets, Transactions)
├── Synthetic Generator (NovaTechDataGenerator)
└── REST API Ingestion Layer
       │
       ▼
[ Ingestion & Staging ]
├── File Reader (Format detection, metadata audit logging)
└── Raw Ingestion Queue
       │
       ▼
[ Cleaning & Transformation (Pandas & NumPy) ]
├── Deduplication Engine (Primary key & compound checks)
├── Date Normalizer (ISO 8601 YYYY-MM-DD enforcement)
├── Missing Value Imputation (Domain-specific business rules)
└── Currency & Monetary Recalculation Engine
       │
       ▼
[ Data Quality & Governance Engine ]
├── 17 Automated Assertions (Completeness, Uniqueness, Validity, Referential Integrity)
├── Z-Score & IQR Outlier Auditing
└── Quality Reports & Audit Logs (pipeline_logs, data_quality_results)
       │
       ▼
[ Enterprise Storage Layer ]
├── PostgreSQL Relational & Star Schema Data Warehouse
└── Local SQLite High-Speed Analytical Engine (finsight360.db)
       │
       ├── Dimension Tables: dim_date, dim_department, dim_employee, dim_customer, dim_product
       └── Fact Tables: fact_sales, fact_expenses, fact_budget, fact_operations, transactions
       │
       ▼
[ Analytics, Machine Learning & Intelligence ]
├── Financial KPI Engine (Revenue, COGS, Gross Profit, OpEx, Net Profit, MoM & YoY Growth)
├── Time-Series Forecasting (Moving Average, Linear Regression, Holt's Exponential Smoothing)
└── Risk & Anomaly Detection (Robust Z-Score, IQR bounds, Diagnostic reason classification)
       │
       ▼
[ Delivery & Presentation Layer ]
├── Power BI Executive Suite (5 Dashboards, 30+ DAX measures, Vanilla Theme)
├── Automated Excel Workbook (Multi-tab OpenPyXL generator with formatted accounting styles)
├── VBA Financial Macros (One-click PDF export, automated data sync, conditional alerting)
└── Executive Management Briefing (Print-ready HTML/PDF reporting packets)
```

## Star Schema Data Model

The analytical model organizes operational facts and dimensional contexts:

| Entity | Type | Primary Key | Description |
|---|---|---|---|
| `dim_date` | Dimension | `date_key` (YYYYMMDD) | Calendar dimension spanning 2022–2027 with fiscal year, quarter, month, and day-of-week attributes |
| `dim_department` | Dimension | `department_id` | Organizational divisions, locations, and headcount aggregates |
| `dim_employee` | Dimension | `employee_id` | Workforce demographics, roles, tenures, and annualized payroll compensation |
| `dim_customer` | Dimension | `customer_id` | Client accounts, countries, segments (Enterprise, Mid-Market, SMB, Startup) |
| `dim_product` | Dimension | `product_id` | Catalog offerings, unit list prices, unit cost of goods, and gross margins |
| `fact_sales` | Fact | `sale_id` | Revenue-generating line-item transactions with discounts and regional markers |
| `fact_expenses` | Fact | `expense_id` | Corporate expenditures with departmental and categorical allocation |
| `fact_budget` | Fact | `budget_id` | Monthly departmental budget ceilings |
| `fact_operations` | Fact | `record_id` | Monthly order counts, delayed orders, cycle time days, CSAT ratings |
| `transactions` | Fact | `transaction_id` | Unified financial ledger reconciling all credit and debit cash flows |


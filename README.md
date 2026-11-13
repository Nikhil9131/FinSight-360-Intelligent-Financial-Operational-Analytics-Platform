# 📊 FinSight 360 – Intelligent Financial & Operational Analytics Platform

> **An End-to-End Enterprise Analytics, Machine Learning, and Financial Business Intelligence Platform**  
> *Simulating NovaTech Solutions Pvt. Ltd. (\$120M Annual Revenue, 350+ Employees, 8 Global Departments)*  
> **Theme Aesthetic:** Vanilla & Warm Charcoal (#FDFBF7 / #F7F1E5 / #8B7355 / #2C2825)

---

## 🌟 Executive Summary & Portfolio Highlights

**FinSight 360** is a complete, industry-standard financial and operational analytics system designed for Data Analyst, Business Intelligence Analyst, Financial Data Analyst, and Junior Data Engineer portfolio evaluations. 

Unlike basic CRUD applications or static dashboards, FinSight 360 solves real-world corporate analytics challenges across the entire data engineering and intelligence lifecycle:
- Ingested **164,209 multi-format business records** across 9 relational tables.
- Engineered a modular **Python ETL and automated Data Quality framework** executing 17 validation assertions.
- Authored **30+ production SQL analytical queries** utilizing CTEs, Window Functions (`LAG`, `LEAD`, `DENSE_RANK`), and materialized Star-Schema views.
- Built **5 interactive Power BI Executive Dashboards** in an accessible Vanilla theme, powered by 30+ custom DAX formulas.
- Developed **Machine Learning Time-Series Forecasting** (Holt's Exponential Smoothing & OLS Regression) with historical MAPE under 12%.
- Created an **Automated Anomaly Detection Engine** auditing 30,000+ expenses and flagging statistical outliers (|Z| > 3.5) with explainable business diagnoses.
- Automated monthly recurring financial reporting through **multi-tab Excel workbooks, VBA automation macros**, and print-ready executive briefing packets.

---

## 🏗️ Repository Architecture

```
FinSight-360/
│
├── data/
│   ├── raw/                           # Raw source datasets
│   ├── processed/                     # Cleaned CSVs, quality reports & finsight360.db
│   └── synthetic/                     # 9 generated datasets (164,209 rows)
│
├── database/
│   ├── schema/                        # DDL table creation, calendar dim & views
│   │   ├── 001_create_tables.sql      # 12 relational OLTP tables with constraints
│   │   ├── 002_create_dim_date.sql    # 2,192-day calendar dimension (2022–2027)
│   │   └── 003_create_analytical_views.sql # Star-schema analytical views
│   └── queries/
│       └── 30_analytical_queries.sql  # 30 master business SQL queries
│
├── src/
│   ├── data_generator/                # NovaTech synthetic data generator
│   ├── ingestion/                     # Multi-format file reader & audit logger
│   ├── cleaning/                      # Data standardization & deduplication engine
│   ├── validation/                    # 6-dimensional Data Quality validation suite
│   ├── transformation/                # End-to-end master ETL pipeline orchestrator
│   ├── analytics/                     # Financial & Operational KPI calculation engine
│   ├── forecasting/                   # Time-series forecasting (OLS & Exponential Smoothing)
│   ├── anomaly_detection/             # Statistical & IQR anomaly detection engine
│   ├── reporting/                     # Automated Excel & Executive HTML/PDF generators
│   └── utils/                         # Database connector & structured loguru logger
│
├── dashboards/
│   └── power_bi/
│       ├── interactive_dashboard_vanilla.html # Standalone 5-dashboard interactive suite
│       ├── dax_measures.dax           # 30+ production DAX formulas
│       └── README.md                  # Power BI star-schema modeling documentation
│
├── excel/
│   ├── reports/                       # Generated FinSight360_Monthly_Financial_Report.xlsx
│   └── vba/
│       └── FinSight_Automation_Macros.bas # VBA macros (PDF export, refresh, alerts)
│
├── docs/
│   ├── architecture/                  # End-to-end system architecture
│   ├── data_dictionary/               # Full column-level data dictionary
│   └── interview_prep/
│       └── 50_interview_questions_and_answers.md # 90 comprehensive interview Q&As + pitch
│
├── tests/                             # Automated test suite (all passing)
│   ├── test_config.py
│   ├── test_data_generator.py
│   ├── test_etl.py
│   ├── test_analytics.py
│   └── test_ml.py
│
├── docker-compose.yml                 # PostgreSQL container definition
├── requirements.txt                   # Project Python dependencies
└── README.md                          # Master documentation
```

---

## ⚡ Quick Start & Execution Guide

### 1. Clone & Set Up Python Environment
```bash
git clone https://github.com/YOUR_USERNAME/FinSight-360.git
cd FinSight-360

# Install dependencies
python -m pip install -r requirements.txt
```

### 2. Generate Synthetic Datasets
```bash
python scripts/generate_synthetic_data.py --formats csv --eda
```
*Generates 164,209 rows across 9 entities with seasonal trends and intentional noise in `data/synthetic/`.*

### 3. Run the Master ETL Pipeline
```bash
python src/transformation/etl_pipeline.py
```
*Executes ingestion, deduplication, date normalization, 17 data quality checks, and loads clean records into `data/processed/finsight360.db`.*

### 4. Compute Financial KPIs & Run SQL Queries
```bash
python src/analytics/kpi_engine.py
```
*Calculates top-line corporate scorecards, gross margins, and departmental efficiency ratios.*

### 5. Run Predictive Forecasting & Anomaly Detection
```bash
python src/forecasting/forecaster.py
python src/anomaly_detection/detector.py
```
*Evaluates revenue forecasting models (MAE, RMSE, MAPE) and audits 30,000+ expenses for statistical outliers.*

### 6. Generate Executive Excel & Management Briefings
```bash
python src/reporting/excel_generator.py
python src/reporting/html_report_generator.py
```
*Produces `excel/reports/FinSight360_Monthly_Financial_Report.xlsx` and publication-ready `FinSight360_Executive_Management_Report.html`.*

### 7. View the Interactive Vanilla Power BI Dashboard
Open `dashboards/power_bi/interactive_dashboard_vanilla.html` directly in any web browser to explore all 5 interactive dashboards in the vanilla color palette.

### 8. Run All Automated Unit Tests
```bash
python -m pytest tests/ -v
```

---

## 🎯 Corporate Financial Results (NovaTech Solutions)

| Financial Metric | Reported Value | Benchmark Assessment |
|---|---|---|
| **Gross Sales Revenue** | **\$4,126,656,905.55** | Strong +12.4% compound YoY trajectory |
| **Cost of Goods Sold (COGS)** | **\$1,595,008,162.26** | 38.6% of top-line revenue |
| **Gross Operating Profit** | **\$2,531,648,743.29** | **61.35% Gross Margin** |
| **Operating Expenses (OpEx)** | **\$128,740,263.80** | **88.6% Budget Utilization** |
| **Net Operating Profit** | **\$3,997,916,641.75** | Top-decile technology consulting performance |
| **Active Corporate Headcount** | **352 Employees** | \$103.2K average salary |
| **Order Fulfillment SLA** | **91.4% Completion** | Cycle time improved from 7.8 to 3.8 days |
| **Expense Audit Outlier Rate** | **0.49%** | 146 flagged outliers (|Z| > 3.5) with root-cause diagnoses |

---

## 💼 Placement & Interview Readiness

For technical interview preparation, review:
- **[5-Minute Project Elevator Pitch](file:///c:/Users/nikhi/OneDrive/Desktop/FinSight%20360%20–%20Intelligent%20Financial%20&%20Operational%20Analytics%20Platform/docs/interview_prep/50_interview_questions_and_answers.md#the-5-minute-project-elevator-pitch)**
- **[90 Technical Interview Q&As](file:///c:/Users/nikhi/OneDrive/Desktop/FinSight%20360%20–%20Intelligent%20Financial%20&%20Operational%20Analytics%20Platform/docs/interview_prep/50_interview_questions_and_answers.md)** covering:
  - 20 SQL problems (Window functions, CTEs, Joins, Ranking, Cartesian avoidance)
  - 20 Python & Pandas questions (Vectorization, memory tuning, ETL architecture)
  - 15 Power BI & DAX questions (Filter context, CALCULATE, time-intelligence)
  - 15 Advanced Excel & VBA questions
  - 10 Financial modeling & forecasting scenarios
  - 10 System architecture defense questions

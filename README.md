# 📊 FinSight 360 — Intelligent Financial & Operational Analytics Platform

> End-to-end analytics platform for financial performance monitoring, forecasting, anomaly detection, and automated reporting.

## 🏢 Simulated Company

**NovaTech Solutions Pvt. Ltd.** — A mid-sized technology services company (~350 employees, ~$120M annual revenue) across 8 departments and 3 global offices.

## 🎯 What This Project Does

| Capability | Technology |
|---|---|
| Data ingestion from CSV, Excel, JSON, APIs | Python, Pandas |
| Data cleaning & validation pipeline | Python, Pandas, Custom Framework |
| Normalized database + analytical model | PostgreSQL, SQL |
| 30+ analytical SQL queries (CTEs, window functions) | SQL |
| 5 interactive executive dashboards | Power BI, DAX |
| Revenue & expense forecasting | Scikit-learn, Statsmodels |
| Transaction anomaly detection | Isolation Forest, Z-score |
| Automated Excel & PDF reports | OpenPyXL, VBA, FPDF |

## 🚧 Status

**Phase 1: Requirement Analysis** ✅ Complete

---

## 📁 Project Structure

```
FinSight-360/
├── data/                   # Raw, processed, external, synthetic datasets
├── database/               # Schema, migrations, views, SQL queries
├── src/                    # Python source code (modular packages)
├── dashboards/             # Power BI files and screenshots
├── excel/                  # Templates, reports, VBA macros
├── automation/             # Pipeline orchestration
├── tests/                  # Unit and integration tests
├── docs/                   # Architecture, data dictionary, KPI docs
├── notebooks/              # EDA and analysis notebooks
├── logs/                   # Pipeline execution logs
├── scripts/                # Utility scripts
├── config/                 # Configuration files
├── .env.example            # Environment variable template
├── requirements.txt        # Python dependencies
├── docker-compose.yml      # PostgreSQL container (optional)
└── README.md               # This file
```

## 🛠️ Setup

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/FinSight-360.git
cd FinSight-360

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env
# Edit .env with your PostgreSQL credentials

# 5. Set up database (details in docs/)
# Option A: Docker
docker-compose up -d

# Option B: Local PostgreSQL
# Run database/schema/create_tables.sql
```

## 📄 License

This project is for educational and portfolio purposes.


"""
FinSight 360 - NovaTech Solutions Synthetic Data Generator
============================================================
Generates realistic, interrelated business datasets simulating a mid-sized
technology services company over Jan 2022 – Oct 2026 (58 months).

Design Principles:
  - Referential integrity: all foreign keys valid
  - Seasonal patterns: Q4 revenue spikes, Q1 dips, summer hiring
  - Growth trends: ~12% YoY revenue growth
  - Intentional noise: ~2% missing values, ~1% duplicates, ~0.5% anomalies
  - Reproducibility: seeded random number generator

Usage:
    from src.data_generator import NovaTechDataGenerator
    gen = NovaTechDataGenerator(seed=42)
    datasets = gen.generate_all()
    gen.save_all(datasets, output_dir="data/synthetic")
"""

import random
import uuid
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from src.utils.logger import get_logger

logger = get_logger("data_generator")


# ═══════════════════════════════════════════════════════════════
#  CONFIGURATION CONSTANTS
# ═══════════════════════════════════════════════════════════════

# Simulation period
START_DATE = date(2022, 1, 1)
END_DATE = date(2026, 10, 31)

# Company structure
DEPARTMENTS = [
    {"name": "Engineering",  "location": "Bangalore",  "headcount_target": 85},
    {"name": "Sales",        "location": "New York",   "headcount_target": 55},
    {"name": "Marketing",    "location": "New York",   "headcount_target": 35},
    {"name": "HR",           "location": "London",     "headcount_target": 20},
    {"name": "Finance",      "location": "London",     "headcount_target": 22},
    {"name": "Operations",   "location": "Bangalore",  "headcount_target": 50},
    {"name": "R&D",          "location": "Bangalore",  "headcount_target": 55},
    {"name": "Support",      "location": "New York",   "headcount_target": 30},
]

# Job titles per department with salary ranges (annual USD)
JOB_TITLES = {
    "Engineering":  [
        ("Software Engineer",       70000, 110000),
        ("Senior Software Engineer", 105000, 155000),
        ("Tech Lead",               130000, 175000),
        ("Engineering Manager",     150000, 200000),
        ("DevOps Engineer",          80000, 130000),
        ("QA Engineer",              65000, 100000),
    ],
    "Sales": [
        ("Sales Representative",     55000, 85000),
        ("Senior Sales Executive",   80000, 120000),
        ("Account Manager",          75000, 115000),
        ("Sales Manager",           110000, 160000),
        ("Business Development Rep", 60000, 90000),
    ],
    "Marketing": [
        ("Marketing Analyst",        55000, 85000),
        ("Content Strategist",       60000, 90000),
        ("Digital Marketing Manager", 85000, 130000),
        ("Marketing Manager",       100000, 150000),
        ("SEO Specialist",           55000, 80000),
    ],
    "HR": [
        ("HR Coordinator",           45000, 65000),
        ("HR Business Partner",      70000, 110000),
        ("Recruiter",                55000, 85000),
        ("HR Manager",              100000, 145000),
    ],
    "Finance": [
        ("Financial Analyst",        65000, 100000),
        ("Senior Accountant",        75000, 115000),
        ("Controller",              110000, 160000),
        ("Finance Manager",         120000, 170000),
        ("Accounts Payable Clerk",   42000, 60000),
    ],
    "Operations": [
        ("Operations Analyst",       55000, 85000),
        ("Operations Coordinator",   45000, 70000),
        ("Operations Manager",      100000, 145000),
        ("Supply Chain Analyst",     60000, 95000),
        ("Logistics Coordinator",    48000, 72000),
    ],
    "R&D": [
        ("Research Scientist",       90000, 140000),
        ("Senior Researcher",       120000, 170000),
        ("Data Scientist",           85000, 135000),
        ("ML Engineer",              95000, 150000),
        ("R&D Manager",             140000, 190000),
    ],
    "Support": [
        ("Support Specialist",       42000, 65000),
        ("Senior Support Engineer",  60000, 95000),
        ("Support Team Lead",        80000, 115000),
        ("Technical Support Manager", 95000, 140000),
    ],
}

# Customer segments
CUSTOMER_SEGMENTS = ["Enterprise", "Mid-Market", "SMB", "Startup"]
CUSTOMER_COUNTRIES = [
    ("United States", ["New York", "San Francisco", "Chicago", "Austin", "Seattle"], 0.35),
    ("United Kingdom", ["London", "Manchester", "Edinburgh"], 0.15),
    ("India", ["Mumbai", "Bangalore", "Delhi", "Hyderabad"], 0.15),
    ("Germany", ["Berlin", "Munich", "Frankfurt"], 0.10),
    ("Canada", ["Toronto", "Vancouver", "Montreal"], 0.08),
    ("Australia", ["Sydney", "Melbourne"], 0.07),
    ("Singapore", ["Singapore"], 0.05),
    ("Japan", ["Tokyo", "Osaka"], 0.05),
]

# Product catalog
PRODUCTS = [
    # (name, category, subcategory, price_range, cost_pct_of_price)
    ("CloudSync Pro",         "Software Licenses",    "Cloud Platform",     (5000, 25000),  0.20),
    ("CloudSync Enterprise",  "Software Licenses",    "Cloud Platform",     (25000, 80000), 0.18),
    ("DataVault Standard",    "Software Licenses",    "Data Management",    (3000, 15000),  0.22),
    ("DataVault Premium",     "Software Licenses",    "Data Management",    (15000, 50000), 0.19),
    ("SecureShield Basic",    "Software Licenses",    "Security",           (2000, 8000),   0.25),
    ("SecureShield Advanced", "Software Licenses",    "Security",           (8000, 35000),  0.21),
    ("AI Analytics Suite",    "Software Licenses",    "Analytics",          (10000, 60000), 0.15),
    ("DevOps Toolkit",        "Software Licenses",    "Developer Tools",    (1500, 6000),   0.28),
    ("Strategy Consulting",   "Consulting Services",  "Strategy",           (15000, 75000), 0.45),
    ("Tech Implementation",   "Consulting Services",  "Implementation",     (20000, 100000),0.40),
    ("Data Migration",        "Consulting Services",  "Migration",          (10000, 50000), 0.42),
    ("Security Audit",        "Consulting Services",  "Security",           (8000, 40000),  0.38),
    ("Cloud Hosting - Basic", "Cloud Services",       "Hosting",            (500, 3000),    0.55),
    ("Cloud Hosting - Pro",   "Cloud Services",       "Hosting",            (3000, 12000),  0.50),
    ("Managed Database",      "Cloud Services",       "Database",           (1000, 8000),   0.52),
    ("API Gateway Service",   "Cloud Services",       "API",                (800, 5000),    0.48),
    ("Onboarding Training",   "Training",             "Onboarding",         (2000, 8000),   0.35),
    ("Advanced Certification","Training",             "Certification",      (3000, 12000),  0.30),
    ("Custom Workshop",       "Training",             "Workshop",           (5000, 20000),  0.38),
    ("Bronze Support Plan",   "Support Plans",        "Standard",           (1000, 5000),   0.60),
    ("Silver Support Plan",   "Support Plans",        "Priority",           (5000, 15000),  0.55),
    ("Gold Support Plan",     "Support Plans",        "Premium",            (15000, 40000), 0.50),
]

# Expense categories per department (with monthly range in USD)
EXPENSE_CATEGORIES = {
    "Salaries":            (None, None),       # computed from employee salaries
    "Office Rent":         (8000, 25000),
    "Software & Tools":    (3000, 15000),
    "Travel & Transport":  (2000, 12000),
    "Marketing & Ads":     (5000, 40000),
    "Training & Development": (1000, 8000),
    "Equipment & Hardware": (2000, 20000),
    "Utilities":           (1500, 5000),
    "Professional Services": (3000, 18000),
    "Miscellaneous":       (500, 4000),
}

VENDORS = [
    "Amazon Web Services", "Microsoft Azure", "Google Cloud", "Salesforce",
    "HubSpot", "Slack Technologies", "Zoom Communications", "Adobe Systems",
    "WeWork Spaces", "Regus Office", "Dell Technologies", "Lenovo",
    "United Airlines", "British Airways", "Marriott Hotels", "FedEx",
    "LinkedIn Ads", "Google Ads", "Facebook Ads", "Coursera Business",
    "Udemy Business", "PwC Consulting", "Deloitte Advisory", "KPMG",
    "AT&T Business", "Verizon Enterprise", "Staples Office", "Office Depot",
]

PAYMENT_METHODS = ["Credit Card", "Bank Transfer", "Wire Transfer", "ACH", "Check"]

REGIONS = ["North America", "Europe", "Asia Pacific", "Middle East"]

# First and last names for realistic employee generation
FIRST_NAMES = [
    "James","Mary","Robert","Patricia","John","Jennifer","Michael","Linda",
    "David","Elizabeth","William","Barbara","Richard","Susan","Joseph","Jessica",
    "Thomas","Sarah","Christopher","Karen","Charles","Lisa","Daniel","Nancy",
    "Matthew","Betty","Anthony","Margaret","Mark","Sandra","Donald","Ashley",
    "Steven","Dorothy","Andrew","Kimberly","Joshua","Emily","Arun","Priya",
    "Rajesh","Deepa","Amit","Sneha","Vikram","Ananya","Suresh","Pooja",
    "Rahul","Kavita","Sanjay","Meera","Oliver","Charlotte","Harry","Amelia",
    "George","Isla","Edward","Sophie","Arthur","Mia","Henry","Isabella",
    "Alexander","Grace","Ethan","Lily","Noah","Chloe","Lucas","Ella",
]

LAST_NAMES = [
    "Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis",
    "Rodriguez","Martinez","Hernandez","Lopez","Gonzalez","Wilson","Anderson",
    "Thomas","Taylor","Moore","Jackson","Martin","Lee","Perez","Thompson",
    "White","Harris","Sanchez","Clark","Ramirez","Lewis","Robinson","Walker",
    "Young","Allen","King","Wright","Scott","Torres","Nguyen","Hill",
    "Patel","Sharma","Kumar","Singh","Gupta","Reddy","Joshi","Mehta",
    "Verma","Shah","Nair","Iyer","Rao","Menon","Pillai","Bhat",
    "Campbell","Mitchell","Roberts","Carter","Phillips","Evans","Turner","Parker",
]


# ═══════════════════════════════════════════════════════════════
#  MAIN GENERATOR CLASS
# ═══════════════════════════════════════════════════════════════

class NovaTechDataGenerator:
    """
    Generates all synthetic datasets for NovaTech Solutions.

    Ensures referential integrity, realistic distributions, seasonal
    patterns, and intentional data quality issues for testing.

    Args:
        seed: Random seed for reproducibility.
    """

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        random.seed(seed)

        # Generated DataFrames (populated by generate_all)
        self.departments: pd.DataFrame | None = None
        self.employees: pd.DataFrame | None = None
        self.customers: pd.DataFrame | None = None
        self.products: pd.DataFrame | None = None
        self.sales: pd.DataFrame | None = None
        self.expenses: pd.DataFrame | None = None
        self.budgets: pd.DataFrame | None = None
        self.transactions: pd.DataFrame | None = None
        self.operational_performance: pd.DataFrame | None = None

    # ─── DEPARTMENTS ──────────────────────────────────────────

    def generate_departments(self) -> pd.DataFrame:
        """Generate 8 departments with locations."""
        logger.info("Generating departments...")
        records = []
        for i, dept in enumerate(DEPARTMENTS, start=1):
            records.append({
                "department_id": i,
                "department_name": dept["name"],
                "location": dept["location"],
                "manager_id": None,   # will be set after employees are generated
                "created_date": date(2020, 1, 1),
                "is_active": True,
            })
        df = pd.DataFrame(records)
        self.departments = df
        logger.info("  → {} departments generated", len(df))
        return df

    # ─── EMPLOYEES ────────────────────────────────────────────

    def generate_employees(self) -> pd.DataFrame:
        """
        Generate ~350 employees across 8 departments.

        Features:
          - Realistic job titles and salary ranges per department
          - Hire dates spread over 2018–2026 (older employees more senior)
          - ~5% terminated employees
          - ~3% on leave
          - Unique email addresses
        """
        logger.info("Generating employees...")
        if self.departments is None:
            self.generate_departments()

        records = []
        emp_id = 1
        used_emails = set()

        for _, dept in self.departments.iterrows():
            dept_name = dept["department_name"]
            target = DEPARTMENTS[dept["department_id"] - 1]["headcount_target"]
            titles = JOB_TITLES[dept_name]

            for _ in range(target):
                # Pick a job title (weighted: more junior roles)
                weights = list(range(len(titles), 0, -1))
                title_info = random.choices(titles, weights=weights, k=1)[0]
                job_title, sal_low, sal_high = title_info

                # Salary with realistic distribution (slightly right-skewed)
                salary = round(self.rng.triangular(sal_low, sal_low * 1.1, sal_high), 2)

                # Hire date: senior titles tend to have earlier dates
                seniority_factor = titles.index(title_info) / len(titles)
                earliest = date(2018, 1, 1)
                latest = date(2026, 6, 30)
                range_days = (latest - earliest).days
                hire_offset = int(range_days * (1 - seniority_factor * 0.6) * self.rng.random())
                hire_date = earliest + timedelta(days=hire_offset)

                # Status
                status_roll = self.rng.random()
                if status_roll < 0.05:
                    status = "terminated"
                    term_date = hire_date + timedelta(days=int(self.rng.integers(180, 1500)))
                    if term_date > END_DATE:
                        status = "active"
                        term_date = None
                elif status_roll < 0.08:
                    status = "on_leave"
                    term_date = None
                else:
                    status = "active"
                    term_date = None

                # Name and email
                first = random.choice(FIRST_NAMES)
                last = random.choice(LAST_NAMES)
                email_base = f"{first.lower()}.{last.lower()}"
                email = f"{email_base}@novatech.com"
                counter = 1
                while email in used_emails:
                    email = f"{email_base}{counter}@novatech.com"
                    counter += 1
                used_emails.add(email)

                records.append({
                    "employee_id": emp_id,
                    "first_name": first,
                    "last_name": last,
                    "email": email,
                    "department_id": dept["department_id"],
                    "job_title": job_title,
                    "salary": salary,
                    "hire_date": hire_date,
                    "termination_date": term_date,
                    "status": status,
                })
                emp_id += 1

        df = pd.DataFrame(records)
        self.employees = df

        # Assign department managers (highest-paid active employee per dept)
        for dept_id in self.departments["department_id"]:
            dept_emps = df[(df["department_id"] == dept_id) & (df["status"] == "active")]
            if len(dept_emps) > 0:
                manager_id = dept_emps.loc[dept_emps["salary"].idxmax(), "employee_id"]
                self.departments.loc[
                    self.departments["department_id"] == dept_id, "manager_id"
                ] = int(manager_id)

        logger.info("  → {} employees generated ({} active, {} terminated)",
                     len(df),
                     len(df[df["status"] == "active"]),
                     len(df[df["status"] == "terminated"]))
        return df

    # ─── CUSTOMERS ────────────────────────────────────────────

    def generate_customers(self, n: int = 500) -> pd.DataFrame:
        """
        Generate B2B customer accounts.

        Features:
          - Distributed across 8 countries (weighted by market size)
          - 4 segments: Enterprise, Mid-Market, SMB, Startup
          - Registration dates spanning 2020–2026
          - ~5% inactive customers
        """
        logger.info("Generating {} customers...", n)
        records = []

        # Build weighted country list
        countries_flat = []
        cities_map = {}
        for country, cities, weight in CUSTOMER_COUNTRIES:
            count = max(1, int(n * weight))
            countries_flat.extend([country] * count)
            cities_map[country] = cities

        random.shuffle(countries_flat)
        countries_flat = countries_flat[:n]
        if len(countries_flat) < n:
            countries_flat.extend(random.choices(
                [c[0] for c in CUSTOMER_COUNTRIES],
                weights=[c[2] for c in CUSTOMER_COUNTRIES],
                k=n - len(countries_flat)
            ))

        company_suffixes = [
            "Technologies", "Solutions", "Systems", "Digital", "Analytics",
            "Innovations", "Corp", "Group", "Industries", "Labs",
            "Dynamics", "Networks", "Partners", "Ventures", "Global",
            "Consulting", "Enterprises", "Holdings", "Media", "Logistics",
            "Software", "Services", "Cloud", "Security", "Robotics"
        ]
        company_prefixes = [
            "Apex", "Vertex", "Pinnacle", "Summit", "Quantum", "Nova",
            "Stellar", "Prime", "Alpha", "Omega", "Nexus", "Zenith",
            "Horizon", "Atlas", "Titan", "Phoenix", "Falcon", "Eagle",
            "Pacific", "Atlantic", "Nordic", "Sterling", "Vanguard",
            "Meridian", "Catalyst", "Synergy", "Prism", "Aurora",
            "Cascade", "Crimson", "Everest", "Harbor", "Ironclad",
            "Aero", "BlueWave", "Cobalt", "Crestview", "Element",
            "Frontier", "Infiniti", "Matrix", "Omni", "Solaris"
        ]

        used_company_names = set()
        for i in range(1, n + 1):
            country = countries_flat[i - 1]
            city = random.choice(cities_map.get(country, ["Unknown"]))

            # Unique company name with counter fallback
            base_name = f"{random.choice(company_prefixes)} {random.choice(company_suffixes)}"
            comp_name = base_name
            counter = 2
            while comp_name in used_company_names:
                comp_name = f"{base_name} {counter}"
                counter += 1
            used_company_names.add(comp_name)

            contact_first = random.choice(FIRST_NAMES)
            contact_last = random.choice(LAST_NAMES)

            # Segment distribution: 15% Enterprise, 30% Mid-Market, 35% SMB, 20% Startup
            segment = self.rng.choice(
                CUSTOMER_SEGMENTS,
                p=[0.15, 0.30, 0.35, 0.20]
            )

            reg_date = date(2020, 1, 1) + timedelta(
                days=int(self.rng.integers(0, (END_DATE - date(2020, 1, 1)).days))
            )

            is_active = self.rng.random() > 0.05

            records.append({
                "customer_id": i,
                "company_name": comp_name,
                "contact_name": f"{contact_first} {contact_last}",
                "email": f"contact@{comp_name.lower().replace(' ', '')}.com",
                "phone": f"+1-{self.rng.integers(200,999)}-{self.rng.integers(100,999)}-{self.rng.integers(1000,9999)}",
                "country": country,
                "city": city,
                "segment": segment,
                "registration_date": reg_date,
                "is_active": bool(is_active),
            })

        df = pd.DataFrame(records)
        self.customers = df
        logger.info("  → {} customers generated across {} countries",
                     len(df), df["country"].nunique())
        return df

    # ─── PRODUCTS ─────────────────────────────────────────────

    def generate_products(self) -> pd.DataFrame:
        """Generate the product catalog with realistic pricing."""
        logger.info("Generating products...")
        records = []
        for i, prod in enumerate(PRODUCTS, start=1):
            name, category, subcategory, (price_low, price_high), cost_pct = prod
            unit_price = round(self.rng.uniform(price_low, price_high), 2)
            unit_cost = round(unit_price * cost_pct, 2)
            launch_date = date(2020, 1, 1) + timedelta(
                days=int(self.rng.integers(0, 730))
            )
            records.append({
                "product_id": i,
                "product_name": name,
                "category": category,
                "subcategory": subcategory,
                "unit_price": unit_price,
                "unit_cost": unit_cost,
                "launch_date": launch_date,
                "status": "active" if self.rng.random() > 0.05 else "discontinued",
            })

        df = pd.DataFrame(records)
        self.products = df
        logger.info("  → {} products generated across {} categories",
                     len(df), df["category"].nunique())
        return df

    # ─── SALES ────────────────────────────────────────────────

    def generate_sales(self, target_count: int = 50000) -> pd.DataFrame:
        """
        Generate ~50K sales transactions over 58 months.

        Features:
          - Seasonal pattern: Q4 ~30% higher, Q1 ~15% lower
          - Year-over-year growth: ~12%
          - Enterprise customers buy higher-value products
          - Discounts: 0–25% (higher for larger deals)
          - Regional distribution based on customer country
        """
        logger.info("Generating ~{} sales transactions...", target_count)
        if self.employees is None or self.customers is None or self.products is None:
            raise ValueError("Generate departments, employees, customers, products first")

        active_sales_emps = self.employees[
            (self.employees["department_id"].isin(
                self.departments[self.departments["department_name"].isin(
                    ["Sales", "Marketing", "Support"]
                )]["department_id"]
            )) & (self.employees["status"] == "active")
        ]["employee_id"].tolist()

        # Fallback: if too few sales employees, use any active employee
        if len(active_sales_emps) < 20:
            active_sales_emps = self.employees[
                self.employees["status"] == "active"
            ]["employee_id"].tolist()

        active_customers = self.customers[
            self.customers["is_active"]
        ]["customer_id"].tolist()

        active_products = self.products[
            self.products["status"] == "active"
        ]["product_id"].tolist()

        # Build a mapping of customer_id → country → region
        customer_regions = {}
        region_map = {
            "United States": "North America", "Canada": "North America",
            "United Kingdom": "Europe", "Germany": "Europe",
            "India": "Asia Pacific", "Singapore": "Asia Pacific",
            "Japan": "Asia Pacific", "Australia": "Asia Pacific",
        }
        for _, cust in self.customers.iterrows():
            customer_regions[cust["customer_id"]] = region_map.get(
                cust["country"], "North America"
            )

        # Customer segment for pricing
        customer_segments = dict(zip(
            self.customers["customer_id"], self.customers["segment"]
        ))

        # Product prices
        product_prices = dict(zip(
            self.products["product_id"], self.products["unit_price"]
        ))

        # Distribute sales across months with seasonality
        months = pd.date_range(START_DATE, END_DATE, freq="MS")
        monthly_weights = []
        for m in months:
            # Base weight with YoY growth
            years_elapsed = (m.year - START_DATE.year) + (m.month - 1) / 12
            base = 1.0 * (1.12 ** years_elapsed)

            # Seasonal multiplier
            if m.month in (10, 11, 12):     # Q4 spike
                seasonal = 1.30
            elif m.month in (1, 2):          # Q1 dip
                seasonal = 0.85
            elif m.month in (6, 7, 8):       # summer moderate
                seasonal = 1.05
            else:
                seasonal = 1.0

            monthly_weights.append(base * seasonal)

        # Normalize weights to distribute target_count
        total_weight = sum(monthly_weights)
        monthly_counts = [max(1, int(w / total_weight * target_count)) for w in monthly_weights]

        records = []
        sale_id = 1

        for month_start, count in zip(months, monthly_counts):
            month_end = (month_start + pd.offsets.MonthEnd(1)).date()

            for _ in range(count):
                # Random date within the month
                day_offset = int(self.rng.integers(0, (month_end - month_start.date()).days + 1))
                sale_date = month_start.date() + timedelta(days=day_offset)

                customer_id = random.choice(active_customers)
                employee_id = random.choice(active_sales_emps)
                product_id = random.choice(active_products)

                # Quantity based on segment
                seg = customer_segments.get(customer_id, "SMB")
                if seg == "Enterprise":
                    quantity = int(self.rng.integers(3, 25))
                elif seg == "Mid-Market":
                    quantity = int(self.rng.integers(2, 12))
                elif seg == "SMB":
                    quantity = int(self.rng.integers(1, 6))
                else:  # Startup
                    quantity = int(self.rng.integers(1, 3))

                unit_price = product_prices[product_id]

                # Discount: larger for bigger deals, Enterprise gets better rates
                base_discount = self.rng.uniform(0, 15)
                if seg == "Enterprise":
                    base_discount += self.rng.uniform(2, 10)
                discount_pct = round(min(base_discount, 25), 2)

                total_amount = round(
                    quantity * unit_price * (1 - discount_pct / 100), 2
                )

                region = customer_regions.get(customer_id, "North America")
                payment = random.choice(PAYMENT_METHODS)

                records.append({
                    "sale_id": sale_id,
                    "sale_date": sale_date,
                    "customer_id": customer_id,
                    "employee_id": employee_id,
                    "product_id": product_id,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "discount_pct": discount_pct,
                    "total_amount": total_amount,
                    "region": region,
                    "payment_method": payment,
                })
                sale_id += 1

        df = pd.DataFrame(records)
        self.sales = df
        logger.info("  → {} sales generated (${:,.0f} total revenue)",
                     len(df), df["total_amount"].sum())
        return df

    # ─── EXPENSES ─────────────────────────────────────────────

    def generate_expenses(self, target_count: int = 30000) -> pd.DataFrame:
        """
        Generate ~30K expense records across 8 departments.

        Features:
          - Category distribution varies by department
          - Monthly patterns: rent stable, travel seasonal
          - Engineering & R&D have higher software/equipment costs
          - Marketing has higher advertising spend
          - Realistic vendor names
        """
        logger.info("Generating ~{} expenses...", target_count)
        if self.departments is None:
            raise ValueError("Generate departments first")

        # Department-specific category weights
        dept_category_weights = {
            "Engineering":  {"Office Rent": 0.10, "Software & Tools": 0.25, "Travel & Transport": 0.05,
                             "Equipment & Hardware": 0.20, "Training & Development": 0.10,
                             "Utilities": 0.05, "Professional Services": 0.10, "Miscellaneous": 0.05, "Marketing & Ads": 0.00},
            "Sales":        {"Office Rent": 0.10, "Software & Tools": 0.10, "Travel & Transport": 0.25,
                             "Equipment & Hardware": 0.05, "Training & Development": 0.08,
                             "Utilities": 0.05, "Professional Services": 0.12, "Miscellaneous": 0.05, "Marketing & Ads": 0.10},
            "Marketing":    {"Office Rent": 0.08, "Software & Tools": 0.10, "Travel & Transport": 0.10,
                             "Equipment & Hardware": 0.05, "Training & Development": 0.05,
                             "Utilities": 0.02, "Professional Services": 0.10, "Miscellaneous": 0.05, "Marketing & Ads": 0.35},
            "HR":           {"Office Rent": 0.15, "Software & Tools": 0.15, "Travel & Transport": 0.10,
                             "Equipment & Hardware": 0.05, "Training & Development": 0.20,
                             "Utilities": 0.08, "Professional Services": 0.12, "Miscellaneous": 0.05, "Marketing & Ads": 0.00},
            "Finance":      {"Office Rent": 0.15, "Software & Tools": 0.20, "Travel & Transport": 0.08,
                             "Equipment & Hardware": 0.05, "Training & Development": 0.10,
                             "Utilities": 0.08, "Professional Services": 0.20, "Miscellaneous": 0.04, "Marketing & Ads": 0.00},
            "Operations":   {"Office Rent": 0.12, "Software & Tools": 0.10, "Travel & Transport": 0.15,
                             "Equipment & Hardware": 0.20, "Training & Development": 0.08,
                             "Utilities": 0.10, "Professional Services": 0.10, "Miscellaneous": 0.05, "Marketing & Ads": 0.00},
            "R&D":          {"Office Rent": 0.08, "Software & Tools": 0.30, "Travel & Transport": 0.05,
                             "Equipment & Hardware": 0.25, "Training & Development": 0.12,
                             "Utilities": 0.05, "Professional Services": 0.05, "Miscellaneous": 0.05, "Marketing & Ads": 0.00},
            "Support":      {"Office Rent": 0.12, "Software & Tools": 0.20, "Travel & Transport": 0.08,
                             "Equipment & Hardware": 0.10, "Training & Development": 0.15,
                             "Utilities": 0.08, "Professional Services": 0.10, "Miscellaneous": 0.07, "Marketing & Ads": 0.00},
        }

        months = pd.date_range(START_DATE, END_DATE, freq="MS")
        records = []
        expense_id = 1

        # Distribute expenses: bigger departments get more entries
        dept_sizes = {d["name"]: d["headcount_target"] for d in DEPARTMENTS}
        total_headcount = sum(dept_sizes.values())

        approved_emps = self.employees[
            self.employees["status"] == "active"
        ]["employee_id"].tolist() if self.employees is not None else []

        for month_start in months:
            month_end = (month_start + pd.offsets.MonthEnd(1)).date()

            for _, dept in self.departments.iterrows():
                dept_name = dept["department_name"]
                dept_id = dept["department_id"]
                dept_share = dept_sizes[dept_name] / total_headcount
                month_count = max(3, int(target_count / len(months) * dept_share))

                cat_weights = dept_category_weights.get(dept_name, {})
                categories = list(cat_weights.keys())
                weights = list(cat_weights.values())

                # Remove zero-weight categories
                valid = [(c, w) for c, w in zip(categories, weights) if w > 0]
                if not valid:
                    continue
                categories, weights = zip(*valid)
                weights = np.array(weights) / sum(weights)

                for _ in range(month_count):
                    category = self.rng.choice(categories, p=weights)
                    cat_range = EXPENSE_CATEGORIES.get(category, (1000, 10000))
                    if cat_range[0] is None:
                        continue

                    # Amount with some variance
                    low, high = cat_range
                    # Scale by department size
                    scale = dept_share * 3
                    amount = round(self.rng.uniform(low * scale, high * scale), 2)
                    amount = max(50, amount)  # minimum expense

                    # Seasonal travel boost in Q2/Q3
                    if category == "Travel & Transport" and month_start.month in (4, 5, 6, 7, 8, 9):
                        amount *= 1.4

                    day_offset = int(self.rng.integers(0, (month_end - month_start.date()).days + 1))
                    expense_date = month_start.date() + timedelta(days=day_offset)

                    vendor = random.choice(VENDORS)
                    payment = random.choice(PAYMENT_METHODS)

                    # Approval status: ~95% approved, 3% pending, 2% rejected
                    status_roll = self.rng.random()
                    if status_roll < 0.95:
                        approval = "approved"
                    elif status_roll < 0.98:
                        approval = "pending"
                    else:
                        approval = "rejected"

                    approved_by = random.choice(approved_emps) if approved_emps and approval == "approved" else None

                    records.append({
                        "expense_id": expense_id,
                        "expense_date": expense_date,
                        "department_id": dept_id,
                        "category": category,
                        "subcategory": None,
                        "vendor": vendor,
                        "description": f"{category} - {dept_name} - {month_start.strftime('%b %Y')}",
                        "amount": round(amount, 2),
                        "currency": "USD",
                        "payment_method": payment,
                        "approval_status": approval,
                        "approved_by": approved_by,
                        "receipt_number": f"REC-{expense_id:06d}",
                    })
                    expense_id += 1

        df = pd.DataFrame(records)
        self.expenses = df
        logger.info("  → {} expenses generated (${:,.0f} total)",
                     len(df), df["amount"].sum())
        return df

    # ─── BUDGETS ──────────────────────────────────────────────

    def generate_budgets(self) -> pd.DataFrame:
        """
        Generate monthly budget allocations per department per category.

        Budget = slightly above average actual spending (realistic planning).
        """
        logger.info("Generating budgets...")
        if self.expenses is None:
            raise ValueError("Generate expenses first")

        records = []
        budget_id = 1

        # Calculate average monthly spend per dept per category from expenses
        exp_agg = self.expenses[self.expenses["approval_status"] == "approved"].copy()
        exp_agg["fiscal_year"] = pd.to_datetime(exp_agg["expense_date"]).dt.year
        exp_agg["fiscal_month"] = pd.to_datetime(exp_agg["expense_date"]).dt.month

        avg_spend = exp_agg.groupby(["department_id", "category"])["amount"].mean().to_dict()

        months = pd.date_range(START_DATE, END_DATE, freq="MS")
        dept_ids = self.departments["department_id"].tolist()
        categories = [c for c in EXPENSE_CATEGORIES.keys() if c != "Salaries"]

        for month_start in months:
            fy = month_start.year
            fm = month_start.month
            approved_date = date(fy, 1, 15) if fm <= 6 else date(fy, 7, 1)

            for dept_id in dept_ids:
                for category in categories:
                    avg = avg_spend.get((dept_id, category), 5000)
                    # Budget is avg spend + 10-25% buffer
                    buffer = self.rng.uniform(1.10, 1.25)
                    approved_amount = round(avg * buffer, 2)

                    # Some years have revisions
                    revised = None
                    if self.rng.random() < 0.15:
                        revised = round(approved_amount * self.rng.uniform(0.90, 1.15), 2)

                    records.append({
                        "budget_id": budget_id,
                        "department_id": dept_id,
                        "fiscal_year": fy,
                        "fiscal_month": fm,
                        "category": category,
                        "approved_amount": approved_amount,
                        "revised_amount": revised,
                        "approved_date": approved_date,
                        "approved_by": None,
                        "notes": None,
                    })
                    budget_id += 1

        df = pd.DataFrame(records)
        self.budgets = df
        logger.info("  → {} budget records generated", len(df))
        return df

    # ─── TRANSACTIONS (unified ledger) ────────────────────────

    def generate_transactions(self) -> pd.DataFrame:
        """
        Generate unified transaction ledger from sales and expenses.
        Sales → credit, Expenses → debit.
        """
        logger.info("Generating unified transactions...")
        if self.sales is None or self.expenses is None:
            raise ValueError("Generate sales and expenses first")

        records = []
        txn_id = 1

        # Sales → credit transactions
        for _, sale in self.sales.iterrows():
            records.append({
                "transaction_id": txn_id,
                "reference_id": sale["sale_id"],
                "reference_type": "sale",
                "transaction_date": sale["sale_date"],
                "amount": sale["total_amount"],
                "transaction_type": "credit",
                "description": f"Sale #{sale['sale_id']}",
                "status": "completed",
            })
            txn_id += 1

        # Expenses → debit transactions (only approved)
        approved_expenses = self.expenses[self.expenses["approval_status"] == "approved"]
        for _, exp in approved_expenses.iterrows():
            records.append({
                "transaction_id": txn_id,
                "reference_id": exp["expense_id"],
                "reference_type": "expense",
                "transaction_date": exp["expense_date"],
                "amount": exp["amount"],
                "transaction_type": "debit",
                "description": f"Expense: {exp['category']}",
                "status": "completed",
            })
            txn_id += 1

        df = pd.DataFrame(records)
        self.transactions = df
        logger.info("  → {} transactions generated ({} credits, {} debits)",
                     len(df),
                     len(df[df["transaction_type"] == "credit"]),
                     len(df[df["transaction_type"] == "debit"]))
        return df

    # ─── OPERATIONAL PERFORMANCE ──────────────────────────────

    def generate_operational_performance(self) -> pd.DataFrame:
        """
        Generate monthly operational metrics per department.

        Patterns:
          - Operations & Engineering have the most orders
          - Completion rate improves over time (process maturity)
          - Some seasonal dips in on-time delivery during Q4 (volume spikes)
        """
        logger.info("Generating operational performance...")
        if self.departments is None:
            raise ValueError("Generate departments first")

        months = pd.date_range(START_DATE, END_DATE, freq="MS")
        records = []
        rec_id = 1

        # Base orders per department
        dept_order_base = {
            "Engineering": 80, "Sales": 120, "Marketing": 40,
            "HR": 15, "Finance": 25, "Operations": 150,
            "R&D": 35, "Support": 100,
        }

        for month_start in months:
            fy = month_start.year
            fm = month_start.month
            months_elapsed = (fy - START_DATE.year) * 12 + (fm - START_DATE.month)

            for _, dept in self.departments.iterrows():
                dept_name = dept["department_name"]
                base_orders = dept_order_base.get(dept_name, 50)

                # Growth over time
                growth = 1 + (months_elapsed * 0.005)
                # Seasonal variation
                seasonal = 1.25 if fm in (10, 11, 12) else (0.90 if fm in (1, 2) else 1.0)

                orders_received = max(5, int(
                    base_orders * growth * seasonal * self.rng.uniform(0.85, 1.15)
                ))

                # Completion rate improves over time (75% → 95%)
                base_completion_rate = min(0.95, 0.75 + months_elapsed * 0.003)
                completion_rate = base_completion_rate * self.rng.uniform(0.92, 1.02)
                orders_completed = int(orders_received * min(completion_rate, 0.99))

                # Delays: inverse of completion improvement
                delay_rate = max(0.02, 0.15 - months_elapsed * 0.002) * self.rng.uniform(0.7, 1.3)
                orders_delayed = int(orders_received * delay_rate)

                orders_cancelled = max(0, orders_received - orders_completed - orders_delayed)
                if orders_cancelled < 0:
                    orders_cancelled = 0

                # Operational cost
                cost_per_order = self.rng.uniform(150, 500)
                operational_cost = round(orders_received * cost_per_order, 2)

                # Average processing days (improves over time)
                avg_days = max(1.5, 8.0 - months_elapsed * 0.05 + self.rng.normal(0, 1))

                # On-time delivery %
                on_time = min(99.0, max(60.0,
                    80 + months_elapsed * 0.2 + self.rng.normal(0, 3)
                ))

                # Customer satisfaction (1-5 scale)
                csat = min(5.0, max(2.0,
                    3.5 + months_elapsed * 0.015 + self.rng.normal(0, 0.3)
                ))

                records.append({
                    "record_id": rec_id,
                    "department_id": dept["department_id"],
                    "fiscal_year": fy,
                    "fiscal_month": fm,
                    "orders_received": orders_received,
                    "orders_completed": orders_completed,
                    "orders_delayed": orders_delayed,
                    "orders_cancelled": orders_cancelled,
                    "operational_cost": operational_cost,
                    "avg_processing_days": round(avg_days, 2),
                    "on_time_delivery_pct": round(on_time, 2),
                    "customer_satisfaction": round(csat, 1),
                    "notes": None,
                })
                rec_id += 1

        df = pd.DataFrame(records)
        self.operational_performance = df
        logger.info("  → {} operational performance records generated", len(df))
        return df

    # ─── NOISE INJECTION ──────────────────────────────────────

    def inject_missing_values(self, df: pd.DataFrame, columns: list[str],
                               rate: float = 0.02) -> pd.DataFrame:
        """
        Inject missing values into specified columns at the given rate.

        Args:
            df: DataFrame to modify.
            columns: Column names to add NaN values to.
            rate: Fraction of values to set to NaN (default 2%).

        Returns:
            DataFrame with missing values injected.
        """
        df = df.copy()
        n = len(df)
        for col in columns:
            if col in df.columns:
                mask = self.rng.random(n) < rate
                df.loc[mask, col] = None
        return df

    def inject_duplicates(self, df: pd.DataFrame, rate: float = 0.01,
                           id_col: str | None = None) -> pd.DataFrame:
        """
        Inject duplicate rows at the given rate.

        Args:
            df: DataFrame to modify.
            rate: Fraction of rows to duplicate (default 1%).
            id_col: If given, the ID column is renumbered to create "hidden" duplicates.

        Returns:
            DataFrame with duplicates appended.
        """
        n_dupes = max(1, int(len(df) * rate))
        dupe_indices = self.rng.choice(len(df), size=n_dupes, replace=False)
        dupes = df.iloc[dupe_indices].copy()

        if id_col and id_col in dupes.columns:
            max_id = df[id_col].max()
            dupes[id_col] = range(max_id + 1, max_id + 1 + n_dupes)

        result = pd.concat([df, dupes], ignore_index=True)
        return result

    def inject_anomalies(self, df: pd.DataFrame, amount_col: str,
                          rate: float = 0.005) -> pd.DataFrame:
        """
        Inject anomalous amounts (unusually high values) for testing.

        Args:
            df: DataFrame to modify.
            amount_col: Column name containing financial amounts.
            rate: Fraction of values to make anomalous (default 0.5%).

        Returns:
            DataFrame with anomalous values.
        """
        df = df.copy()
        n = len(df)
        mask = self.rng.random(n) < rate
        anomaly_count = mask.sum()

        if anomaly_count > 0 and amount_col in df.columns:
            mean_val = df[amount_col].mean()
            std_val = df[amount_col].std()
            # Anomalies are 4-8x standard deviations above mean
            anomalous_values = mean_val + self.rng.uniform(4, 8, size=anomaly_count) * std_val
            df.loc[mask, amount_col] = np.round(anomalous_values, 2)

        return df

    # ─── MASTER GENERATE METHOD ───────────────────────────────

    def generate_all(self) -> dict[str, pd.DataFrame]:
        """
        Generate all datasets in the correct order (respecting FK dependencies).

        Returns:
            Dictionary of {table_name: DataFrame}.
        """
        logger.info("=" * 60)
        logger.info("NovaTech Solutions — Synthetic Data Generation")
        logger.info("Seed: {} | Period: {} to {}", self.seed, START_DATE, END_DATE)
        logger.info("=" * 60)

        # 1. Generate in FK-dependency order
        self.generate_departments()
        self.generate_employees()
        self.generate_customers()
        self.generate_products()
        self.generate_sales()
        self.generate_expenses()
        self.generate_budgets()
        self.generate_transactions()
        self.generate_operational_performance()

        # 2. Inject noise for data quality testing
        logger.info("Injecting data quality issues...")

        self.sales = self.inject_missing_values(
            self.sales, ["payment_method", "discount_pct"], rate=0.02
        )
        self.sales = self.inject_duplicates(self.sales, rate=0.008, id_col="sale_id")
        self.sales = self.inject_anomalies(self.sales, "total_amount", rate=0.005)

        self.expenses = self.inject_missing_values(
            self.expenses, ["vendor", "subcategory", "receipt_number"], rate=0.03
        )
        self.expenses = self.inject_duplicates(self.expenses, rate=0.01, id_col="expense_id")
        self.expenses = self.inject_anomalies(self.expenses, "amount", rate=0.005)

        self.customers = self.inject_missing_values(
            self.customers, ["phone", "email", "city"], rate=0.02
        )

        self.employees = self.inject_missing_values(
            self.employees, ["termination_date"], rate=0.01
        )

        logger.info("  → Missing values, duplicates, and anomalies injected")

        datasets = {
            "departments": self.departments,
            "employees": self.employees,
            "customers": self.customers,
            "products": self.products,
            "sales": self.sales,
            "expenses": self.expenses,
            "budgets": self.budgets,
            "transactions": self.transactions,
            "operational_performance": self.operational_performance,
        }

        # Summary
        logger.info("=" * 60)
        logger.info("GENERATION SUMMARY")
        logger.info("=" * 60)
        total_rows = 0
        for name, df in datasets.items():
            rows = len(df)
            total_rows += rows
            logger.info("  {:30s} {:>8,d} rows", name, rows)
        logger.info("  {:30s} {:>8,d} rows", "TOTAL", total_rows)
        logger.info("=" * 60)

        return datasets

    # ─── SAVE TO FILES ────────────────────────────────────────

    def save_all(self, datasets: dict[str, pd.DataFrame],
                  output_dir: str | Path, formats: list[str] | None = None) -> dict[str, Path]:
        """
        Save all datasets to disk in specified formats.

        Args:
            datasets: Dictionary from generate_all().
            output_dir: Directory to save files.
            formats: List of formats to save. Default: ["csv", "json"].
                     Supported: "csv", "json", "xlsx"

        Returns:
            Dictionary of {filename: Path} for all saved files.
        """
        if formats is None:
            formats = ["csv"]

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        saved_files = {}
        for name, df in datasets.items():
            for fmt in formats:
                if fmt == "csv":
                    filepath = output_path / f"{name}.csv"
                    df.to_csv(filepath, index=False)
                elif fmt == "json":
                    filepath = output_path / f"{name}.json"
                    df.to_json(filepath, orient="records", indent=2, date_format="iso")
                elif fmt == "xlsx":
                    filepath = output_path / f"{name}.xlsx"
                    df.to_excel(filepath, index=False, engine="openpyxl")
                else:
                    continue
                saved_files[filepath.name] = filepath
                logger.debug("  Saved: {}", filepath)

        logger.info("Saved {} files to {}", len(saved_files), output_path)
        return saved_files

    # ─── EDA SUMMARY ──────────────────────────────────────────

    def print_eda_summary(self, datasets: dict[str, pd.DataFrame]) -> None:
        """Print a quick exploratory data analysis summary."""
        print("\n" + "=" * 70)
        print("EXPLORATORY DATA ANALYSIS SUMMARY")
        print("=" * 70)

        for name, df in datasets.items():
            print(f"\n{'─' * 50}")
            print(f"📊 {name.upper()} ({len(df):,d} rows × {len(df.columns)} cols)")
            print(f"{'─' * 50}")

            # Dtypes summary
            print(f"  Columns: {list(df.columns)}")

            # Missing values
            missing = df.isnull().sum()
            missing = missing[missing > 0]
            if len(missing) > 0:
                print(f"  Missing values:")
                for col, count in missing.items():
                    pct = count / len(df) * 100
                    print(f"    {col}: {count} ({pct:.1f}%)")
            else:
                print(f"  Missing values: None")

            # Numeric summary
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                for col in numeric_cols[:3]:  # top 3 numeric columns
                    print(f"  {col}: min={df[col].min():.2f}, "
                          f"mean={df[col].mean():.2f}, "
                          f"max={df[col].max():.2f}")

            # Duplicates
            dupes = df.duplicated().sum()
            if dupes > 0:
                print(f"  ⚠ Duplicate rows: {dupes}")


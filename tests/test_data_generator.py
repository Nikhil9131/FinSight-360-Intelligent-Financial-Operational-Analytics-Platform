"""
FinSight 360 - Tests for Synthetic Data Generator
=================================================
Validates referential integrity, record counts, schema structure,
and noise injection properties of the synthetic data generator.
"""

import sys
from pathlib import Path
import pytest
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.data_generator.generator import NovaTechDataGenerator


@pytest.fixture(scope="module")
def generator_and_data():
    """Generate a smaller test dataset for rapid testing."""
    gen = NovaTechDataGenerator(seed=123)
    # Generate smaller slices for speed
    gen.generate_departments()
    gen.generate_employees()
    gen.generate_customers(n=50)
    gen.generate_products()
    gen.generate_sales(target_count=1000)
    gen.generate_expenses(target_count=800)
    gen.generate_budgets()
    gen.generate_transactions()
    gen.generate_operational_performance()
    return gen


def test_department_generation(generator_and_data):
    gen = generator_and_data
    df = gen.departments
    assert df is not None
    assert len(df) == 8
    assert "department_id" in df.columns
    assert "department_name" in df.columns
    assert df["department_name"].nunique() == 8


def test_employee_generation_and_fk(generator_and_data):
    gen = generator_and_data
    df = gen.employees
    assert df is not None
    assert len(df) >= 300
    # Every employee belongs to a valid department
    valid_depts = set(gen.departments["department_id"])
    assert set(df["department_id"]).issubset(valid_depts)
    assert (df["salary"] > 0).all()


def test_customer_generation(generator_and_data):
    gen = generator_and_data
    df = gen.customers
    assert df is not None
    assert len(df) == 50
    assert set(df["segment"]).issubset({"Enterprise", "Mid-Market", "SMB", "Startup"})


def test_sales_referential_integrity(generator_and_data):
    gen = generator_and_data
    df = gen.sales
    assert df is not None
    assert len(df) >= 900
    
    valid_customers = set(gen.customers["customer_id"])
    valid_employees = set(gen.employees["employee_id"])
    valid_products = set(gen.products["product_id"])

    assert set(df["customer_id"]).issubset(valid_customers)
    assert set(df["employee_id"]).issubset(valid_employees)
    assert set(df["product_id"]).issubset(valid_products)


def test_expenses_referential_integrity(generator_and_data):
    gen = generator_and_data
    df = gen.expenses
    assert df is not None
    assert len(df) >= 700

    valid_depts = set(gen.departments["department_id"])
    assert set(df["department_id"]).issubset(valid_depts)
    assert (df["amount"] > 0).all()


def test_transactions_reconciliation(generator_and_data):
    gen = generator_and_data
    txns = gen.transactions
    assert txns is not None
    assert len(txns) == len(gen.sales) + len(gen.expenses[gen.expenses["approval_status"] == "approved"])
    assert set(txns["transaction_type"]).issubset({"credit", "debit"})


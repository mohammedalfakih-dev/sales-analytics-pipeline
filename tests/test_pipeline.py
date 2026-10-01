"""Regression checks for cleaning, joins, metrics, and local execution."""

import pandas as pd
import pytest

from src.clean import clean_sales
from src.pipeline import get_config
from src.report import build_reports
from src.transform import join_customers


def test_get_config_reads_environment(monkeypatch):
    for name in ["INPUT_SOURCE", "DATA_DIR", "OUTPUT_DIR", "UPLOAD_TO_AZURE"]:
        monkeypatch.delenv(name, raising=False)

    config = get_config()

    assert config["input_source"] == "local"
    assert config["data_dir"] == "data/sample"
    assert config["output_dir"] == "reports/generated"
    assert config["upload_to_azure"] is False


def test_get_config_requires_cloud_settings_only_for_azure(monkeypatch):
    monkeypatch.setenv("INPUT_SOURCE", "azure")
    monkeypatch.setenv("UPLOAD_TO_AZURE", "false")
    monkeypatch.delenv("AZURE_STORAGE_ACCOUNT_URL", raising=False)

    with pytest.raises(RuntimeError):
        get_config()


def test_clean_sales_removes_bad_rows_and_normalizes_values():
    sales = pd.DataFrame(
        [
            {
                "transaction_id": 1,
                "product_name": " laptop ",
                "customer_email": " TEST@EMAIL.COM ",
                "price": "100",
                "quantity": 1,
                "date": "2026-01-01",
            },
            {
                "transaction_id": 2,
                "product_name": "",
                "customer_email": "bad@email.com",
                "price": "50",
                "quantity": 1,
                "date": "2026-01-01",
            },
            {
                "transaction_id": 3,
                "product_name": "Mouse",
                "customer_email": "bad@email.com",
                "price": "-10",
                "quantity": 1,
                "date": "2026-01-01",
            },
        ]
    )

    cleaned = clean_sales(sales)

    assert len(cleaned) == 1
    assert cleaned.iloc[0]["product_name"] == "Laptop"
    assert cleaned.iloc[0]["customer_email"] == "test@email.com"


def test_join_customers_adds_high_value_column():
    sales = pd.DataFrame(
        [
            {
                "transaction_id": 1,
                "product_name": "Laptop",
                "customer_email": "TEST@EMAIL.COM",
                "price": 100,
                "quantity": 2,
                "date": pd.Timestamp("2026-01-01"),
                "category": "Electronics",
            }
        ]
    )

    customers = pd.DataFrame(
        [
            {
                "customer_email": "test@email.com",
                "customer_name": "Mohammed",
                "region": "EU",
                "loyalty_tier": "Gold",
            }
        ]
    )

    enriched = join_customers(sales, customers)

    assert len(enriched) == 1
    assert enriched.iloc[0]["is_high_value"]


def test_build_reports_returns_expected_tables():
    enriched = pd.DataFrame(
        [
            {
                "transaction_id": 1,
                "customer_email": "test@email.com",
                "customer_name": "Mohammed",
                "region": "EU",
                "loyalty_tier": "Gold",
                "category": "Electronics",
                "price": 100,
                "quantity": 2,
                "date": pd.Timestamp("2026-01-01"),
            }
        ]
    )

    reports = build_reports(enriched)

    assert set(reports) == {
        "weekly_revenue",
        "customer_summary",
        "category_performance",
        "loyalty_analysis",
    }
    assert reports["customer_summary"].iloc[0]["total_spent"] == 200

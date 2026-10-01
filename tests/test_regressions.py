"""Checks for invalid data, report grain, and an offline end-to-end run."""

from pathlib import Path

import pandas as pd
import pytest

from src.clean import clean_sales
from src.pipeline import get_config, run
from src.report import build_reports
from src.transform import join_customers


def sale(**changes):
    record = {
        "transaction_id": 1,
        "product_name": " Laptop ",
        "customer_email": " buyer@example.com ",
        "price": "100",
        "quantity": "2",
        "date": "2024-01-03",
        "category": "Electronics",
    }
    return record | changes


def customer(**changes):
    return {
        "customer_email": "BUYER@EXAMPLE.COM",
        "customer_name": "Example Buyer",
        "region": "NL",
        "loyalty_tier": "Gold",
    } | changes


@pytest.mark.parametrize(
    "changes",
    [
        {"quantity": "bad"},
        {"quantity": -1},
        {"quantity": 0},
        {"price": "bad"},
        {"date": "2024-13-01"},
        {"customer_email": "  "},
        {"customer_email": None},
        {"transaction_id": None},
    ],
)
def test_unusable_transactions_are_removed(changes):
    assert clean_sales(pd.DataFrame([sale(**changes)])).empty


def test_duplicates_keep_first_valid_transaction_and_missing_categories_survive():
    rows = [sale(price=-1), sale(category=None), sale(price=999)]
    result = clean_sales(pd.DataFrame(rows))
    assert len(result) == 1
    assert result.iloc[0]["price"] == 100
    assert result.iloc[0]["category"] == "Unknown"


def test_duplicate_normalized_customer_keys_fail_instead_of_inflating_revenue():
    sales = clean_sales(pd.DataFrame([sale()]))
    customers = pd.DataFrame([customer(), customer(customer_email=" buyer@example.com ")])
    with pytest.raises(pd.errors.MergeError):
        join_customers(sales, customers)


def test_unmatched_sales_and_blank_customer_keys_do_not_join():
    sales = clean_sales(pd.DataFrame([sale(customer_email="missing@example.com")]))
    assert join_customers(sales, pd.DataFrame([customer(), customer(customer_email=None)])).empty


def test_iso_year_separates_week_one_and_category_totals_reconcile():
    sales = clean_sales(
        pd.DataFrame(
            [sale(date="2024-01-03"), sale(transaction_id=2, date="2025-01-01", category=None)]
        )
    )
    enriched = join_customers(sales, pd.DataFrame([customer()]))
    reports = build_reports(enriched)
    weekly = reports["weekly_revenue"]
    assert set(zip(weekly["iso_year"], weekly["week"])) == {(2024, 1), (2025, 1)}
    assert reports["category_performance"]["total_revenue"].sum() == 400
    assert reports["customer_summary"]["total_spent"].sum() == 400


@pytest.mark.parametrize("name,value", [("INPUT_SOURCE", "typo"), ("UPLOAD_TO_AZURE", "yes")])
def test_invalid_mode_settings_fail(name, value, monkeypatch):
    monkeypatch.setenv("INPUT_SOURCE", "local")
    monkeypatch.setenv("UPLOAD_TO_AZURE", "false")
    monkeypatch.setenv(name, value)
    with pytest.raises(ValueError):
        get_config()


def test_azure_input_defaults_to_download_folder(monkeypatch):
    monkeypatch.setenv("INPUT_SOURCE", "azure")
    monkeypatch.setenv("UPLOAD_TO_AZURE", "false")
    monkeypatch.setenv("AZURE_STORAGE_ACCOUNT_URL", "https://example.blob.core.windows.net")
    monkeypatch.setenv("AZURE_INPUT_CONTAINER", "inputs")
    monkeypatch.delenv("DATA_DIR", raising=False)
    assert get_config()["data_dir"] == "data/downloaded"


def test_empty_join_fails_without_writing_reports(tmp_path, monkeypatch):
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    pd.DataFrame([sale(customer_email="missing@example.com")]).to_csv(
        inputs / "messy_sales.csv", index=False
    )
    pd.DataFrame([customer()]).to_csv(inputs / "messy_customers.csv", index=False)
    monkeypatch.setenv("INPUT_SOURCE", "local")
    monkeypatch.setenv("UPLOAD_TO_AZURE", "false")
    monkeypatch.setenv("DATA_DIR", str(inputs))
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "output"))
    with pytest.raises(ValueError, match="No matched transactions"):
        run()
    assert not (tmp_path / "output").exists()


def test_sample_run_is_offline_repeatable_and_writes_all_reports(tmp_path, monkeypatch):
    fixture_dir = Path(__file__).resolve().parents[1] / "data" / "sample"
    monkeypatch.setenv("INPUT_SOURCE", "local")
    monkeypatch.setenv("DATA_DIR", str(fixture_dir))
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path / "nested" / "reports"))
    monkeypatch.setenv("UPLOAD_TO_AZURE", "false")
    monkeypatch.delenv("GITHUB_USERNAME", raising=False)
    monkeypatch.delenv("AZURE_STORAGE_ACCOUNT_URL", raising=False)
    # Catch any accidental network access in the default path.
    import socket

    def reject_network(*args, **kwargs):
        raise AssertionError("Local sample execution must not use the network")

    monkeypatch.setattr(socket, "create_connection", reject_network)
    monkeypatch.setattr(socket.socket, "connect", reject_network)
    run()
    directory = tmp_path / "nested" / "reports"
    files = {path.name for path in directory.iterdir()}
    assert files == {
        "weekly_revenue.csv",
        "customer_summary.parquet",
        "category_performance.csv",
        "loyalty_analysis.csv",
        "category_revenue.png",
    }
    first = pd.read_csv(directory / "weekly_revenue.csv")
    customer_report = pd.read_parquet(directory / "customer_summary.parquet")
    category_report = pd.read_csv(directory / "category_performance.csv")
    assert customer_report["customer_email"].is_unique
    assert first["order_count"].sum() > 0
    assert first["total_revenue"].sum() == pytest.approx(customer_report["total_spent"].sum())
    assert first["total_revenue"].sum() == pytest.approx(category_report["total_revenue"].sum())
    assert (directory / "category_revenue.png").stat().st_size > 1000
    run()
    pd.testing.assert_frame_equal(first, pd.read_csv(directory / "weekly_revenue.csv"))

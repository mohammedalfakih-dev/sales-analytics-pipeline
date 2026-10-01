"""Load inputs and normalize valid sales records."""

import logging
from pathlib import Path

import pandas as pd


def load_and_explore(data_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    sales = pd.read_csv(data_dir / "messy_sales.csv")
    customers = pd.read_csv(data_dir / "messy_customers.csv")

    logging.info("=== SALES INFO ===")
    logging.info("Sales input rows: %s", len(sales))

    logging.info("=== SALES DESCRIBE ===")
    logging.info("\n%s", sales.describe(include="all"))

    logging.info("=== SALES MISSING VALUES ===")
    logging.info("\n%s", sales.isna().sum())

    logging.info("=== CUSTOMERS INFO ===")
    logging.info("Customer input rows: %s", len(customers))

    logging.info("=== CUSTOMERS DESCRIBE ===")
    logging.info("\n%s", customers.describe(include="all"))

    logging.info("=== CUSTOMERS MISSING VALUES ===")
    logging.info("\n%s", customers.isna().sum())

    return sales, customers


def clean_sales(sales: pd.DataFrame) -> pd.DataFrame:
    """Keep usable positive-quantity transactions; keep the first valid ID."""
    sales = sales.copy()

    sales["product_name"] = sales["product_name"].astype("string").str.strip().str.title()
    sales["customer_email"] = sales["customer_email"].astype("string").str.lower().str.strip()
    sales["price"] = pd.to_numeric(sales["price"], errors="coerce")
    sales["quantity"] = pd.to_numeric(sales["quantity"], errors="coerce")
    sales["date"] = pd.to_datetime(sales["date"], format="%Y-%m-%d", errors="coerce")

    sales = sales[
        sales["product_name"].notna()
        & (sales["product_name"] != "")
        & (sales["price"] >= 0)
        & (sales["quantity"] > 0)
        & sales["date"].notna()
        & sales["transaction_id"].notna()
        & sales["customer_email"].notna()
        & (sales["customer_email"] != "")
    ].copy()

    if "category" in sales:
        sales["category"] = sales["category"].astype("string").str.strip()
        sales["category"] = sales["category"].replace("", pd.NA).fillna("Unknown")

    sales = sales.drop_duplicates(
        subset="transaction_id",
        keep="first",
    )

    logging.info("Cleaned sales rows: %s", len(sales))

    return sales

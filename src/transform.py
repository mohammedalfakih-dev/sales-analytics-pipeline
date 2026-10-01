"""Join customer data without multiplying sales rows."""

import logging

import pandas as pd


def join_customers(sales: pd.DataFrame, customers: pd.DataFrame) -> pd.DataFrame:
    """Normalize email keys and join to one customer per key."""
    sales = sales.copy()
    customers = customers.copy()

    sales["customer_email"] = sales["customer_email"].astype("string").str.lower().str.strip()
    customers["customer_email"] = (
        customers["customer_email"].astype("string").str.lower().str.strip()
    )
    customers = customers[
        customers["customer_email"].notna() & (customers["customer_email"] != "")
    ].copy()
    for column in ["region", "loyalty_tier"]:
        customers[column] = (
            customers[column].astype("string").str.strip().replace("", pd.NA).fillna("Unknown")
        )

    enriched = sales.merge(
        customers,
        on="customer_email",
        how="inner",
        validate="many_to_one",
    )

    enriched["is_high_value"] = enriched["price"] * enriched["quantity"] >= 150

    logging.info("Rows after customer join: %s", len(enriched))

    return enriched

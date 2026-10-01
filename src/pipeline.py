"""Run the sales analytics pipeline with local CSVs or optional Azure input."""

import logging
import os
from pathlib import Path

from src.clean import clean_sales, load_and_explore
from src.report import build_reports, write_outputs
from src.transform import join_customers

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def get_config() -> dict:
    """Use local fixtures by default; require cloud settings only in cloud mode."""
    source = os.getenv("INPUT_SOURCE", "local").lower()
    upload_value = os.getenv("UPLOAD_TO_AZURE", "false").lower()
    if source not in {"local", "azure"}:
        raise ValueError("INPUT_SOURCE must be local or azure")
    if upload_value not in {"true", "false"}:
        raise ValueError("UPLOAD_TO_AZURE must be true or false")
    config = {
        "input_source": source,
        "data_dir": os.getenv(
            "DATA_DIR", "data/sample" if source == "local" else "data/downloaded"
        ),
        "output_dir": os.getenv("OUTPUT_DIR", "reports/generated"),
        "upload_to_azure": upload_value == "true",
        "account_url": os.getenv("AZURE_STORAGE_ACCOUNT_URL"),
        "input_container": os.getenv("AZURE_INPUT_CONTAINER"),
        "output_container": os.getenv("AZURE_OUTPUT_CONTAINER"),
    }
    required = []
    if source == "azure":
        required.extend(["account_url", "input_container"])
    if config["upload_to_azure"]:
        required.extend(["account_url", "output_container"])
    for key in required:
        if not config[key]:
            raise RuntimeError(f"Missing Azure setting: {key}; see .env.example")
    return config


def run() -> None:
    """Clean, join, aggregate, and persist reports; fail on an empty result."""
    config = get_config()
    data_dir = Path(config["data_dir"])
    output_dir = Path(config["output_dir"])
    if config["input_source"] == "azure":
        from src.ingest import download_inputs

        download_inputs(data_dir, config["account_url"], config["input_container"])
    sales_raw, customers_raw = load_and_explore(data_dir)
    cleaned = clean_sales(sales_raw)
    enriched = join_customers(cleaned, customers_raw)
    logger.info("Rows: raw=%s cleaned=%s matched=%s", len(sales_raw), len(cleaned), len(enriched))
    if enriched.empty:
        raise ValueError("No matched transactions remain; no reports were written")
    reports = build_reports(enriched)
    write_outputs(reports, output_dir)
    if config["upload_to_azure"]:
        from src.ingest import upload_outputs

        upload_outputs(output_dir, config["account_url"], config["output_container"])
    logger.info("Pipeline complete: %s", output_dir)


if __name__ == "__main__":
    run()

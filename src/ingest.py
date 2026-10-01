"""Optional Azure Blob transfers using the caller's own account and containers."""

import io
from pathlib import Path

import pandas as pd
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from pandas.testing import assert_frame_equal

FILES = ["messy_sales.csv", "messy_customers.csv"]


def download_inputs(data_dir: Path, account_url: str, container_name: str) -> None:
    """Download the two CSV inputs with an authorized Azure identity."""
    data_dir.mkdir(parents=True, exist_ok=True)
    with DefaultAzureCredential() as credential:
        with BlobServiceClient(account_url=account_url, credential=credential) as service:
            container = service.get_container_client(container_name)
            for filename in FILES:
                payload = container.get_blob_client(filename).download_blob().readall()
                (data_dir / filename).write_bytes(payload)


def upload_outputs(output_dir: Path, account_url: str, container_name: str) -> None:
    """Upload reports to an existing container and verify the Parquet contents."""
    with DefaultAzureCredential() as credential:
        with BlobServiceClient(account_url=account_url, credential=credential) as service:
            container = service.get_container_client(container_name)
            for path in sorted(output_dir.iterdir()):
                if path.suffix in {".csv", ".parquet", ".png"}:
                    with path.open("rb") as stream:
                        container.upload_blob(path.name, stream, overwrite=True)
            local = pd.read_parquet(output_dir / "customer_summary.parquet")
            payload = (
                container.get_blob_client("customer_summary.parquet").download_blob().readall()
            )
            remote = pd.read_parquet(io.BytesIO(payload))
            assert_frame_equal(local, remote)

from pathlib import Path

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient

from config import AZURE_STORAGE_ACCOUNT_URL


def get_blob_service_client() -> BlobServiceClient:
    """
    Authenticate to Azure Blob Storage using
    the current Azure developer identity.
    """

    credential = DefaultAzureCredential()

    return BlobServiceClient(
        account_url=AZURE_STORAGE_ACCOUNT_URL,
        credential=credential
    )


def upload_file(
    local_path: Path,
    container_name: str,
    blob_name: str,
    overwrite: bool = True
) -> None:
    """
    Upload a local file to Azure Blob Storage.
    """

    blob_service_client = get_blob_service_client()

    blob_client = blob_service_client.get_blob_client(
        container=container_name,
        blob=blob_name
    )

    with open(local_path, "rb") as file:
        blob_client.upload_blob(
            file,
            overwrite=overwrite
        )

    print(
        f"[AZURE] Uploaded {local_path.name} "
        f"→ {container_name}/{blob_name}"
    )


def list_blobs(container_name: str) -> None:
    """
    List blobs inside an Azure container.
    """

    blob_service_client = get_blob_service_client()

    container_client = (
        blob_service_client.get_container_client(
            container_name
        )
    )

    print(f"[AZURE] Blobs in '{container_name}':")

    found_blob = False

    for blob in container_client.list_blobs():
        found_blob = True
        print(f" - {blob.name}")

    if not found_blob:
        print(" - Container is empty")

def download_blob_bytes(
    container_name: str,
    blob_name: str
) -> bytes:
    """
    Download a blob from Azure Storage
    and return its contents as bytes.
    """

    blob_service_client = get_blob_service_client()

    blob_client = blob_service_client.get_blob_client(
        container=container_name,
        blob=blob_name
    )

    data = blob_client.download_blob().readall()

    print(
        f"[AZURE] Downloaded "
        f"{container_name}/{blob_name} "
        f"({len(data) / 1024 / 1024:.2f} MB)"
    )

    return data

if __name__ == "__main__":

    from config import (
        RAW_DATA_FILE,
        AZURE_RAW_CONTAINER
    )

    upload_file(
        local_path=RAW_DATA_FILE,
        container_name=AZURE_RAW_CONTAINER,
        blob_name=RAW_DATA_FILE.name
    )

    list_blobs(AZURE_RAW_CONTAINER)

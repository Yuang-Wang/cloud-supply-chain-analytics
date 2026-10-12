from io import BytesIO

import pandas as pd

from azure_storage import download_blob_bytes
from config import (
    RAW_DATA_FILE,
    AZURE_RAW_CONTAINER
)

import pandas as pd

from config import RAW_DATA_FILE


def extract_data() -> pd.DataFrame:
    """
    Load the raw DataCo supply-chain dataset.

    Returns
    -------
    pd.DataFrame
        Raw supply-chain data.
    """

    df = pd.read_csv(
        RAW_DATA_FILE,
        encoding="latin-1"
    )

    print(
        f"[EXTRACT] Loaded {len(df):,} rows "
        f"and {df.shape[1]} columns."
    )

    return df

def extract_data_from_azure() -> pd.DataFrame:
    """
    Load the raw DataCo dataset directly
    from Azure Blob Storage.
    """

    blob_data = download_blob_bytes(
        container_name=AZURE_RAW_CONTAINER,
        blob_name=RAW_DATA_FILE.name
    )

    df = pd.read_csv(
        BytesIO(blob_data),
        encoding="latin-1"
    )

    print(
        f"[EXTRACT] Loaded {len(df):,} rows "
        f"and {df.shape[1]} columns "
        f"from Azure Blob Storage."
    )

    return df


if __name__ == "__main__":

    df = extract_data_from_azure()

    print(df.shape)
    print(df.head())
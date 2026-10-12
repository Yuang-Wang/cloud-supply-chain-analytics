import pandas as pd

from config import (
    CLEAN_DATA_FILE,
    DQ_REPORT_FILE,
)


def save_validation_report(
    validation_report: pd.DataFrame
) -> None:
    """
    Save the data-quality validation report.
    """

    DQ_REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    validation_report.to_csv(
        DQ_REPORT_FILE,
        index=False
    )

    print(
        f"[LOAD] Data-quality report saved to: "
        f"{DQ_REPORT_FILE}"
    )


def save_clean_data(
    df: pd.DataFrame
) -> None:
    """
    Save analytics-ready supply-chain data.
    """

    CLEAN_DATA_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        CLEAN_DATA_FILE,
        index=False
    )

    file_size_mb = (
        CLEAN_DATA_FILE.stat().st_size
        / 1024
        / 1024
    )

    print(
        f"[LOAD] Clean dataset saved: "
        f"{len(df):,} rows × "
        f"{df.shape[1]} columns"
    )

    print(
        f"[LOAD] Output size: "
        f"{file_size_mb:.2f} MB"
    )

    print(
        f"[LOAD] File: "
        f"{CLEAN_DATA_FILE}"
    )


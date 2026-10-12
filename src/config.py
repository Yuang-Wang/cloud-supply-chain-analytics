from pathlib import Path


# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Data directories
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
REJECTED_DATA_DIR = PROJECT_ROOT / "data" / "rejected"

# Source file
RAW_DATA_FILE = RAW_DATA_DIR / "DataCoSupplyChainDataset.csv"

# Output files
CLEAN_DATA_FILE = PROCESSED_DATA_DIR / "supply_chain_clean.csv"
REPORTS_DIR = PROJECT_ROOT / "reports"

DQ_REPORT_FILE = REPORTS_DIR / "data_quality_summary.csv"

PIPELINE_RUN_LOG_FILE = (
    REPORTS_DIR
    / "pipeline_run_log.csv"
)

DQ_EXCEL_FILE = (
    REPORTS_DIR
    / "data_quality_report.xlsx"
)

# Azure Blob Storage
AZURE_STORAGE_ACCOUNT_NAME = "stcloudsupplychain2026yw"

AZURE_STORAGE_ACCOUNT_URL = (
    f"https://{AZURE_STORAGE_ACCOUNT_NAME}.blob.core.windows.net"
)

AZURE_RAW_CONTAINER = "raw"
AZURE_CURATED_CONTAINER = "curated"
AZURE_REJECTED_CONTAINER = "rejected"
AZURE_AUDIT_CONTAINER = "audit"
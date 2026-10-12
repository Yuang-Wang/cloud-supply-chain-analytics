import os
import time
from pathlib import Path

import pyodbc
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=ENV_FILE)


def get_sql_connection(
    max_retries: int = 3,
    retry_delay: int = 15
):

    server = os.getenv("AZURE_SQL_SERVER")
    database = os.getenv("AZURE_SQL_DATABASE")
    username = os.getenv("AZURE_SQL_USERNAME")
    password = os.getenv("AZURE_SQL_PASSWORD")

    required_variables = {
        "AZURE_SQL_SERVER": server,
        "AZURE_SQL_DATABASE": database,
        "AZURE_SQL_USERNAME": username,
        "AZURE_SQL_PASSWORD": password,
    }

    missing_variables = [
        name
        for name, value in required_variables.items()
        if not value
    ]

    if missing_variables:
        raise ValueError(
            "Missing environment variables: "
            + ", ".join(missing_variables)
        )

    connection_string = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER=tcp:{server},1433;"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=60;"
    )

    for attempt in range(1, max_retries + 1):

        try:

            connection = pyodbc.connect(
                connection_string
            )

            return connection

        except pyodbc.OperationalError as exc:

            if attempt == max_retries:
                raise

            print(
                f"[AZURE SQL] Connection attempt "
                f"{attempt}/{max_retries} failed."
            )

            print(
                f"[AZURE SQL] Retrying in "
                f"{retry_delay} seconds..."
            )

            time.sleep(retry_delay)
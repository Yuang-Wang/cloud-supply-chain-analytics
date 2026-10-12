import re
import sys
from pathlib import Path

from sql_connection import get_sql_connection


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_sql_file(sql_file: Path) -> None:
    sql_script = sql_file.read_text(
        encoding="utf-8"
    )

    # Split only when GO appears alone on a line
    batches = [
        batch.strip()
        for batch in re.split(
            r"^\s*GO\s*$",
            sql_script,
            flags=re.MULTILINE | re.IGNORECASE
        )
        if batch.strip()
    ]

    print(
        f"[SQL RUNNER] File: {sql_file.name}"
    )

    print(
        f"[SQL RUNNER] Batches found: {len(batches)}"
    )

    connection = get_sql_connection()

    try:
        cursor = connection.cursor()

        for i, batch in enumerate(
            batches,
            start=1
        ):
            print(
                f"[SQL RUNNER] Executing batch "
                f"{i}/{len(batches)}"
            )

            cursor.execute(batch)

        connection.commit()

        print(
            f"[AZURE SQL] Successfully executed: "
            f"{sql_file.name}"
        )

        cursor.close()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise ValueError(
            "Usage: python src/run_sql_file.py "
            "sql/<filename>.sql"
        )

    sql_file = PROJECT_ROOT / sys.argv[1]

    if not sql_file.exists():
        raise FileNotFoundError(
            f"SQL file not found: {sql_file}"
        )

    run_sql_file(sql_file)
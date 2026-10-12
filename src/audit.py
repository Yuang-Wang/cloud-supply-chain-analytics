import pandas as pd

from config import PIPELINE_RUN_LOG_FILE


def append_pipeline_run(
    run_id: str,
    run_timestamp_utc: str,
    source_rows: int,
    output_rows: int,
    dq_rules_passed: int,
    dq_rules_failed: int,
    runtime_seconds: float,
    pipeline_status: str,
    error_message: str = ""
) -> None:

    PIPELINE_RUN_LOG_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    run_record = pd.DataFrame([
        {
            "run_id": run_id,
            "run_timestamp_utc": run_timestamp_utc,
            "source_rows": source_rows,
            "output_rows": output_rows,
            "dq_rules_passed": dq_rules_passed,
            "dq_rules_failed": dq_rules_failed,
            "runtime_seconds": round(runtime_seconds, 2),
            "pipeline_status": pipeline_status,
            "error_message": error_message
        }
    ])

    file_exists = PIPELINE_RUN_LOG_FILE.exists()

    run_record.to_csv(
        PIPELINE_RUN_LOG_FILE,
        mode="a",
        header=not file_exists,
        index=False
    )

    print(
        f"[AUDIT] Pipeline run logged to: "
        f"{PIPELINE_RUN_LOG_FILE}"
    )
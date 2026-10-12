from datetime import datetime, timezone
from time import perf_counter
from uuid import uuid4

from extract import extract_data_from_azure
from transform import transform_data
from validate import run_validations
from load import (
    save_clean_data,
    save_validation_report,
)
from audit import append_pipeline_run
from report import create_excel_dq_report
from azure_storage import upload_file

from config import (
    CLEAN_DATA_FILE,
    DQ_REPORT_FILE,
    DQ_EXCEL_FILE,
    PIPELINE_RUN_LOG_FILE,
    AZURE_CURATED_CONTAINER,
    AZURE_AUDIT_CONTAINER
)

def run_pipeline() -> None:

    start_time = perf_counter()

    run_id = uuid4().hex[:12]

    run_timestamp_utc = (
        datetime.now(
            timezone.utc
        ).isoformat()
    )

    raw_df = None
    clean_df = None
    validation_report = None

    pipeline_status = "FAILED"
    error_message = ""

    print("=" * 60)
    print("SUPPLY CHAIN ANALYTICS PIPELINE")
    print("=" * 60)

    try:

        # -----------------------------
        # EXTRACT
        # -----------------------------

        raw_df = extract_data_from_azure()

        # -----------------------------
        # TRANSFORM
        # -----------------------------

        clean_df = transform_data(
            raw_df
        )

        print(
            f"[TRANSFORM] Produced "
            f"{len(clean_df):,} rows × "
            f"{clean_df.shape[1]} columns."
        )

        # -----------------------------
        # VALIDATE
        # -----------------------------

        validation_report = (
            run_validations(clean_df)
        )

        print("\n[VALIDATE]")

        print(
            validation_report.to_string(
                index=False
            )
        )

        save_validation_report(
            validation_report
        )
        upload_file(
            local_path=DQ_REPORT_FILE,
            container_name=AZURE_AUDIT_CONTAINER,
            blob_name=DQ_REPORT_FILE.name
        )
        # -----------------------------
        # QUALITY GATE
        # -----------------------------

        critical_failures = (
            validation_report[
                (
                    validation_report[
                        "status"
                    ] == "FAIL"
                )
                &
                (
                    validation_report[
                        "severity"
                    ] == "ERROR"
                )
            ]
        )

        if not critical_failures.empty:

            raise ValueError(
                "Critical data-quality "
                "rules failed."
            )

        # -----------------------------
        # LOAD
        # -----------------------------

        save_clean_data(
            clean_df
        )

        upload_file(
            local_path=CLEAN_DATA_FILE,
            container_name=AZURE_CURATED_CONTAINER,
            blob_name=CLEAN_DATA_FILE.name
        )

        pipeline_status = "SUCCESS"

    except Exception as exc:

        error_message = str(exc)

        print(
            f"\n[PIPELINE ERROR] "
            f"{error_message}"
        )

        raise

    finally:

        runtime_seconds = (
            perf_counter()
            -
            start_time
        )

        source_rows = (
            len(raw_df)
            if raw_df is not None
            else 0
        )

        output_rows = (
            len(clean_df)
            if clean_df is not None
            else 0
        )

        if validation_report is not None:

            passed_rules = int(
                (
                    validation_report[
                        "status"
                    ] == "PASS"
                ).sum()
            )

            failed_rules = int(
                (
                    validation_report[
                        "status"
                    ] == "FAIL"
                ).sum()
            )

        else:

            passed_rules = 0
            failed_rules = 0

        append_pipeline_run(
            run_id=run_id,
            run_timestamp_utc=run_timestamp_utc,
            source_rows=source_rows,
            output_rows=output_rows,
            dq_rules_passed=passed_rules,
            dq_rules_failed=failed_rules,
            runtime_seconds=runtime_seconds,
            pipeline_status=pipeline_status,
            error_message=error_message
        )

        if PIPELINE_RUN_LOG_FILE.exists():
            upload_file(
                local_path=PIPELINE_RUN_LOG_FILE,
                container_name=AZURE_AUDIT_CONTAINER,
                blob_name=PIPELINE_RUN_LOG_FILE.name
            )

        if (
            clean_df is not None
            and
            validation_report is not None
        ):

            create_excel_dq_report(
                df=clean_df,
                validation_report=validation_report,
                runtime_seconds=runtime_seconds,
                pipeline_status=pipeline_status
            )

            if DQ_EXCEL_FILE.exists():
                upload_file(
                    local_path=DQ_EXCEL_FILE,
                    container_name=AZURE_AUDIT_CONTAINER,
                    blob_name=DQ_EXCEL_FILE.name
                )

        print("\n" + "=" * 60)

        print(
            f"PIPELINE STATUS: "
            f"{pipeline_status}"
        )

        print("=" * 60)

        print(
            f"Run ID: "
            f"{run_id}"
        )

        print(
            f"Rows processed: "
            f"{output_rows:,}"
        )

        print(
            f"DQ rules passed: "
            f"{passed_rules}"
        )

        print(
            f"DQ rules failed: "
            f"{failed_rules}"
        )

        print(
            f"Runtime: "
            f"{runtime_seconds:.2f} seconds"
        )


if __name__ == "__main__":
    run_pipeline()
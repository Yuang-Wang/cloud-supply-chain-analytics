import pandas as pd

from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

from config import DQ_EXCEL_FILE


def build_column_profile(
    df: pd.DataFrame
) -> pd.DataFrame:

    profile = pd.DataFrame({
        "column_name": df.columns,
        "data_type": df.dtypes.astype(str).values,
        "non_null_count": df.notna().sum().values,
        "null_count": df.isna().sum().values,
        "null_pct": (
            df.isna().mean().values * 100
        ),
        "unique_count": [
            df[col].nunique(dropna=True)
            for col in df.columns
        ]
    })

    profile["null_pct"] = (
        profile["null_pct"].round(2)
    )

    return profile


def autosize_worksheet(ws) -> None:

    for column_cells in ws.columns:

        max_length = 0

        column_letter = get_column_letter(
            column_cells[0].column
        )

        for cell in column_cells:

            value = (
                ""
                if cell.value is None
                else str(cell.value)
            )

            max_length = max(
                max_length,
                len(value)
            )

        ws.column_dimensions[
            column_letter
        ].width = min(
            max_length + 2,
            40
        )


def create_excel_dq_report(
    df: pd.DataFrame,
    validation_report: pd.DataFrame,
    runtime_seconds: float,
    pipeline_status: str
) -> None:

    DQ_EXCEL_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    passed_rules = (
        validation_report["status"]
        == "PASS"
    ).sum()

    failed_rules = (
        validation_report["status"]
        == "FAIL"
    ).sum()

    summary = pd.DataFrame({
        "metric": [
            "Pipeline Status",
            "Rows Processed",
            "Columns",
            "Unique Orders",
            "Unique Customers",
            "Unique Products",
            "DQ Rules Passed",
            "DQ Rules Failed",
            "SLA Breach Rate",
            "Loss-Making Rate",
            "Runtime Seconds"
        ],
        "value": [
            pipeline_status,
            len(df),
            df.shape[1],
            df["order_id"].nunique(),
            df["customer_id"].nunique(),
            df["product_card_id"].nunique(),
            passed_rules,
            failed_rules,
            round(
                df["sla_breach_flag"].mean(),
                4
            ),
            round(
                df["loss_making_flag"].mean(),
                4
            ),
            round(runtime_seconds, 2)
        ]
    })

    column_profile = (
        build_column_profile(df)
    )

    with pd.ExcelWriter(
        DQ_EXCEL_FILE,
        engine="openpyxl"
    ) as writer:

        summary.to_excel(
            writer,
            sheet_name="Summary",
            index=False
        )

        validation_report.to_excel(
            writer,
            sheet_name="Validation Rules",
            index=False
        )

        column_profile.to_excel(
            writer,
            sheet_name="Column Profile",
            index=False
        )

        for worksheet in writer.book.worksheets:

            worksheet.freeze_panes = "A2"

            for cell in worksheet[1]:
                cell.font = Font(
                    bold=True
                )

            autosize_worksheet(
                worksheet
            )

    print(
        f"[REPORT] Excel DQ report saved to: "
        f"{DQ_EXCEL_FILE}"
    )
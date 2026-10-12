import numpy as np
import pandas as pd

def create_result(
    rule_id: str,
    rule_name: str,
    failed_rows: int,
    total_rows: int,
    severity: str = "ERROR"
) -> dict:
    """
    Create a standardized data-quality validation result.
    """

    failure_rate = (
        failed_rows / total_rows
        if total_rows > 0
        else 0
    )

    return {
        "rule_id": rule_id,
        "rule_name": rule_name,
        "status": "PASS" if failed_rows == 0 else "FAIL",
        "severity": severity,
        "failed_rows": failed_rows,
        "total_rows": total_rows,
        "failure_rate": round(failure_rate, 6)
    }

def validate_primary_key(df: pd.DataFrame) -> dict:

    failed_rows = (
        df["order_item_id"].isna().sum()
        +
        df["order_item_id"].duplicated().sum()
    )

    return create_result(
        rule_id="DQ001",
        rule_name="Order Item ID must be unique and non-null",
        failed_rows=int(failed_rows),
        total_rows=len(df)
    )

def validate_dates(df: pd.DataFrame) -> dict:

    invalid_dates = (
        df["order_date"].isna()
        |
        df["shipping_date"].isna()
    )

    return create_result(
        rule_id="DQ002",
        rule_name="Order and shipping dates must be valid",
        failed_rows=int(invalid_dates.sum()),
        total_rows=len(df)
    )

def validate_shipping_days(df: pd.DataFrame) -> dict:

    mismatch = (
        df["calculated_shipping_days"]
        !=
        df["days_for_shipping_real"]
    )

    return create_result(
        rule_id="DQ003",
        rule_name="Calculated shipping days must match source value",
        failed_rows=int(mismatch.sum()),
        total_rows=len(df)
    )

def validate_sla_rule(df: pd.DataFrame) -> dict:

    mismatch = (
        df["sla_breach_flag"]
        !=
        df["late_delivery_risk"]
    )

    return create_result(
        rule_id="DQ004",
        rule_name="Derived SLA breach must match source late-delivery flag",
        failed_rows=int(mismatch.sum()),
        total_rows=len(df)
    )

def validate_quantity(df: pd.DataFrame) -> dict:

    invalid_quantity = (
        df["order_item_quantity"] <= 0
    )

    return create_result(
        rule_id="DQ005",
        rule_name="Order quantity must be greater than zero",
        failed_rows=int(invalid_quantity.sum()),
        total_rows=len(df)
    )

def validate_product_price(df: pd.DataFrame) -> dict:

    invalid_price = (
        df["order_item_product_price"] <= 0
    )

    return create_result(
        rule_id="DQ006",
        rule_name="Product price must be greater than zero",
        failed_rows=int(invalid_price.sum()),
        total_rows=len(df)
    )

def validate_sales(df: pd.DataFrame) -> dict:

    calculated_sales = (
        df["order_item_quantity"]
        *
        df["order_item_product_price"]
    )

    valid_sales = np.isclose(
        df["sales"],
        calculated_sales,
        atol=0.01,
        rtol=0
    )

    return create_result(
        rule_id="DQ007",
        rule_name="Sales must reconcile to quantity × product price",
        failed_rows=int((~valid_sales).sum()),
        total_rows=len(df)
    )

def validate_discount_rate(df: pd.DataFrame) -> dict:

    invalid_rate = (
        (df["effective_discount_rate"] < 0)
        |
        (df["effective_discount_rate"] > 1)
        |
        (df["effective_discount_rate"].isna())
    )

    return create_result(
        rule_id="DQ008",
        rule_name="Effective discount rate must be between 0 and 1",
        failed_rows=int(invalid_rate.sum()),
        total_rows=len(df)
    )

def validate_order_total(df: pd.DataFrame) -> dict:

    calculated_total = (
        df["sales"]
        -
        df["order_item_discount"]
    )

    difference = (
        df["order_item_total"]
        -
        calculated_total
    ).abs()

    valid_total = difference <= 0.02

    return create_result(
        rule_id="DQ009",
        rule_name="Order total must reconcile within $0.02",
        failed_rows=int((~valid_total).sum()),
        total_rows=len(df)
    )

def validate_profit(df: pd.DataFrame) -> dict:

    invalid_profit = (
        df["order_profit_per_order"].isna()
    )

    return create_result(
        rule_id="DQ010",
        rule_name="Profit value must be present",
        failed_rows=int(invalid_profit.sum()),
        total_rows=len(df)
    )

def run_validations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run all data-quality rules and return
    a standardized validation report.
    """

    validation_functions = [
        validate_primary_key,
        validate_dates,
        validate_shipping_days,
        validate_sla_rule,
        validate_quantity,
        validate_product_price,
        validate_sales,
        validate_discount_rate,
        validate_order_total,
        validate_profit,
    ]

    results = []

    for validation_function in validation_functions:
        result = validation_function(df)
        results.append(result)

    report = pd.DataFrame(results)

    return report

if __name__ == "__main__":

    from extract import extract_data
    from transform import transform_data

    raw_df = extract_data()

    clean_df = transform_data(raw_df)

    validation_report = run_validations(clean_df)

    print("\n[DATA QUALITY REPORT]")
    print(validation_report.to_string(index=False))
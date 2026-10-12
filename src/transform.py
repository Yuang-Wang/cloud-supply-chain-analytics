import pandas as pd


DROP_COLUMNS = [
    "Product Description",
    "Customer Email",
    "Customer Password",
    "Customer Fname",
    "Customer Lname",
    "Customer Street",
    "Customer Zipcode",
    "Order Zipcode",
    "Product Image",
    "Benefit per order",
]


def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert raw column names to snake_case.
    """

    df = df.copy()

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(r"[()]", "", regex=True)
        .str.replace(r"[^a-z0-9]+", "_", regex=True)
        .str.strip("_")
    )

    return df

def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and transform raw supply-chain data
    into an analytics-ready dataset.
    """

    df = df.copy()

    # Remove redundant, sensitive and low-value columns
    columns_to_drop = [
        col for col in DROP_COLUMNS
        if col in df.columns
    ]

    df = df.drop(columns=columns_to_drop)

    # Standardize names after dropping raw columns
    df = standardize_column_names(df)

    # Parse timestamps
    df["order_date"] = pd.to_datetime(
        df["order_date_dateorders"],
        format="%m/%d/%Y %H:%M",
        errors="coerce"
    )

    df["shipping_date"] = pd.to_datetime(
        df["shipping_date_dateorders"],
        format="%m/%d/%Y %H:%M",
        errors="coerce"
    )

    # Recalculate calendar-based shipping duration
    df["calculated_shipping_days"] = (
        df["shipping_date"].dt.normalize()
        -
        df["order_date"].dt.normalize()
    ).dt.days

    # Analytics SLA breach rule discovered during profiling
    df["sla_breach_flag"] = (
        (
            df["days_for_shipping_real"]
            >
            df["days_for_shipment_scheduled"]
        )
        &
        (
            df["delivery_status"]
            != "Shipping canceled"
        )
    ).astype(int)

    # Effective discount rate based on actual discount amount
    df["effective_discount_rate"] = (
        df["order_item_discount"]
        /
        df["sales"]
    ).where(df["sales"] != 0)

    # Profitability indicator
    df["loss_making_flag"] = (
        df["order_profit_per_order"] < 0
    ).astype(int)


    return df

if __name__ == "__main__":

    from extract import extract_data

    raw_df = extract_data()

    clean_df = transform_data(raw_df)

    print(
        f"[TRANSFORM] Final shape: "
        f"{clean_df.shape[0]:,} rows × "
        f"{clean_df.shape[1]} columns"
    )

    print(
        clean_df[
            [
                "order_item_id",
                "order_id",
                "order_date",
                "shipping_date",
                "sla_breach_flag",
                "effective_discount_rate",
                "loss_making_flag",
            ]
        ].head()
    )
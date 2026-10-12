import math

import pandas as pd

from extract import extract_data_from_azure
from transform import transform_data
from sql_connection import get_sql_connection


# ============================================================
# DIMENSION BUILDERS
# ============================================================

def build_dim_customer(df: pd.DataFrame) -> pd.DataFrame:

    conflicts = (
        df.groupby("customer_id")["customer_segment"]
        .nunique(dropna=False)
    )

    if (conflicts > 1).any():
        raise ValueError(
            "Customer dimension integrity check failed: "
            "one customer_id maps to multiple segments."
        )

    dim = (
        df[
            [
                "customer_id",
                "customer_segment",
            ]
        ]
        .drop_duplicates()
        .sort_values("customer_id")
        .reset_index(drop=True)
    )

    dim.insert(
        0,
        "customer_key",
        range(1, len(dim) + 1)
    )

    return dim


def build_dim_product(df: pd.DataFrame) -> pd.DataFrame:

    conflicts = (
        df.groupby("product_card_id")["product_name"]
        .nunique(dropna=False)
    )

    if (conflicts > 1).any():
        raise ValueError(
            "Product dimension integrity check failed: "
            "one product_card_id maps to multiple names."
        )

    dim = (
        df[
            [
                "product_card_id",
                "product_name",
                "category_id",
                "category_name",
                "department_id",
                "department_name",
            ]
        ]
        .drop_duplicates()
        .sort_values("product_card_id")
        .reset_index(drop=True)
    )

    dim.insert(
        0,
        "product_key",
        range(1, len(dim) + 1)
    )

    return dim


def build_dim_geography(df: pd.DataFrame) -> pd.DataFrame:

    columns = [
        "market",
        "order_region",
        "order_country",
        "order_state",
        "order_city",
    ]

    dim = (
        df[columns]
        .drop_duplicates()
        .sort_values(columns)
        .reset_index(drop=True)
    )

    dim.insert(
        0,
        "geography_key",
        range(1, len(dim) + 1)
    )

    return dim


def build_dim_shipping(df: pd.DataFrame) -> pd.DataFrame:

    columns = [
        "shipping_mode",
        "delivery_status",
        "order_status",
    ]

    dim = (
        df[columns]
        .drop_duplicates()
        .sort_values(columns)
        .reset_index(drop=True)
    )

    dim.insert(
        0,
        "shipping_key",
        range(1, len(dim) + 1)
    )

    return dim


def build_dim_date(df: pd.DataFrame) -> pd.DataFrame:

    dates = pd.concat(
        [
            df["order_date"].dt.normalize(),
            df["shipping_date"].dt.normalize(),
        ]
    )

    dates = (
        dates
        .dropna()
        .drop_duplicates()
        .sort_values()
        .reset_index(drop=True)
    )

    dim = pd.DataFrame(
        {"full_date": dates}
    )

    dim["date_key"] = (
        dim["full_date"]
        .dt.strftime("%Y%m%d")
        .astype(int)
    )

    dim["calendar_year"] = dim["full_date"].dt.year
    dim["calendar_quarter"] = dim["full_date"].dt.quarter
    dim["calendar_month"] = dim["full_date"].dt.month
    dim["month_name"] = dim["full_date"].dt.month_name()
    dim["day_of_month"] = dim["full_date"].dt.day
    dim["day_of_week"] = dim["full_date"].dt.dayofweek + 1
    dim["day_name"] = dim["full_date"].dt.day_name()

    dim["full_date"] = dim["full_date"].dt.date

    return dim[
        [
            "date_key",
            "full_date",
            "calendar_year",
            "calendar_quarter",
            "calendar_month",
            "month_name",
            "day_of_month",
            "day_of_week",
            "day_name",
        ]
    ]


# ============================================================
# FACT BUILDER
# ============================================================

def build_fact_order_item(
    df: pd.DataFrame,
    dim_customer: pd.DataFrame,
    dim_product: pd.DataFrame,
    dim_geography: pd.DataFrame,
    dim_shipping: pd.DataFrame,
) -> pd.DataFrame:

    fact = df.copy()

    fact = fact.merge(
        dim_customer,
        on=[
            "customer_id",
            "customer_segment"
        ],
        how="left"
    )

    fact = fact.merge(
        dim_product,
        on=[
            "product_card_id",
            "product_name",
            "category_id",
            "category_name",
            "department_id",
            "department_name",
        ],
        how="left"
    )

    geography_columns = [
        "market",
        "order_region",
        "order_country",
        "order_state",
        "order_city",
    ]

    fact = fact.merge(
        dim_geography,
        on=geography_columns,
        how="left"
    )

    shipping_columns = [
        "shipping_mode",
        "delivery_status",
        "order_status",
    ]

    fact = fact.merge(
        dim_shipping,
        on=shipping_columns,
        how="left"
    )

    fact["order_date_key"] = (
        fact["order_date"]
        .dt.strftime("%Y%m%d")
        .astype(int)
    )

    fact["shipping_date_key"] = (
        fact["shipping_date"]
        .dt.strftime("%Y%m%d")
        .astype(int)
    )

    fact = fact.rename(
        columns={
            "order_item_quantity": "quantity",
            "order_item_product_price": "unit_price",
            "sales": "gross_sales",
            "order_item_discount": "discount_amount",
            "order_item_total": "net_sales",
            "order_profit_per_order": "profit_amount",
            "order_item_profit_ratio": "profit_ratio",
            "days_for_shipping_real": "actual_shipping_days",
            "days_for_shipment_scheduled": "scheduled_shipping_days",
        }
    )

    fact["order_datetime"] = fact["order_date"]
    fact["shipping_datetime"] = fact["shipping_date"]

    required_keys = [
        "customer_key",
        "product_key",
        "geography_key",
        "shipping_key",
        "order_date_key",
        "shipping_date_key",
    ]

    if fact[required_keys].isna().any().any():
        raise ValueError(
            "Fact table contains missing foreign keys."
        )

    return fact[
        [
            "order_item_id",
            "order_id",
            "customer_key",
            "product_key",
            "geography_key",
            "shipping_key",
            "order_date_key",
            "shipping_date_key",
            "order_datetime",
            "shipping_datetime",
            "quantity",
            "unit_price",
            "gross_sales",
            "discount_amount",
            "effective_discount_rate",
            "net_sales",
            "profit_amount",
            "profit_ratio",
            "actual_shipping_days",
            "scheduled_shipping_days",
            "late_delivery_risk",
            "sla_breach_flag",
            "loss_making_flag",
        ]
    ]


# ============================================================
# SQL HELPERS
# ============================================================

def clean_sql_value(value):

    if pd.isna(value):
        return None

    if hasattr(value, "item"):
        try:
            return value.item()
        except ValueError:
            pass

    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()

    return value


def dataframe_records(df: pd.DataFrame):

    return [
        tuple(
            clean_sql_value(value)
            for value in row
        )
        for row in df.itertuples(
            index=False,
            name=None
        )
    ]


def clear_warehouse(cursor):

    print("[WAREHOUSE] Clearing existing data...")

    cursor.execute(
        "DELETE FROM dw.fact_order_item;"
    )

    cursor.execute(
        "DELETE FROM dw.dim_shipping;"
    )

    cursor.execute(
        "DELETE FROM dw.dim_geography;"
    )

    cursor.execute(
        "DELETE FROM dw.dim_product;"
    )

    cursor.execute(
        "DELETE FROM dw.dim_customer;"
    )

    cursor.execute(
        "DELETE FROM dw.dim_date;"
    )


def bulk_insert(
    cursor,
    sql: str,
    df: pd.DataFrame,
    table_name: str,
    batch_size: int = 5000,
):

    records = dataframe_records(df)

    cursor.fast_executemany = True

    total_batches = math.ceil(
        len(records) / batch_size
    )

    for batch_number, start in enumerate(
        range(0, len(records), batch_size),
        start=1
    ):

        batch = records[
            start:start + batch_size
        ]

        cursor.executemany(
            sql,
            batch
        )

        print(
            f"[LOAD] {table_name}: "
            f"batch {batch_number}/{total_batches}"
        )


# ============================================================
# MAIN WAREHOUSE LOAD
# ============================================================

def load_warehouse():

    print("=" * 60)
    print("AZURE SQL WAREHOUSE LOAD")
    print("=" * 60)

    raw_df = extract_data_from_azure()
    df = transform_data(raw_df)

    # Build dimensions
    dim_customer = build_dim_customer(df)
    dim_product = build_dim_product(df)
    dim_geography = build_dim_geography(df)
    dim_shipping = build_dim_shipping(df)
    dim_date = build_dim_date(df)

    print("\n[DIMENSION COUNTS]")
    print(f"Customers:   {len(dim_customer):,}")
    print(f"Products:    {len(dim_product):,}")
    print(f"Geographies: {len(dim_geography):,}")
    print(f"Shipping:    {len(dim_shipping):,}")
    print(f"Dates:       {len(dim_date):,}")

    # Build fact
    fact = build_fact_order_item(
        df,
        dim_customer,
        dim_product,
        dim_geography,
        dim_shipping,
    )

    print(
        f"Fact rows:   {len(fact):,}"
    )

    if fact["order_item_id"].nunique() != len(fact):
        raise ValueError(
            "Fact grain validation failed: "
            "order_item_id is not unique."
        )

    connection = get_sql_connection()

    try:

        cursor = connection.cursor()

        clear_warehouse(cursor)

        # ----------------------------------------
        # DATE
        # ----------------------------------------

        bulk_insert(
            cursor,
            """
            INSERT INTO dw.dim_date (
                date_key,
                full_date,
                calendar_year,
                calendar_quarter,
                calendar_month,
                month_name,
                day_of_month,
                day_of_week,
                day_name
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            dim_date,
            "dim_date"
        )

        # ----------------------------------------
        # CUSTOMER
        # ----------------------------------------

        cursor.execute(
            "SET IDENTITY_INSERT dw.dim_customer ON;"
        )

        bulk_insert(
            cursor,
            """
            INSERT INTO dw.dim_customer (
                customer_key,
                customer_id,
                customer_segment
            )
            VALUES (?, ?, ?)
            """,
            dim_customer,
            "dim_customer"
        )

        cursor.execute(
            "SET IDENTITY_INSERT dw.dim_customer OFF;"
        )

        # ----------------------------------------
        # PRODUCT
        # ----------------------------------------

        cursor.execute(
            "SET IDENTITY_INSERT dw.dim_product ON;"
        )

        bulk_insert(
            cursor,
            """
            INSERT INTO dw.dim_product (
                product_key,
                product_card_id,
                product_name,
                category_id,
                category_name,
                department_id,
                department_name
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            dim_product,
            "dim_product"
        )

        cursor.execute(
            "SET IDENTITY_INSERT dw.dim_product OFF;"
        )

        # ----------------------------------------
        # GEOGRAPHY
        # ----------------------------------------

        cursor.execute(
            "SET IDENTITY_INSERT dw.dim_geography ON;"
        )

        bulk_insert(
            cursor,
            """
            INSERT INTO dw.dim_geography (
                geography_key,
                market,
                order_region,
                order_country,
                order_state,
                order_city
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            dim_geography,
            "dim_geography"
        )

        cursor.execute(
            "SET IDENTITY_INSERT dw.dim_geography OFF;"
        )

        # ----------------------------------------
        # SHIPPING
        # ----------------------------------------

        cursor.execute(
            "SET IDENTITY_INSERT dw.dim_shipping ON;"
        )

        bulk_insert(
            cursor,
            """
            INSERT INTO dw.dim_shipping (
                shipping_key,
                shipping_mode,
                delivery_status,
                order_status
            )
            VALUES (?, ?, ?, ?)
            """,
            dim_shipping,
            "dim_shipping"
        )

        cursor.execute(
            "SET IDENTITY_INSERT dw.dim_shipping OFF;"
        )

        # ----------------------------------------
        # FACT
        # ----------------------------------------

        bulk_insert(
            cursor,
            """
            INSERT INTO dw.fact_order_item (
                order_item_id,
                order_id,
                customer_key,
                product_key,
                geography_key,
                shipping_key,
                order_date_key,
                shipping_date_key,
                order_datetime,
                shipping_datetime,
                quantity,
                unit_price,
                gross_sales,
                discount_amount,
                effective_discount_rate,
                net_sales,
                profit_amount,
                profit_ratio,
                actual_shipping_days,
                scheduled_shipping_days,
                late_delivery_risk,
                sla_breach_flag,
                loss_making_flag
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?
            )
            """,
            fact,
            "fact_order_item"
        )

        connection.commit()

        print("\n" + "=" * 60)
        print("WAREHOUSE LOAD COMPLETED")
        print("=" * 60)

    except Exception:

        connection.rollback()

        print(
            "\n[WAREHOUSE] Load failed. "
            "Transaction rolled back."
        )

        raise

    finally:

        connection.close()


if __name__ == "__main__":
    load_warehouse()
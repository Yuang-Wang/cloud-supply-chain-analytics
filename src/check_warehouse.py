from sql_connection import get_sql_connection

from sql_connection import get_sql_connection


connection = get_sql_connection()
cursor = connection.cursor()

tables = [
    "dim_customer",
    "dim_product",
    "dim_geography",
    "dim_shipping",
    "dim_date",
    "fact_order_item",
]

print("[WAREHOUSE ROW COUNTS]")

for table in tables:

    cursor.execute(
        f"SELECT COUNT(*) FROM dw.{table}"
    )

    count = cursor.fetchone()[0]

    print(
        f"{table:<20} {count:>10,}"
    )


cursor.execute(
    """
    SELECT
        COUNT(*) AS fact_rows,
        COUNT(DISTINCT order_item_id)
            AS unique_order_items,
        COUNT(DISTINCT order_id)
            AS unique_orders
    FROM dw.fact_order_item;
    """
)

row = cursor.fetchone()

print("\n[FACT GRAIN VALIDATION]")
print(f"Fact rows:          {row.fact_rows:,}")
print(f"Unique order items: {row.unique_order_items:,}")
print(f"Unique orders:      {row.unique_orders:,}")

cursor.close()
connection.close()
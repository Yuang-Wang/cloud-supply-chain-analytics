/* ============================================================
   Cloud Supply Chain Analytics
   Analytics Views
   ============================================================ */


/* ============================================================
   1. MONTHLY EXECUTIVE KPIs

   Includes:
   - Revenue
   - Profit
   - Orders
   - Customers
   - SLA breach rate
   - Loss-making rate
   - MoM sales growth
   - MoM profit growth
   ============================================================ */

CREATE OR ALTER VIEW dw.vw_monthly_kpis
AS

WITH monthly_metrics AS (

    SELECT
        d.calendar_year,
        d.calendar_month,
        d.month_name,

        COUNT(DISTINCT f.order_id)
            AS total_orders,

        COUNT(DISTINCT f.customer_key)
            AS unique_customers,

        SUM(f.quantity)
            AS units_sold,

        SUM(f.gross_sales)
            AS gross_sales,

        SUM(f.discount_amount)
            AS discount_amount,

        SUM(f.net_sales)
            AS net_sales,

        SUM(f.profit_amount)
            AS profit_amount,

        AVG(
            CAST(f.sla_breach_flag AS FLOAT)
        )
            AS sla_breach_rate,

        AVG(
            CAST(f.loss_making_flag AS FLOAT)
        )
            AS loss_making_rate

    FROM dw.fact_order_item f

    JOIN dw.dim_date d
        ON f.order_date_key = d.date_key

    GROUP BY
        d.calendar_year,
        d.calendar_month,
        d.month_name
),

with_previous AS (

    SELECT
        *,

        LAG(net_sales) OVER (
            ORDER BY
                calendar_year,
                calendar_month
        )
            AS previous_month_sales,

        LAG(profit_amount) OVER (
            ORDER BY
                calendar_year,
                calendar_month
        )
            AS previous_month_profit

    FROM monthly_metrics
)

SELECT
    calendar_year,
    calendar_month,
    month_name,

    total_orders,
    unique_customers,
    units_sold,

    gross_sales,
    discount_amount,
    net_sales,
    profit_amount,

    sla_breach_rate,
    loss_making_rate,

    CASE
        WHEN previous_month_sales IS NULL
            OR previous_month_sales = 0
        THEN NULL

        ELSE
            (
                net_sales
                - previous_month_sales
            )
            / ABS(previous_month_sales)

    END AS mom_sales_growth,

    CASE
        WHEN previous_month_profit IS NULL
            OR previous_month_profit = 0
        THEN NULL

        ELSE
            (
                profit_amount
                - previous_month_profit
            )
            / ABS(previous_month_profit)

    END AS mom_profit_growth

FROM with_previous;
GO


/* ============================================================
   2. PRODUCT PROFITABILITY

   Product-level:
   - Revenue
   - Profit
   - Margin
   - Loss rate
   - Profit ranking
   ============================================================ */

CREATE OR ALTER VIEW dw.vw_product_profitability
AS

WITH product_metrics AS (

    SELECT
        p.product_key,
        p.product_card_id,
        p.product_name,
        p.category_name,
        p.department_name,

        COUNT(DISTINCT f.order_id)
            AS total_orders,

        SUM(f.quantity)
            AS units_sold,

        SUM(f.net_sales)
            AS net_sales,

        SUM(f.profit_amount)
            AS profit_amount,

        AVG(
            CAST(f.loss_making_flag AS FLOAT)
        )
            AS loss_making_rate

    FROM dw.fact_order_item f

    JOIN dw.dim_product p
        ON f.product_key = p.product_key

    GROUP BY
        p.product_key,
        p.product_card_id,
        p.product_name,
        p.category_name,
        p.department_name
)

SELECT
    *,

    CASE
        WHEN net_sales = 0
        THEN NULL

        ELSE
            profit_amount / net_sales

    END AS profit_margin,

    RANK() OVER (
        ORDER BY profit_amount DESC
    ) AS profit_rank,

    RANK() OVER (
        ORDER BY net_sales DESC
    ) AS sales_rank

FROM product_metrics;
GO


/* ============================================================
   3. SHIPPING PERFORMANCE

   Compare shipping modes:
   - Orders
   - Average shipping days
   - SLA breach rate
   - Cancellation rate
   ============================================================ */

CREATE OR ALTER VIEW dw.vw_shipping_performance
AS

SELECT
    s.shipping_mode,

    COUNT(DISTINCT f.order_id)
        AS total_orders,

    COUNT(*)
        AS total_line_items,

    AVG(
        CAST(f.actual_shipping_days AS FLOAT)
    )
        AS avg_actual_shipping_days,

    AVG(
        CAST(f.scheduled_shipping_days AS FLOAT)
    )
        AS avg_scheduled_shipping_days,

    AVG(
        CAST(f.sla_breach_flag AS FLOAT)
    )
        AS sla_breach_rate,

    AVG(
        CASE
            WHEN s.delivery_status = 'Shipping canceled'
            THEN 1.0
            ELSE 0.0
        END
    )
        AS cancellation_rate

FROM dw.fact_order_item f

JOIN dw.dim_shipping s
    ON f.shipping_key = s.shipping_key

GROUP BY
    s.shipping_mode;
GO


/* ============================================================
   4. PRODUCT SALES PARETO ANALYSIS

   Uses:
   - CTE
   - Window SUM
   - Running total
   - Cumulative contribution
   ============================================================ */

CREATE OR ALTER VIEW dw.vw_product_sales_pareto
AS

WITH product_sales AS (

    SELECT
        p.product_key,
        p.product_name,
        p.category_name,
        SUM(f.net_sales) AS net_sales

    FROM dw.fact_order_item f

    JOIN dw.dim_product p
        ON f.product_key = p.product_key

    GROUP BY
        p.product_key,
        p.product_name,
        p.category_name
),

ranked_products AS (

    SELECT
        *,

        SUM(net_sales) OVER ()
            AS total_sales,

        SUM(net_sales) OVER (
            ORDER BY net_sales DESC
            ROWS BETWEEN
                UNBOUNDED PRECEDING
                AND CURRENT ROW
        ) AS cumulative_sales

    FROM product_sales
),

with_previous AS (

    SELECT
        *,

        LAG(cumulative_sales, 1, 0)
        OVER (ORDER BY net_sales DESC)
            AS previous_cumulative_sales

    FROM ranked_products
)

SELECT
    product_key,
    product_name,
    category_name,
    net_sales,

    net_sales
        / NULLIF(total_sales, 0)
        AS sales_share,

    cumulative_sales
        / NULLIF(total_sales, 0)
        AS cumulative_sales_share,

    CASE
        WHEN previous_cumulative_sales
             / NULLIF(total_sales, 0) < 0.80
        THEN 'Core 80% Contributor'
        ELSE 'Long Tail'
    END AS pareto_group

FROM with_previous;
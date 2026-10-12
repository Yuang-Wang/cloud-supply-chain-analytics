/* ============================================================
   Cloud Supply Chain Analytics
   Azure SQL Star Schema
   ============================================================ */

IF NOT EXISTS (
    SELECT 1
    FROM sys.schemas
    WHERE name = 'dw'
)
BEGIN
    EXEC('CREATE SCHEMA dw');
END;


/* ============================================================
   DROP TABLES
   Fact must be dropped before dimensions because of FKs.
   ============================================================ */

DROP TABLE IF EXISTS dw.fact_order_item;
DROP TABLE IF EXISTS dw.dim_shipping;
DROP TABLE IF EXISTS dw.dim_geography;
DROP TABLE IF EXISTS dw.dim_product;
DROP TABLE IF EXISTS dw.dim_customer;
DROP TABLE IF EXISTS dw.dim_date;


/* ============================================================
   DIMENSION: DATE
   Role-playing dimension:
   - order_date_key
   - shipping_date_key
   ============================================================ */

CREATE TABLE dw.dim_date (
    date_key        INT            NOT NULL,
    full_date       DATE           NOT NULL,
    calendar_year   SMALLINT       NOT NULL,
    calendar_quarter TINYINT       NOT NULL,
    calendar_month  TINYINT        NOT NULL,
    month_name      VARCHAR(15)    NOT NULL,
    day_of_month    TINYINT        NOT NULL,
    day_of_week     TINYINT        NOT NULL,
    day_name        VARCHAR(15)    NOT NULL,

    CONSTRAINT PK_dim_date
        PRIMARY KEY (date_key),

    CONSTRAINT UQ_dim_date_full_date
        UNIQUE (full_date)
);


/* ============================================================
   DIMENSION: CUSTOMER

   PII such as name, email, password and street is deliberately
   excluded from the analytical warehouse.
   ============================================================ */

CREATE TABLE dw.dim_customer (
    customer_key        INT IDENTITY(1,1) NOT NULL,
    customer_id         INT               NOT NULL,
    customer_segment    VARCHAR(50)       NULL,

    CONSTRAINT PK_dim_customer
        PRIMARY KEY (customer_key),

    CONSTRAINT UQ_dim_customer
        UNIQUE (customer_id)
);


/* ============================================================
   DIMENSION: PRODUCT
   ============================================================ */

CREATE TABLE dw.dim_product (
    product_key         INT IDENTITY(1,1) NOT NULL,
    product_card_id     INT               NOT NULL,
    product_name        VARCHAR(255)      NULL,
    category_id         INT               NULL,
    category_name       VARCHAR(100)      NULL,
    department_id       INT               NULL,
    department_name     VARCHAR(100)      NULL,

    CONSTRAINT PK_dim_product
        PRIMARY KEY (product_key),

    CONSTRAINT UQ_dim_product
        UNIQUE (product_card_id)
);


/* ============================================================
   DIMENSION: GEOGRAPHY

   Grain:
   one unique combination of order destination attributes.
   ============================================================ */

CREATE TABLE dw.dim_geography (
    geography_key       INT IDENTITY(1,1) NOT NULL,
    market              VARCHAR(50)       NULL,
    order_region        VARCHAR(100)      NULL,
    order_country       VARCHAR(100)      NULL,
    order_state         VARCHAR(100)      NULL,
    order_city          VARCHAR(100)      NULL,

    CONSTRAINT PK_dim_geography
        PRIMARY KEY (geography_key)
);


/* ============================================================
   DIMENSION: SHIPPING
   ============================================================ */

CREATE TABLE dw.dim_shipping (
    shipping_key        INT IDENTITY(1,1) NOT NULL,
    shipping_mode       VARCHAR(50)       NULL,
    delivery_status     VARCHAR(50)       NULL,
    order_status        VARCHAR(50)       NULL,

    CONSTRAINT PK_dim_shipping
        PRIMARY KEY (shipping_key)
);


/* ============================================================
   FACT TABLE

   Grain:
   One row = one order line item.
   ============================================================ */

CREATE TABLE dw.fact_order_item (
    order_item_key              BIGINT IDENTITY(1,1) NOT NULL,

    order_item_id               INT        NOT NULL,
    order_id                    INT        NOT NULL,

    customer_key                INT        NOT NULL,
    product_key                 INT        NOT NULL,
    geography_key               INT        NOT NULL,
    shipping_key                INT        NOT NULL,

    order_date_key              INT        NOT NULL,
    shipping_date_key           INT        NOT NULL,

    order_datetime              DATETIME2(0) NULL,
    shipping_datetime           DATETIME2(0) NULL,

    quantity                    SMALLINT       NOT NULL,
    unit_price                  DECIMAL(12,2)  NOT NULL,
    gross_sales                 DECIMAL(12,2)  NOT NULL,
    discount_amount             DECIMAL(12,2)  NOT NULL,
    effective_discount_rate     DECIMAL(9,6)   NULL,
    net_sales                   DECIMAL(12,2)  NOT NULL,

    profit_amount               DECIMAL(12,2)  NULL,
    profit_ratio                DECIMAL(9,6)   NULL,

    actual_shipping_days        SMALLINT       NULL,
    scheduled_shipping_days     SMALLINT       NULL,

    late_delivery_risk          BIT            NOT NULL,
    sla_breach_flag             BIT            NOT NULL,
    loss_making_flag            BIT            NOT NULL,

    loaded_at_utc               DATETIME2(0)
        NOT NULL
        CONSTRAINT DF_fact_loaded_at
        DEFAULT SYSUTCDATETIME(),

    CONSTRAINT PK_fact_order_item
        PRIMARY KEY (order_item_key),

    CONSTRAINT UQ_fact_order_item
        UNIQUE (order_item_id),

    CONSTRAINT FK_fact_customer
        FOREIGN KEY (customer_key)
        REFERENCES dw.dim_customer(customer_key),

    CONSTRAINT FK_fact_product
        FOREIGN KEY (product_key)
        REFERENCES dw.dim_product(product_key),

    CONSTRAINT FK_fact_geography
        FOREIGN KEY (geography_key)
        REFERENCES dw.dim_geography(geography_key),

    CONSTRAINT FK_fact_shipping
        FOREIGN KEY (shipping_key)
        REFERENCES dw.dim_shipping(shipping_key),

    CONSTRAINT FK_fact_order_date
        FOREIGN KEY (order_date_key)
        REFERENCES dw.dim_date(date_key),

    CONSTRAINT FK_fact_shipping_date
        FOREIGN KEY (shipping_date_key)
        REFERENCES dw.dim_date(date_key)
);


/* ============================================================
   PERFORMANCE INDEXES
   ============================================================ */

CREATE INDEX IX_fact_order_date
ON dw.fact_order_item(order_date_key);

CREATE INDEX IX_fact_customer
ON dw.fact_order_item(customer_key);

CREATE INDEX IX_fact_product
ON dw.fact_order_item(product_key);

CREATE INDEX IX_fact_geography
ON dw.fact_order_item(geography_key);

CREATE INDEX IX_fact_shipping
ON dw.fact_order_item(shipping_key);
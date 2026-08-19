-- ==============================================================================
-- Schema: Subscription & Billing Analytics Data Warehouse
-- Component: DuckDB Analytical Engine Schema & Parquet Views
-- ==============================================================================

-- Direct analytical tables in DuckDB
CREATE TABLE IF NOT EXISTS dim_date (
    date_sk             INTEGER PRIMARY KEY,
    calendar_date       DATE NOT NULL,
    year                SMALLINT NOT NULL,
    quarter             SMALLINT NOT NULL,
    quarter_name        VARCHAR,
    month               SMALLINT NOT NULL,
    month_name          VARCHAR,
    month_year          VARCHAR,
    day_of_month        SMALLINT NOT NULL,
    day_of_week         SMALLINT NOT NULL,
    day_name            VARCHAR,
    is_weekend          BOOLEAN NOT NULL,
    is_month_start      BOOLEAN NOT NULL,
    is_month_end        BOOLEAN NOT NULL,
    fiscal_quarter      VARCHAR,
    fiscal_year         SMALLINT NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_subscription_plan (
    plan_sk             INTEGER PRIMARY KEY,
    plan_id             VARCHAR NOT NULL,
    plan_code           VARCHAR NOT NULL,
    plan_name           VARCHAR NOT NULL,
    billing_interval    VARCHAR NOT NULL,
    tier_level          SMALLINT NOT NULL,
    base_price_usd      DECIMAL(10, 2) NOT NULL,
    seat_limit          INTEGER NOT NULL,
    is_active           BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_users (
    user_sk             BIGINT PRIMARY KEY,
    user_id             VARCHAR NOT NULL,
    email               VARCHAR NOT NULL,
    country             VARCHAR NOT NULL,
    acquisition_channel VARCHAR NOT NULL,
    billing_currency    VARCHAR NOT NULL,
    subscription_tier   VARCHAR NOT NULL,
    account_status      VARCHAR NOT NULL,
    start_date          TIMESTAMP NOT NULL,
    end_date            TIMESTAMP,
    is_current          BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_subscription_events (
    event_sk            BIGINT,
    event_id            VARCHAR NOT NULL,
    user_sk             BIGINT NOT NULL,
    plan_sk             INTEGER NOT NULL,
    date_sk             INTEGER NOT NULL,
    event_type          VARCHAR NOT NULL,
    quantity            INTEGER NOT NULL,
    gross_amount_usd    DECIMAL(12, 2) NOT NULL,
    discount_amount_usd DECIMAL(12, 2) NOT NULL,
    tax_amount_usd      DECIMAL(12, 2) NOT NULL,
    net_amount_usd      DECIMAL(12, 2) NOT NULL,
    mrr_delta_usd       DECIMAL(12, 2) NOT NULL,
    event_timestamp     TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_monthly_financial_snapshot (
    snapshot_sk             BIGINT PRIMARY KEY,
    snapshot_month_sk       INTEGER NOT NULL,
    snapshot_date           DATE NOT NULL,
    user_sk                 BIGINT NOT NULL,
    user_id                 VARCHAR NOT NULL,
    plan_sk                 INTEGER NOT NULL,
    is_active_subscriber    BOOLEAN NOT NULL,
    mrr_usd                 DECIMAL(12, 2) NOT NULL,
    arr_usd                 DECIMAL(12, 2) NOT NULL,
    new_mrr_usd             DECIMAL(12, 2) NOT NULL,
    expansion_mrr_usd       DECIMAL(12, 2) NOT NULL,
    contraction_mrr_usd     DECIMAL(12, 2) NOT NULL,
    churned_mrr_usd         DECIMAL(12, 2) NOT NULL,
    net_mrr_movement_usd    DECIMAL(12, 2) NOT NULL,
    discount_applied_usd    DECIMAL(12, 2) NOT NULL,
    cumulative_revenue_usd  DECIMAL(14, 2) NOT NULL
);

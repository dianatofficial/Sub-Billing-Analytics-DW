-- ==============================================================================
-- Schema: Subscription & Billing Analytics Data Warehouse
-- Component: Fact Tables (Kimball Star Schema)
-- Database Engine: PostgreSQL 14+ / Declarative Range Partitioning
-- ==============================================================================

-- 1. Subscription Events Fact (Transactional Event Fact Table)
-- Partitioned declaratively by range on event_timestamp to optimize time-series queries.
CREATE TABLE IF NOT EXISTS fact_subscription_events (
    event_sk            BIGSERIAL,
    event_id            VARCHAR(64) NOT NULL,
    user_sk             BIGINT NOT NULL,             -- Foreign Key -> dim_users (SCD2 snapshot key)
    plan_sk             INTEGER NOT NULL,            -- Foreign Key -> dim_subscription_plan
    date_sk             INTEGER NOT NULL,            -- Foreign Key -> dim_date (YYYYMMDD)
    event_type          VARCHAR(32) NOT NULL,        -- 'signup', 'trial_start', 'upgrade', 'downgrade', 'renewal', 'cancellation', 'invoice_paid', 'payment_failed', 'refund'
    quantity            INTEGER NOT NULL DEFAULT 1,
    gross_amount_usd    NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    discount_amount_usd NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    tax_amount_usd      NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    net_amount_usd      NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    mrr_delta_usd       NUMERIC(12, 2) NOT NULL DEFAULT 0.00, -- Incremental MRR impact of this transaction
    event_timestamp     TIMESTAMP NOT NULL,
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (event_sk, event_timestamp)
) PARTITION BY RANGE (event_timestamp);

-- 2. Monthly Financial Snapshot Fact (Periodic Snapshot Fact Table)
-- Pre-aggregates subscriber and financial state at each month-end boundary.
CREATE TABLE IF NOT EXISTS fact_monthly_financial_snapshot (
    snapshot_sk             BIGSERIAL PRIMARY KEY,
    snapshot_month_sk       INTEGER NOT NULL,            -- Format: YYYYMM (Month grain)
    snapshot_date           DATE NOT NULL,               -- End of month date (e.g., 2024-01-31)
    user_sk                 BIGINT NOT NULL,             -- Foreign Key -> dim_users (SCD2 current at month-end)
    user_id                 VARCHAR(64) NOT NULL,        -- Natural Key for user aggregation
    plan_sk                 INTEGER NOT NULL,            -- Foreign Key -> dim_subscription_plan
    is_active_subscriber    BOOLEAN NOT NULL,
    mrr_usd                 NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    arr_usd                 NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    new_mrr_usd             NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    expansion_mrr_usd       NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    contraction_mrr_usd     NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    churned_mrr_usd         NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    net_mrr_movement_usd    NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    discount_applied_usd    NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    cumulative_revenue_usd  NUMERIC(14, 2) NOT NULL DEFAULT 0.00,
    created_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_monthly_snapshot_user_month UNIQUE (snapshot_month_sk, user_id)
);

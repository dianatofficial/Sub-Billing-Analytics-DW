-- ==============================================================================
-- Schema: Subscription & Billing Analytics Data Warehouse
-- Component: Dimension Tables (Kimball Star Schema)
-- Database Engine: PostgreSQL 14+ / OLAP Architecture
-- ==============================================================================

-- 1. Date Dimension (Standard Conformed Dimension)
CREATE TABLE IF NOT EXISTS dim_date (
    date_sk             INTEGER PRIMARY KEY, -- Format: YYYYMMDD
    calendar_date       DATE NOT NULL UNIQUE,
    year                SMALLINT NOT NULL,
    quarter             SMALLINT NOT NULL,
    quarter_name        VARCHAR(6) NOT NULL, -- e.g., 'Q1-2024'
    month               SMALLINT NOT NULL,
    month_name          VARCHAR(12) NOT NULL, -- e.g., 'January'
    month_year          VARCHAR(8) NOT NULL, -- e.g., '2024-01'
    day_of_month        SMALLINT NOT NULL,
    day_of_week         SMALLINT NOT NULL, -- 1=Monday, 7=Sunday
    day_name            VARCHAR(12) NOT NULL, -- e.g., 'Monday'
    is_weekend          BOOLEAN NOT NULL,
    is_month_start      BOOLEAN NOT NULL,
    is_month_end        BOOLEAN NOT NULL,
    fiscal_quarter      VARCHAR(6) NOT NULL,
    fiscal_year         SMALLINT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_dim_date_calendar_date ON dim_date(calendar_date);
CREATE INDEX IF NOT EXISTS idx_dim_date_month_year ON dim_date(month_year);

-- 2. Subscription Plan Dimension
CREATE TABLE IF NOT EXISTS dim_subscription_plan (
    plan_sk             SERIAL PRIMARY KEY,
    plan_id             VARCHAR(64) NOT NULL UNIQUE, -- Natural Key
    plan_code           VARCHAR(64) NOT NULL,        -- e.g., 'PRO_ANNUAL', 'STARTER_MONTHLY'
    plan_name           VARCHAR(128) NOT NULL,
    billing_interval    VARCHAR(16) NOT NULL,        -- 'monthly', 'annual'
    tier_level          SMALLINT NOT NULL,           -- 1=Free, 2=Starter, 3=Pro, 4=Enterprise
    base_price_usd      NUMERIC(10, 2) NOT NULL,
    seat_limit          INTEGER NOT NULL,
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_dim_plan_code ON dim_subscription_plan(plan_code);
CREATE INDEX IF NOT EXISTS idx_dim_plan_tier ON dim_subscription_plan(tier_level);

-- 3. Users Dimension (SCD Type 2: Slowly Changing Dimension)
-- Tracks historical changes in subscriber tier, account status, and commercial profile.
CREATE TABLE IF NOT EXISTS dim_users (
    user_sk             BIGSERIAL PRIMARY KEY,       -- Surrogate Key
    user_id             VARCHAR(64) NOT NULL,        -- Natural Key (UUID/Account ID)
    email               VARCHAR(255) NOT NULL,
    country             VARCHAR(64) NOT NULL,
    acquisition_channel VARCHAR(64) NOT NULL,        -- 'organic', 'paid_search', 'referral', 'outbound'
    billing_currency    VARCHAR(8) NOT NULL DEFAULT 'USD',
    subscription_tier   VARCHAR(32) NOT NULL,        -- 'free', 'starter', 'pro', 'enterprise'
    account_status      VARCHAR(32) NOT NULL,        -- 'active', 'trial', 'past_due', 'canceled', 'paused'
    start_date          TIMESTAMP NOT NULL,          -- Validity window start
    end_date            TIMESTAMP NULL,              -- Validity window end (NULL indicates current record)
    is_current          BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Fast lookup for current user dimension state
CREATE INDEX IF NOT EXISTS idx_dim_users_natural_current 
ON dim_users(user_id, is_current) 
WHERE is_current = TRUE;

-- Fast point-in-time historical lookup
CREATE INDEX IF NOT EXISTS idx_dim_users_history_lookup 
ON dim_users(user_id, start_date, end_date);

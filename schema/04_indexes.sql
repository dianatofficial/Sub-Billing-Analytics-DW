-- ==============================================================================
-- Schema: Subscription & Billing Analytics Data Warehouse
-- Component: High-Performance Indexing Strategy (BRIN & Composite B-Tree)
-- Database Engine: PostgreSQL 14+ / OLAP Query Optimization
-- ==============================================================================

-- 1. BRIN Index for High-Volume Chronological Event Ingestion & Pruning
-- BRIN (Block Range Index) is exceptionally lightweight for sequential/appended time-series data.
CREATE INDEX IF NOT EXISTS idx_fact_events_brin_timestamp 
ON fact_subscription_events 
USING BRIN (event_timestamp) 
WITH (pages_per_range = 32);

-- 2. Composite B-Tree Indexes on Fact Tables for High-Selectivity Multi-Dimensional Filtering
CREATE INDEX IF NOT EXISTS idx_fact_events_user_type_ts 
ON fact_subscription_events (user_sk, event_type, event_timestamp);

CREATE INDEX IF NOT EXISTS idx_fact_events_date_type 
ON fact_subscription_events (date_sk, event_type);

CREATE INDEX IF NOT EXISTS idx_fact_events_plan_ts 
ON fact_subscription_events (plan_sk, event_timestamp);

-- 3. Monthly Financial Snapshot Indexes
CREATE INDEX IF NOT EXISTS idx_snapshot_month_plan 
ON fact_monthly_financial_snapshot (snapshot_month_sk, plan_sk);

CREATE INDEX IF NOT EXISTS idx_snapshot_user_month 
ON fact_monthly_financial_snapshot (user_sk, snapshot_month_sk);

CREATE INDEX IF NOT EXISTS idx_snapshot_active_month 
ON fact_monthly_financial_snapshot (is_active_subscriber, snapshot_month_sk);

-- 4. Dimension Table Indexes
CREATE INDEX IF NOT EXISTS idx_dim_users_tier_status 
ON dim_users (subscription_tier, account_status) 
WHERE is_current = TRUE;

CREATE INDEX IF NOT EXISTS idx_dim_users_channel_country 
ON dim_users (acquisition_channel, country);

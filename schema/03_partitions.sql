-- ==============================================================================
-- Schema: Subscription & Billing Analytics Data Warehouse
-- Component: Declarative Range Partitions for fact_subscription_events
-- Database Engine: PostgreSQL 14+
-- ==============================================================================

-- 2023 Monthly Partitions
CREATE TABLE IF NOT EXISTS fact_subscription_events_2023_01 PARTITION OF fact_subscription_events
    FOR VALUES FROM ('2023-01-01 00:00:00') TO ('2023-02-01 00:00:00');

CREATE TABLE IF NOT EXISTS fact_subscription_events_2023_02 PARTITION OF fact_subscription_events
    FOR VALUES FROM ('2023-02-01 00:00:00') TO ('2023-03-01 00:00:00');

CREATE TABLE IF NOT EXISTS fact_subscription_events_2023_03 PARTITION OF fact_subscription_events
    FOR VALUES FROM ('2023-03-01 00:00:00') TO ('2023-04-01 00:00:00');

CREATE TABLE IF NOT EXISTS fact_subscription_events_2023_04 PARTITION OF fact_subscription_events
    FOR VALUES FROM ('2023-04-01 00:00:00') TO ('2023-05-01 00:00:00');

CREATE TABLE IF NOT EXISTS fact_subscription_events_2023_05 PARTITION OF fact_subscription_events
    FOR VALUES FROM ('2023-05-01 00:00:00') TO ('2023-06-01 00:00:00');

CREATE TABLE IF NOT EXISTS fact_subscription_events_2023_06 PARTITION OF fact_subscription_events
    FOR VALUES FROM ('2023-06-01 00:00:00') TO ('2023-07-01 00:00:00');

CREATE TABLE IF NOT EXISTS fact_subscription_events_2023_07 PARTITION OF fact_subscription_events
    FOR VALUES FROM ('2023-07-01 00:00:00') TO ('2023-08-01 00:00:00');

CREATE TABLE IF NOT EXISTS fact_subscription_events_2023_08 PARTITION OF fact_subscription_events
    FOR VALUES FROM ('2023-08-01 00:00:00') TO ('2023-09-01 00:00:00');

CREATE TABLE IF NOT EXISTS fact_subscription_events_2023_09 PARTITION OF fact_subscription_events
    FOR VALUES FROM ('2023-09-01 00:00:00') TO ('2023-10-01 00:00:00');

CREATE TABLE IF NOT EXISTS fact_subscription_events_2023_10 PARTITION OF fact_subscription_events
    FOR VALUES FROM ('2023-10-01 00:00:00') TO ('2023-11-01 00:00:00');

CREATE TABLE IF NOT EXISTS fact_subscription_events_2023_11 PARTITION OF fact_subscription_events
    FOR VALUES FROM ('2023-11-01 00:00:00') TO ('2023-12-01 00:00:00');

CREATE TABLE IF NOT EXISTS fact_subscription_events_2023_12 PARTITION OF fact_subscription_events
    FOR VALUES FROM ('2023-12-01 00:00:00') TO ('2024-01-01 00:00:00');

-- 2024 Monthly Partitions
CREATE TABLE IF NOT EXISTS fact_subscription_events_2024_01 PARTITION OF fact_subscription_events
    FOR VALUES FROM ('2024-01-01 00:00:00') TO ('2024-02-01 00:00:00');

CREATE TABLE IF NOT EXISTS fact_subscription_events_2024_02 PARTITION OF fact_subscription_events
    FOR VALUES FROM ('2024-02-01 00:00:00') TO ('2024-03-01 00:00:00');

CREATE TABLE IF NOT EXISTS fact_subscription_events_2024_03 PARTITION OF fact_subscription_events
    FOR VALUES FROM ('2024-03-01 00:00:00') TO ('2024-04-01 00:00:00');

CREATE TABLE IF NOT EXISTS fact_subscription_events_2024_04 PARTITION OF fact_subscription_events
    FOR VALUES FROM ('2024-04-01 00:00:00') TO ('2024-05-01 00:00:00');

CREATE TABLE IF NOT EXISTS fact_subscription_events_2024_05 PARTITION OF fact_subscription_events
    FOR VALUES FROM ('2024-05-01 00:00:00') TO ('2024-06-01 00:00:00');

CREATE TABLE IF NOT EXISTS fact_subscription_events_2024_06 PARTITION OF fact_subscription_events
    FOR VALUES FROM ('2024-06-01 00:00:00') TO ('2024-07-01 00:00:00');

CREATE TABLE IF NOT EXISTS fact_subscription_events_2024_07 PARTITION OF fact_subscription_events
    FOR VALUES FROM ('2024-07-01 00:00:00') TO ('2024-08-01 00:00:00');

CREATE TABLE IF NOT EXISTS fact_subscription_events_2024_08 PARTITION OF fact_subscription_events
    FOR VALUES FROM ('2024-08-01 00:00:00') TO ('2024-09-01 00:00:00');

CREATE TABLE IF NOT EXISTS fact_subscription_events_2024_09 PARTITION OF fact_subscription_events
    FOR VALUES FROM ('2024-09-01 00:00:00') TO ('2024-10-01 00:00:00');

CREATE TABLE IF NOT EXISTS fact_subscription_events_2024_10 PARTITION OF fact_subscription_events
    FOR VALUES FROM ('2024-10-01 00:00:00') TO ('2024-11-01 00:00:00');

CREATE TABLE IF NOT EXISTS fact_subscription_events_2024_11 PARTITION OF fact_subscription_events
    FOR VALUES FROM ('2024-11-01 00:00:00') TO ('2024-12-01 00:00:00');

CREATE TABLE IF NOT EXISTS fact_subscription_events_2024_12 PARTITION OF fact_subscription_events
    FOR VALUES FROM ('2024-12-01 00:00:00') TO ('2025-01-01 00:00:00');

-- 2025 Monthly Partitions
CREATE TABLE IF NOT EXISTS fact_subscription_events_2025_01 PARTITION OF fact_subscription_events
    FOR VALUES FROM ('2025-01-01 00:00:00') TO ('2025-02-01 00:00:00');

CREATE TABLE IF NOT EXISTS fact_subscription_events_2025_02 PARTITION OF fact_subscription_events
    FOR VALUES FROM ('2025-02-01 00:00:00') TO ('2025-03-01 00:00:00');

CREATE TABLE IF NOT EXISTS fact_subscription_events_2025_03 PARTITION OF fact_subscription_events
    FOR VALUES FROM ('2025-03-01 00:00:00') TO ('2025-04-01 00:00:00');

CREATE TABLE IF NOT EXISTS fact_subscription_events_2025_04 PARTITION OF fact_subscription_events
    FOR VALUES FROM ('2025-04-01 00:00:00') TO ('2025-05-01 00:00:00');

CREATE TABLE IF NOT EXISTS fact_subscription_events_2025_05 PARTITION OF fact_subscription_events
    FOR VALUES FROM ('2025-05-01 00:00:00') TO ('2025-06-01 00:00:00');

CREATE TABLE IF NOT EXISTS fact_subscription_events_2025_06 PARTITION OF fact_subscription_events
    FOR VALUES FROM ('2025-06-01 00:00:00') TO ('2025-07-01 00:00:00');

CREATE TABLE IF NOT EXISTS fact_subscription_events_2025_07 PARTITION OF fact_subscription_events
    FOR VALUES FROM ('2025-07-01 00:00:00') TO ('2025-08-01 00:00:00');

CREATE TABLE IF NOT EXISTS fact_subscription_events_2025_08 PARTITION OF fact_subscription_events
    FOR VALUES FROM ('2025-08-01 00:00:00') TO ('2025-09-01 00:00:00');

CREATE TABLE IF NOT EXISTS fact_subscription_events_2025_09 PARTITION OF fact_subscription_events
    FOR VALUES FROM ('2025-09-01 00:00:00') TO ('2025-10-01 00:00:00');

CREATE TABLE IF NOT EXISTS fact_subscription_events_2025_10 PARTITION OF fact_subscription_events
    FOR VALUES FROM ('2025-10-01 00:00:00') TO ('2025-11-01 00:00:00');

CREATE TABLE IF NOT EXISTS fact_subscription_events_2025_11 PARTITION OF fact_subscription_events
    FOR VALUES FROM ('2025-11-01 00:00:00') TO ('2025-12-01 00:00:00');

CREATE TABLE IF NOT EXISTS fact_subscription_events_2025_12 PARTITION OF fact_subscription_events
    FOR VALUES FROM ('2025-12-01 00:00:00') TO ('2026-01-01 00:00:00');

-- 2026 Partitions
CREATE TABLE IF NOT EXISTS fact_subscription_events_2026_01 PARTITION OF fact_subscription_events
    FOR VALUES FROM ('2026-01-01 00:00:00') TO ('2026-02-01 00:00:00');

CREATE TABLE IF NOT EXISTS fact_subscription_events_2026_02 PARTITION OF fact_subscription_events
    FOR VALUES FROM ('2026-02-01 00:00:00') TO ('2026-03-01 00:00:00');

CREATE TABLE IF NOT EXISTS fact_subscription_events_2026_03 PARTITION OF fact_subscription_events
    FOR VALUES FROM ('2026-03-01 00:00:00') TO ('2026-04-01 00:00:00');

CREATE TABLE IF NOT EXISTS fact_subscription_events_2026_04 PARTITION OF fact_subscription_events
    FOR VALUES FROM ('2026-04-01 00:00:00') TO ('2026-05-01 00:00:00');

-- Default Partition for Out-of-Range Guarding
CREATE TABLE IF NOT EXISTS fact_subscription_events_default PARTITION OF fact_subscription_events DEFAULT;

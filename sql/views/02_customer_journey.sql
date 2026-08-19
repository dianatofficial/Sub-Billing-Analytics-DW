-- ==============================================================================
-- View: Customer Lifecycle Journey & Touchpoint Sequence
-- Purpose: Complete chronological history of user subscription state transitions.
-- ==============================================================================

CREATE OR REPLACE VIEW vw_customer_journey AS
SELECT
    f.event_id,
    u.user_id,
    u.email,
    f.event_timestamp,
    d.calendar_date,
    f.event_type,
    p.plan_name,
    p.billing_interval,
    f.net_amount_usd,
    f.mrr_delta_usd,
    SUM(f.mrr_delta_usd) OVER (
        PARTITION BY u.user_id 
        ORDER BY f.event_timestamp 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS running_user_mrr_usd,
    SUM(f.net_amount_usd) OVER (
        PARTITION BY u.user_id 
        ORDER BY f.event_timestamp 
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulative_cash_collected_usd,
    ROW_NUMBER() OVER (
        PARTITION BY u.user_id 
        ORDER BY f.event_timestamp
    ) AS event_sequence_number
FROM fact_subscription_events f
JOIN dim_users u ON f.user_sk = u.user_sk
JOIN dim_subscription_plan p ON f.plan_sk = p.plan_sk
JOIN dim_date d ON f.date_sk = d.date_sk;

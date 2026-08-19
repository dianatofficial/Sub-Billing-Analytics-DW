-- ==============================================================================
-- View: Active Subscriptions Overview
-- Purpose: Denormalized current operational view for business stakeholders.
-- ==============================================================================

CREATE OR REPLACE VIEW vw_active_subscriptions AS
SELECT
    u.user_id,
    u.email,
    u.country,
    u.acquisition_channel,
    u.subscription_tier,
    u.account_status,
    p.plan_code,
    p.plan_name,
    p.billing_interval,
    p.base_price_usd AS current_plan_price,
    u.start_date AS tier_effective_date,
    CURRENT_DATE - u.start_date::DATE AS days_on_current_tier,
    COALESCE(rev.total_paid_usd, 0.00) AS lifetime_paid_amount_usd,
    COALESCE(rev.total_invoices_count, 0) AS total_successful_invoices
FROM dim_users u
JOIN (
    SELECT DISTINCT ON (user_sk) user_sk, plan_sk
    FROM fact_subscription_events
    ORDER BY user_sk, event_timestamp DESC
) latest_ev ON u.user_sk = latest_ev.user_sk
JOIN dim_subscription_plan p ON latest_ev.plan_sk = p.plan_sk
LEFT JOIN (
    SELECT
        user_sk,
        SUM(net_amount_usd) AS total_paid_usd,
        COUNT(CASE WHEN event_type = 'invoice_paid' THEN 1 END) AS total_invoices_count
    FROM fact_subscription_events
    GROUP BY user_sk
) rev ON u.user_sk = rev.user_sk
WHERE u.is_current = TRUE
  AND u.account_status = 'active';

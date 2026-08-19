-- ==============================================================================
-- Query: Customer Lifetime Value (LTV) & Unit Economics by Subscription Tier
-- Purpose: Evaluates realized historical customer value, average tenure,
--          and predictive LTV based on empirical churn dynamics.
-- ==============================================================================

WITH user_lifecycle_stats AS (
    SELECT
        u.user_id,
        u.subscription_tier,
        u.acquisition_channel,
        u.country,
        MIN(f.event_timestamp) AS first_event_timestamp,
        MAX(f.event_timestamp) AS latest_event_timestamp,
        COUNT(DISTINCT CASE WHEN f.event_type = 'invoice_paid' THEN f.event_id END) AS total_invoices_paid,
        SUM(f.net_amount_usd) AS realized_lifetime_revenue_usd,
        MAX(CASE WHEN u.is_current = TRUE AND u.account_status = 'canceled' THEN 1 ELSE 0 END) AS is_churned
    FROM dim_users u
    JOIN fact_subscription_events f ON u.user_sk = f.user_sk
    GROUP BY u.user_id, u.subscription_tier, u.acquisition_channel, u.country
),
tier_aggregations AS (
    SELECT
        subscription_tier,
        COUNT(DISTINCT user_id) AS total_customers,
        COUNT(DISTINCT CASE WHEN is_churned = 1 THEN user_id END) AS churned_customers,
        SUM(realized_lifetime_revenue_usd) AS aggregate_tier_revenue_usd,
        ROUND(AVG(realized_lifetime_revenue_usd), 2) AS realized_arpu_per_customer_usd,
        ROUND(AVG(total_invoices_paid), 1) AS avg_invoices_paid_per_customer,
        ROUND(
            AVG(EXTRACT(DAY FROM (latest_event_timestamp - first_event_timestamp)) / 30.4375),
            1
        ) AS avg_tenure_months
    FROM user_lifecycle_stats
    GROUP BY subscription_tier
)
SELECT
    subscription_tier,
    total_customers,
    churned_customers,
    aggregate_tier_revenue_usd,
    realized_arpu_per_customer_usd,
    avg_tenure_months,
    -- Empirical Churn Rate
    ROUND(
        (churned_customers::NUMERIC / NULLIF(total_customers, 0)) * 100.0,
        2
    ) AS tier_churn_rate_pct,
    -- Modeled Lifetime Value (LTV = ARPU / Churn Rate)
    ROUND(
        realized_arpu_per_customer_usd / 
        NULLIF((churned_customers::NUMERIC / NULLIF(total_customers, 0)), 0),
        2
    ) AS modeled_ltv_usd
FROM tier_aggregations
ORDER BY aggregate_tier_revenue_usd DESC;

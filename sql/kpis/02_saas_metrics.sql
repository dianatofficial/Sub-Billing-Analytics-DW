-- ==============================================================================
-- Query: SaaS Core Efficiency & Retention Metrics
-- Purpose: Calculates SaaS Quick Ratio, Net Revenue Retention (NRR), Gross Revenue Churn,
--          Logo Churn, and Average Revenue Per Account (ARPA).
-- ==============================================================================

WITH monthly_base AS (
    SELECT
        snapshot_month_sk,
        snapshot_date,
        SUM(mrr_usd) AS ending_mrr,
        SUM(new_mrr_usd) AS new_mrr,
        SUM(expansion_mrr_usd) AS expansion_mrr,
        SUM(contraction_mrr_usd) AS contraction_mrr,
        SUM(churned_mrr_usd) AS churned_mrr,
        COUNT(DISTINCT CASE WHEN is_active_subscriber = TRUE THEN user_id END) AS active_subscribers,
        COUNT(DISTINCT CASE WHEN churned_mrr_usd > 0 THEN user_id END) AS churned_subscribers
    FROM fact_monthly_financial_snapshot
    GROUP BY snapshot_month_sk, snapshot_date
),
metrics_with_lag AS (
    SELECT
        snapshot_month_sk,
        snapshot_date,
        COALESCE(LAG(ending_mrr, 1) OVER (ORDER BY snapshot_month_sk), 0.00) AS starting_mrr,
        COALESCE(LAG(active_subscribers, 1) OVER (ORDER BY snapshot_month_sk), 0) AS starting_subscribers,
        new_mrr,
        expansion_mrr,
        contraction_mrr,
        churned_mrr,
        ending_mrr,
        active_subscribers,
        churned_subscribers
    FROM monthly_base
)
SELECT
    snapshot_month_sk AS month_id,
    snapshot_date,
    ending_mrr,
    active_subscribers,
    -- Average Revenue Per Account (ARPA / ARPU)
    ROUND(
        ending_mrr / NULLIF(active_subscribers, 0),
        2
    ) AS arpa_usd,
    -- SaaS Quick Ratio: (New + Expansion) / (Churn + Contraction)
    ROUND(
        (new_mrr + expansion_mrr) /
        NULLIF((churned_mrr + contraction_mrr), 0),
        2
    ) AS saas_quick_ratio,
    -- Gross Revenue Churn Rate (%)
    ROUND(
        (churned_mrr / NULLIF(starting_mrr, 0)) * 100.0,
        2
    ) AS gross_revenue_churn_pct,
    -- Net Revenue Retention (NRR) (%)
    ROUND(
        ((starting_mrr + expansion_mrr - contraction_mrr - churned_mrr) /
         NULLIF(starting_mrr, 0)) * 100.0,
        2
    ) AS net_revenue_retention_nrr_pct,
    -- Logo Churn Rate (%)
    ROUND(
        (churned_subscribers::NUMERIC / NULLIF(starting_subscribers, 0)) * 100.0,
        2
    ) AS logo_churn_pct
FROM metrics_with_lag
WHERE starting_mrr > 0
ORDER BY snapshot_month_sk ASC;

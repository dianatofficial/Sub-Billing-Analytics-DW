-- ==============================================================================
-- Query: SaaS MRR Waterfall & Financial Bridge
-- Purpose: Decomposes monthly revenue movements into New, Expansion, Contraction,
--          and Churn components with month-over-month reconciliation.
-- Source: fact_monthly_financial_snapshot
-- ==============================================================================

WITH monthly_aggregates AS (
    SELECT
        snapshot_month_sk,
        snapshot_date,
        SUM(mrr_usd) AS ending_mrr,
        SUM(arr_usd) AS ending_arr,
        SUM(new_mrr_usd) AS new_mrr,
        SUM(expansion_mrr_usd) AS expansion_mrr,
        SUM(contraction_mrr_usd) AS contraction_mrr,
        SUM(churned_mrr_usd) AS churned_mrr,
        SUM(net_mrr_movement_usd) AS net_mrr_movement,
        COUNT(DISTINCT CASE WHEN is_active_subscriber = TRUE THEN user_id END) AS active_subscribers
    FROM fact_monthly_financial_snapshot
    GROUP BY snapshot_month_sk, snapshot_date
),
waterfall_calculation AS (
    SELECT
        snapshot_month_sk,
        snapshot_date,
        COALESCE(
            LAG(ending_mrr, 1) OVER (ORDER BY snapshot_month_sk),
            0.00
        ) AS starting_mrr,
        new_mrr,
        expansion_mrr,
        contraction_mrr,
        churned_mrr,
        net_mrr_movement,
        ending_mrr,
        ending_arr,
        active_subscribers,
        ROUND(
            (ending_mrr - LAG(ending_mrr, 1) OVER (ORDER BY snapshot_month_sk)) /
            NULLIF(LAG(ending_mrr, 1) OVER (ORDER BY snapshot_month_sk), 0) * 100.0,
            2
        ) AS mrr_growth_rate_pct
    FROM monthly_aggregates
)
SELECT
    snapshot_month_sk AS month_id,
    snapshot_date,
    starting_mrr,
    new_mrr,
    expansion_mrr,
    contraction_mrr,
    churned_mrr,
    net_mrr_movement,
    ending_mrr,
    ending_arr,
    active_subscribers,
    mrr_growth_rate_pct
FROM waterfall_calculation
ORDER BY snapshot_month_sk ASC;

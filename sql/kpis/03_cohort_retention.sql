-- ==============================================================================
-- Query: SaaS Cohort Retention & Net Dollar Retention (NDR)
-- Purpose: Analyzes subscriber retention decay and revenue expansion curves
--          grouped by original acquisition cohort month over an N-month horizon.
-- ==============================================================================

WITH user_cohorts AS (
    -- Determine the first active month (cohort) for each subscriber
    SELECT
        user_id,
        MIN(snapshot_month_sk) AS cohort_month_sk
    FROM fact_monthly_financial_snapshot
    WHERE is_active_subscriber = TRUE
    GROUP BY user_id
),
cohort_sizes AS (
    -- Count starting subscribers and initial MRR in Month 0
    SELECT
        c.cohort_month_sk,
        COUNT(DISTINCT c.user_id) AS cohort_users_month_0,
        SUM(f.mrr_usd) AS cohort_mrr_month_0
    FROM user_cohorts c
    JOIN fact_monthly_financial_snapshot f
        ON c.user_id = f.user_id 
       AND c.cohort_month_sk = f.snapshot_month_sk
    GROUP BY c.cohort_month_sk
),
monthly_cohort_activity AS (
    -- Track subsequent monthly performance for each cohort
    SELECT
        c.cohort_month_sk,
        f.snapshot_month_sk,
        -- Calculate month offset (0 = inception month)
        (
            (EXTRACT(YEAR FROM f.snapshot_date) - (c.cohort_month_sk / 100)) * 12 +
            (EXTRACT(MONTH FROM f.snapshot_date) - (c.cohort_month_sk % 100))
        )::INTEGER AS month_offset,
        COUNT(DISTINCT CASE WHEN f.is_active_subscriber = TRUE THEN f.user_id END) AS active_users,
        SUM(CASE WHEN f.is_active_subscriber = TRUE THEN f.mrr_usd ELSE 0.00 END) AS active_mrr
    FROM user_cohorts c
    JOIN fact_monthly_financial_snapshot f
        ON c.user_id = f.user_id
    GROUP BY c.cohort_month_sk, f.snapshot_month_sk, f.snapshot_date
)
SELECT
    m.cohort_month_sk,
    m.month_offset,
    m.snapshot_month_sk AS active_calendar_month,
    s.cohort_users_month_0,
    m.active_users,
    ROUND(
        (m.active_users::NUMERIC / NULLIF(s.cohort_users_month_0, 0)) * 100.0,
        2
    ) AS user_retention_rate_pct,
    s.cohort_mrr_month_0,
    m.active_mrr,
    ROUND(
        (m.active_mrr / NULLIF(s.cohort_mrr_month_0, 0)) * 100.0,
        2
    ) AS net_dollar_retention_ndr_pct
FROM monthly_cohort_activity m
JOIN cohort_sizes s ON m.cohort_month_sk = s.cohort_month_sk
WHERE m.month_offset >= 0
ORDER BY m.cohort_month_sk ASC, m.month_offset ASC;

-- ==============================================================================
-- Schema: Subscription & Billing Analytics Data Warehouse
-- Component: Stored Procedures for SCD Type 2 Dimensions & Snapshot Maintenance
-- Database Engine: PostgreSQL 14+ / PL/pgSQL
-- ==============================================================================

-- 1. Procedure to Process SCD Type 2 User Dimension Updates
CREATE OR REPLACE FUNCTION upsert_dim_user_scd2(
    p_user_id               VARCHAR(64),
    p_email                 VARCHAR(255),
    p_country               VARCHAR(64),
    p_acquisition_channel   VARCHAR(64),
    p_billing_currency      VARCHAR(8),
    p_subscription_tier     VARCHAR(32),
    p_account_status        VARCHAR(32),
    p_effective_timestamp   TIMESTAMP
)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_current_user_sk       BIGINT;
    v_new_user_sk           BIGINT;
    v_tier_changed          BOOLEAN;
    v_status_changed        BOOLEAN;
BEGIN
    -- Check for existing active record
    SELECT user_sk,
           (subscription_tier <> p_subscription_tier),
           (account_status <> p_account_status)
    INTO v_current_user_sk, v_tier_changed, v_status_changed
    FROM dim_users
    WHERE user_id = p_user_id AND is_current = TRUE;

    IF v_current_user_sk IS NULL THEN
        -- Brand new user insertion
        INSERT INTO dim_users (
            user_id, email, country, acquisition_channel,
            billing_currency, subscription_tier, account_status,
            start_date, end_date, is_current
        ) VALUES (
            p_user_id, p_email, p_country, p_acquisition_channel,
            p_billing_currency, p_subscription_tier, p_account_status,
            p_effective_timestamp, NULL, TRUE
        ) RETURNING user_sk INTO v_new_user_sk;

        RETURN v_new_user_sk;

    ELSIF v_tier_changed OR v_status_changed THEN
        -- Historical change detected: Expire existing record
        UPDATE dim_users
        SET end_date = p_effective_timestamp,
            is_current = FALSE
        WHERE user_sk = v_current_user_sk;

        -- Insert new active version
        INSERT INTO dim_users (
            user_id, email, country, acquisition_channel,
            billing_currency, subscription_tier, account_status,
            start_date, end_date, is_current
        ) VALUES (
            p_user_id, p_email, p_country, p_acquisition_channel,
            p_billing_currency, p_subscription_tier, p_account_status,
            p_effective_timestamp, NULL, TRUE
        ) RETURNING user_sk INTO v_new_user_sk;

        RETURN v_new_user_sk;
    ELSE
        -- No dimensionally tracked attribute change; keep existing surrogate key
        RETURN v_current_user_sk;
    END IF;
END;
$$;

-- 2. Procedure to Populate Calendar Dimension across a Date Range
CREATE OR REPLACE PROCEDURE populate_dim_date(p_start_date DATE, p_end_date DATE)
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO dim_date (
        date_sk, calendar_date, year, quarter, quarter_name,
        month, month_name, month_year, day_of_month, day_of_week,
        day_name, is_weekend, is_month_start, is_month_end,
        fiscal_quarter, fiscal_year
    )
    SELECT
        TO_CHAR(d, 'YYYYMMDD')::INTEGER AS date_sk,
        d::DATE AS calendar_date,
        EXTRACT(YEAR FROM d)::SMALLINT AS year,
        EXTRACT(QUARTER FROM d)::SMALLINT AS quarter,
        'Q' || EXTRACT(QUARTER FROM d)::TEXT || '-' || EXTRACT(YEAR FROM d)::TEXT AS quarter_name,
        EXTRACT(MONTH FROM d)::SMALLINT AS month,
        TO_CHAR(d, 'Month') AS month_name,
        TO_CHAR(d, 'YYYY-MM') AS month_year,
        EXTRACT(DAY FROM d)::SMALLINT AS day_of_month,
        EXTRACT(ISODOW FROM d)::SMALLINT AS day_of_week,
        TO_CHAR(d, 'Day') AS day_name,
        CASE WHEN EXTRACT(ISODOW FROM d) IN (6, 7) THEN TRUE ELSE FALSE END AS is_weekend,
        CASE WHEN d = DATE_TRUNC('month', d)::DATE THEN TRUE ELSE FALSE END AS is_month_start,
        CASE WHEN d = (DATE_TRUNC('month', d) + INTERVAL '1 month - 1 day')::DATE THEN TRUE ELSE FALSE END AS is_month_end,
        'FQ' || EXTRACT(QUARTER FROM d)::TEXT AS fiscal_quarter,
        EXTRACT(YEAR FROM d)::SMALLINT AS fiscal_year
    FROM GENERATE_SERIES(p_start_date::TIMESTAMP, p_end_date::TIMESTAMP, '1 day'::INTERVAL) AS d
    ON CONFLICT (date_sk) DO NOTHING;
END;
$$;

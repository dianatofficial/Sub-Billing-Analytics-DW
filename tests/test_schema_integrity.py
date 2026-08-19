"""
Test: Schema and Referential Integrity
Verifies primary key uniqueness, non-null constraints, and valid foreign key references.
"""

import pytest
import pandas as pd
from pipeline.generator import generate_saas_dataset
from pipeline.scd2_processor import (
    build_date_dimension,
    build_plan_dimension,
    build_users_scd2_dimension,
    SCD2Resolver
)
from pipeline.fact_builder import build_events_fact, build_monthly_financial_snapshot


@pytest.fixture(scope="module")
def dw_data():
    users_hist, raw_ev = generate_saas_dataset(num_users=300)
    df_date = build_date_dimension("2023-01-01", "2025-12-31")
    df_plan = build_plan_dimension()
    df_users = build_users_scd2_dimension(users_hist)
    resolver = SCD2Resolver(df_users, df_plan)
    df_events = build_events_fact(raw_ev, resolver)
    df_snapshot = build_monthly_financial_snapshot(df_events, df_users, resolver, 2023, 2025)
    return {
        "date": df_date,
        "plan": df_plan,
        "users": df_users,
        "events": df_events,
        "snapshot": df_snapshot
    }


def test_dimension_primary_keys_unique(dw_data):
    """Verify all dimension surrogate keys are strictly unique."""
    assert dw_data["date"]["date_sk"].is_unique, "date_sk must be unique in dim_date"
    assert dw_data["plan"]["plan_sk"].is_unique, "plan_sk must be unique in dim_subscription_plan"
    assert dw_data["users"]["user_sk"].is_unique, "user_sk must be unique in dim_users"


def test_surrogate_keys_non_null(dw_data):
    """Verify surrogate keys contain no null values."""
    assert dw_data["date"]["date_sk"].notnull().all()
    assert dw_data["plan"]["plan_sk"].notnull().all()
    assert dw_data["users"]["user_sk"].notnull().all()
    assert dw_data["events"]["event_sk"].notnull().all()
    assert dw_data["snapshot"]["snapshot_sk"].notnull().all()


def test_fact_events_referential_integrity(dw_data):
    """Verify all foreign keys in fact_subscription_events point to valid dimension records."""
    valid_user_sks = set(dw_data["users"]["user_sk"])
    valid_plan_sks = set(dw_data["plan"]["plan_sk"])
    valid_date_sks = set(dw_data["date"]["date_sk"])

    assert dw_data["events"]["user_sk"].isin(valid_user_sks).all(), "Invalid user_sk in fact_subscription_events"
    assert dw_data["events"]["plan_sk"].isin(valid_plan_sks).all(), "Invalid plan_sk in fact_subscription_events"
    assert dw_data["events"]["date_sk"].isin(valid_date_sks).all(), "Invalid date_sk in fact_subscription_events"


def test_fact_snapshot_referential_integrity(dw_data):
    """Verify all foreign keys in fact_monthly_financial_snapshot point to valid dimension records."""
    valid_user_sks = set(dw_data["users"]["user_sk"])
    valid_plan_sks = set(dw_data["plan"]["plan_sk"])

    assert dw_data["snapshot"]["user_sk"].isin(valid_user_sks).all(), "Invalid user_sk in fact_monthly_financial_snapshot"
    assert dw_data["snapshot"]["plan_sk"].isin(valid_plan_sks).all(), "Invalid plan_sk in fact_monthly_financial_snapshot"

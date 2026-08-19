"""
Test: Financial Reconciliation & MRR Equation Balance
Verifies that monthly financial snapshot aggregations perfectly reconcile against
individual event movements and mathematical accounting identities.
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
def financial_tables():
    users_hist, raw_ev = generate_saas_dataset(num_users=300)
    df_date = build_date_dimension("2023-01-01", "2025-12-31")
    df_plan = build_plan_dimension()
    df_users = build_users_scd2_dimension(users_hist)
    resolver = SCD2Resolver(df_users, df_plan)
    df_events = build_events_fact(raw_ev, resolver)
    df_snapshot = build_monthly_financial_snapshot(df_events, df_users, resolver, 2023, 2025)
    return {
        "events": df_events,
        "snapshot": df_snapshot
    }


def test_arr_equals_twelve_times_mrr(financial_tables):
    """Ensure ARR = MRR * 12 across all snapshot records."""
    df_snap = financial_tables["snapshot"]
    diff = (df_snap["arr_usd"] - (df_snap["mrr_usd"] * 12.0)).abs()
    assert (diff < 0.05).all(), "ARR must equal exactly 12 * MRR within floating point tolerance"


def test_mrr_waterfall_reconciliation(financial_tables):
    """Ensure Ending MRR = Starting MRR + New + Expansion - Contraction - Churn."""
    df_snap = financial_tables["snapshot"]
    monthly_agg = df_snap.groupby("snapshot_month_sk").agg({
        "mrr_usd": "sum",
        "new_mrr_usd": "sum",
        "expansion_mrr_usd": "sum",
        "contraction_mrr_usd": "sum",
        "churned_mrr_usd": "sum"
    }).reset_index()

    starting_mrr = 0.00
    for row in monthly_agg.itertuples():
        expected_ending = starting_mrr + row.new_mrr_usd + row.expansion_mrr_usd - row.contraction_mrr_usd - row.churned_mrr_usd
        actual_ending = row.mrr_usd
        assert abs(expected_ending - actual_ending) < 0.10, (
            f"MRR waterfall mismatch at month {row.snapshot_month_sk}: "
            f"Expected {expected_ending:.2f}, got {actual_ending:.2f}"
        )
        starting_mrr = actual_ending


def test_cumulative_revenue_monotonicity(financial_tables):
    """Ensure cumulative revenue per customer never decreases."""
    df_snap = financial_tables["snapshot"]
    for user_id, group in df_snap.groupby("user_id"):
        sorted_group = group.sort_values("snapshot_month_sk")
        rev_values = sorted_group["cumulative_revenue_usd"].tolist()
        for idx in range(len(rev_values) - 1):
            assert rev_values[idx] <= rev_values[idx + 1], (
                f"Cumulative revenue decreased for user {user_id} between snapshots: "
                f"{rev_values[idx]} -> {rev_values[idx+1]}"
            )

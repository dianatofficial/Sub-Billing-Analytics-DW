"""
Test: SCD Type 2 Dimension Correctness
Validates non-overlapping temporal ranges, single active record per natural key,
and proper closure of historical records.
"""

import pytest
import pandas as pd
from pipeline.generator import generate_saas_dataset
from pipeline.scd2_processor import build_users_scd2_dimension


@pytest.fixture(scope="module")
def df_users_scd2():
    users_hist, _ = generate_saas_dataset(num_users=300)
    return build_users_scd2_dimension(users_hist)


def test_single_current_record_per_user(df_users_scd2):
    """Ensure exactly one record has is_current = True for each natural user_id."""
    current_records = df_users_scd2[df_users_scd2["is_current"] == True]
    counts_per_user = current_records.groupby("user_id").size()
    assert (counts_per_user == 1).all(), "Every user must have exactly one active (is_current=True) record"


def test_historical_records_have_end_date(df_users_scd2):
    """Ensure all expired historical records (is_current = False) have a non-null end_date."""
    expired_records = df_users_scd2[df_users_scd2["is_current"] == False]
    assert expired_records["end_date"].notnull().all(), "Expired records must have a valid end_date"


def test_temporal_order_and_non_overlapping_intervals(df_users_scd2):
    """Ensure start_date <= end_date and versions for each user do not overlap."""
    for user_id, group in df_users_scd2.groupby("user_id"):
        sorted_versions = group.sort_values("start_date")
        
        for idx in range(len(sorted_versions)):
            row = sorted_versions.iloc[idx]
            if pd.notna(row["end_date"]):
                assert row["start_date"] <= row["end_date"], f"start_date must precede end_date for user {user_id}"
            
            # Check subsequent version continuity
            if idx < len(sorted_versions) - 1:
                next_row = sorted_versions.iloc[idx + 1]
                assert row["end_date"] == next_row["start_date"], (
                    f"Gap or overlap detected in SCD2 history for user {user_id}: "
                    f"current end {row['end_date']} != next start {next_row['start_date']}"
                )

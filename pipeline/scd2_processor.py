"""
SCD Type 2 Dimension Processor & Dimension Builders.
Handles creation and point-in-time surrogate key resolution for Kimball dimensions.
"""

from datetime import datetime, timedelta
import pandas as pd
from pipeline.config import SUBSCRIPTION_PLANS


def build_date_dimension(start_date_str: str = "2022-01-01", end_date_str: str = "2026-12-31") -> pd.DataFrame:
    """
    Constructs a comprehensive calendar dimension table.
    """
    start_dt = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date_str, "%Y-%m-%d")
    
    records = []
    curr = start_dt
    while curr <= end_dt:
        date_sk = int(curr.strftime("%Y%m%d"))
        year = curr.year
        quarter = (curr.month - 1) // 3 + 1
        quarter_name = f"Q{quarter}-{year}"
        month = curr.month
        month_name = curr.strftime("%B")
        month_year = curr.strftime("%Y-%m")
        day_of_month = curr.day
        day_of_week = curr.isoweekday()
        day_name = curr.strftime("%A")
        is_weekend = day_of_week in (6, 7)
        
        # Month boundary checks
        next_day = curr + timedelta(days=1)
        is_month_start = (curr.day == 1)
        is_month_end = (next_day.day == 1)
        
        records.append({
            "date_sk": date_sk,
            "calendar_date": curr.date(),
            "year": year,
            "quarter": quarter,
            "quarter_name": quarter_name,
            "month": month,
            "month_name": month_name,
            "month_year": month_year,
            "day_of_month": day_of_month,
            "day_of_week": day_of_week,
            "day_name": day_name,
            "is_weekend": is_weekend,
            "is_month_start": is_month_start,
            "is_month_end": is_month_end,
            "fiscal_quarter": f"FQ{quarter}",
            "fiscal_year": year
        })
        curr += timedelta(days=1)
        
    return pd.DataFrame(records)


def build_plan_dimension() -> pd.DataFrame:
    """
    Builds the subscription plan dimension table with surrogate keys.
    """
    records = []
    for idx, plan in enumerate(SUBSCRIPTION_PLANS, start=1):
        records.append({
            "plan_sk": idx,
            "plan_id": plan["plan_id"],
            "plan_code": plan["plan_code"],
            "plan_name": plan["plan_name"],
            "billing_interval": plan["billing_interval"],
            "tier_level": plan["tier_level"],
            "base_price_usd": plan["base_price_usd"],
            "seat_limit": plan["seat_limit"],
            "is_active": plan["is_active"]
        })
    return pd.DataFrame(records)


def build_users_scd2_dimension(users_histories: list) -> pd.DataFrame:
    """
    Builds the SCD Type 2 User dimension with assigned surrogate keys.
    """
    records = []
    current_sk = 1
    
    for user_history in users_histories:
        for version in user_history:
            records.append({
                "user_sk": current_sk,
                "user_id": version["user_id"],
                "email": version["email"],
                "country": version["country"],
                "acquisition_channel": version["acquisition_channel"],
                "billing_currency": version["billing_currency"],
                "subscription_tier": version["subscription_tier"],
                "account_status": version["account_status"],
                "start_date": version["start_date"],
                "end_date": version["end_date"],
                "is_current": version["is_current"]
            })
            current_sk += 1
            
    return pd.DataFrame(records)


class SCD2Resolver:
    """
    Fast in-memory index for resolving point-in-time SCD2 surrogate keys.
    """
    def __init__(self, df_users_scd2: pd.DataFrame, df_plans: pd.DataFrame):
        self.df_users = df_users_scd2
        self.df_plans = df_plans
        
        # Build plan_id -> plan_sk map
        self.plan_map = dict(zip(df_plans["plan_id"], df_plans["plan_sk"]))
        
        # Index user versions by user_id
        self.user_history_map = {}
        for row in df_users_scd2.itertuples():
            uid = row.user_id
            if uid not in self.user_history_map:
                self.user_history_map[uid] = []
            self.user_history_map[uid].append({
                "user_sk": row.user_sk,
                "start_date": row.start_date,
                "end_date": row.end_date,
                "is_current": row.is_current,
                "tier": row.subscription_tier,
                "status": row.account_status
            })

    def resolve_plan_sk(self, plan_id: str) -> int:
        return self.plan_map[plan_id]

    def resolve_user_sk(self, user_id: str, as_of_time: datetime) -> int:
        """
        Finds the exact user_sk valid at as_of_time.
        """
        versions = self.user_history_map.get(user_id, [])
        for v in versions:
            start_ok = v["start_date"] <= as_of_time
            end_ok = (v["end_date"] is None) or (as_of_time < v["end_date"])
            if start_ok and end_ok:
                return v["user_sk"]
        
        # Fallback to current version or most recent
        if versions:
            return versions[-1]["user_sk"]
        raise ValueError(f"No dimension record found for user_id {user_id}")

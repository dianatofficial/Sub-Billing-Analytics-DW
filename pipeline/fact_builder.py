"""
Fact Builder Module.
Constructs transactional event facts (fact_subscription_events) with point-in-time
surrogate key resolution and aggregates periodic monthly snapshots (fact_monthly_financial_snapshot).
"""

from datetime import datetime, date
import calendar
import pandas as pd
from pipeline.scd2_processor import SCD2Resolver


def build_events_fact(raw_events: list, resolver: SCD2Resolver) -> pd.DataFrame:
    """
    Transforms raw billing and lifecycle events into the fact_subscription_events schema.
    """
    records = []
    # Sort chronologically
    sorted_events = sorted(raw_events, key=lambda x: x["event_timestamp"])
    
    for idx, ev in enumerate(sorted_events, start=1):
        ts = ev["event_timestamp"]
        date_sk = int(ts.strftime("%Y%m%d"))
        user_sk = resolver.resolve_user_sk(ev["user_id"], ts)
        plan_sk = resolver.resolve_plan_sk(ev["plan_id"])
        
        records.append({
            "event_sk": idx,
            "event_id": ev["event_id"],
            "user_sk": user_sk,
            "plan_sk": plan_sk,
            "date_sk": date_sk,
            "event_type": ev["event_type"],
            "quantity": ev["quantity"],
            "gross_amount_usd": float(ev["gross_amount_usd"]),
            "discount_amount_usd": float(ev["discount_amount_usd"]),
            "tax_amount_usd": float(ev["tax_amount_usd"]),
            "net_amount_usd": float(ev["net_amount_usd"]),
            "mrr_delta_usd": float(ev["mrr_delta_usd"]),
            "event_timestamp": ts
        })
        
    return pd.DataFrame(records)


def build_monthly_financial_snapshot(
    df_events: pd.DataFrame,
    df_users_scd2: pd.DataFrame,
    resolver: SCD2Resolver,
    start_year: int = 2023,
    end_year: int = 2025
) -> pd.DataFrame:
    """
    Constructs the periodic monthly financial snapshot fact table.
    Evaluates customer status at each month-end boundary.
    """
    # Track state per user over time
    user_state = {}
    snapshot_records = []
    snapshot_sk = 1
    
    months = []
    for y in range(start_year, end_year + 1):
        for m in range(1, 13):
            last_day = calendar.monthrange(y, m)[1]
            month_end_dt = datetime(y, m, last_day, 23, 59, 59)
            month_sk = y * 100 + m
            months.append((month_sk, month_end_dt, date(y, m, last_day)))

    # Process month by month
    for month_sk, month_end_dt, month_end_date in months:
        # Get all events up to this month-end
        prev_month_end = datetime(
            month_end_dt.year if month_end_dt.month > 1 else month_end_dt.year - 1,
            month_end_dt.month - 1 if month_end_dt.month > 1 else 12,
            calendar.monthrange(
                month_end_dt.year if month_end_dt.month > 1 else month_end_dt.year - 1,
                month_end_dt.month - 1 if month_end_dt.month > 1 else 12
            )[1],
            23, 59, 59
        )
        
        events_this_month = df_events[
            (df_events["event_timestamp"] > prev_month_end) &
            (df_events["event_timestamp"] <= month_end_dt)
        ]
        
        # Determine active users and events
        month_events_by_user = {}
        for ev in events_this_month.itertuples():
            uid_match = df_users_scd2[df_users_scd2["user_sk"] == ev.user_sk]
            if not uid_match.empty:
                uid = uid_match.iloc[0]["user_id"]
                if uid not in month_events_by_user:
                    month_events_by_user[uid] = []
                month_events_by_user[uid].append(ev)

        # Update running states
        all_known_users = set(user_state.keys()).union(set(month_events_by_user.keys()))
        
        for uid in all_known_users:
            state = user_state.get(uid, {
                "mrr": 0.00,
                "plan_sk": 1,
                "is_active": False,
                "cumulative_revenue": 0.00,
                "was_active": False
            })
            
            prev_mrr = state["mrr"]
            prior_active = state["is_active"]
            
            # Process events this month for this user
            new_mrr = 0.00
            expansion_mrr = 0.00
            contraction_mrr = 0.00
            churned_mrr = 0.00
            month_revenue = 0.00
            month_discount = 0.00
            
            user_evs = month_events_by_user.get(uid, [])
            for ev in user_evs:
                month_revenue += ev.net_amount_usd
                month_discount += ev.discount_amount_usd
                state["cumulative_revenue"] += ev.net_amount_usd
                state["plan_sk"] = ev.plan_sk
                
                if ev.event_type in ("invoice_paid", "upgrade"):
                    if not prior_active and prev_mrr == 0:
                        new_mrr += ev.mrr_delta_usd
                    elif ev.mrr_delta_usd > 0:
                        expansion_mrr += ev.mrr_delta_usd
                    elif ev.mrr_delta_usd < 0:
                        contraction_mrr += abs(ev.mrr_delta_usd)
                    state["mrr"] += ev.mrr_delta_usd
                    state["is_active"] = True
                elif ev.event_type == "cancellation":
                    churned_mrr += state["mrr"]
                    state["mrr"] = 0.00
                    state["is_active"] = False

            curr_mrr = max(0.00, round(state["mrr"], 2))
            state["mrr"] = curr_mrr
            net_movement = round(curr_mrr - prev_mrr, 2)
            
            # Record snapshot if user is active, churned this month, or has activity
            should_record = state["is_active"] or (churned_mrr > 0) or (month_revenue > 0)
            
            if should_record:
                user_sk = resolver.resolve_user_sk(uid, month_end_dt)
                
                snapshot_records.append({
                    "snapshot_sk": snapshot_sk,
                    "snapshot_month_sk": month_sk,
                    "snapshot_date": month_end_date,
                    "user_sk": user_sk,
                    "user_id": uid,
                    "plan_sk": state["plan_sk"],
                    "is_active_subscriber": state["is_active"],
                    "mrr_usd": curr_mrr,
                    "arr_usd": round(curr_mrr * 12.0, 2),
                    "new_mrr_usd": round(new_mrr, 2),
                    "expansion_mrr_usd": round(expansion_mrr, 2),
                    "contraction_mrr_usd": round(contraction_mrr, 2),
                    "churned_mrr_usd": round(churned_mrr, 2),
                    "net_mrr_movement_usd": net_movement,
                    "discount_applied_usd": round(month_discount, 2),
                    "cumulative_revenue_usd": round(state["cumulative_revenue"], 2)
                })
                snapshot_sk += 1
                
            user_state[uid] = state

    return pd.DataFrame(snapshot_records)

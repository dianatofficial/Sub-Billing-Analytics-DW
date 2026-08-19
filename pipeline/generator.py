"""
Synthetic SaaS Transactional & Lifecycle Event Generator.
Generates realistic multi-year subscriber data with upgrades, downgrades,
churn dynamics, and billing transactions.
"""

from datetime import datetime, timedelta
import random
import uuid
from faker import Faker
from pipeline.config import (
    SUBSCRIPTION_PLANS,
    SIMULATION_START_DATE,
    SIMULATION_END_DATE,
    SIMULATION_USER_COUNT
)

fake = Faker()
Faker.seed(42)
random.seed(42)

ACQUISITION_CHANNELS = ["organic", "paid_search", "referral", "outbound", "social"]
COUNTRIES = ["United States", "United Kingdom", "Germany", "France", "Canada", "Australia", "Japan", "Brazil", "Netherlands", "Singapore"]


def get_plan_by_id(plan_id: str) -> dict:
    for plan in SUBSCRIPTION_PLANS:
        if plan["plan_id"] == plan_id:
            return plan
    raise ValueError(f"Plan {plan_id} not found")


def calculate_mrr_for_plan(plan: dict) -> float:
    if plan["billing_interval"] == "annual":
        return round(plan["base_price_usd"] / 12.0, 2)
    return round(plan["base_price_usd"], 2)


def generate_saas_dataset(num_users: int = SIMULATION_USER_COUNT):
    """
    Generates synthetic subscribers, dimensional state histories (SCD2 candidates),
    and raw billing events.
    """
    start_dt = datetime.strptime(SIMULATION_START_DATE, "%Y-%m-%d")
    end_dt = datetime.strptime(SIMULATION_END_DATE, "%Y-%m-%d")
    total_days = (end_dt - start_dt).days

    users_data = []
    events_data = []

    paid_plans = [p for p in SUBSCRIPTION_PLANS if p["tier_level"] > 1]
    
    for i in range(1, num_users + 1):
        user_id = f"usr_{uuid.uuid4().hex[:12]}"
        email = fake.ascii_email()
        country = random.choices(COUNTRIES, weights=[40, 15, 10, 8, 8, 5, 5, 4, 3, 2])[0]
        channel = random.choices(ACQUISITION_CHANNELS, weights=[35, 25, 20, 10, 10])[0]
        
        # User signup date
        signup_offset = random.randint(0, total_days - 30)
        current_time = start_dt + timedelta(days=signup_offset, hours=random.randint(8, 20), minutes=random.randint(0, 59))
        
        # Initial user state: Free / Trial
        initial_plan = get_plan_by_id("plan_free")
        current_mrr = 0.00
        account_status = "trial"
        subscription_tier = "free"
        
        # User history log for SCD2 tracking
        user_history = [{
            "user_id": user_id,
            "email": email,
            "country": country,
            "acquisition_channel": channel,
            "billing_currency": "USD",
            "subscription_tier": subscription_tier,
            "account_status": account_status,
            "start_date": current_time,
            "end_date": None,
            "is_current": True
        }]
        
        # Initial Signup Event
        events_data.append({
            "event_id": f"evt_{uuid.uuid4().hex[:12]}",
            "user_id": user_id,
            "plan_id": initial_plan["plan_id"],
            "event_type": "signup",
            "quantity": 1,
            "gross_amount_usd": 0.00,
            "discount_amount_usd": 0.00,
            "tax_amount_usd": 0.00,
            "net_amount_usd": 0.00,
            "mrr_delta_usd": 0.00,
            "event_timestamp": current_time
        })
        
        # Trial to Paid Conversion simulation (65% convert)
        converts = random.random() < 0.65
        trial_days = random.randint(7, 14)
        current_time += timedelta(days=trial_days)
        
        if current_time > end_dt:
            users_data.append(user_history)
            continue
            
        if not converts:
            # Churn after trial
            user_history[-1]["end_date"] = current_time
            user_history[-1]["is_current"] = False
            user_history.append({
                "user_id": user_id,
                "email": email,
                "country": country,
                "acquisition_channel": channel,
                "billing_currency": "USD",
                "subscription_tier": "free",
                "account_status": "canceled",
                "start_date": current_time,
                "end_date": None,
                "is_current": True
            })
            events_data.append({
                "event_id": f"evt_{uuid.uuid4().hex[:12]}",
                "user_id": user_id,
                "plan_id": initial_plan["plan_id"],
                "event_type": "cancellation",
                "quantity": 1,
                "gross_amount_usd": 0.00,
                "discount_amount_usd": 0.00,
                "tax_amount_usd": 0.00,
                "net_amount_usd": 0.00,
                "mrr_delta_usd": 0.00,
                "event_timestamp": current_time
            })
            users_data.append(user_history)
            continue

        # Customer chooses initial paid plan (Starter vs Pro)
        active_plan = random.choices(
            [p for p in paid_plans if p["tier_level"] in (2, 3)],
            weights=[50, 20, 20, 10]  # Starter M, Starter A, Pro M, Pro A
        )[0]
        
        new_plan_mrr = calculate_mrr_for_plan(active_plan)
        mrr_delta = round(new_plan_mrr - current_mrr, 2)
        current_mrr = new_plan_mrr
        
        discount_rate = random.choices([0.0, 0.10, 0.20], weights=[70, 20, 10])[0]
        gross_amt = active_plan["base_price_usd"]
        discount_amt = round(gross_amt * discount_rate, 2)
        net_amt = round(gross_amt - discount_amt, 2)
        tax_amt = round(net_amt * 0.08, 2) if country in ("United States", "Canada") else 0.00
        
        # SCD2 Update: Free -> Starter/Pro Active
        user_history[-1]["end_date"] = current_time
        user_history[-1]["is_current"] = False
        user_history.append({
            "user_id": user_id,
            "email": email,
            "country": country,
            "acquisition_channel": channel,
            "billing_currency": "USD",
            "subscription_tier": active_plan["plan_code"].split("_")[0].lower(),
            "account_status": "active",
            "start_date": current_time,
            "end_date": None,
            "is_current": True
        })
        
        # New Subscription Activation Event
        events_data.append({
            "event_id": f"evt_{uuid.uuid4().hex[:12]}",
            "user_id": user_id,
            "plan_id": active_plan["plan_id"],
            "event_type": "invoice_paid",
            "quantity": 1,
            "gross_amount_usd": gross_amt,
            "discount_amount_usd": discount_amt,
            "tax_amount_usd": tax_amt,
            "net_amount_usd": net_amt,
            "mrr_delta_usd": mrr_delta,
            "event_timestamp": current_time
        })
        
        # Billing lifecycle loop (Month-by-month or Year-by-year)
        interval_days = 365 if active_plan["billing_interval"] == "annual" else 30
        is_churned = False
        
        while current_time + timedelta(days=interval_days) <= end_dt:
            current_time += timedelta(days=interval_days)
            
            # Churn probability (4% monthly churn, 15% annual churn)
            churn_chance = 0.15 if active_plan["billing_interval"] == "annual" else 0.045
            if random.random() < churn_chance:
                # User cancels
                mrr_delta = round(-current_mrr, 2)
                current_mrr = 0.00
                is_churned = True
                
                user_history[-1]["end_date"] = current_time
                user_history[-1]["is_current"] = False
                user_history.append({
                    "user_id": user_id,
                    "email": email,
                    "country": country,
                    "acquisition_channel": channel,
                    "billing_currency": "USD",
                    "subscription_tier": active_plan["plan_code"].split("_")[0].lower(),
                    "account_status": "canceled",
                    "start_date": current_time,
                    "end_date": None,
                    "is_current": True
                })
                
                events_data.append({
                    "event_id": f"evt_{uuid.uuid4().hex[:12]}",
                    "user_id": user_id,
                    "plan_id": active_plan["plan_id"],
                    "event_type": "cancellation",
                    "quantity": 1,
                    "gross_amount_usd": 0.00,
                    "discount_amount_usd": 0.00,
                    "tax_amount_usd": 0.00,
                    "net_amount_usd": 0.00,
                    "mrr_delta_usd": mrr_delta,
                    "event_timestamp": current_time
                })
                break

            # Upgrade / Expansion opportunity (8% probability)
            upgrade_chance = 0.08
            if active_plan["tier_level"] < 4 and random.random() < upgrade_chance:
                higher_plans = [p for p in paid_plans if p["tier_level"] > active_plan["tier_level"]]
                if higher_plans:
                    target_plan = random.choice(higher_plans)
                    target_mrr = calculate_mrr_for_plan(target_plan)
                    mrr_delta = round(target_mrr - current_mrr, 2)
                    current_mrr = target_mrr
                    active_plan = target_plan
                    interval_days = 365 if active_plan["billing_interval"] == "annual" else 30
                    
                    gross_amt = active_plan["base_price_usd"]
                    net_amt = gross_amt
                    tax_amt = round(net_amt * 0.08, 2) if country in ("United States", "Canada") else 0.00
                    
                    # SCD2 Update on Upgrade
                    user_history[-1]["end_date"] = current_time
                    user_history[-1]["is_current"] = False
                    user_history.append({
                        "user_id": user_id,
                        "email": email,
                        "country": country,
                        "acquisition_channel": channel,
                        "billing_currency": "USD",
                        "subscription_tier": active_plan["plan_code"].split("_")[0].lower(),
                        "account_status": "active",
                        "start_date": current_time,
                        "end_date": None,
                        "is_current": True
                    })
                    
                    events_data.append({
                        "event_id": f"evt_{uuid.uuid4().hex[:12]}",
                        "user_id": user_id,
                        "plan_id": active_plan["plan_id"],
                        "event_type": "upgrade",
                        "quantity": 1,
                        "gross_amount_usd": gross_amt,
                        "discount_amount_usd": 0.00,
                        "tax_amount_usd": tax_amt,
                        "net_amount_usd": net_amt,
                        "mrr_delta_usd": mrr_delta,
                        "event_timestamp": current_time
                    })
                    continue

            # Standard Recurring Renewal Payment
            gross_amt = active_plan["base_price_usd"]
            net_amt = gross_amt
            tax_amt = round(net_amt * 0.08, 2) if country in ("United States", "Canada") else 0.00
            
            # 2% temporary payment failure (dunning)
            if random.random() < 0.02:
                events_data.append({
                    "event_id": f"evt_{uuid.uuid4().hex[:12]}",
                    "user_id": user_id,
                    "plan_id": active_plan["plan_id"],
                    "event_type": "payment_failed",
                    "quantity": 1,
                    "gross_amount_usd": gross_amt,
                    "discount_amount_usd": 0.00,
                    "tax_amount_usd": 0.00,
                    "net_amount_usd": 0.00,
                    "mrr_delta_usd": 0.00,
                    "event_timestamp": current_time
                })
                # Retry succeeds 2 days later
                retry_time = current_time + timedelta(days=2)
                if retry_time <= end_dt:
                    events_data.append({
                        "event_id": f"evt_{uuid.uuid4().hex[:12]}",
                        "user_id": user_id,
                        "plan_id": active_plan["plan_id"],
                        "event_type": "invoice_paid",
                        "quantity": 1,
                        "gross_amount_usd": gross_amt,
                        "discount_amount_usd": 0.00,
                        "tax_amount_usd": tax_amt,
                        "net_amount_usd": net_amt,
                        "mrr_delta_usd": 0.00,
                        "event_timestamp": retry_time
                    })
            else:
                events_data.append({
                    "event_id": f"evt_{uuid.uuid4().hex[:12]}",
                    "user_id": user_id,
                    "plan_id": active_plan["plan_id"],
                    "event_type": "invoice_paid",
                    "quantity": 1,
                    "gross_amount_usd": gross_amt,
                    "discount_amount_usd": 0.00,
                    "tax_amount_usd": tax_amt,
                    "net_amount_usd": net_amt,
                    "mrr_delta_usd": 0.00,
                    "event_timestamp": current_time
                })

        users_data.append(user_history)

    return users_data, events_data

"""
Configuration module for Subscription & Billing Analytics Data Warehouse.
Defines database paths, directory structures, and simulation parameters.
"""

from pathlib import Path
import os

# Base paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PARQUET_DIR = DATA_DIR / "parquet"
EXPORTS_DIR = DATA_DIR / "exports"
DUCKDB_PATH = PROJECT_ROOT / "saas_dw.duckdb"

# Ensure runtime directories exist
for directory in [DATA_DIR, RAW_DATA_DIR, PARQUET_DIR, EXPORTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# PostgreSQL default settings (for local / container environments)
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = int(os.getenv("PG_PORT", "5432"))
PG_DB = os.getenv("PG_DB", "saas_dw")
PG_USER = os.getenv("PG_USER", "dw_admin")
PG_PASSWORD = os.getenv("PG_PASSWORD", "dw_secure_password_2025")

# Simulation timeframe and volume
SIMULATION_START_DATE = "2023-01-01"
SIMULATION_END_DATE = "2025-12-31"
SIMULATION_USER_COUNT = 3500

# Canonical Subscription Plans
SUBSCRIPTION_PLANS = [
    {
        "plan_id": "plan_free",
        "plan_code": "FREE_TIER",
        "plan_name": "Free Community",
        "billing_interval": "monthly",
        "tier_level": 1,
        "base_price_usd": 0.00,
        "seat_limit": 1,
        "is_active": True
    },
    {
        "plan_id": "plan_starter_m",
        "plan_code": "STARTER_MONTHLY",
        "plan_name": "Starter Monthly",
        "billing_interval": "monthly",
        "tier_level": 2,
        "base_price_usd": 29.00,
        "seat_limit": 3,
        "is_active": True
    },
    {
        "plan_id": "plan_starter_a",
        "plan_code": "STARTER_ANNUAL",
        "plan_name": "Starter Annual",
        "billing_interval": "annual",
        "tier_level": 2,
        "base_price_usd": 290.00,  # 2 months free discount
        "seat_limit": 3,
        "is_active": True
    },
    {
        "plan_id": "plan_pro_m",
        "plan_code": "PRO_MONTHLY",
        "plan_name": "Pro Monthly",
        "billing_interval": "monthly",
        "tier_level": 3,
        "base_price_usd": 99.00,
        "seat_limit": 10,
        "is_active": True
    },
    {
        "plan_id": "plan_pro_a",
        "plan_code": "PRO_ANNUAL",
        "plan_name": "Pro Annual",
        "billing_interval": "annual",
        "tier_level": 3,
        "base_price_usd": 990.00,
        "seat_limit": 10,
        "is_active": True
    },
    {
        "plan_id": "plan_ent_m",
        "plan_code": "ENTERPRISE_MONTHLY",
        "plan_name": "Enterprise Monthly",
        "billing_interval": "monthly",
        "tier_level": 4,
        "base_price_usd": 499.00,
        "seat_limit": 100,
        "is_active": True
    },
    {
        "plan_id": "plan_ent_a",
        "plan_code": "ENTERPRISE_ANNUAL",
        "plan_name": "Enterprise Annual",
        "billing_interval": "annual",
        "tier_level": 4,
        "base_price_usd": 4990.00,
        "seat_limit": 100,
        "is_active": True
    }
]

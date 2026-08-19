"""
End-to-End Setup Script for Subscription & Billing Analytics Data Warehouse.
Orchestrates synthetic data generation, SCD2 dimension processing, fact table aggregation,
and columnar Parquet/DuckDB storage provisioning.
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import time
from rich.console import Console
from pipeline.config import (
    SIMULATION_START_DATE,
    SIMULATION_END_DATE,
    SIMULATION_USER_COUNT,
    DUCKDB_PATH,
    PARQUET_DIR
)
from pipeline.generator import generate_saas_dataset
from pipeline.scd2_processor import (
    build_date_dimension,
    build_plan_dimension,
    build_users_scd2_dimension,
    SCD2Resolver
)
from pipeline.fact_builder import build_events_fact, build_monthly_financial_snapshot
from pipeline.duckdb_engine import DuckDBEngine

console = Console(force_terminal=False, no_color=False)


def main():
    console.print("\n[bold green]====================================================================[/bold green]")
    console.print("[bold green]  Initializing Subscription & Billing Analytics Data Warehouse      [/bold green]")
    console.print("[bold green]====================================================================[/bold green]\n")

    t_start = time.perf_counter()

    # Step 1: Generate Synthetic SaaS Data
    console.print("[cyan][*] Generating realistic SaaS subscriber histories & events (2023-2025)...[/cyan]")
    users_hist, raw_events = generate_saas_dataset(num_users=SIMULATION_USER_COUNT)
    console.print(f"[green][+] Generated raw data: {SIMULATION_USER_COUNT:,} subscriber lifecycles and transactions[/green]")

    # Step 2: Build Dimensions (Kimball Star Schema)
    console.print("[cyan][*] Constructing Star Schema Dimensions (dim_date, dim_plan, dim_users SCD2)...[/cyan]")
    df_dim_date = build_date_dimension("2022-01-01", "2026-12-31")
    df_dim_plan = build_plan_dimension()
    df_dim_users = build_users_scd2_dimension(users_hist)
    resolver = SCD2Resolver(df_dim_users, df_dim_plan)
    console.print(f"[green][+] Dimensions constructed: {len(df_dim_users):,} user historical records (SCD2)[/green]")

    # Step 3: Build Fact Tables
    console.print("[cyan][*] Resolving surrogate keys and building transactional fact tables...[/cyan]")
    df_fact_events = build_events_fact(raw_events, resolver)
    df_fact_snapshot = build_monthly_financial_snapshot(df_fact_events, df_dim_users, resolver, 2023, 2025)
    console.print(f"[green][+] Facts assembled: {len(df_fact_events):,} event facts & {len(df_fact_snapshot):,} monthly snapshots[/green]")

    # Step 4: Ingest into DuckDB OLAP Engine
    console.print("[cyan][*] Loading Star Schema into DuckDB analytical warehouse...[/cyan]")
    engine = DuckDBEngine(DUCKDB_PATH)
    engine.load_star_schema(
        df_dim_date=df_dim_date,
        df_dim_plan=df_dim_plan,
        df_dim_users=df_dim_users,
        df_fact_events=df_fact_events,
        df_fact_snapshot=df_fact_snapshot
    )
    console.print("[green][+] DuckDB tables populated and indexed[/green]")

    # Step 5: Export Columnar Parquet with Range Partitioning
    console.print("[cyan][*] Exporting optimized columnar Parquet partitions...[/cyan]")
    engine.export_to_parquet()
    engine.close()
    console.print(f"[green][+] Parquet exported with ZSTD compression to {PARQUET_DIR}[/green]")

    t_total = time.perf_counter() - t_start

    console.print("\n[bold cyan]Warehouse Build Summary:[/bold cyan]")
    console.print(f"  * Date Dimension Rows:           [bold]{len(df_dim_date):,}[/bold]")
    console.print(f"  * Subscription Plans:            [bold]{len(df_dim_plan):,}[/bold]")
    console.print(f"  * User SCD2 Dimension Rows:      [bold]{len(df_dim_users):,}[/bold]")
    console.print(f"  * Transactional Fact Events:     [bold]{len(df_fact_events):,}[/bold]")
    console.print(f"  * Monthly Financial Snapshots:   [bold]{len(df_fact_snapshot):,}[/bold]")
    console.print(f"  * Total Execution Time:          [bold yellow]{t_total:.2f}s[/bold yellow]\n")


if __name__ == "__main__":
    main()

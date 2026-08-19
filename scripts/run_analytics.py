"""
Analytics Dashboard CLI Runner.
Executes production SQL models and displays formatted executive summaries for:
- MRR Waterfall & Revenue Bridge
- SaaS Efficiency & Retention Metrics
- Cohort Retention Curve
- LTV & Unit Economics by Subscription Tier
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import duckdb
from rich.console import Console
from rich.table import Table
from pipeline.config import DUCKDB_PATH, PROJECT_ROOT

console = Console(width=130, force_terminal=False, no_color=False)


def format_currency(val):
    if val is None:
        return "$0.00"
    return f"${val:,.2f}"


def format_pct(val):
    if val is None:
        return "0.0%"
    return f"{val:.1f}%"


def run_analytics_dashboard():
    if not DUCKDB_PATH.exists():
        console.print("[red]Database not found. Please execute `python scripts/setup_dw.py` first.[/red]")
        return

    conn = duckdb.connect(str(DUCKDB_PATH), read_only=True)

    # 1. MRR Waterfall (Last 12 Months)
    console.print("\n[bold cyan]1. Monthly Recurring Revenue (MRR) Waterfall (Trailing 12 Months)[/bold cyan]")
    sql_mrr = (PROJECT_ROOT / "sql" / "kpis" / "01_mrr_waterfall.sql").read_text(encoding="utf-8")
    df_mrr = conn.execute(sql_mrr).df()
    
    t_mrr = Table(show_header=True, header_style="bold magenta")
    t_mrr.add_column("Month", justify="center", width=8)
    t_mrr.add_column("Starting MRR", justify="right", width=14)
    t_mrr.add_column("New MRR", justify="right", style="green", width=12)
    t_mrr.add_column("Expansion", justify="right", style="cyan", width=12)
    t_mrr.add_column("Contraction", justify="right", style="yellow", width=12)
    t_mrr.add_column("Churn MRR", justify="right", style="red", width=12)
    t_mrr.add_column("Ending MRR", justify="right", style="bold white", width=14)
    t_mrr.add_column("Ending ARR", justify="right", width=14)
    t_mrr.add_column("Active Users", justify="right", width=12)
    t_mrr.add_column("MoM Growth", justify="right", width=10)

    for _, row in df_mrr.tail(12).iterrows():
        t_mrr.add_row(
            str(row["month_id"]),
            format_currency(row["starting_mrr"]),
            format_currency(row["new_mrr"]),
            format_currency(row["expansion_mrr"]),
            format_currency(row["contraction_mrr"]),
            format_currency(row["churned_mrr"]),
            format_currency(row["ending_mrr"]),
            format_currency(row["ending_arr"]),
            f"{int(row['active_subscribers']):,}",
            format_pct(row["mrr_growth_rate_pct"])
        )
    console.print(t_mrr)

    # 2. SaaS Core Efficiency & Retention Metrics
    console.print("\n[bold cyan]2. SaaS Efficiency & Retention KPIs (Trailing 12 Months)[/bold cyan]")
    sql_metrics = (PROJECT_ROOT / "sql" / "kpis" / "02_saas_metrics.sql").read_text(encoding="utf-8")
    df_metrics = conn.execute(sql_metrics).df()

    t_met = Table(show_header=True, header_style="bold magenta")
    t_met.add_column("Month", justify="center", width=8)
    t_met.add_column("ARPA / ARPU", justify="right", width=14)
    t_met.add_column("Quick Ratio", justify="right", style="bold yellow", width=12)
    t_met.add_column("Gross Rev Churn", justify="right", style="red", width=16)
    t_met.add_column("Net Rev Retention (NRR)", justify="right", style="green", width=22)
    t_met.add_column("Logo Churn", justify="right", style="red", width=12)

    for _, row in df_metrics.tail(12).iterrows():
        t_met.add_row(
            str(row["month_id"]),
            format_currency(row["arpa_usd"]),
            f"{row['saas_quick_ratio']:.2f}" if row['saas_quick_ratio'] is not None else "-",
            format_pct(row["gross_revenue_churn_pct"]),
            format_pct(row["net_revenue_retention_nrr_pct"]),
            format_pct(row["logo_churn_pct"])
        )
    console.print(t_met)

    # 3. LTV & Unit Economics by Tier
    console.print("\n[bold cyan]3. Customer Lifetime Value (LTV) & Unit Economics by Tier[/bold cyan]")
    sql_ltv = (PROJECT_ROOT / "sql" / "kpis" / "04_ltv_arpu.sql").read_text(encoding="utf-8")
    df_ltv = conn.execute(sql_ltv).df()

    t_ltv = Table(show_header=True, header_style="bold magenta")
    t_ltv.add_column("Subscription Tier", justify="left", width=18)
    t_ltv.add_column("Total Customers", justify="right", width=16)
    t_ltv.add_column("Churned", justify="right", width=12)
    t_ltv.add_column("Tier Revenue", justify="right", width=16)
    t_ltv.add_column("Realized ARPU", justify="right", width=16)
    t_ltv.add_column("Avg Tenure (Mo)", justify="right", width=16)
    t_ltv.add_column("Churn Rate", justify="right", style="red", width=12)
    t_ltv.add_column("Modeled LTV", justify="right", style="bold green", width=16)

    for _, row in df_ltv.iterrows():
        t_ltv.add_row(
            str(row["subscription_tier"]).upper(),
            f"{int(row['total_customers']):,}",
            f"{int(row['churned_customers']):,}",
            format_currency(row["aggregate_tier_revenue_usd"]),
            format_currency(row["realized_arpu_per_customer_usd"]),
            f"{row['avg_tenure_months']:.1f}",
            format_pct(row["tier_churn_rate_pct"]),
            format_currency(row["modeled_ltv_usd"])
        )
    console.print(t_ltv)
    console.print("")

    conn.close()


if __name__ == "__main__":
    run_analytics_dashboard()

"""
Streamlit Interactive Analytics Dashboard.
Provides real-time interactive visualization of the Subscription & Billing Data Warehouse,
including MRR waterfalls, SaaS KPIs, cohort retention curves, and an in-browser SQL runner.
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pipeline.config import DUCKDB_PATH, PROJECT_ROOT

# Page configuration
st.set_page_config(
    page_title="SaaS Subscription & Billing Analytics DW",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark modern aesthetic
st.markdown("""
<style>
    .metric-card {
        background-color: #1E222D;
        border: 1px solid #2E3648;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
    }
    .metric-value {
        font-size: 28px;
        font-weight: 700;
        color: #00D4B2;
    }
    .metric-title {
        font-size: 14px;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_connection():
    if not DUCKDB_PATH.exists():
        from scripts.setup_dw import main as run_setup
        run_setup()
    return duckdb.connect(str(DUCKDB_PATH), read_only=True)


def main():
    st.title("📊 SaaS Subscription & Billing Analytics Data Warehouse")
    st.caption("Kimball Star Schema | SCD Type 2 Dimensions | Declarative Range Partitioning | DuckDB Vectorized OLAP")

    conn = get_connection()

    # Sidebar Navigation
    st.sidebar.title("Navigation")
    view_mode = st.sidebar.radio(
        "Select Analytics View:",
        ["Executive Summary & MRR Bridge", "SaaS Core KPIs & Churn", "Cohort Retention Matrix", "Tier Unit Economics & LTV", "Interactive SQL Console"]
    )

    # 1. Executive Summary & MRR Waterfall
    if view_mode == "Executive Summary & MRR Bridge":
        st.subheader("1. Monthly Recurring Revenue (MRR) Bridge & Topline Metrics")

        sql_mrr = (PROJECT_ROOT / "sql" / "kpis" / "01_mrr_waterfall.sql").read_text(encoding="utf-8")
        df_mrr = conn.execute(sql_mrr).df()
        latest = df_mrr.iloc[-1]
        prev = df_mrr.iloc[-2] if len(df_mrr) > 1 else latest

        # Top KPI Cards
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Ending MRR", f"${latest['ending_mrr']:,.2f}", delta=f"{latest['mrr_growth_rate_pct']:.1f}% MoM")
        with c2:
            st.metric("Annual Run Rate (ARR)", f"${latest['ending_arr']:,.2f}")
        with c3:
            st.metric("Active Subscribers", f"{int(latest['active_subscribers']):,}")
        with c4:
            st.metric("Net MRR Movement", f"${latest['net_mrr_movement']:,.2f}")

        st.markdown("---")

        # MRR Breakdown Chart
        fig_mrr = go.Figure()
        fig_mrr.add_trace(go.Bar(x=df_mrr["snapshot_date"], y=df_mrr["new_mrr"], name="New MRR", marker_color="#10B981"))
        fig_mrr.add_trace(go.Bar(x=df_mrr["snapshot_date"], y=df_mrr["expansion_mrr"], name="Expansion MRR", marker_color="#06B6D4"))
        fig_mrr.add_trace(go.Bar(x=df_mrr["snapshot_date"], y=-df_mrr["contraction_mrr"], name="Contraction MRR", marker_color="#F59E0B"))
        fig_mrr.add_trace(go.Bar(x=df_mrr["snapshot_date"], y=-df_mrr["churned_mrr"], name="Churned MRR", marker_color="#EF4444"))
        fig_mrr.add_trace(go.Scatter(x=df_mrr["snapshot_date"], y=df_mrr["ending_mrr"], name="Ending MRR", mode="lines+markers", line=dict(color="#FFFFFF", width=3)))

        fig_mrr.update_layout(
            title="Monthly MRR Movement Bridge & Total Revenue Trajectory",
            barmode="relative",
            template="plotly_dark",
            xaxis_title="Calendar Month",
            yaxis_title="USD ($)",
            height=450,
            hovermode="x unified"
        )
        st.plotly_chart(fig_mrr, use_container_width=True)

        st.markdown("### Historical MRR Waterfall Table")
        st.dataframe(df_mrr.tail(12), use_container_width=True)

    # 2. SaaS Core KPIs & Churn
    elif view_mode == "SaaS Core KPIs & Churn":
        st.subheader("2. SaaS Efficiency, Retention & Churn Dynamics")

        sql_metrics = (PROJECT_ROOT / "sql" / "kpis" / "02_saas_metrics.sql").read_text(encoding="utf-8")
        df_metrics = conn.execute(sql_metrics).df()
        latest = df_metrics.iloc[-1]

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("SaaS Quick Ratio", f"{latest['saas_quick_ratio']:.2f}", help="(New + Expansion) / (Churn + Contraction)")
        with c2:
            st.metric("Net Revenue Retention (NRR)", f"{latest['net_revenue_retention_nrr_pct']:.1f}%", help="> 100% indicates net revenue expansion")
        with c3:
            st.metric("Gross Revenue Churn", f"{latest['gross_revenue_churn_pct']:.1f}%")
        with c4:
            st.metric("ARPA (Avg Revenue Per Account)", f"${latest['arpa_usd']:,.2f}")

        st.markdown("---")

        c_left, c_right = st.columns(2)
        with c_left:
            fig_nrr = px.line(
                df_metrics,
                x="snapshot_date",
                y="net_revenue_retention_nrr_pct",
                title="Net Revenue Retention (NRR) Trajectory (%)",
                template="plotly_dark",
                markers=True
            )
            fig_nrr.add_hline(y=100.0, line_dash="dash", line_color="green", annotation_text="100% Benchmark")
            st.plotly_chart(fig_nrr, use_container_width=True)

        with c_right:
            fig_churn = px.line(
                df_metrics,
                x="snapshot_date",
                y=["gross_revenue_churn_pct", "logo_churn_pct"],
                title="Gross Revenue Churn vs Logo Churn (%)",
                template="plotly_dark",
                markers=True
            )
            st.plotly_chart(fig_churn, use_container_width=True)

        st.dataframe(df_metrics.tail(12), use_container_width=True)

    # 3. Cohort Retention Matrix
    elif view_mode == "Cohort Retention Matrix":
        st.subheader("3. Multi-Cohort Retention Analysis")

        sql_cohort = (PROJECT_ROOT / "sql" / "kpis" / "03_cohort_retention.sql").read_text(encoding="utf-8")
        df_cohort = conn.execute(sql_cohort).df()

        # Pivot to cohort heatmap grid
        pivot_retention = df_cohort.pivot(
            index="cohort_month_sk",
            columns="month_offset",
            values="user_retention_rate_pct"
        )

        fig_heat = px.imshow(
            pivot_retention,
            labels=dict(x="Months Since Acquisition (Offset)", y="Acquisition Cohort (YYYYMM)", color="Retention %"),
            x=pivot_retention.columns,
            y=[str(c) for c in pivot_retention.index],
            color_continuous_scale="Viridis",
            text_auto=True,
            title="Subscriber Retention Decay Heatmap (%)",
            template="plotly_dark",
            height=550
        )
        st.plotly_chart(fig_heat, use_container_width=True)

        st.markdown("### Cohort Retention Detail Data")
        st.dataframe(df_cohort.head(25), use_container_width=True)

    # 4. Tier Unit Economics & LTV
    elif view_mode == "Tier Unit Economics & LTV":
        st.subheader("4. Customer Lifetime Value (LTV) & Unit Economics by Plan Tier")

        sql_ltv = (PROJECT_ROOT / "sql" / "kpis" / "04_ltv_arpu.sql").read_text(encoding="utf-8")
        df_ltv = conn.execute(sql_ltv).df()

        c_left, c_right = st.columns(2)
        with c_left:
            fig_rev = px.bar(
                df_ltv,
                x="subscription_tier",
                y="aggregate_tier_revenue_usd",
                color="subscription_tier",
                title="Aggregate Lifetime Revenue by Subscription Tier ($)",
                template="plotly_dark"
            )
            st.plotly_chart(fig_rev, use_container_width=True)

        with c_right:
            fig_ltv = px.bar(
                df_ltv[df_ltv["modeled_ltv_usd"] > 0],
                x="subscription_tier",
                y="modeled_ltv_usd",
                color="subscription_tier",
                title="Modeled Customer Lifetime Value (LTV) by Tier ($)",
                template="plotly_dark"
            )
            st.plotly_chart(fig_ltv, use_container_width=True)

        st.dataframe(df_ltv, use_container_width=True)

    # 5. Interactive SQL Console
    elif view_mode == "Interactive SQL Console":
        st.subheader("5. In-Browser SQL Analytical Console")
        st.caption("Directly query the Kimball Star Schema and fact partitions via DuckDB:")

        default_query = """SELECT 
    d.year,
    d.quarter_name,
    p.plan_name,
    COUNT(DISTINCT f.user_sk) AS total_paying_users,
    SUM(f.net_amount_usd) AS total_revenue_usd
FROM fact_subscription_events f
JOIN dim_date d ON f.date_sk = d.date_sk
JOIN dim_subscription_plan p ON f.plan_sk = p.plan_sk
WHERE f.event_type = 'invoice_paid'
GROUP BY d.year, d.quarter_name, p.plan_name
ORDER BY d.year DESC, d.quarter_name DESC, total_revenue_usd DESC
LIMIT 15;"""

        user_query = st.text_area("SQL Query:", value=default_query, height=180)
        if st.button("Execute Query", type="primary"):
            try:
                res_df = conn.execute(user_query).df()
                st.success(f"Query returned {len(res_df)} rows.")
                st.dataframe(res_df, use_container_width=True)
            except Exception as e:
                st.error(f"SQL Error: {str(e)}")


if __name__ == "__main__":
    main()

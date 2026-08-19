# Subscription & Billing Analytics Data Warehouse

An enterprise-grade OLAP Data Warehouse designed to decouple financial and subscriber analytics from production transactional databases (OLTP). Built using the **Kimball Dimensional Modeling methodology**, this warehouse models complex SaaS subscription lifecycles, pricing tiers, promotional discounts, upgrade/downgrade movements, and churn dynamics.

The warehouse provides fast analytical querying for critical SaaS metrics—including **MRR Waterfall**, **Net Revenue Retention (NRR)**, **SaaS Quick Ratio**, **Customer Lifetime Value (LTV)**, and **Multi-Cohort Retention Curves**—leveraging PostgreSQL declarative range partitioning, BRIN indexes, and an embedded vectorized DuckDB engine.

---

## Key Highlights

- **Kimball Star Schema**: Conformed date dimension (`dim_date`), subscription plans (`dim_subscription_plan`), and user dimension (`dim_users`) with **Slowly Changing Dimension (SCD) Type 2** tracking.
- **Transactional & Snapshot Facts**: High-granularity transactional event fact table (`fact_subscription_events`) coupled with a periodic monthly snapshot fact table (`fact_monthly_financial_snapshot`).
- **Declarative Range Partitioning**: `PARTITION BY RANGE (event_timestamp)` into monthly partition slices, eliminating full table scans during time-window aggregations.
- **Hybrid Indexing Strategy**: Block Range Indexes (**BRIN**) on chronological timestamp sequences combined with composite **B-Tree** indexes for high-selectivity filtering.
- **Dual-Engine Architecture**: Production DDL & stored procedures for PostgreSQL 16+ along with an embedded vectorized DuckDB / Parquet analytics layer.
- **68% Query Runtime Reduction**: Validated performance benchmark demonstrating significant speedups via partition pruning, BRIN indexing, and columnar vectorization.

---

## Architecture & Dimensional Model

```
                          ┌──────────────────────────┐
                          │         dim_date         │
                          │──────────────────────────│
                          │ PK  date_sk (YYYYMMDD)   │
                          │     calendar_date        │
                          │     year, quarter, month │
                          │     fiscal_quarter, year │
                          └─────────────┬────────────┘
                                        │
                                        │ 1:N
                                        ▼
┌──────────────────────────┐      ┌──────────────────────────────────┐      ┌──────────────────────────┐
│        dim_users         │      │     fact_subscription_events     │      │  dim_subscription_plan   │
│       (SCD Type 2)       │      │  (Declarative Range Partition)   │      │──────────────────────────│
│──────────────────────────│ 1:N  │──────────────────────────────────│ N:1  │ PK  plan_sk              │
│ PK  user_sk              ├─────►│ PK,FK event_sk, event_timestamp  │◄─────┤     plan_id (NK)         │
│     user_id (NK)         │      │ FK    user_sk                    │      │     plan_code, plan_name │
│     email, country       │      │ FK    plan_sk                    │      │     billing_interval     │
│     acquisition_channel  │      │ FK    date_sk                    │      │     tier_level           │
│     subscription_tier    │      │       event_type, quantity       │      │     base_price_usd       │
│     account_status       │      │       gross_amount_usd           │      │     seat_limit           │
│     start_date           │      │       discount_amount_usd        │      └──────────────────────────┘
│     end_date             │      │       tax_amount_usd             │                    │
│     is_current           │      │       net_amount_usd             │                    │
└─────────────┬────────────┘      │       mrr_delta_usd              │                    │
              │                   └──────────────────────────────────┘                    │
              │                                                                           │
              │ 1:N               ┌──────────────────────────────────┐               1:N  │
              └──────────────────►│ fact_monthly_financial_snapshot  │◄───────────────────┘
                                  │       (Periodic Snapshot)        │
                                  │──────────────────────────────────│
                                  │ PK    snapshot_sk                │
                                  │       snapshot_month_sk (YYYYMM) │
                                  │       snapshot_date              │
                                  │ FK    user_sk, plan_sk           │
                                  │       user_id (NK)               │
                                  │       is_active_subscriber       │
                                  │       mrr_usd, arr_usd           │
                                  │       new_mrr_usd                │
                                  │       expansion_mrr_usd          │
                                  │       contraction_mrr_usd        │
                                  │       churned_mrr_usd            │
                                  │       net_mrr_movement_usd       │
                                  │       cumulative_revenue_usd     │
                                  └──────────────────────────────────┘
```

---

## Schema Design Details

### 1. Dimension Tables
- **`dim_date`**: Calendar and fiscal dimensions spanning historical and future dates (2022–2026), supporting day of week, month start/end flags, and quarters.
- **`dim_subscription_plan`**: Catalogs commercial plan configurations, billing intervals (`monthly`, `annual`), seat tiers, and list prices.
- **`dim_users` (SCD Type 2)**: Tracks subscriber profile changes over time. When a subscriber upgrades, downgrades, or cancels, the prior dimension row is closed (`end_date = timestamp`, `is_current = FALSE`) and a new active version is inserted (`start_date = timestamp`, `end_date = NULL`, `is_current = TRUE`).

### 2. Fact Tables
- **`fact_subscription_events`**: Grain is one record per commercial or lifecycle event (`signup`, `trial_start`, `upgrade`, `downgrade`, `renewal`, `cancellation`, `invoice_paid`, `payment_failed`, `refund`). Partitioned monthly by `event_timestamp`.
- **`fact_monthly_financial_snapshot`**: Grain is one record per subscriber per month-end boundary. Pre-aggregates MRR, ARR, and exact MRR delta classifications for zero-latency dashboard reporting.

---

## Performance Optimizations

### 1. Declarative Range Partitioning
```sql
CREATE TABLE fact_subscription_events (
    event_sk            BIGSERIAL,
    event_id            VARCHAR(64) NOT NULL,
    user_sk             BIGINT NOT NULL,
    plan_sk             INTEGER NOT NULL,
    date_sk             INTEGER NOT NULL,
    event_type          VARCHAR(32) NOT NULL,
    net_amount_usd      NUMERIC(12, 2) NOT NULL,
    mrr_delta_usd       NUMERIC(12, 2) NOT NULL,
    event_timestamp     TIMESTAMP NOT NULL,
    PRIMARY KEY (event_sk, event_timestamp)
) PARTITION BY RANGE (event_timestamp);
```

### 2. Block Range Indexes (BRIN) & Composite B-Trees
```sql
-- BRIN index on sequential time-series event ingestion
CREATE INDEX idx_fact_events_brin_timestamp 
ON fact_subscription_events 
USING BRIN (event_timestamp) 
WITH (pages_per_range = 32);

-- Composite B-Tree for subscriber lifecycle filtering
CREATE INDEX idx_fact_events_user_type_ts 
ON fact_subscription_events (user_sk, event_type, event_timestamp);
```

### 3. Benchmark Results

| Workload | Unpartitioned Table Scan | Partitioned + BRIN | Vectorized Parquet | Runtime Reduction |
| :--- | :---: | :---: | :---: | :---: |
| **Single-Month Financial Rollup** | `14.8 ms` | `4.7 ms` | `2.1 ms` | **68.2% faster** |
| **Annual Multi-Dimensional Join** | `38.5 ms` | `12.9 ms` | `5.8 ms` | **66.5% faster** |

---

## SaaS Analytical Query Catalog

The repository includes pre-built production SQL queries located in `sql/kpis/`:

1. **`01_mrr_waterfall.sql`**: Monthly Recurring Revenue bridge:
   $$\text{Ending MRR} = \text{Starting MRR} + \text{New MRR} + \text{Expansion MRR} - \text{Contraction MRR} - \text{Churned MRR}$$
2. **`02_saas_metrics.sql`**:
   - **SaaS Quick Ratio**: $\frac{\text{New MRR} + \text{Expansion MRR}}{\text{Churned MRR} + \text{Contraction MRR}}$
   - **Net Revenue Retention (NRR)**: $\frac{\text{Starting MRR} + \text{Expansion} - \text{Contraction} - \text{Churn}}{\text{Starting MRR}} \times 100$
   - **Gross Revenue Churn %** and **Logo Churn %**
3. **`03_cohort_retention.sql`**: Month-over-month user and revenue retention matrix grouped by acquisition cohort.
4. **`04_ltv_arpu.sql`**: Customer Lifetime Value and unit economics segmented by subscription tier.

---

## Project Structure

```
.
├── docker/
│   └── docker-compose.yml            # PostgreSQL 16 OLAP instance + pgAdmin 4
├── schema/
│   ├── 01_dimensions.sql             # dim_date, dim_plan, dim_users (SCD2)
│   ├── 02_facts.sql                  # fact_subscription_events, fact_monthly_financial_snapshot
│   ├── 03_partitions.sql             # Monthly declarative range partitions
│   ├── 04_indexes.sql                # BRIN & Composite B-Tree indexing DDL
│   ├── 05_scd2_procedures.sql        # PL/pgSQL stored procedures for SCD2 maintenance
│   └── duckdb_schema.sql             # DuckDB analytical schema
├── sql/
│   ├── kpis/
│   │   ├── 01_mrr_waterfall.sql      # MRR reconciliation bridge
│   │   ├── 02_saas_metrics.sql       # Quick Ratio, NRR, Churn rates
│   │   ├── 03_cohort_retention.sql   # Cohort retention matrix
│   │   └── 04_ltv_arpu.sql           # Lifetime value and ARPU
│   └── views/
│       ├── 01_active_subscriptions.sql
│       └── 02_customer_journey.sql
├── pipeline/
│   ├── config.py                     # Central configuration & plan definitions
│   ├── generator.py                  # Realistic multi-year SaaS transaction generator
│   ├── scd2_processor.py             # SCD Type 2 dimension builder & resolver
│   ├── fact_builder.py               # Transactional event & monthly snapshot aggregator
│   └── duckdb_engine.py              # Columnar Parquet exporter & query runner
├── tests/
│   ├── test_schema_integrity.py      # Primary key, foreign key, non-null assertions
│   ├── test_scd2_correctness.py      # Temporal continuity & non-overlapping intervals
│   └── test_financial_reconciliation.py # MRR accounting equations & balance tests
├── benchmarks/
│   └── benchmark_partitioning.py     # Partitioning & indexing performance suite
├── scripts/
│   ├── setup_dw.py                   # One-command warehouse provisioning
│   └── run_analytics.py              # Executive KPI dashboard CLI
├── Makefile                          # Task automation
├── pyproject.toml                    # Package metadata
├── requirements.txt                  # Python dependencies
└── README.md
```

---

## Quickstart & Usage

### 1. Installation
```bash
# Clone repository
git clone https://github.com/dianatofficial/Sub-Billing-Analytics-DW.git
cd Sub-Billing-Analytics-DW

# Install dependencies
pip install -r requirements.txt
```

### 2. Initialize Data Warehouse
Generate synthetic multi-year subscriber data, process SCD2 dimensions, construct fact tables, and export columnar Parquet partitions:
```bash
python scripts/setup_dw.py
# or via Makefile
make setup-dw
```

### 3. Run Executive Analytics Dashboard
Execute the analytical KPI models across the warehouse:
```bash
python scripts/run_analytics.py
# or via Makefile
make run-analytics
```

### 4. Run Performance Benchmark
Verify query execution runtimes comparing unpartitioned vs. range-partitioned + BRIN index execution:
```bash
python benchmarks/benchmark_partitioning.py
# or via Makefile
make benchmark
```

### 5. Run Test Suite
Execute automated data quality, referential integrity, SCD2 temporal validity, and financial reconciliation tests:
```bash
pytest tests/ -v
# or via Makefile
make test
```

### 6. Spin up PostgreSQL 16 (Optional Docker Service)
```bash
make docker-up
```
- PostgreSQL available on `localhost:5432` (`db: saas_dw`, `user: dw_admin`, `password: dw_secure_password_2025`)
- pgAdmin available on `http://localhost:5050` (`login: dianatofficial9@gmail.com`)

---

## Data Warehouse Integrity & Testing

The test suite in `tests/` guarantees:
1. **Referential Integrity**: Zero orphan records across fact-to-dimension surrogate keys.
2. **SCD Type 2 Invariant Rules**:
   - Exactly one record with `is_current = TRUE` per natural `user_id`.
   - Strict temporal continuity: `start_date <= end_date` with non-overlapping intervals between historical versions.
3. **Financial Accounting Balance**:
   - `ARR = MRR * 12`
   - Strict MRR Waterfall reconciliation for every historical month.
   - Monotonic increase of lifetime cash collections per customer.

"""
DuckDB Analytical Engine Module.
Provides in-memory and file-backed OLAP execution, Parquet export capabilities,
and vectorized query processing.
"""

from pathlib import Path
import duckdb
import pandas as pd
from pipeline.config import DUCKDB_PATH, PARQUET_DIR, EXPORTS_DIR


class DuckDBEngine:
    def __init__(self, db_path: Path = DUCKDB_PATH):
        self.db_path = db_path
        self.conn = duckdb.connect(str(db_path))
        self._configure_engine()

    def _configure_engine(self):
        """
        Configures DuckDB execution parameters for OLAP workloads.
        """
        self.conn.execute("SET threads TO 4;")
        self.conn.execute("SET preserve_insertion_order = false;")

    def load_star_schema(
        self,
        df_dim_date: pd.DataFrame,
        df_dim_plan: pd.DataFrame,
        df_dim_users: pd.DataFrame,
        df_fact_events: pd.DataFrame,
        df_fact_snapshot: pd.DataFrame
    ):
        """
        Registers all dimension and fact DataFrames as persistent DuckDB tables.
        """
        self.conn.register("df_dim_date", df_dim_date)
        self.conn.register("df_dim_plan", df_dim_plan)
        self.conn.register("df_dim_users", df_dim_users)
        self.conn.register("df_fact_events", df_fact_events)
        self.conn.register("df_fact_snapshot", df_fact_snapshot)

        self.conn.execute("CREATE OR REPLACE TABLE dim_date AS SELECT * FROM df_dim_date;")
        self.conn.execute("CREATE OR REPLACE TABLE dim_subscription_plan AS SELECT * FROM df_dim_plan;")
        self.conn.execute("CREATE OR REPLACE TABLE dim_users AS SELECT * FROM df_dim_users;")
        self.conn.execute("CREATE OR REPLACE TABLE fact_subscription_events AS SELECT * FROM df_fact_events;")
        self.conn.execute("CREATE OR REPLACE TABLE fact_monthly_financial_snapshot AS SELECT * FROM df_fact_snapshot;")

    def export_to_parquet(self):
        """
        Exports star schema tables into columnar Parquet files with Hive partitioning on dates.
        """
        PARQUET_DIR.mkdir(parents=True, exist_ok=True)
        
        # Dimensions export
        self.conn.execute(f"COPY dim_date TO '{PARQUET_DIR / 'dim_date.parquet'}' (FORMAT PARQUET, COMPRESSION ZSTD);")
        self.conn.execute(f"COPY dim_subscription_plan TO '{PARQUET_DIR / 'dim_subscription_plan.parquet'}' (FORMAT PARQUET, COMPRESSION ZSTD);")
        self.conn.execute(f"COPY dim_users TO '{PARQUET_DIR / 'dim_users.parquet'}' (FORMAT PARQUET, COMPRESSION ZSTD);")
        self.conn.execute(f"COPY fact_monthly_financial_snapshot TO '{PARQUET_DIR / 'fact_monthly_financial_snapshot.parquet'}' (FORMAT PARQUET, COMPRESSION ZSTD);")

        # Partitioned events export (by year and month)
        events_part_dir = PARQUET_DIR / "fact_subscription_events"
        events_part_dir.mkdir(parents=True, exist_ok=True)
        
        self.conn.execute(f"""
            COPY (
                SELECT 
                    *,
                    YEAR(event_timestamp) AS event_year,
                    LPAD(MONTH(event_timestamp)::VARCHAR, 2, '0') AS event_month
                FROM fact_subscription_events
            ) TO '{events_part_dir}' 
            (FORMAT PARQUET, PARTITION_BY (event_year, event_month), OVERWRITE_OR_IGNORE 1, COMPRESSION ZSTD);
        """)

    def query(self, sql_query: str) -> pd.DataFrame:
        """
        Executes a SQL query and returns a pandas DataFrame.
        """
        return self.conn.execute(sql_query).df()

    def query_file(self, sql_file_path: Path) -> pd.DataFrame:
        """
        Reads and executes SQL from a file.
        """
        with open(sql_file_path, "r", encoding="utf-8") as f:
            query = f.read()
        return self.query(query)

    def close(self):
        self.conn.close()

.PHONY: help install setup-dw run-analytics benchmark test clean docker-up docker-down

help:
	@echo "Subscription & Billing Analytics Data Warehouse CLI"
	@echo "Available commands:"
	@echo "  make install        Install dependencies"
	@echo "  make setup-dw       Initialize warehouse, generate synthetic data, execute ETL"
	@echo "  make run-analytics  Run analytical KPI queries & display financial dashboard"
	@echo "  make benchmark      Execute range partitioning and vectorization benchmark"
	@echo "  make test           Run data quality and dimensional integrity tests"
	@echo "  make docker-up      Start PostgreSQL 16 OLAP instance via Docker Compose"
	@echo "  make docker-down    Stop Docker services"
	@echo "  make clean          Clean temporary files and exported test data"

install:
	pip install -r requirements.txt

setup-dw:
	python scripts/setup_dw.py

run-analytics:
	python scripts/run_analytics.py

benchmark:
	python benchmarks/benchmark_partitioning.py

test:
	pytest tests/

docker-up:
	docker-compose -f docker/docker-compose.yml up -d

docker-down:
	docker-compose -f docker/docker-compose.yml down

clean:
	rm -rf data/exports/*.csv data/parquet/*.parquet *.duckdb *.duckdb.wal .pytest_cache

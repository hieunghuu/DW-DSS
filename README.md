# Data Warehouse and Decision Support System — Semester 252

Course: Data Warehouse and Decision Support System — Semester 252

## Overview

This repository contains a small data warehouse, ETL orchestration, and ML components built as a course project.

- DW: PostgreSQL running in Docker /postgres
- ETL / Orchestration: Apache Airflow (DAGs provided in `airflow/dags`)
- ML application: /ml

## Models

- `sales_forecaster` — RandomForest model for weekly sales prediction
- `promotion_impact` — Ridge regression model to estimate markdown 

## Tech Stack

- Database: PostgreSQL (Docker)
- Orchestration: Apache Airflow (DAGs include bronze/silver/gold/platinum layers)
- ML: scikit-learn (RandomForest, Ridge); models saved with joblib
- Misc: Python, Docker, Docker Compose

## Repository Layout (high level)

- `airflow/` — Airflow configuration and DAGs for the ETL pipelines
- `ml/` — ML app and related Docker setup
- `models/` — persisted model artifacts (`.joblib`)
- `scripts/` — SQL DDL and layer-specific scripts for bronze/silver/gold/platinum
- `dataset/`, `data-source/` — sample datasets used for development and testing

## Quick Start (developer)

Prerequisites: Docker & Docker Compose, Python 3.8+ (for local development)

1. Start PostgreSQL (uses `postgres/docker-compose.yml`):

```powershell
cd postgres
docker compose up -d
```

2. Start Airflow (if you run locally using provided configs):

```powershell
cd airflow
# Follow your local airflow run instructions (docker-compose or native)
```

3. ML service (optional):

```powershell
cd ml
docker compose up -d
```

## ETL / DAGs

DAGs are under `airflow/dags/` and implement layered ETL: bronze ingestion, silver transform, gold star schema and platinum aggregates.

## Models & Inference

The trained models are in `models/`. See `ml/app` for a minimal API and `ml/README.md` for usage details.

## Notes

- This repo is structured for teaching and demonstration: expect sample data under `data-source/` and `dataset/`.
- Adjust credentials and connection strings (Postgres, Airflow connections) before running in a production environment.

## Data Sources
- **Source**: Kaggle  
- **Dataset name**: Walmart Recruiting – Store Sales Forecasting  
- **URL**: https://www.kaggle.com/c/walmart-recruiting-store-sales-forecasting/data  
- **Data type**: Structured data (CSV files)  
- **Domain**: Retail / Sales / Decision Support Systems  
- **Date**: from 2010-02-05 to 2012-10-26

## DataSet
`dataset/` — curated or preprocessed copies of datasets used for experiments and model training.

When testing or re-running ETL, update or point the ingestion DAGs to the files in `dataset/`.

## Documentation

- `docs/` — project documentation and data dictionaries. Notable files:
	- `docs/data-defination-ENG.md` — English data definitions
	- `docs/data-defination-VN.md` — Vietnamese data definitions
	- `docs/DW-datadefination.md` — data warehouse definitions and schema notes

Refer to the `docs/` folder for column definitions, business rules, and additional project notes before running transformations or using datasets for modelling.
---


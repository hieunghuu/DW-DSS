# Walmart DSS — ML API

FastAPI + scikit-learn app for sales forecasting and promotion optimization.
Reads from the **Silver layer** of the 4-layer Medallion DWH, with automatic
fallback to raw CSVs when the database is unavailable.

## Folder structure

```
ml/
├── app/
│   ├── main.py                   ← FastAPI entrypoint
│   ├── core/
│   │   ├── config.py             ← Settings (reads .env)
│   │   └── database.py           ← SQLAlchemy engine
│   ├── ml/
│   │   └── engine.py             ← Train / predict / optimize
│   ├── schemas/
│   │   └── schemas.py            ← Pydantic request/response models
│   ├── services/
│   │   └── data_loader.py        ← DB query + CSV fallback
│   └── api/routers/
│       ├── train.py              ← POST /train
│       ├── forecast.py           ← POST /forecast/sales
│       ├── promotion.py          ← GET|POST /promotion/*
│       ├── stores.py             ← GET /stores/*
│       └── analytics.py         ← GET /analytics/*
├── models/                       ← Persisted .joblib files (git-ignored)
├── .env                          ← DB connection (mirrors postgres/.env)
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Quick start

### 1 — Configure DB connection (.env already set)

```env
POSTGRES_HOST=host.docker.internal
POSTGRES_PORT=15432
POSTGRES_DB=walmart_dwh
POSTGRES_USER=dwadmin
POSTGRES_PASSWORD=hellofromtheotherside
```

### 2 — Mount CSV data (for fallback / first-time training)

```bash
mkdir -p ml/data
cp stores.csv features.csv train.csv ml/data/
```

### 3 — Build & run

```bash
cd ml
docker compose up --build
```

- API:     http://localhost:8000
- Swagger: http://localhost:8000/docs

### 4 — Train models (required before forecasting)

```bash
curl -X POST http://localhost:8000/api/v1/train
```

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/train` | Train both ML models |
| `GET`  | `/api/v1/train/status` | Model status & metrics |
| `POST` | `/api/v1/forecast/sales` | Predict weekly sales |
| `GET`  | `/api/v1/promotion/effectiveness` | Markdown ROI per store |
| `GET`  | `/api/v1/promotion/ranking` | Rank MarkDown1-5 by lift |
| `POST` | `/api/v1/promotion/optimize` | Best markdown allocation for budget |
| `GET`  | `/api/v1/stores` | All stores with KPIs |
| `GET`  | `/api/v1/stores/{id}/performance` | Per-department breakdown |
| `GET`  | `/api/v1/stores/compare?store_a=1&store_b=2` | Side-by-side comparison |
| `GET`  | `/api/v1/analytics/summary` | Executive KPIs |
| `GET`  | `/api/v1/analytics/top-departments` | Top revenue departments |
| `GET`  | `/api/v1/analytics/economic-impact` | CPI & unemployment vs sales |

## Example workflow

```bash
# Train
curl -X POST http://localhost:8000/api/v1/train

# Forecast
curl -X POST http://localhost:8000/api/v1/forecast/sales \
  -H "Content-Type: application/json" \
  -d '{"store_id":1,"department_id":1,"date":"2012-11-02","markdown1":5000,"is_holiday":false}'

# Optimize $10k budget
curl -X POST http://localhost:8000/api/v1/promotion/optimize \
  -H "Content-Type: application/json" \
  -d '{"store_id":1,"department_id":2,"budget":10000,"is_holiday":false}'
```

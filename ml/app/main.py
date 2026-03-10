from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.database import check_connection
from app.api.routers import forecast, promotion, stores, analytics, train

settings = get_settings()

app = FastAPI(
    title="Walmart DSS — ML & Promotion Optimization API",
    description="""
Decision Support System for evaluating and optimizing promotional strategies at Walmart.

## Workflow
1. **Train models** → `POST /api/v1/train`
2. **Forecast sales** → `POST /api/v1/forecast/sales`
3. **Analyze promotions** → `GET /api/v1/promotion/effectiveness`
4. **Optimize markdown spend** → `POST /api/v1/promotion/optimize`

## Data source
Reads from the **Silver layer** of the 4-layer Medallion architecture
(`silver.sales`, `silver.stores`, `silver.economic_features`).
Falls back to raw CSVs mounted at `DATA_DIR` when the database is unavailable.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────
PREFIX = "/api/v1"
app.include_router(train.router,      prefix=PREFIX)
app.include_router(forecast.router,   prefix=PREFIX)
app.include_router(promotion.router,  prefix=PREFIX)
app.include_router(stores.router,     prefix=PREFIX)
app.include_router(analytics.router,  prefix=PREFIX)


# ─── Health ───────────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
def health():
    db_ok = check_connection()
    return {
        "status": "ok",
        "env":    settings.api_env,
        "database": "connected" if db_ok else "unreachable (CSV fallback active)",
    }


@app.get("/", tags=["Health"])
def root():
    return {"message": "Walmart DSS ML API — visit /docs for Swagger UI"}

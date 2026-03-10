"""
ML Engine
─────────
Models
  • SalesForecaster   — RandomForestRegressor predicts weekly_sales
  • PromotionImpact   — Ridge regression estimates markdown → sales lift

Both models are persisted to MODEL_DIR via joblib and hot-loaded on startup.
"""
from __future__ import annotations

import os
import joblib
import numpy as np
import pandas as pd
from typing import Tuple

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

from app.core.config import get_settings

settings = get_settings()

_SALES_MODEL_PATH     = os.path.join(settings.model_dir, "sales_forecaster.joblib")
_PROMOTION_MODEL_PATH = os.path.join(settings.model_dir, "promotion_impact.joblib")

# Features used by each model
SALES_FEATURES = [
    "store_id", "department_id",
    "week_of_year", "month", "year", "quarter",
    "is_holiday",
    "temperature", "fuel_price",
    "markdown1", "markdown2", "markdown3", "markdown4", "markdown5",
    "cpi", "unemployment",
    "store_type", "store_size",
]

PROMOTION_FEATURES = [
    "markdown1", "markdown2", "markdown3", "markdown4", "markdown5",
    "is_holiday", "store_type_code",
]


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _ensure_model_dir() -> None:
    os.makedirs(settings.model_dir, exist_ok=True)


def _encode_store_type(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    type_map = {"A": 0, "B": 1, "C": 2}
    if "store_type" in df.columns:
        if df["store_type"].dtype == object:
            df["store_type"] = df["store_type"].map(type_map).fillna(0).astype(int)
    return df


def _prepare_sales_df(df: pd.DataFrame) -> pd.DataFrame:
    df = _encode_store_type(df)
    df["is_holiday"] = df["is_holiday"].astype(int)
    for col in SALES_FEATURES:
        if col not in df.columns:
            df[col] = 0
    return df[SALES_FEATURES]


def _prepare_promo_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    type_map = {"A": 0, "B": 1, "C": 2}
    if "store_type" in df.columns and df["store_type"].dtype == object:
        df["store_type_code"] = df["store_type"].map(type_map).fillna(0).astype(int)
    else:
        df["store_type_code"] = df.get("store_type", 0)
    df["is_holiday"] = df["is_holiday"].astype(int)
    for col in PROMOTION_FEATURES:
        if col not in df.columns:
            df[col] = 0
    return df[PROMOTION_FEATURES]


# ─── Training ─────────────────────────────────────────────────────────────────

def train_sales_model(df: pd.DataFrame) -> dict:
    """Train RandomForestRegressor on sales data. Returns eval metrics."""
    _ensure_model_dir()

    X = _prepare_sales_df(df)
    y = df["weekly_sales"].astype(float)

    # Drop rows with NaN in features
    mask = X.notna().all(axis=1) & y.notna()
    X, y = X[mask], y[mask]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=20,
        min_samples_leaf=4,
        n_jobs=-1,
        random_state=42,
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    metrics = {
        "mae": round(float(mean_absolute_error(y_test, y_pred)), 2),
        "r2":  round(float(r2_score(y_test, y_pred)), 4),
        "training_rows": len(X_train),
        "test_rows":     len(X_test),
    }

    joblib.dump({"model": model, "features": SALES_FEATURES, "metrics": metrics},
                _SALES_MODEL_PATH)
    print(f"[ML] Sales model saved → MAE={metrics['mae']}, R²={metrics['r2']}")
    return metrics


def train_promotion_model(df: pd.DataFrame) -> dict:
    """Train Ridge regression to estimate markdown → sales lift."""
    _ensure_model_dir()

    # Target: weekly_sales (we'll compute lift from baseline at inference time)
    X = _prepare_promo_df(df)
    y = df["weekly_sales"].astype(float)

    mask = X.notna().all(axis=1) & y.notna()
    X, y = X[mask], y[mask]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("ridge",  Ridge(alpha=1.0)),
    ])
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    metrics = {
        "mae": round(float(mean_absolute_error(y_test, y_pred)), 2),
        "r2":  round(float(r2_score(y_test, y_pred)), 4),
        "training_rows": len(X_train),
    }

    joblib.dump({"model": pipeline, "features": PROMOTION_FEATURES, "metrics": metrics},
                _PROMOTION_MODEL_PATH)
    print(f"[ML] Promotion model saved → MAE={metrics['mae']}, R²={metrics['r2']}")
    return metrics


# ─── Inference ────────────────────────────────────────────────────────────────

def _load_sales_model():
    if not os.path.exists(_SALES_MODEL_PATH):
        raise FileNotFoundError("Sales model not trained yet. POST /api/v1/train first.")
    return joblib.load(_SALES_MODEL_PATH)


def _load_promo_model():
    if not os.path.exists(_PROMOTION_MODEL_PATH):
        raise FileNotFoundError("Promotion model not trained yet. POST /api/v1/train first.")
    return joblib.load(_PROMOTION_MODEL_PATH)


def predict_sales(features: dict) -> float:
    """Predict weekly_sales for a single observation dict."""
    artifact = _load_sales_model()
    model = artifact["model"]

    row = pd.DataFrame([features])
    row = _prepare_sales_df(row)
    prediction = model.predict(row)[0]
    return round(float(prediction), 2)


def get_model_status() -> dict:
    status = {}
    for name, path in [
        ("sales_forecaster", _SALES_MODEL_PATH),
        ("promotion_impact", _PROMOTION_MODEL_PATH),
    ]:
        if os.path.exists(path):
            art = joblib.load(path)
            status[name] = {"trained": True, "metrics": art.get("metrics", {})}
        else:
            status[name] = {"trained": False}
    return status


def optimize_markdown_allocation(
    budget: float,
    store_id: int,
    department_id: int,
    is_holiday: bool,
    store_type: str,
) -> dict:
    """
    Grid-search the markdown allocation that maximises predicted sales
    under the given budget constraint.

    Strategy: try a handful of candidate distributions and pick the best.
    """
    artifact = _load_promo_model()
    model = artifact["model"]

    best_sales = -np.inf
    best_alloc = None
    store_type_code = {"A": 0, "B": 1, "C": 2}.get(store_type, 0)

    # Candidate weight distributions across 5 markdown slots
    distributions = [
        [1, 0, 0, 0, 0],
        [0, 1, 0, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 0, 1, 0],
        [0, 0, 0, 0, 1],
        [0.5, 0.5, 0, 0, 0],
        [0.4, 0.3, 0.2, 0.1, 0],
        [0.3, 0.3, 0.2, 0.1, 0.1],
        [0.2, 0.2, 0.2, 0.2, 0.2],
        [0.5, 0.2, 0.1, 0.1, 0.1],
        [0.1, 0.5, 0.2, 0.1, 0.1],
    ]

    for weights in distributions:
        md = [w * budget for w in weights]
        row = {
            "markdown1": md[0], "markdown2": md[1], "markdown3": md[2],
            "markdown4": md[3], "markdown5": md[4],
            "is_holiday": int(is_holiday),
            "store_type_code": store_type_code,
        }
        X = pd.DataFrame([row])[PROMOTION_FEATURES]
        pred = model.predict(X)[0]
        if pred > best_sales:
            best_sales = pred
            best_alloc = md

    # Baseline: no markdown
    baseline_row = {
        "markdown1": 0, "markdown2": 0, "markdown3": 0,
        "markdown4": 0, "markdown5": 0,
        "is_holiday": int(is_holiday),
        "store_type_code": store_type_code,
    }
    baseline = float(model.predict(pd.DataFrame([baseline_row])[PROMOTION_FEATURES])[0])
    projected = float(best_sales)
    lift = projected - baseline

    return {
        "markdown1": round(best_alloc[0], 2),
        "markdown2": round(best_alloc[1], 2),
        "markdown3": round(best_alloc[2], 2),
        "markdown4": round(best_alloc[3], 2),
        "markdown5": round(best_alloc[4], 2),
        "total":     round(sum(best_alloc), 2),
        "baseline_sales":  round(baseline, 2),
        "projected_sales": round(projected, 2),
        "sales_lift":      round(lift, 2),
        "roi": round(lift / budget, 4) if budget > 0 else 0,
    }

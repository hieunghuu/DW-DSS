"""
Loads training data from Silver layer tables.
Falls back to raw CSVs (mounted at DATA_DIR) when DB is unavailable.
"""
from __future__ import annotations

import os
import pandas as pd
import numpy as np
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import engine

settings = get_settings()


# ─── SQL queries against Silver layer ─────────────────────────────────────────

_SALES_QUERY = text("""
    SELECT
        s.store_id,
        s.department_id,
        s.date,
        s.weekly_sales,
        s.is_holiday,
        st.store_type,
        st.store_size,
        COALESCE(f.temperature, 60.0)    AS temperature,
        COALESCE(f.fuel_price, 3.0)      AS fuel_price,
        COALESCE(f.markdown1, 0)         AS markdown1,
        COALESCE(f.markdown2, 0)         AS markdown2,
        COALESCE(f.markdown3, 0)         AS markdown3,
        COALESCE(f.markdown4, 0)         AS markdown4,
        COALESCE(f.markdown5, 0)         AS markdown5,
        COALESCE(f.cpi, 210.0)           AS cpi,
        COALESCE(f.unemployment, 8.0)    AS unemployment
    FROM silver.sales s
    JOIN silver.stores st
        ON s.store_id = st.store_id AND st.is_current = TRUE
    LEFT JOIN silver.economic_features f
        ON s.store_id = f.store_id AND s.date = f.date
    ORDER BY s.store_id, s.department_id, s.date
""")

_FEATURES_QUERY = text("""
    SELECT
        ef.store_id,
        ef.date,
        ef.temperature,
        ef.fuel_price,
        ef.markdown1, ef.markdown2, ef.markdown3, ef.markdown4, ef.markdown5,
        ef.cpi,
        ef.unemployment,
        ef.is_holiday
    FROM silver.economic_features ef
    ORDER BY ef.store_id, ef.date
""")

_PROMOTION_QUERY = text("""
    SELECT
        s.store_id,
        s.department_id,
        s.date,
        s.weekly_sales,
        s.is_holiday,
        st.store_type,
        COALESCE(f.markdown1, 0) AS markdown1,
        COALESCE(f.markdown2, 0) AS markdown2,
        COALESCE(f.markdown3, 0) AS markdown3,
        COALESCE(f.markdown4, 0) AS markdown4,
        COALESCE(f.markdown5, 0) AS markdown5
    FROM silver.sales s
    JOIN silver.stores st
        ON s.store_id = st.store_id AND st.is_current = TRUE
    LEFT JOIN silver.economic_features f
        ON s.store_id = f.store_id AND s.date = f.date
""")


def _table_exists(schema: str, table: str) -> bool:
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT to_regclass(:name) IS NOT NULL AS exists"
            ),
            {"name": f"{schema}.{table}"},
        ).scalar()
    return bool(result)


def load_training_data() -> pd.DataFrame:
    """Return enriched sales DataFrame for model training."""
    try:
        if _table_exists("silver", "sales"):
            with engine.connect() as conn:
                df = pd.read_sql(_SALES_QUERY, conn)
            if len(df) > 100:
                return _add_date_features(df)
    except Exception as exc:
        print(f"[DataLoader] DB query failed ({exc}), falling back to CSV.")

    return _load_from_csv()


def load_promotion_data() -> pd.DataFrame:
    """Return promotion + sales DataFrame for ROI analysis."""
    try:
        if _table_exists("silver", "sales"):
            with engine.connect() as conn:
                df = pd.read_sql(_PROMOTION_QUERY, conn)
            if len(df) > 100:
                return df
    except Exception as exc:
        print(f"[DataLoader] Promotion query failed ({exc}), falling back to CSV.")

    return _load_promotion_from_csv()


# ─── CSV fallback ─────────────────────────────────────────────────────────────

def _load_from_csv() -> pd.DataFrame:
    data_dir = settings.data_dir
    sales_path    = os.path.join(data_dir, "train.csv")
    features_path = os.path.join(data_dir, "features.csv")
    stores_path   = os.path.join(data_dir, "stores.csv")

    sales = pd.read_csv(sales_path)
    features = pd.read_csv(features_path)
    stores = pd.read_csv(stores_path)

    # Normalise column names to lowercase
    sales.columns    = [c.lower() for c in sales.columns]
    features.columns = [c.lower() for c in features.columns]
    stores.columns   = [c.lower() for c in stores.columns]

    sales = sales.rename(columns={"dept": "department_id", "isholiday": "is_holiday"})
    features = features.rename(columns={"isholiday": "is_holiday"})
    stores = stores.rename(columns={"type": "store_type", "size": "store_size"})

    # Fill NaN markdowns with 0
    md_cols = ["markdown1", "markdown2", "markdown3", "markdown4", "markdown5"]
    for col in md_cols:
        if col in features.columns:
            features[col] = pd.to_numeric(features[col], errors="coerce").fillna(0)

    df = (
        sales
        .merge(stores, on="store", how="left")
        .merge(
            features[["store", "date"] + md_cols + ["temperature", "fuel_price", "cpi", "unemployment"]],
            on=["store", "date"],
            how="left",
        )
        .rename(columns={"store": "store_id"})
    )

    for col in ["temperature", "fuel_price", "cpi", "unemployment"]:
        df[col] = df[col].fillna(df[col].median())

    df["store_type"] = df["store_type"].astype("category").cat.codes
    df["date"] = pd.to_datetime(df["date"])
    return _add_date_features(df)


def _load_promotion_from_csv() -> pd.DataFrame:
    data_dir = settings.data_dir
    sales    = pd.read_csv(os.path.join(data_dir, "train.csv"))
    features = pd.read_csv(os.path.join(data_dir, "features.csv"))
    stores   = pd.read_csv(os.path.join(data_dir, "stores.csv"))

    sales.columns    = [c.lower() for c in sales.columns]
    features.columns = [c.lower() for c in features.columns]
    stores.columns   = [c.lower() for c in stores.columns]

    sales    = sales.rename(columns={"dept": "department_id", "isholiday": "is_holiday"})
    features = features.rename(columns={"isholiday": "is_holiday"})
    stores   = stores.rename(columns={"type": "store_type"})

    md_cols = ["markdown1", "markdown2", "markdown3", "markdown4", "markdown5"]
    for col in md_cols:
        if col in features.columns:
            features[col] = pd.to_numeric(features[col], errors="coerce").fillna(0)

    df = (
        sales
        .merge(stores[["store", "store_type"]], on="store", how="left")
        .merge(features[["store", "date"] + md_cols], on=["store", "date"], how="left")
        .rename(columns={"store": "store_id"})
    )
    for col in md_cols:
        df[col] = df[col].fillna(0)
    return df


# ─── Feature engineering ──────────────────────────────────────────────────────

def _add_date_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df["week_of_year"] = df["date"].dt.isocalendar().week.astype(int)
    df["month"]        = df["date"].dt.month
    df["year"]         = df["date"].dt.year
    df["quarter"]      = df["date"].dt.quarter
    return df

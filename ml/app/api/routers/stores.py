from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text

from app.core.database import engine, check_connection
from app.services.data_loader import load_training_data

router = APIRouter(prefix="/stores", tags=["Stores"])


@router.get("", summary="List all stores with aggregated performance")
def list_stores():
    _QUERY = text("""
        SELECT
            st.store_id,
            st.store_type,
            st.store_size,
            ROUND(SUM(s.weekly_sales)::numeric, 2)      AS total_sales,
            ROUND(AVG(s.weekly_sales)::numeric, 2)      AS avg_weekly_sales,
            COUNT(DISTINCT s.department_id)             AS active_departments,
            COUNT(DISTINCT s.date)                      AS weeks_recorded
        FROM silver.stores st
        JOIN silver.sales s ON st.store_id = s.store_id
        WHERE st.is_current = TRUE
        GROUP BY st.store_id, st.store_type, st.store_size
        ORDER BY total_sales DESC
    """)

    try:
        if check_connection():
            with engine.connect() as conn:
                rows = conn.execute(_QUERY).mappings().all()
            return {"source": "database", "data": [dict(r) for r in rows]}
    except Exception as exc:
        print(f"[stores] DB failed: {exc}")

    # CSV fallback
    df = load_training_data()
    result = (
        df.groupby(["store_id", "store_type", "store_size"])
        .agg(
            total_sales=("weekly_sales", "sum"),
            avg_weekly_sales=("weekly_sales", "mean"),
            active_departments=("department_id", "nunique"),
            weeks_recorded=("date", "nunique"),
        )
        .reset_index()
        .sort_values("total_sales", ascending=False)
    )
    result["total_sales"]       = result["total_sales"].round(2)
    result["avg_weekly_sales"]  = result["avg_weekly_sales"].round(2)
    return {"source": "csv_fallback", "data": result.to_dict(orient="records")}


@router.get("/{store_id}/performance", summary="Deep-dive metrics for a single store")
def store_performance(store_id: int):
    _QUERY = text("""
        SELECT
            s.department_id,
            ROUND(SUM(s.weekly_sales)::numeric, 2)    AS total_sales,
            ROUND(AVG(s.weekly_sales)::numeric, 2)    AS avg_weekly_sales,
            ROUND(MAX(s.weekly_sales)::numeric, 2)    AS max_weekly_sales,
            ROUND(MIN(s.weekly_sales)::numeric, 2)    AS min_weekly_sales,
            SUM(CASE WHEN s.is_holiday THEN 1 ELSE 0 END) AS holiday_weeks,
            ROUND(AVG(CASE WHEN s.is_holiday THEN s.weekly_sales END)::numeric, 2) AS avg_holiday_sales,
            ROUND(AVG(CASE WHEN NOT s.is_holiday THEN s.weekly_sales END)::numeric, 2) AS avg_normal_sales
        FROM silver.sales s
        WHERE s.store_id = :sid
        GROUP BY s.department_id
        ORDER BY total_sales DESC
    """)

    try:
        if check_connection():
            with engine.connect() as conn:
                rows = conn.execute(_QUERY, {"sid": store_id}).mappings().all()
            if not rows:
                raise HTTPException(status_code=404, detail=f"Store {store_id} not found")
            return {"store_id": store_id, "source": "database", "departments": [dict(r) for r in rows]}
    except HTTPException:
        raise
    except Exception as exc:
        print(f"[stores/{store_id}] DB failed: {exc}")

    df = load_training_data()
    store_df = df[df["store_id"] == store_id]
    if store_df.empty:
        raise HTTPException(status_code=404, detail=f"Store {store_id} not found")

    result = (
        store_df.groupby("department_id")
        .agg(
            total_sales=("weekly_sales", "sum"),
            avg_weekly_sales=("weekly_sales", "mean"),
            max_weekly_sales=("weekly_sales", "max"),
            min_weekly_sales=("weekly_sales", "min"),
        )
        .reset_index()
        .sort_values("total_sales", ascending=False)
    )
    return {"store_id": store_id, "source": "csv_fallback", "departments": result.to_dict(orient="records")}


@router.get("/compare", summary="Compare two stores side-by-side")
def compare_stores(
    store_a: int = Query(..., ge=1, le=45),
    store_b: int = Query(..., ge=1, le=45),
):
    df = load_training_data()

    def _metrics(sid):
        s = df[df["store_id"] == sid]
        if s.empty:
            return None
        return {
            "store_id":         sid,
            "total_sales":      round(float(s["weekly_sales"].sum()), 2),
            "avg_weekly_sales": round(float(s["weekly_sales"].mean()), 2),
            "num_departments":  int(s["department_id"].nunique()),
            "store_type":       s["store_type"].iloc[0] if "store_type" in s.columns else "N/A",
            "store_size":       int(s["store_size"].iloc[0]) if "store_size" in s.columns else 0,
        }

    a = _metrics(store_a)
    b = _metrics(store_b)
    if not a:
        raise HTTPException(status_code=404, detail=f"Store {store_a} not found")
    if not b:
        raise HTTPException(status_code=404, detail=f"Store {store_b} not found")

    return {
        "store_a": a,
        "store_b": b,
        "comparison": {
            "sales_diff":     round(a["total_sales"] - b["total_sales"], 2),
            "sales_diff_pct": round((a["total_sales"] - b["total_sales"]) / max(b["total_sales"], 1) * 100, 2),
        }
    }

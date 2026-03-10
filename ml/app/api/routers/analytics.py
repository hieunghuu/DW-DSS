from fastapi import APIRouter, Query
from sqlalchemy import text

from app.core.database import engine, check_connection
from app.services.data_loader import load_training_data, load_promotion_data

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary", summary="Executive KPI summary")
def summary():
    """Overall dataset KPIs: total sales, store count, holiday lift, etc."""
    _QUERY = text("""
        SELECT
            COUNT(DISTINCT s.store_id)                              AS num_stores,
            COUNT(DISTINCT s.department_id)                         AS num_departments,
            COUNT(DISTINCT s.date)                                  AS num_weeks,
            ROUND(SUM(s.weekly_sales)::numeric, 2)                  AS total_sales,
            ROUND(AVG(s.weekly_sales)::numeric, 2)                  AS avg_weekly_sales,
            ROUND(AVG(CASE WHEN s.is_holiday THEN s.weekly_sales END)::numeric, 2)     AS avg_holiday_sales,
            ROUND(AVG(CASE WHEN NOT s.is_holiday THEN s.weekly_sales END)::numeric, 2) AS avg_normal_sales,
            ROUND(
                (AVG(CASE WHEN s.is_holiday THEN s.weekly_sales END) -
                 AVG(CASE WHEN NOT s.is_holiday THEN s.weekly_sales END)) /
                NULLIF(AVG(CASE WHEN NOT s.is_holiday THEN s.weekly_sales END), 0) * 100
            ::numeric, 2)                                           AS holiday_lift_pct
        FROM silver.sales s
    """)

    try:
        if check_connection():
            with engine.connect() as conn:
                row = conn.execute(_QUERY).mappings().fetchone()
            return {"source": "database", "kpis": dict(row)}
    except Exception as exc:
        print(f"[analytics/summary] DB failed: {exc}")

    df = load_training_data()
    holiday_avg = df[df["is_holiday"] == True]["weekly_sales"].mean()
    normal_avg  = df[df["is_holiday"] == False]["weekly_sales"].mean()
    lift_pct = (holiday_avg - normal_avg) / normal_avg * 100 if normal_avg else 0

    return {
        "source": "csv_fallback",
        "kpis": {
            "num_stores":        int(df["store_id"].nunique()),
            "num_departments":   int(df["department_id"].nunique()),
            "num_weeks":         int(df["date"].nunique()) if "date" in df.columns else 0,
            "total_sales":       round(float(df["weekly_sales"].sum()), 2),
            "avg_weekly_sales":  round(float(df["weekly_sales"].mean()), 2),
            "avg_holiday_sales": round(float(holiday_avg), 2),
            "avg_normal_sales":  round(float(normal_avg), 2),
            "holiday_lift_pct":  round(float(lift_pct), 2),
        }
    }


@router.get("/top-departments", summary="Highest revenue departments")
def top_departments(limit: int = Query(10, ge=1, le=99)):
    _QUERY = text("""
        SELECT
            department_id,
            ROUND(SUM(weekly_sales)::numeric, 2)  AS total_sales,
            ROUND(AVG(weekly_sales)::numeric, 2)  AS avg_weekly_sales,
            COUNT(DISTINCT store_id)              AS num_stores
        FROM silver.sales
        GROUP BY department_id
        ORDER BY total_sales DESC
        LIMIT :limit
    """)

    try:
        if check_connection():
            with engine.connect() as conn:
                rows = conn.execute(_QUERY, {"limit": limit}).mappings().all()
            return {"source": "database", "data": [dict(r) for r in rows]}
    except Exception as exc:
        print(f"[analytics/top-departments] DB failed: {exc}")

    df = load_training_data()
    result = (
        df.groupby("department_id")
        .agg(
            total_sales=("weekly_sales", "sum"),
            avg_weekly_sales=("weekly_sales", "mean"),
            num_stores=("store_id", "nunique"),
        )
        .reset_index()
        .sort_values("total_sales", ascending=False)
        .head(limit)
    )
    result["total_sales"]      = result["total_sales"].round(2)
    result["avg_weekly_sales"] = result["avg_weekly_sales"].round(2)
    return {"source": "csv_fallback", "data": result.to_dict(orient="records")}


@router.get("/economic-impact", summary="Correlation: CPI & unemployment vs sales")
def economic_impact():
    """
    Bucketed analysis showing how CPI and unemployment levels
    correlate with average weekly sales.
    """
    df = load_training_data()

    if "cpi" not in df.columns or "unemployment" not in df.columns:
        return {"error": "Economic features not available in training data"}

    df = df.dropna(subset=["cpi", "unemployment", "weekly_sales"])

    # CPI buckets
    df["cpi_band"] = df["cpi"].apply(
        lambda x: "Low(<200)" if x < 200 else "Moderate(200-220)" if x <= 220 else "High(>220)"
    )
    # Unemployment buckets
    df["unemp_band"] = df["unemployment"].apply(
        lambda x: "Low(<5%)" if x < 5 else "Medium(5-8%)" if x <= 8 else "High(>8%)"
    )

    cpi_impact = (
        df.groupby("cpi_band")["weekly_sales"]
        .agg(avg_sales="mean", records="count")
        .reset_index()
        .sort_values("avg_sales", ascending=False)
        .to_dict(orient="records")
    )
    unemp_impact = (
        df.groupby("unemp_band")["weekly_sales"]
        .agg(avg_sales="mean", records="count")
        .reset_index()
        .sort_values("avg_sales", ascending=False)
        .to_dict(orient="records")
    )

    return {
        "cpi_impact":          cpi_impact,
        "unemployment_impact": unemp_impact,
    }

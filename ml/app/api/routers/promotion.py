from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text
import pandas as pd

from app.core.database import engine, check_connection
from app.schemas.schemas import PromotionOptimizeRequest, PromotionOptimizeResponse, MarkdownAllocation
from app.ml.engine import optimize_markdown_allocation
from app.services.data_loader import load_promotion_data

router = APIRouter(prefix="/promotion", tags=["Promotion"])


@router.get("/effectiveness", summary="Markdown ROI by store and type")
def promotion_effectiveness(
    store_id: int | None = Query(None, ge=1, le=45, description="Filter by store"),
    store_type: str | None = Query(None, regex="^[ABC]$", description="Filter by store type A/B/C"),
    limit: int = Query(50, ge=1, le=200),
):
    """
    Returns aggregated markdown spend vs sales for each store.
    Computes a simple ROI = total_sales / total_markdown_spend.

    Pulls from the Silver layer when available, otherwise from CSVs.
    """
    _QUERY = text("""
        SELECT
            s.store_id,
            st.store_type,
            ROUND(SUM(s.weekly_sales)::numeric, 2)          AS total_sales,
            ROUND(COALESCE(SUM(f.markdown1),0)::numeric, 2) AS total_md1,
            ROUND(COALESCE(SUM(f.markdown2),0)::numeric, 2) AS total_md2,
            ROUND(COALESCE(SUM(f.markdown3),0)::numeric, 2) AS total_md3,
            ROUND(COALESCE(SUM(f.markdown4),0)::numeric, 2) AS total_md4,
            ROUND(COALESCE(SUM(f.markdown5),0)::numeric, 2) AS total_md5,
            ROUND((
                COALESCE(SUM(f.markdown1),0) +
                COALESCE(SUM(f.markdown2),0) +
                COALESCE(SUM(f.markdown3),0) +
                COALESCE(SUM(f.markdown4),0) +
                COALESCE(SUM(f.markdown5),0)
            )::numeric, 2) AS total_markdown,
            ROUND(
                SUM(s.weekly_sales) /
                NULLIF(
                    COALESCE(SUM(f.markdown1),0) +
                    COALESCE(SUM(f.markdown2),0) +
                    COALESCE(SUM(f.markdown3),0) +
                    COALESCE(SUM(f.markdown4),0) +
                    COALESCE(SUM(f.markdown5),0), 0
                )::numeric, 4
            ) AS roi
        FROM silver.sales s
        JOIN silver.stores st ON s.store_id = st.store_id AND st.is_current = TRUE
        LEFT JOIN silver.economic_features f ON s.store_id = f.store_id AND s.date = f.date
        WHERE (:store_id IS NULL OR s.store_id = :store_id)
          AND (:store_type IS NULL OR st.store_type = :store_type)
        GROUP BY s.store_id, st.store_type
        ORDER BY total_sales DESC
        LIMIT :limit
    """)

    try:
        if check_connection():
            with engine.connect() as conn:
                rows = conn.execute(
                    _QUERY,
                    {"store_id": store_id, "store_type": store_type, "limit": limit}
                ).mappings().all()
            return {"source": "database", "data": [dict(r) for r in rows]}
    except Exception as exc:
        print(f"[promotion/effectiveness] DB failed: {exc}, falling back to CSV")

    # ── CSV fallback ──────────────────────────────────────────────────────────
    df = load_promotion_data()
    if store_id:
        df = df[df["store_id"] == store_id]
    if store_type:
        df = df[df["store_type"] == store_type]

    md_cols = ["markdown1", "markdown2", "markdown3", "markdown4", "markdown5"]
    df["total_markdown"] = df[md_cols].sum(axis=1)

    grouped = (
        df.groupby(["store_id", "store_type"])
        .agg(
            total_sales=("weekly_sales", "sum"),
            total_md1=("markdown1", "sum"),
            total_md2=("markdown2", "sum"),
            total_md3=("markdown3", "sum"),
            total_md4=("markdown4", "sum"),
            total_md5=("markdown5", "sum"),
            total_markdown=("total_markdown", "sum"),
        )
        .reset_index()
    )
    grouped["roi"] = (grouped["total_sales"] / grouped["total_markdown"].replace(0, float("nan"))).round(4)
    grouped = grouped.sort_values("total_sales", ascending=False).head(limit)
    return {"source": "csv_fallback", "data": grouped.to_dict(orient="records")}


@router.get("/ranking", summary="Rank markdown types by sales impact")
def markdown_ranking():
    """
    Compute average weekly sales for weeks WITH vs WITHOUT each markdown type,
    and derive the average lift per markdown.
    """
    df = load_promotion_data()
    md_cols = ["markdown1", "markdown2", "markdown3", "markdown4", "markdown5"]
    results = []

    for i, col in enumerate(md_cols, 1):
        has_md  = df[df[col] > 0]["weekly_sales"]
        no_md   = df[df[col] == 0]["weekly_sales"]
        avg_with    = round(float(has_md.mean()),   2) if len(has_md) else 0
        avg_without = round(float(no_md.mean()),    2) if len(no_md)  else 0
        lift_pct    = round((avg_with - avg_without) / max(avg_without, 1) * 100, 2)
        results.append({
            "markdown_type":  f"MarkDown{i}",
            "weeks_active":   int(len(has_md)),
            "avg_sales_with_markdown":    avg_with,
            "avg_sales_without_markdown": avg_without,
            "avg_sales_lift_pct":         lift_pct,
        })

    results.sort(key=lambda x: x["avg_sales_lift_pct"], reverse=True)
    return {"data": results}


@router.post(
    "/optimize",
    response_model=PromotionOptimizeResponse,
    summary="Recommend optimal markdown allocation for a given budget",
)
def optimize_promotion(req: PromotionOptimizeRequest):
    """
    Given a total markdown budget, returns the markdown allocation
    (across MarkDown1–5) that maximises predicted weekly sales for
    the specified store and department.
    """
    # Derive store_type from DB or default to A
    store_type = "A"
    try:
        if check_connection():
            with engine.connect() as conn:
                row = conn.execute(
                    text("SELECT store_type FROM silver.stores WHERE store_id=:sid AND is_current=TRUE"),
                    {"sid": req.store_id},
                ).fetchone()
                if row:
                    store_type = row[0]
    except Exception:
        pass

    try:
        result = optimize_markdown_allocation(
            budget=req.budget,
            store_id=req.store_id,
            department_id=req.department_id,
            is_holiday=req.is_holiday,
            store_type=store_type,
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))

    allocation = MarkdownAllocation(
        markdown1=result["markdown1"],
        markdown2=result["markdown2"],
        markdown3=result["markdown3"],
        markdown4=result["markdown4"],
        markdown5=result["markdown5"],
        total=result["total"],
        estimated_sales_lift=result["sales_lift"],
    )

    return PromotionOptimizeResponse(
        store_id=req.store_id,
        department_id=req.department_id,
        budget=req.budget,
        recommended_allocation=allocation,
        baseline_sales=result["baseline_sales"],
        projected_sales=result["projected_sales"],
        projected_roi=result["roi"],
    )

from fastapi import APIRouter, HTTPException
from datetime import datetime

from app.schemas.schemas import ForecastRequest, ForecastResponse
from app.ml.engine import predict_sales

router = APIRouter(prefix="/forecast", tags=["Forecasting"])


@router.post(
    "/sales",
    response_model=ForecastResponse,
    summary="Predict weekly sales for a store/department",
)
def forecast_sales(req: ForecastRequest):
    """
    Predict `weekly_sales` using the trained RandomForest model.

    Provide store, department, week date, and optional economic/promotion context.
    Economic fields default to dataset medians when omitted.
    """
    try:
        dt = datetime.strptime(req.date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=422, detail="date must be YYYY-MM-DD")

    features = {
        "store_id":      req.store_id,
        "department_id": req.department_id,
        "week_of_year":  dt.isocalendar()[1],
        "month":         dt.month,
        "year":          dt.year,
        "quarter":       (dt.month - 1) // 3 + 1,
        "is_holiday":    int(req.is_holiday),
        "temperature":   req.temperature if req.temperature is not None else 60.0,
        "fuel_price":    req.fuel_price  if req.fuel_price  is not None else 3.0,
        "markdown1":     req.markdown1,
        "markdown2":     req.markdown2,
        "markdown3":     req.markdown3,
        "markdown4":     req.markdown4,
        "markdown5":     req.markdown5,
        "cpi":           req.cpi          if req.cpi          is not None else 211.0,
        "unemployment":  req.unemployment if req.unemployment is not None else 8.0,
        # store_type / store_size default to 0 when not supplied at request time
        "store_type":  0,
        "store_size":  150000,
    }

    try:
        prediction = predict_sales(features)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {e}")

    return ForecastResponse(
        store_id=req.store_id,
        department_id=req.department_id,
        date=req.date,
        predicted_sales=prediction,
        model_version="sales_forecaster_v1",
    )

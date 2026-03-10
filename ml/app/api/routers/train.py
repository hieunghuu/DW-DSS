from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from app.ml.engine import train_sales_model, train_promotion_model, get_model_status
from app.services.data_loader import load_training_data, load_promotion_data

router = APIRouter(prefix="/train", tags=["Training"])


class TrainResponse(BaseModel):
    status: str
    sales_model: dict
    promotion_model: dict


@router.post("", response_model=TrainResponse, summary="Train all ML models")
def train_all():
    """
    Load data from Silver layer (or CSV fallback) and train:
    - `sales_forecaster`   — RandomForest for weekly sales prediction
    - `promotion_impact`   — Ridge regression for markdown → sales lift
    """
    try:
        sales_df = load_training_data()
        if len(sales_df) < 100:
            raise HTTPException(
                status_code=422,
                detail="Not enough training data. Make sure CSVs are mounted at DATA_DIR.",
            )
        sales_metrics = train_sales_model(sales_df)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Sales model training failed: {exc}")

    try:
        promo_df = load_promotion_data()
        promo_metrics = train_promotion_model(promo_df)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Promotion model training failed: {exc}")

    return TrainResponse(
        status="success",
        sales_model=sales_metrics,
        promotion_model=promo_metrics,
    )


@router.get("/status", summary="Check model training status")
def model_status():
    """Returns training status and evaluation metrics for each model."""
    return get_model_status()

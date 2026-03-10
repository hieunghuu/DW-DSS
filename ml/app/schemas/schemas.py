from pydantic import BaseModel, Field
from typing import Optional


# ─── Forecast ─────────────────────────────────────────────────────────────────

class ForecastRequest(BaseModel):
    store_id: int = Field(..., ge=1, le=45, example=1)
    department_id: int = Field(..., ge=1, le=99, example=1)
    date: str = Field(..., example="2012-11-02",
                      description="Week ending date (YYYY-MM-DD)")
    temperature: Optional[float] = Field(None, example=55.0)
    fuel_price: Optional[float] = Field(None, example=3.25)
    markdown1: float = Field(0.0, ge=0, example=5000.0)
    markdown2: float = Field(0.0, ge=0, example=0.0)
    markdown3: float = Field(0.0, ge=0, example=0.0)
    markdown4: float = Field(0.0, ge=0, example=0.0)
    markdown5: float = Field(0.0, ge=0, example=0.0)
    cpi: Optional[float] = Field(None, example=211.5)
    unemployment: Optional[float] = Field(None, example=8.1)
    is_holiday: bool = Field(False, example=False)


class ForecastResponse(BaseModel):
    store_id: int
    department_id: int
    date: str
    predicted_sales: float
    model_version: str


# ─── Promotion ────────────────────────────────────────────────────────────────

class PromotionOptimizeRequest(BaseModel):
    store_id: int = Field(..., ge=1, le=45, example=1)
    department_id: int = Field(..., ge=1, le=99, example=1)
    budget: float = Field(..., gt=0, example=10000.0,
                          description="Total markdown budget in USD")
    is_holiday: bool = Field(False)


class MarkdownAllocation(BaseModel):
    markdown1: float
    markdown2: float
    markdown3: float
    markdown4: float
    markdown5: float
    total: float
    estimated_sales_lift: float


class PromotionOptimizeResponse(BaseModel):
    store_id: int
    department_id: int
    budget: float
    recommended_allocation: MarkdownAllocation
    baseline_sales: float
    projected_sales: float
    projected_roi: float

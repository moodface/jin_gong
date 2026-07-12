from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DashboardData(BaseModel):
    total_gmv: float
    gmv_trend: list
    platform_traffic: list
    competitor_prices: list
    sentiment_trend: list
    alert_count: int
    update_time: str


class ReportRequest(BaseModel):
    report_type: str = "daily"


class ReportResponse(BaseModel):
    content: str
    generated_time: str


class MonitorItem(BaseModel):
    id: int
    brand: str
    platform: str
    product_name: str
    price: float
    promo_info: str
    rating: float
    review_count: int


class SentimentItem(BaseModel):
    keyword: str
    platform: str
    mention_count: int
    positive_ratio: float
    negative_ratio: float
    neutral_ratio: float


class AlertInfo(BaseModel):
    type: str
    message: str
    severity: str
    time: str


class ScrapeTask(BaseModel):
    id: int
    platform: str
    status: str
    start_time: Optional[str]
    end_time: Optional[str]
    records_fetched: int
    error_msg: Optional[str]

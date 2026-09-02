import datetime

from pydantic import BaseModel, ConfigDict


class RecommendationBlock(BaseModel):
    treatment: str
    prevention: str
    urgency_note: str | None = None


class ScanResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    scan_uuid: str
    crop_name: str
    disease_code: str
    disease_display_name: str
    confidence: float
    infected_area_pct: float
    severity: str
    original_image_url: str
    overlay_image_url: str
    report_id: str
    model_status: str | None = None
    prediction_warning: str | None = None
    recommendations: RecommendationBlock
    created_at: datetime.datetime


class ScanSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    scan_uuid: str
    crop_name: str
    disease_display_name: str
    confidence: float
    infected_area_pct: float
    severity: str
    overlay_image_url: str
    prediction_warning: str | None = None
    created_at: datetime.datetime


class PaginatedScans(BaseModel):
    items: list[ScanSummary]
    total: int
    page: int
    page_size: int

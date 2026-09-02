from pydantic import BaseModel


class BreakdownItem(BaseModel):
    label: str
    count: int


class TrendPoint(BaseModel):
    date: str
    count: int


class DashboardStatsResponse(BaseModel):
    total_scans: int
    severity_breakdown: list[BreakdownItem]
    crop_breakdown: list[BreakdownItem]
    trend_over_time: list[TrendPoint]
    most_common_diseases: list[BreakdownItem]

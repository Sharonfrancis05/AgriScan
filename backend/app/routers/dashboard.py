import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.dashboard import DashboardStatsResponse
from app.services.scan_service import get_dashboard_stats

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStatsResponse)
def dashboard_stats(
    date_from: datetime.date | None = Query(default=None),
    date_to: datetime.date | None = Query(default=None),
    db: Session = Depends(get_db),
) -> DashboardStatsResponse:
    return get_dashboard_stats(db, date_from, date_to)

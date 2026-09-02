import datetime

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from sqlalchemy.orm import Session

from app.core.constants import SEVERITY_LEVELS, SUPPORTED_CROPS
from app.db.session import get_db
from app.schemas.scan import PaginatedScans, ScanResultResponse
from app.services import scan_service

router = APIRouter(prefix="/api/scans", tags=["scans"])

_MAX_UPLOAD_BYTES = 15 * 1024 * 1024  # 15 MB


@router.post("", response_model=ScanResultResponse)
async def submit_scan(
    request: Request,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ScanResultResponse:
    if image.content_type not in ("image/jpeg", "image/png", "image/webp"):
        raise HTTPException(status_code=415, detail="Only JPEG, PNG, or WEBP images are supported.")

    image_bytes = await image.read()
    if len(image_bytes) > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image exceeds the 15MB upload limit.")
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded image is empty.")

    inference_service = request.app.state.inference_service
    return scan_service.create_scan(db, image_bytes, inference_service)


@router.get("", response_model=PaginatedScans)
def list_scans(
    crop: str | None = Query(default=None, description=f"One of {SUPPORTED_CROPS}"),
    severity: str | None = Query(default=None, description=f"One of {SEVERITY_LEVELS}"),
    date_from: datetime.date | None = Query(default=None),
    date_to: datetime.date | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PaginatedScans:
    return scan_service.list_scans(db, crop, severity, date_from, date_to, page, page_size)


@router.get("/{scan_uuid}", response_model=ScanResultResponse)
def get_scan(scan_uuid: str, db: Session = Depends(get_db)) -> ScanResultResponse:
    result = scan_service.get_scan_detail(db, scan_uuid)
    if result is None:
        raise HTTPException(status_code=404, detail="Scan not found.")
    return result

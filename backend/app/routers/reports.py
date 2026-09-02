from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.report_service import get_report_by_id

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("/{report_id}/download")
def download_report(report_id: str, db: Session = Depends(get_db)) -> FileResponse:
    report = get_report_by_id(db, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found.")

    return FileResponse(
        path=report.pdf_path,
        media_type="application/pdf",
        filename=f"{report.report_id}.pdf",
    )

import datetime

from sqlalchemy.orm import Session

from app.models.report import Report
from app.models.scan import Scan
from app.pdf.report_template import ReportData, generate_report_pdf
from app.schemas.scan import RecommendationBlock
from app.utils.file_storage import report_pdf_path
from app.utils.id_generator import generate_report_id


def create_report(
    db: Session,
    scan: Scan,
    recommendations: RecommendationBlock,
    model_status: str,
    segmentation_backend: str,
) -> Report:
    report_id = generate_report_id()
    # Extremely unlikely, but guard against the (hex-suffix) collision anyway.
    while db.query(Report).filter_by(report_id=report_id).first() is not None:
        report_id = generate_report_id()

    pdf_path = report_pdf_path(report_id)
    generate_report_pdf(
        pdf_path,
        ReportData(
            report_id=report_id,
            scan_uuid=scan.scan_uuid,
            original_image_path=scan.original_image_path,
            overlay_image_path=scan.overlay_image_path,
            crop_name=scan.crop_name,
            disease_display_name=scan.disease_display_name,
            confidence=scan.confidence,
            infected_area_pct=scan.infected_area_pct,
            severity=scan.severity,
            treatment_text=recommendations.treatment,
            prevention_text=recommendations.prevention,
            urgency_note=recommendations.urgency_note,
            model_status=model_status,
            segmentation_backend=segmentation_backend,
            prediction_warning=scan.prediction_warning,
            scanned_at=scan.created_at or datetime.datetime.now(datetime.timezone.utc),
        ),
    )

    report = Report(report_id=report_id, scan_id=scan.id, pdf_path=str(pdf_path))
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def get_report_by_id(db: Session, report_id: str) -> Report | None:
    return db.query(Report).filter_by(report_id=report_id).first()

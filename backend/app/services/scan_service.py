import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.disease_reference import DiseaseReference
from app.models.report import Report
from app.models.scan import Scan
from app.schemas.dashboard import BreakdownItem, DashboardStatsResponse, TrendPoint
from app.schemas.scan import PaginatedScans, RecommendationBlock, ScanResultResponse, ScanSummary
from app.services.inference_service import InferenceService
from app.services.recommendation_service import get_recommendations
from app.services.report_service import create_report
from app.utils.file_storage import new_scan_uuid, save_overlay_image, save_upload_image


def _image_url(scan_uuid: str, filename: str) -> str:
    return f"/static/uploads/{scan_uuid}/{filename}"


def _to_result_response(
    db: Session, scan: Scan, report: Report, recommendations: RecommendationBlock
) -> ScanResultResponse:
    return ScanResultResponse(
        scan_uuid=scan.scan_uuid,
        crop_name=scan.crop_name,
        disease_code=scan.disease_code,
        disease_display_name=scan.disease_display_name,
        confidence=scan.confidence,
        infected_area_pct=scan.infected_area_pct,
        severity=scan.severity,
        original_image_url=_image_url(scan.scan_uuid, "original.jpg"),
        overlay_image_url=_image_url(scan.scan_uuid, "overlay.jpg"),
        report_id=report.report_id,
        model_status=scan.model_status,
        prediction_warning=scan.prediction_warning,
        recommendations=recommendations,
        created_at=scan.created_at,
    )


def create_scan(db: Session, image_bytes: bytes, inference_service: InferenceService) -> ScanResultResponse:
    result = inference_service.run_inference(image_bytes)
    scan_uuid = new_scan_uuid()

    original_path = save_upload_image(result.display_image, scan_uuid)
    overlay_path = save_overlay_image(result.overlay_image, scan_uuid)

    scan = Scan(
        scan_uuid=scan_uuid,
        original_image_path=original_path,
        overlay_image_path=overlay_path,
        crop_name=result.classification.crop_name,
        disease_code=result.classification.disease_code,
        disease_display_name=result.classification.disease_display_name,
        confidence=result.classification.confidence,
        infected_area_pct=result.segmentation.infected_area_pct,
        severity=result.severity,
        model_version=result.classification.model_version,
        segmentation_backend=result.segmentation.backend_name,
        model_status=result.classification.model_status,
        prediction_warning=result.leaf_validity.warning,
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    recommendations = get_recommendations(db, scan.disease_code, scan.severity)
    report = create_report(
        db,
        scan,
        recommendations,
        model_status=scan.model_status,
        segmentation_backend=scan.segmentation_backend,
    )

    return _to_result_response(db, scan, report, recommendations)


def get_scan_detail(db: Session, scan_uuid: str) -> ScanResultResponse | None:
    scan = db.query(Scan).filter_by(scan_uuid=scan_uuid).first()
    if scan is None:
        return None

    report = db.query(Report).filter_by(scan_id=scan.id).order_by(Report.generated_at.desc()).first()
    if report is None:
        return None

    recommendations = get_recommendations(db, scan.disease_code, scan.severity)
    return _to_result_response(db, scan, report, recommendations)


def list_scans(
    db: Session,
    crop: str | None,
    severity: str | None,
    date_from: datetime.date | None,
    date_to: datetime.date | None,
    page: int,
    page_size: int,
) -> PaginatedScans:
    query = db.query(Scan)

    if crop:
        query = query.filter(Scan.crop_name == crop)
    if severity:
        query = query.filter(Scan.severity == severity)
    if date_from:
        query = query.filter(Scan.created_at >= date_from)
    if date_to:
        query = query.filter(Scan.created_at < date_to + datetime.timedelta(days=1))

    total = query.with_entities(func.count(Scan.id)).scalar() or 0

    rows = (
        query.order_by(Scan.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [
        ScanSummary(
            scan_uuid=row.scan_uuid,
            crop_name=row.crop_name,
            disease_display_name=row.disease_display_name,
            confidence=row.confidence,
            infected_area_pct=row.infected_area_pct,
            severity=row.severity,
            overlay_image_url=_image_url(row.scan_uuid, "overlay.jpg"),
            prediction_warning=row.prediction_warning,
            created_at=row.created_at,
        )
        for row in rows
    ]

    return PaginatedScans(items=items, total=total, page=page, page_size=page_size)


def get_dashboard_stats(
    db: Session, date_from: datetime.date | None, date_to: datetime.date | None
) -> DashboardStatsResponse:
    query = db.query(Scan)
    if date_from:
        query = query.filter(Scan.created_at >= date_from)
    if date_to:
        query = query.filter(Scan.created_at < date_to + datetime.timedelta(days=1))

    total_scans = query.with_entities(func.count(Scan.id)).scalar() or 0

    severity_rows = (
        query.with_entities(Scan.severity, func.count(Scan.id)).group_by(Scan.severity).all()
    )
    crop_rows = query.with_entities(Scan.crop_name, func.count(Scan.id)).group_by(Scan.crop_name).all()

    trend_rows = (
        query.with_entities(func.date(Scan.created_at), func.count(Scan.id))
        .group_by(func.date(Scan.created_at))
        .order_by(func.date(Scan.created_at))
        .all()
    )

    disease_rows = (
        query.with_entities(Scan.disease_display_name, func.count(Scan.id))
        .filter(Scan.disease_code.notin_(
            db.query(DiseaseReference.disease_code).filter(DiseaseReference.is_healthy_label.is_(True))
        ))
        .group_by(Scan.disease_display_name)
        .order_by(func.count(Scan.id).desc())
        .limit(5)
        .all()
    )

    return DashboardStatsResponse(
        total_scans=total_scans,
        severity_breakdown=[BreakdownItem(label=label, count=count) for label, count in severity_rows],
        crop_breakdown=[BreakdownItem(label=label, count=count) for label, count in crop_rows],
        trend_over_time=[
            TrendPoint(date=str(date_value), count=count) for date_value, count in trend_rows
        ],
        most_common_diseases=[
            BreakdownItem(label=label, count=count) for label, count in disease_rows
        ],
    )

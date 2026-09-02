import datetime

from app.pdf.report_template import ReportData, generate_report_pdf
from app.utils.id_generator import generate_report_id
from tests.conftest import make_synthetic_leaf_jpeg


def test_generate_report_pdf_writes_a_valid_pdf(tmp_path):
    image_path = tmp_path / "original.jpg"
    overlay_path = tmp_path / "overlay.jpg"
    image_path.write_bytes(make_synthetic_leaf_jpeg())
    overlay_path.write_bytes(make_synthetic_leaf_jpeg(patch_fraction=0.3))

    data = ReportData(
        report_id=generate_report_id(),
        scan_uuid="test-uuid-0001",
        original_image_path=str(image_path),
        overlay_image_path=str(overlay_path),
        crop_name="Tomato",
        disease_display_name="Late blight",
        confidence=0.87,
        infected_area_pct=34.5,
        severity="Severe",
        treatment_text="Apply a labeled fungicide immediately.",
        prevention_text="Avoid overhead irrigation.",
        urgency_note="Severity is Severe: isolate affected plants promptly.",
        model_status="fine_tuned",
        segmentation_backend="classical_cv",
        prediction_warning=None,
        scanned_at=datetime.datetime.now(datetime.timezone.utc),
    )

    output_path = tmp_path / "report.pdf"
    result_path = generate_report_pdf(output_path, data)

    assert result_path.exists()
    assert result_path.read_bytes()[:4] == b"%PDF"


def test_generate_report_pdf_without_urgency_note(tmp_path):
    image_path = tmp_path / "original.jpg"
    overlay_path = tmp_path / "overlay.jpg"
    image_path.write_bytes(make_synthetic_leaf_jpeg())
    overlay_path.write_bytes(make_synthetic_leaf_jpeg())

    data = ReportData(
        report_id=generate_report_id(),
        scan_uuid="test-uuid-0002",
        original_image_path=str(image_path),
        overlay_image_path=str(overlay_path),
        crop_name="Apple",
        disease_display_name="Healthy",
        confidence=0.99,
        infected_area_pct=0.0,
        severity="Healthy",
        treatment_text="No treatment necessary.",
        prevention_text="Continue routine monitoring.",
        urgency_note=None,
        model_status="fine_tuned",
        segmentation_backend="classical_cv",
        prediction_warning="Low prediction confidence (42%) — treat this result with caution.",
        scanned_at=datetime.datetime.now(datetime.timezone.utc),
    )

    output_path = tmp_path / "report_healthy.pdf"
    result_path = generate_report_pdf(output_path, data)

    assert result_path.exists()
    assert result_path.stat().st_size > 0

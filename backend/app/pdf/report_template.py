"""ReportLab-based PDF report layout.

Produces a single-page (auto-flowing to 2 pages if recommendation text is
long) report containing everything required: original + highlighted images,
plant name, disease name, confidence, % affected area, severity, treatment
and prevention recommendations, scan date/time, and report ID.
"""
import datetime
from dataclasses import dataclass
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

_SEVERITY_COLORS = {
    "Healthy": colors.HexColor("#15803d"),
    "Mild": colors.HexColor("#a16207"),
    "Moderate": colors.HexColor("#c2410c"),
    "Severe": colors.HexColor("#dc2626"),
    "Critical": colors.HexColor("#7f1d1d"),
}


@dataclass
class ReportData:
    report_id: str
    scan_uuid: str
    original_image_path: str
    overlay_image_path: str
    crop_name: str
    disease_display_name: str
    confidence: float
    infected_area_pct: float
    severity: str
    treatment_text: str
    prevention_text: str
    urgency_note: str | None
    model_status: str
    segmentation_backend: str
    prediction_warning: str | None
    scanned_at: datetime.datetime


def _styles():
    stylesheet = getSampleStyleSheet()
    stylesheet.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=stylesheet["Title"],
            textColor=colors.HexColor("#1c3d2e"),
        )
    )
    stylesheet.add(
        ParagraphStyle(name="SectionHeading", parent=stylesheet["Heading2"], spaceBefore=10, spaceAfter=4)
    )
    stylesheet.add(ParagraphStyle(name="BodySmall", parent=stylesheet["BodyText"], fontSize=9, leading=12))
    return stylesheet


def generate_report_pdf(output_path: str | Path, data: ReportData) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    stylesheet = _styles()

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        topMargin=18 * mm,
        bottomMargin=16 * mm,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
    )

    story = []

    story.append(Paragraph("AgriVision — Leaf Disease Scan Report", stylesheet["ReportTitle"]))
    story.append(
        Paragraph(
            f"Report ID: <b>{data.report_id}</b> &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"Scanned: {data.scanned_at.strftime('%Y-%m-%d %H:%M UTC')}",
            stylesheet["BodyText"],
        )
    )
    story.append(Spacer(1, 8))

    if data.prediction_warning:
        story.append(
            Paragraph(
                f"<b>Reliability warning:</b> {data.prediction_warning}",
                ParagraphStyle(
                    name="ReliabilityWarning",
                    parent=stylesheet["BodyText"],
                    textColor=colors.HexColor("#a16207"),
                    borderColor=colors.HexColor("#a16207"),
                    borderWidth=0.75,
                    borderPadding=6,
                ),
            )
        )
        story.append(Spacer(1, 8))

    image_width = 80 * mm
    images_row = Table(
        [
            [
                Paragraph("Original Image", stylesheet["SectionHeading"]),
                Paragraph("Disease-Highlighted Image", stylesheet["SectionHeading"]),
            ],
            [
                Image(data.original_image_path, width=image_width, height=image_width),
                Image(data.overlay_image_path, width=image_width, height=image_width),
            ],
        ],
        colWidths=[image_width + 5 * mm, image_width + 5 * mm],
    )
    images_row.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
    story.append(images_row)
    story.append(Spacer(1, 10))

    severity_color = _SEVERITY_COLORS.get(data.severity, colors.grey)
    summary_table = Table(
        [
            ["Plant Species", data.crop_name],
            ["Disease", data.disease_display_name],
            ["Prediction Confidence", f"{data.confidence * 100:.1f}%"],
            ["Affected Leaf Area", f"{data.infected_area_pct:.1f}%"],
            ["Severity", data.severity],
        ],
        colWidths=[55 * mm, 105 * mm],
    )
    summary_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d0d5d1")),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eef3ef")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("BACKGROUND", (1, 4), (1, 4), severity_color),
                ("TEXTCOLOR", (1, 4), (1, 4), colors.white),
                ("FONTNAME", (1, 4), (1, 4), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(summary_table)
    story.append(Spacer(1, 10))

    if data.urgency_note:
        story.append(
            Paragraph(f"<b>Urgent:</b> {data.urgency_note}", ParagraphStyle(
                name="Urgency", parent=stylesheet["BodyText"], textColor=colors.HexColor("#c2273d")
            ))
        )
        story.append(Spacer(1, 6))

    story.append(Paragraph("Treatment Recommendations", stylesheet["SectionHeading"]))
    story.append(Paragraph(data.treatment_text or "—", stylesheet["BodyText"]))

    story.append(Paragraph("Prevention Recommendations", stylesheet["SectionHeading"]))
    story.append(Paragraph(data.prevention_text or "—", stylesheet["BodyText"]))

    story.append(Spacer(1, 14))
    disclaimer = (
        f"Methodology note: disease classification model status is '{data.model_status}'. "
        f"Infected-area segmentation used the '{data.segmentation_backend}' backend, a "
        "classical color-based image analysis method (not a trained neural segmentation "
        "model) unless otherwise noted. Results are decision support, not a substitute for "
        "in-person diagnosis by a plant pathologist for high-value or ambiguous cases."
    )
    story.append(Paragraph(disclaimer, stylesheet["BodySmall"]))

    doc.build(story)
    return output_path

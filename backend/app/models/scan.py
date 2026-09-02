import datetime
import uuid

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import SEVERITY_LEVELS
from app.db.base import Base

SeverityEnum = Enum(*SEVERITY_LEVELS, name="severity_level")


class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    scan_uuid: Mapped[str] = mapped_column(
        String(36), nullable=False, unique=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[int | None] = mapped_column(nullable=True)

    original_image_path: Mapped[str] = mapped_column(String(500), nullable=False)
    overlay_image_path: Mapped[str] = mapped_column(String(500), nullable=False)

    crop_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    disease_code: Mapped[str] = mapped_column(
        String(100), ForeignKey("diseases_reference.disease_code"), nullable=False
    )
    disease_display_name: Mapped[str] = mapped_column(String(150), nullable=False)

    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    infected_area_pct: Mapped[float] = mapped_column(Float, nullable=False)
    severity: Mapped[str] = mapped_column(SeverityEnum, nullable=False, index=True)

    model_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    segmentation_backend: Mapped[str | None] = mapped_column(String(50), nullable=True)
    model_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # Set when app/ml/leaf_validity.py's heuristics flag the image as not
    # confidently a supported leaf photo (e.g. no leaf detected, or a
    # low-confidence prediction) — null when the result looks reliable.
    prediction_warning: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), index=True
    )

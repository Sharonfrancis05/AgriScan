import uuid
from pathlib import Path

import cv2
import numpy as np

from app.core.config import get_settings


def save_upload_image(rgb_image: np.ndarray, scan_uuid: str) -> str:
    """Saves the original (preprocessed-for-display) image; returns the path on disk."""
    settings = get_settings()
    scan_dir = settings.uploads_dir / scan_uuid
    scan_dir.mkdir(parents=True, exist_ok=True)
    path = scan_dir / "original.jpg"
    cv2.imwrite(str(path), cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR))
    return str(path)


def save_overlay_image(rgb_image: np.ndarray, scan_uuid: str) -> str:
    settings = get_settings()
    scan_dir = settings.uploads_dir / scan_uuid
    scan_dir.mkdir(parents=True, exist_ok=True)
    path = scan_dir / "overlay.jpg"
    cv2.imwrite(str(path), cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR))
    return str(path)


def report_pdf_path(report_id: str) -> Path:
    settings = get_settings()
    return settings.reports_dir / f"{report_id}.pdf"


def new_scan_uuid() -> str:
    return str(uuid.uuid4())

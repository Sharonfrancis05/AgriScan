"""Orchestrates the full ML pipeline: preprocess -> classify -> segment ->
severity -> overlay. This is the single seam the API layer calls through
(`scan_service.create_scan`) — everything ML-related is swappable behind it.
"""
from dataclasses import dataclass

import numpy as np

from app.core.config import Settings
from app.ml.classifier import ClassificationResult, DiseaseClassifier
from app.ml.leaf_validity import LeafValidityCheck, check_leaf_validity
from app.ml.preprocessing import preprocess_for_display, preprocess_for_model
from app.ml.segmentation import SegmentationResult, build_segmentation_backend
from app.ml.severity import classify_severity
from app.pdf.overlay_image import build_overlay


@dataclass
class InferenceResult:
    display_image: np.ndarray
    overlay_image: np.ndarray
    classification: ClassificationResult
    segmentation: SegmentationResult
    severity: str
    leaf_validity: LeafValidityCheck


class InferenceService:
    """Loaded once at app startup (see app.main) so model weights aren't reloaded per-request."""

    def __init__(self, settings: Settings):
        self.classifier = DiseaseClassifier(settings.model_checkpoint_path)
        self.segmenter = build_segmentation_backend(
            settings.segmentation_backend, settings.model_checkpoint_path.replace(
                "classifier_best.pt", "unet_best.pt"
            )
        )

    def run_inference(self, image_bytes: bytes) -> InferenceResult:
        display_image = preprocess_for_display(image_bytes)
        model_input = preprocess_for_model(display_image)

        classification = self.classifier.predict(model_input)
        segmentation = self.segmenter.segment(display_image)
        severity = classify_severity(segmentation.infected_area_pct)
        overlay_image = build_overlay(display_image, segmentation.lesion_mask)
        leaf_validity = check_leaf_validity(segmentation.leaf_mask, classification.confidence)

        return InferenceResult(
            display_image=display_image,
            overlay_image=overlay_image,
            classification=classification,
            segmentation=segmentation,
            severity=severity,
            leaf_validity=leaf_validity,
        )

"""Guards against the closed-set classifier confidently mislabeling an image
that isn't actually a supported leaf photo at all (wrong subject, heavy
occlusion, a screenshot, an AI-generated/fake image, etc.). A plain softmax
classifier has no built-in concept of "not one of my classes" — it always
forces its best guess onto one of the trained labels. Two independent,
no-training-required signals combine into one human-readable warning
surfaced through the whole pipeline (API, UI, PDF), so a confident-looking
result is never presented for an image that plainly isn't a leaf:

1. Leaf coverage from the classical-CV leaf mask (already computed by the
   segmentation step) — if the segmented leaf-colored region covers only a
   small fraction of the frame, the photo probably isn't primarily a leaf.
2. Classifier top-1 confidence (max softmax probability) — a simple,
   well-established out-of-distribution heuristic: genuine photos of the 6
   trained crops tend to produce a confident top prediction, while
   out-of-distribution inputs tend to spread probability more evenly across
   classes.

This is a heuristic safety net, not a trained "is this a leaf" detector —
see docs/ml_pipeline.md for the honest limitations, same spirit as
docs/segmentation_upgrade.md for the segmentation backend.
"""
from dataclasses import dataclass

import numpy as np

MIN_LEAF_AREA_FRACTION = 0.08
MIN_CLASSIFIER_CONFIDENCE = 0.50


@dataclass
class LeafValidityCheck:
    is_reliable: bool
    warning: str | None


def check_leaf_validity(leaf_mask: np.ndarray, confidence: float) -> LeafValidityCheck:
    leaf_area_fraction = float(leaf_mask.sum()) / leaf_mask.size if leaf_mask.size else 0.0

    if leaf_area_fraction < MIN_LEAF_AREA_FRACTION:
        return LeafValidityCheck(
            is_reliable=False,
            warning=(
                f"No clear leaf detected — a leaf-colored region covers only "
                f"{leaf_area_fraction * 100:.0f}% of the frame. This result may not reflect "
                "a real leaf photo; try a closer, well-lit photo of a single leaf."
            ),
        )

    if confidence < MIN_CLASSIFIER_CONFIDENCE:
        return LeafValidityCheck(
            is_reliable=False,
            warning=(
                f"Low prediction confidence ({confidence * 100:.0f}%) — this may not be one "
                "of the 6 supported crops (Apple, Grape, Corn, Tomato, Strawberry, Peach), or "
                "the image quality/angle made it hard to classify. Treat this result with caution."
            ),
        )

    return LeafValidityCheck(is_reliable=True, warning=None)

"""Classical OpenCV segmentation: leaf-vs-background, then lesion-vs-healthy-tissue.

This is the DEFAULT, working-today segmentation backend. It is a heuristic,
not a learned model — accuracy varies with lighting, lesion type (e.g. a
powdery-mildew coating segments differently than rust pustules or blight
patches), and background clutter. See docs/segmentation_upgrade.md for the
honest limitations write-up and the staged U-Net upgrade path.

Pipeline:
  1. Leaf mask: HSV threshold over typical leaf hues (green/brown/yellow),
     cleaned with an OPEN-then-CLOSE morphology pass (erode away spatially
     uncorrelated false positives — background clutter, noise — before
     filling small gaps within whatever coherent region survives), then
     largest-connected-component selection, to isolate the leaf from
     background (soil, hand, other leaves) and from non-leaf inputs
     entirely (a flat non-leaf color or visual noise should end up with
     ~0% leaf coverage, not accidentally pass as "leaf").
  2. Lesion mask (within the leaf only): Lab color space is used because
     necrotic/chlorotic lesions separate from healthy green tissue much more
     cleanly on the `a` (green-red) channel than in RGB/HSV alone. Otsu
     thresholding on `a` (restricted to leaf pixels) is unioned with a
     secondary HSV brown/yellow/black lesion-color range, then cleaned with
     morphological opening/closing and a minimum-connected-component-area
     filter to drop micro-noise specks.
  3. % infected = lesion_pixels / leaf_pixels * 100, computed only over the
     leaf mask (never the background) — the biologically meaningful
     denominator.
"""
import cv2
import numpy as np

from app.ml.segmentation.base import SegmentationBackend, SegmentationResult

_MIN_COMPONENT_AREA_FRACTION = 0.0005  # drop connected components smaller than this fraction of the leaf area


def _largest_component_mask(mask: np.ndarray) -> np.ndarray:
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), connectivity=8)
    if num_labels <= 1:
        return mask
    largest_label = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    return labels == largest_label


def _build_leaf_mask(rgb_image: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2HSV)

    # Broad leaf-hue band: green through yellow-brown, covers both healthy tissue
    # and diseased tissue (we only want to exclude background/non-leaf here).
    # NOTE: an earlier version also OR'd in a global Otsu-on-saturation vote as
    # a second signal, but that accepted ANY sufficiently saturated color
    # (a flat blue image, colorful noise, etc.) as "leaf" regardless of hue —
    # defeating the purpose. Hue is the only signal now.
    lower = np.array([5, 25, 25])
    upper = np.array([100, 255, 255])
    hue_mask = cv2.inRange(hsv, lower, upper)

    # OPEN first: erodes away small, spatially uncorrelated false-positive
    # pixels (background clutter, visual noise) that pass the hue check by
    # chance but aren't part of one coherent region — a real photographed
    # leaf survives this since it's a large contiguous blob, even a
    # disease-mottled one. CLOSE second: fills small gaps (veins, minor
    # occlusion, disease-mottled hue breaks) within whatever survives.
    # Doing this in the opposite order would instead bridge scattered noise
    # into a single false "leaf" blob before erosion ever got a chance to
    # remove it. The open kernel/iterations are deliberately gentler than the
    # close pass — a 7x7 double-open was tested and reliably destroyed real,
    # disease-mottled leaf regions (e.g. a rust-covered corn leaf dropped
    # from ~48% to ~5% coverage) while a 5x5 single-open still crushes
    # uncorrelated per-pixel noise to ~0%.
    open_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    close_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    cleaned = cv2.morphologyEx(hue_mask, cv2.MORPH_OPEN, open_kernel, iterations=1)
    cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, close_kernel, iterations=2)

    leaf_mask = cleaned > 0
    if leaf_mask.any():
        leaf_mask = _largest_component_mask(leaf_mask)
    return leaf_mask


def _build_lesion_mask(rgb_image: np.ndarray, leaf_mask: np.ndarray) -> np.ndarray:
    lab = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2LAB)
    a_channel = lab[:, :, 1]

    leaf_pixels_a = a_channel[leaf_mask]
    if leaf_pixels_a.size == 0:
        return np.zeros(leaf_mask.shape, dtype=bool)

    # Otsu restricted to leaf pixels: healthy tissue sits low on `a` (green),
    # lesions (necrotic/chlorotic) sit higher (red/yellow-brown).
    _, a_otsu = cv2.threshold(
        leaf_pixels_a.reshape(-1, 1).astype(np.uint8), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    a_threshold = float(np.mean(leaf_pixels_a[a_otsu.flatten() > 0])) if a_otsu.any() else 140.0
    a_lesion_mask = a_channel > a_threshold

    # Secondary vote: classic brown/black/yellow lesion colors in HSV.
    hsv = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2HSV)
    brown_black = cv2.inRange(hsv, np.array([0, 40, 20]), np.array([30, 255, 200]))
    yellow = cv2.inRange(hsv, np.array([20, 60, 100]), np.array([35, 255, 255]))
    hsv_lesion_mask = (brown_black > 0) | (yellow > 0)

    lesion_mask = (a_lesion_mask | hsv_lesion_mask) & leaf_mask

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    lesion_mask = cv2.morphologyEx(lesion_mask.astype(np.uint8), cv2.MORPH_OPEN, kernel, iterations=1)
    lesion_mask = cv2.morphologyEx(lesion_mask, cv2.MORPH_CLOSE, kernel, iterations=1)

    leaf_area = int(leaf_mask.sum())
    min_area = max(1, int(leaf_area * _MIN_COMPONENT_AREA_FRACTION))
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(lesion_mask, connectivity=8)
    cleaned = np.zeros_like(lesion_mask, dtype=bool)
    for label_idx in range(1, num_labels):
        if stats[label_idx, cv2.CC_STAT_AREA] >= min_area:
            cleaned |= labels == label_idx

    return cleaned


class ClassicalCVSegmenter(SegmentationBackend):
    name = "classical_cv"

    def segment(self, rgb_image: np.ndarray) -> SegmentationResult:
        leaf_mask = _build_leaf_mask(rgb_image)
        lesion_mask = _build_lesion_mask(rgb_image, leaf_mask)

        leaf_area = int(leaf_mask.sum())
        lesion_area = int(lesion_mask.sum())
        infected_area_pct = (lesion_area / leaf_area * 100.0) if leaf_area > 0 else 0.0

        return SegmentationResult(
            leaf_mask=leaf_mask,
            lesion_mask=lesion_mask,
            infected_area_pct=round(infected_area_pct, 2),
            backend_name=self.name,
        )

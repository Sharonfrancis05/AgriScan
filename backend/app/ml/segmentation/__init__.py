from app.ml.segmentation.base import SegmentationBackend, SegmentationResult
from app.ml.segmentation.classical_cv import ClassicalCVSegmenter
from app.ml.segmentation.unet_backend import UNetSegmenter


def build_segmentation_backend(backend_name: str, checkpoint_path: str) -> SegmentationBackend:
    if backend_name == "unet":
        return UNetSegmenter(checkpoint_path)
    return ClassicalCVSegmenter()


__all__ = [
    "SegmentationBackend",
    "SegmentationResult",
    "ClassicalCVSegmenter",
    "UNetSegmenter",
    "build_segmentation_backend",
]

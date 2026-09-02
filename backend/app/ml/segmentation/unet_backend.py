"""U-Net segmentation backend — staged upgrade path, not usable until trained.

PlantVillage-style classification datasets (including the user's Kaggle
dataset) ship without pixel-level lesion masks, so there is nothing to
supervise a U-Net with yet. See ml_training/train_segmentation.py and
docs/segmentation_upgrade.md for the three documented ways to acquire masks
(weak/pseudo-masks bootstrapped from ClassicalCVSegmenter, GrabCut-assisted
semi-manual labeling, or a future labeled dataset).

This class implements the same SegmentationBackend interface as
ClassicalCVSegmenter so switching SEGMENTATION_BACKEND=unet in .env is a
drop-in change once a checkpoint exists at the configured path — no API
contract change required.
"""
import logging
from pathlib import Path

import numpy as np
import torch

from app.ml.segmentation.base import SegmentationBackend, SegmentationResult
from app.ml.segmentation.classical_cv import ClassicalCVSegmenter

logger = logging.getLogger(__name__)


class UNetSegmenter(SegmentationBackend):
    name = "unet"

    def __init__(self, checkpoint_path: str):
        self.checkpoint_path = Path(checkpoint_path)
        self.model = None
        self._fallback = ClassicalCVSegmenter()

        if self.checkpoint_path.exists():
            self.model = torch.jit.load(str(self.checkpoint_path), map_location="cpu")
            self.model.eval()
            logger.info("Loaded U-Net segmentation checkpoint from %s", self.checkpoint_path)
        else:
            logger.warning(
                "SEGMENTATION_BACKEND=unet but no checkpoint found at %s — falling back to "
                "ClassicalCVSegmenter for this process. Train a U-Net with "
                "ml_training/train_segmentation.py once labeled masks are available.",
                self.checkpoint_path,
            )

    @torch.inference_mode()
    def segment(self, rgb_image: np.ndarray) -> SegmentationResult:
        if self.model is None:
            result = self._fallback.segment(rgb_image)
            return SegmentationResult(
                leaf_mask=result.leaf_mask,
                lesion_mask=result.lesion_mask,
                infected_area_pct=result.infected_area_pct,
                backend_name=f"{self.name}_fallback_classical_cv",
            )

        h, w = rgb_image.shape[:2]
        tensor = torch.from_numpy(rgb_image).permute(2, 0, 1).float().unsqueeze(0) / 255.0
        logits = self.model(tensor)
        probs = torch.sigmoid(logits)[0, 0].numpy()

        lesion_mask = probs > 0.5
        # Leaf mask still comes from the classical pipeline until a dedicated
        # leaf-vs-background head is trained alongside the lesion head.
        leaf_mask = self._fallback.segment(rgb_image).leaf_mask
        lesion_mask = lesion_mask & leaf_mask

        leaf_area = int(leaf_mask.sum())
        lesion_area = int(lesion_mask.sum())
        infected_area_pct = (lesion_area / leaf_area * 100.0) if leaf_area > 0 else 0.0

        return SegmentationResult(
            leaf_mask=leaf_mask,
            lesion_mask=lesion_mask,
            infected_area_pct=round(infected_area_pct, 2),
            backend_name=self.name,
        )

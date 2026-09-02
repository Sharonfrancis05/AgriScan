from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np


@dataclass
class SegmentationResult:
    leaf_mask: np.ndarray  # bool array, HxW: True where pixel is leaf tissue
    lesion_mask: np.ndarray  # bool array, HxW: True where pixel is diseased tissue
    infected_area_pct: float  # lesion_pixels / leaf_pixels * 100, 0 if leaf_pixels == 0
    backend_name: str


class SegmentationBackend(ABC):
    """Common interface so swapping classical CV <-> U-Net is a one-line config change."""

    name: str

    @abstractmethod
    def segment(self, rgb_image: np.ndarray) -> SegmentationResult: ...

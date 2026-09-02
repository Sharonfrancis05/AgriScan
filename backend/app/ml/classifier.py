"""EfficientNet-B0 transfer-learning classifier over the combined crop___disease labels.

Loads a fine-tuned checkpoint from `models_store/` when present. If no
checkpoint has been produced yet (see ml_training/train_classifier.py),
falls back to the torchvision ImageNet-pretrained backbone with a freshly
initialized (untrained) classification head, so the API stays fully
functional end-to-end. In that fallback mode `model_status` is set to
"pretrained_backbone_untrained_head" and returned all the way to the API
response / PDF report, so results are never silently presented as more
accurate than they are.
"""
import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torchvision.models import efficientnet_b0

from app.ml.labels import LABELS, NUM_CLASSES, split_label

logger = logging.getLogger(__name__)

MODEL_STATUS_FINE_TUNED = "fine_tuned"
MODEL_STATUS_UNTRAINED_HEAD = "pretrained_backbone_untrained_head"


@dataclass
class ClassificationResult:
    crop_name: str
    disease_code: str
    disease_display_name: str
    confidence: float
    model_status: str
    model_version: str


def _build_model(num_classes: int) -> nn.Module:
    model = efficientnet_b0(weights="IMAGENET1K_V1")
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, num_classes)
    return model


class DiseaseClassifier:
    def __init__(self, checkpoint_path: str):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = _build_model(NUM_CLASSES).to(self.device)
        self.model_status = MODEL_STATUS_UNTRAINED_HEAD
        self.model_version = "efficientnet_b0-untrained_head"

        path = Path(checkpoint_path)
        if path.exists():
            checkpoint = torch.load(path, map_location=self.device)
            self.model.load_state_dict(checkpoint["state_dict"])
            self.model_status = MODEL_STATUS_FINE_TUNED
            self.model_version = checkpoint.get("model_version", "efficientnet_b0-fine_tuned")
            logger.info("Loaded fine-tuned classifier checkpoint from %s", path)
        else:
            logger.warning(
                "No fine-tuned checkpoint found at %s — serving predictions from an "
                "ImageNet-pretrained backbone with an UNTRAINED classification head. "
                "Run ml_training/train_classifier.py to produce a real checkpoint.",
                path,
            )

        self.model.eval()

    @torch.inference_mode()
    def predict(self, model_input_chw: np.ndarray) -> ClassificationResult:
        tensor = torch.from_numpy(model_input_chw).float().unsqueeze(0).to(self.device)
        logits = self.model(tensor)
        probs = torch.softmax(logits, dim=1)[0]
        top_idx = int(torch.argmax(probs).item())
        confidence = float(probs[top_idx].item())

        disease_code = LABELS[top_idx]
        crop_name, disease_display_name = split_label(disease_code)

        return ClassificationResult(
            crop_name=crop_name,
            disease_code=disease_code,
            disease_display_name=disease_display_name,
            confidence=confidence,
            model_status=self.model_status,
            model_version=self.model_version,
        )

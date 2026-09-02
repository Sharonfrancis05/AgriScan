"""Converts a fine-tuned classifier checkpoint to ONNX for lighter-weight
inference and the future mobile-deployment path.

Run from backend/:
    python ml_training/export_to_onnx.py --checkpoint models_store/classifier_best.pt
"""
import argparse
from pathlib import Path

import torch
from torchvision.models import efficientnet_b0, mobilenet_v3_small

from app.core.constants import MODEL_INPUT_SIZE

_BACKBONES = {"efficientnet_b0": efficientnet_b0, "mobilenet_v3_small": mobilenet_v3_small}


def _build_model(backbone_name: str, num_classes: int):
    model = _BACKBONES[backbone_name](weights=None)
    if backbone_name == "efficientnet_b0":
        in_features = model.classifier[1].in_features
        model.classifier[1] = torch.nn.Linear(in_features, num_classes)
    else:
        in_features = model.classifier[3].in_features
        model.classifier[3] = torch.nn.Linear(in_features, num_classes)
    return model


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, default=Path("models_store/classifier_best.pt"))
    parser.add_argument("--output", type=Path, default=Path("models_store/classifier_best.onnx"))
    parser.add_argument("--backbone", choices=list(_BACKBONES), default="efficientnet_b0")
    args = parser.parse_args()

    checkpoint = torch.load(args.checkpoint, map_location="cpu")
    class_names = checkpoint["class_names"]

    model = _build_model(args.backbone, len(class_names))
    model.load_state_dict(checkpoint["state_dict"])
    model.eval()

    dummy_input = torch.randn(1, 3, MODEL_INPUT_SIZE, MODEL_INPUT_SIZE)
    torch.onnx.export(
        model,
        dummy_input,
        str(args.output),
        input_names=["image"],
        output_names=["logits"],
        dynamic_axes={"image": {0: "batch"}, "logits": {0: "batch"}},
        opset_version=17,
    )
    print(f"Exported ONNX model to {args.output} ({len(class_names)} classes)")


if __name__ == "__main__":
    main()

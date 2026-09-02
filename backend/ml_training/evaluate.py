"""Evaluates a trained classifier checkpoint on the held-out validation split:
per-class precision/recall/F1 and a confusion matrix image.

Run from backend/:
    python ml_training/evaluate.py --checkpoint models_store/classifier_best.pt
"""
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import torch
from sklearn.metrics import ConfusionMatrixDisplay, classification_report, confusion_matrix
from torch.utils.data import DataLoader
from torchvision.models import efficientnet_b0, mobilenet_v3_small

from ml_training.datasets.leaf_dataset import load_train_val_datasets

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
    parser.add_argument("--data-dir", type=Path, default=Path("ml_training/data_prepared"))
    parser.add_argument("--backbone", choices=list(_BACKBONES), default="efficientnet_b0")
    parser.add_argument("--output-confusion-matrix", type=Path, default=Path("ml_training/confusion_matrix.png"))
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    checkpoint = torch.load(args.checkpoint, map_location=device)
    class_names = checkpoint["class_names"]

    _, val_ds, _ = load_train_val_datasets(args.data_dir)
    val_loader = DataLoader(val_ds, batch_size=32, shuffle=False)

    model = _build_model(args.backbone, len(class_names)).to(device)
    model.load_state_dict(checkpoint["state_dict"])
    model.eval()

    all_preds, all_labels = [], []
    with torch.no_grad():
        for images, labels in val_loader:
            images = images.to(device)
            preds = model(images).argmax(dim=1).cpu().numpy()
            all_preds.extend(preds)
            all_labels.extend(labels.numpy())

    print(classification_report(all_labels, all_preds, target_names=class_names, zero_division=0))

    cm = confusion_matrix(all_labels, all_preds)
    fig, ax = plt.subplots(figsize=(max(8, len(class_names) * 0.5), max(8, len(class_names) * 0.5)))
    ConfusionMatrixDisplay(cm, display_labels=class_names).plot(ax=ax, xticks_rotation=90, colorbar=False)
    fig.tight_layout()
    fig.savefig(args.output_confusion_matrix, dpi=150)
    print(f"Confusion matrix saved to {args.output_confusion_matrix}")


if __name__ == "__main__":
    main()

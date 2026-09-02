"""Transfer-learning fine-tune script for the EfficientNet-B0 (or
MobileNetV3-Small) disease classifier.

Run from the backend/ directory (so the `app` package resolves):
    python ml_training/train_classifier.py --data-dir ml_training/data_prepared \
        --epochs 15 --backbone efficientnet_b0

Writes the best checkpoint (by validation accuracy) to
models_store/classifier_best.pt in the format app/ml/classifier.py expects:
    {"state_dict": ..., "model_version": ..., "class_names": [...]}

Not executed automatically by this repository — run it yourself once
ml_training/prepare_dataset.py has populated data_prepared/ from your
uploaded dataset.
"""
import argparse
import csv
import datetime
from pathlib import Path

import torch
from torch import nn, optim
from torch.utils.data import DataLoader
from torchvision.models import efficientnet_b0, mobilenet_v3_small

from ml_training.datasets.leaf_dataset import load_train_val_datasets

_BACKBONES = {
    "efficientnet_b0": efficientnet_b0,
    "mobilenet_v3_small": mobilenet_v3_small,
}


def _build_model(backbone_name: str, num_classes: int) -> nn.Module:
    model = _BACKBONES[backbone_name](weights="IMAGENET1K_V1")
    if backbone_name == "efficientnet_b0":
        in_features = model.classifier[1].in_features
        model.classifier[1] = nn.Linear(in_features, num_classes)
    else:  # mobilenet_v3_small
        in_features = model.classifier[3].in_features
        model.classifier[3] = nn.Linear(in_features, num_classes)
    return model


def _run_epoch(model, loader, device, optimizer=None) -> tuple[float, float]:
    is_train = optimizer is not None
    model.train(is_train)
    criterion = nn.CrossEntropyLoss()

    total_loss, correct, total = 0.0, 0, 0
    with torch.set_grad_enabled(is_train):
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)

            if is_train:
                optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            if is_train:
                loss.backward()
                optimizer.step()

            total_loss += loss.item() * images.size(0)
            correct += (outputs.argmax(dim=1) == labels).sum().item()
            total += images.size(0)

    return total_loss / total, correct / total


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("ml_training/data_prepared"))
    parser.add_argument("--output", type=Path, default=Path("models_store/classifier_best.pt"))
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--backbone", choices=list(_BACKBONES), default="efficientnet_b0")
    parser.add_argument("--metrics-csv", type=Path, default=Path("ml_training/train_metrics.csv"))
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training on {device}")

    train_ds, val_ds, class_names = load_train_val_datasets(args.data_dir)
    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, num_workers=2)

    model = _build_model(args.backbone, len(class_names)).to(device)
    optimizer = optim.AdamW(model.parameters(), lr=args.lr)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    best_val_acc = 0.0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.metrics_csv.parent.mkdir(parents=True, exist_ok=True)

    with open(args.metrics_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["epoch", "train_loss", "train_acc", "val_loss", "val_acc"])

        for epoch in range(1, args.epochs + 1):
            train_loss, train_acc = _run_epoch(model, train_loader, device, optimizer)
            val_loss, val_acc = _run_epoch(model, val_loader, device)
            scheduler.step()

            writer.writerow([epoch, train_loss, train_acc, val_loss, val_acc])
            f.flush()
            print(
                f"epoch {epoch}/{args.epochs} | train_loss={train_loss:.4f} train_acc={train_acc:.4f} "
                f"| val_loss={val_loss:.4f} val_acc={val_acc:.4f}"
            )

            if val_acc > best_val_acc:
                best_val_acc = val_acc
                torch.save(
                    {
                        "state_dict": model.state_dict(),
                        "model_version": f"{args.backbone}-fine_tuned-{datetime.date.today().isoformat()}",
                        "class_names": class_names,
                    },
                    args.output,
                )
                print(f"  -> new best (val_acc={val_acc:.4f}), saved to {args.output}")

    print(f"Done. Best val_acc={best_val_acc:.4f}. Checkpoint: {args.output}")


if __name__ == "__main__":
    main()

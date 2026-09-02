"""U-Net training script for lesion segmentation — the staged upgrade path
described in docs/segmentation_upgrade.md. NOT usable until you have pixel
masks, since the Kaggle classification dataset ships without them.

Three ways to get masks (see docs/segmentation_upgrade.md for detail):
  1. Weak/pseudo-masks: run app.ml.segmentation.classical_cv.ClassicalCVSegmenter
     over your training images and save its lesion_mask output as the target
     — noisy but free, and a CNN trained on it often generalizes better than
     the heuristic alone (a form of self-distillation).
  2. ml_training/scripts/label_assist_grabcut.py: a human seeds a few
     foreground/background points per image and OpenCV's GrabCut refines the
     mask — much faster than manual pixel painting.
  3. A future dataset that ships with real lesion masks.

Expected directory layout (produced by whichever masking approach you use):
    masks_dir/
        images/*.jpg
        masks/*.png       # same filename stem as the matching image, 0/255 binary mask

Run from backend/:
    python ml_training/train_segmentation.py --masks-dir ml_training/data_masks --epochs 20

Exports the best checkpoint as TorchScript to
models_store/unet_best.pt, matching what app/ml/segmentation/unet_backend.py
loads via torch.jit.load.
"""
import argparse
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch import nn, optim
from torch.utils.data import DataLoader, Dataset

from app.core.constants import MODEL_INPUT_SIZE


class _ConvBlock(nn.Module):
    def __init__(self, in_ch: int, out_ch: int):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, 3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, 3, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        return self.block(x)


class SmallUNet(nn.Module):
    """A deliberately small U-Net (few channels) — this is a lesion/leaf
    binary segmentation task on modest data volumes, not a task that needs a
    heavyweight encoder."""

    def __init__(self, base_channels: int = 32):
        super().__init__()
        c = base_channels
        self.enc1 = _ConvBlock(3, c)
        self.enc2 = _ConvBlock(c, c * 2)
        self.enc3 = _ConvBlock(c * 2, c * 4)
        self.pool = nn.MaxPool2d(2)

        self.bottleneck = _ConvBlock(c * 4, c * 8)

        self.up3 = nn.ConvTranspose2d(c * 8, c * 4, 2, stride=2)
        self.dec3 = _ConvBlock(c * 8, c * 4)
        self.up2 = nn.ConvTranspose2d(c * 4, c * 2, 2, stride=2)
        self.dec2 = _ConvBlock(c * 4, c * 2)
        self.up1 = nn.ConvTranspose2d(c * 2, c, 2, stride=2)
        self.dec1 = _ConvBlock(c * 2, c)

        self.out_conv = nn.Conv2d(c, 1, 1)

    def forward(self, x):
        e1 = self.enc1(x)
        e2 = self.enc2(self.pool(e1))
        e3 = self.enc3(self.pool(e2))
        b = self.bottleneck(self.pool(e3))

        d3 = self.dec3(torch.cat([self.up3(b), e3], dim=1))
        d2 = self.dec2(torch.cat([self.up2(d3), e2], dim=1))
        d1 = self.dec1(torch.cat([self.up1(d2), e1], dim=1))
        return self.out_conv(d1)


class LesionMaskDataset(Dataset):
    def __init__(self, masks_dir: Path, size: int = MODEL_INPUT_SIZE):
        self.image_paths = sorted((masks_dir / "images").glob("*"))
        self.masks_dir = masks_dir
        self.size = size

    def __len__(self) -> int:
        return len(self.image_paths)

    def __getitem__(self, idx: int):
        image_path = self.image_paths[idx]
        mask_path = self.masks_dir / "masks" / f"{image_path.stem}.png"

        image = Image.open(image_path).convert("RGB").resize((self.size, self.size))
        mask = Image.open(mask_path).convert("L").resize((self.size, self.size))

        image_tensor = torch.from_numpy(np.array(image)).permute(2, 0, 1).float() / 255.0
        mask_tensor = (torch.from_numpy(np.array(mask)).float() / 255.0 > 0.5).float().unsqueeze(0)
        return image_tensor, mask_tensor


def _dice_loss(logits: torch.Tensor, targets: torch.Tensor, eps: float = 1e-6) -> torch.Tensor:
    probs = torch.sigmoid(logits)
    intersection = (probs * targets).sum(dim=(1, 2, 3))
    union = probs.sum(dim=(1, 2, 3)) + targets.sum(dim=(1, 2, 3))
    dice = (2 * intersection + eps) / (union + eps)
    return 1 - dice.mean()


def _iou(logits: torch.Tensor, targets: torch.Tensor, eps: float = 1e-6) -> float:
    preds = (torch.sigmoid(logits) > 0.5).float()
    intersection = (preds * targets).sum(dim=(1, 2, 3))
    union = ((preds + targets) > 0).float().sum(dim=(1, 2, 3))
    return ((intersection + eps) / (union + eps)).mean().item()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--masks-dir", type=Path, default=Path("ml_training/data_masks"))
    parser.add_argument("--output", type=Path, default=Path("models_store/unet_best.pt"))
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--batch-size", type=int, default=8)
    args = parser.parse_args()

    if not (args.masks_dir / "images").exists():
        raise SystemExit(
            f"{args.masks_dir}/images not found. See this script's module docstring for the "
            "3 ways to acquire lesion masks before training a U-Net."
        )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    dataset = LesionMaskDataset(args.masks_dir)
    val_size = max(1, int(len(dataset) * 0.15))
    train_ds, val_ds = torch.utils.data.random_split(dataset, [len(dataset) - val_size, val_size])

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, num_workers=2)

    model = SmallUNet().to(device)
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    bce = nn.BCEWithLogitsLoss()

    best_iou = 0.0
    args.output.parent.mkdir(parents=True, exist_ok=True)

    for epoch in range(1, args.epochs + 1):
        model.train()
        for images, masks in train_loader:
            images, masks = images.to(device), masks.to(device)
            optimizer.zero_grad()
            logits = model(images)
            loss = bce(logits, masks) + _dice_loss(logits, masks)
            loss.backward()
            optimizer.step()

        model.eval()
        ious = []
        with torch.no_grad():
            for images, masks in val_loader:
                images, masks = images.to(device), masks.to(device)
                logits = model(images)
                ious.append(_iou(logits, masks))
        mean_iou = sum(ious) / len(ious)
        print(f"epoch {epoch}/{args.epochs} | val_iou={mean_iou:.4f}")

        if mean_iou > best_iou:
            best_iou = mean_iou
            scripted = torch.jit.script(model.cpu())
            torch.jit.save(scripted, str(args.output))
            model.to(device)
            print(f"  -> new best (val_iou={mean_iou:.4f}), saved TorchScript to {args.output}")

    print(f"Done. Best val_iou={best_iou:.4f}. Checkpoint: {args.output}")


if __name__ == "__main__":
    main()

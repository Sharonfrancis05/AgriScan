"""ImageFolder-style loader over ml_training/data_prepared/, with train/val
split and augmentation. Run prepare_dataset.py first to populate that
directory from the raw uploaded dataset.
"""
from pathlib import Path

import torch
from PIL import Image
from torch.utils.data import Subset
from torchvision import datasets, transforms

from app.core.constants import IMAGENET_MEAN, IMAGENET_STD, MODEL_INPUT_SIZE


class AspectPreservingResize:
    """Scales to fit within size x size, then center-pads to a square with
    black — must exactly mirror app/ml/preprocessing.py's resize_for_model,
    since that is what real inference actually does to an uploaded photo. If
    this drifts from that function, validation accuracy stops reflecting
    real deployed accuracy (images get evaluated on a different visual
    distribution than the one they're served on)."""

    def __init__(self, size: int):
        self.size = size

    def __call__(self, img: Image.Image) -> Image.Image:
        img = img.copy()
        img.thumbnail((self.size, self.size), Image.BICUBIC)
        canvas = Image.new("RGB", (self.size, self.size), (0, 0, 0))
        offset = ((self.size - img.width) // 2, (self.size - img.height) // 2)
        canvas.paste(img, offset)
        return canvas


TRAIN_TRANSFORMS = transforms.Compose(
    [
        # Random-crop augmentation is intentionally allowed to differ from the
        # inference-time resize strategy below — augmentation diversity during
        # training is fine even though it doesn't match serving-time preprocessing.
        transforms.RandomResizedCrop(MODEL_INPUT_SIZE, scale=(0.8, 1.0)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        # Mild color jitter only — lesion color is a supervisory signal, so we
        # don't want augmentation to wash out the difference between a healthy
        # green leaf and a diseased one.
        transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.1),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ]
)

VAL_TRANSFORMS = transforms.Compose(
    [
        AspectPreservingResize(MODEL_INPUT_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ]
)


def load_train_val_datasets(data_dir: Path, val_fraction: float = 0.15, seed: int = 42):
    """Returns (train_dataset, val_dataset, class_names) where class_names is
    ordered to match the label indices the model will predict — this order
    must match app/ml/labels_generated.json exactly (both are derived from
    the same directory listing)."""
    full_dataset = datasets.ImageFolder(str(data_dir))
    class_names = full_dataset.classes

    generator = torch.Generator().manual_seed(seed)
    val_size = int(len(full_dataset) * val_fraction)
    train_size = len(full_dataset) - val_size
    train_indices, val_indices = torch.utils.data.random_split(
        range(len(full_dataset)), [train_size, val_size], generator=generator
    )

    train_dataset = datasets.ImageFolder(str(data_dir), transform=TRAIN_TRANSFORMS)
    val_dataset = datasets.ImageFolder(str(data_dir), transform=VAL_TRANSFORMS)

    return (
        Subset(train_dataset, list(train_indices)),
        Subset(val_dataset, list(val_indices)),
        class_names,
    )

"""OpenCV-based preprocessing shared by classification and segmentation.

Both stages need the same cleaned-up RGB image, so preprocessing happens once
in `inference_service` and both consumers work off its output.
"""
import io

import cv2
import numpy as np
from PIL import Image, ImageOps

from app.core.constants import IMAGENET_MEAN, IMAGENET_STD, MODEL_INPUT_SIZE


def decode_and_orient(image_bytes: bytes) -> np.ndarray:
    """Decode uploaded bytes, correct EXIF rotation, return RGB uint8 array."""
    pil_image = Image.open(io.BytesIO(image_bytes))
    pil_image = ImageOps.exif_transpose(pil_image)
    pil_image = pil_image.convert("RGB")
    return np.array(pil_image)


def resize_for_model(rgb_image: np.ndarray, size: int = MODEL_INPUT_SIZE) -> np.ndarray:
    """Aspect-preserving resize with center padding to a square `size x size`."""
    h, w = rgb_image.shape[:2]
    scale = size / max(h, w)
    new_h, new_w = round(h * scale), round(w * scale)
    resized = cv2.resize(rgb_image, (new_w, new_h), interpolation=cv2.INTER_AREA)

    canvas = np.zeros((size, size, 3), dtype=np.uint8)
    top = (size - new_h) // 2
    left = (size - new_w) // 2
    canvas[top : top + new_h, left : left + new_w] = resized
    return canvas


def denoise(rgb_image: np.ndarray) -> np.ndarray:
    """Mild bilateral filter: reduces phone-camera sensor noise, preserves lesion edges."""
    return cv2.bilateralFilter(rgb_image, d=5, sigmaColor=50, sigmaSpace=50)


def normalize_gray_world(rgb_image: np.ndarray) -> np.ndarray:
    """Gray-world white balance. NOT used by preprocess_for_display below —
    kept here only as a documented cautionary tale (see its docstring) and
    in case a future caller with a well-controlled photo setup wants it.

    Gray-world assumes the frame's average color should be neutral gray,
    which badly misfires whenever a large fraction of the frame is a
    non-neutral background (very common in leaf photos — dark/black
    photography backgrounds, soil, hands, sky). Confirmed on real dataset
    images: applying this before the classical-CV leaf-hue detector dropped
    correctly-detected leaf coverage from ~48% to ~8% on a real, correctly
    classified corn-rust photo, because the global per-channel rescale it
    computes from a background-dominated frame shifts genuine leaf-green
    hues out of the detector's expected range. It's also inconsistent with
    training: ml_training/datasets/leaf_dataset.py never applies it, so
    using it only at inference time was also a train/inference mismatch for
    the classifier itself.
    """
    result = rgb_image.astype(np.float32)
    means = result.reshape(-1, 3).mean(axis=0)
    overall_mean = means.mean()
    gains = np.divide(overall_mean, means, out=np.ones_like(means), where=means != 0)
    result = np.clip(result * gains, 0, 255)
    return result.astype(np.uint8)


def preprocess_for_display(image_bytes: bytes) -> np.ndarray:
    """Cleaned-up, full-resolution-ish RGB image used for segmentation + overlay + PDF."""
    rgb = decode_and_orient(image_bytes)
    rgb = denoise(rgb)
    return rgb


def preprocess_for_model(rgb_image: np.ndarray) -> np.ndarray:
    """Model-ready float32 CHW tensor-array, normalized with ImageNet stats."""
    resized = resize_for_model(rgb_image)
    normalized = resized.astype(np.float32) / 255.0
    normalized = (normalized - np.array(IMAGENET_MEAN)) / np.array(IMAGENET_STD)
    return normalized.transpose(2, 0, 1)  # HWC -> CHW

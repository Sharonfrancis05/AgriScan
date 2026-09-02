"""The flat `crop___disease` label space the classifier predicts over.

This list mirrors the actual class structure of the Kaggle
"plant-disease-detection-dataset" (mgmitesh) this project targets, filtered
to the 6 preferred crops — i.e. exactly what ml_training/prepare_dataset.py
produces from that dataset. IMPORTANT: once the dataset (uploaded into
backend/ml_training/data_raw/) is actually processed by
ml_training/prepare_dataset.py, that script writes the *authoritative*
label list (derived from whatever class folders actually exist) to
backend/app/ml/labels_generated.json, which takes priority over this
fallback — so if your dataset differs even slightly (extra/missing disease
folders), the generated file is always the source of truth. This module
loads that file when present and falls back to the list below otherwise, so
the app can still run before the dataset has been prepared.

Disease codes are lowercase snake_case (e.g. "apple_scab") regardless of how
the source dataset capitalized its folder names — see
ml_training/prepare_dataset.py's _normalize_disease_name — so the same
disease always maps to the same code, and diseases_reference_seed.json's
disease_code values must match this exact casing.
"""
import json
from pathlib import Path

_GENERATED_LABELS_PATH = Path(__file__).parent / "labels_generated.json"

_FALLBACK_LABELS = [
    "Apple___apple_scab",
    "Apple___black_rot",
    "Apple___cedar_apple_rust",
    "Apple___healthy",
    "Grape___black_rot",
    "Grape___esca",
    "Grape___leaf_blight",
    "Grape___healthy",
    "Corn___common_rust",
    "Corn___gray_leaf_spot",
    "Corn___northern_leaf_blight",
    "Corn___healthy",
    "Tomato___bacterial_spot",
    "Tomato___early_blight",
    "Tomato___late_blight",
    "Tomato___healthy",
    "Strawberry___leaf_scorch",
    "Strawberry___healthy",
    "Peach___bacterial_spot",
    "Peach___healthy",
]


def load_label_list() -> list[str]:
    if _GENERATED_LABELS_PATH.exists():
        return json.loads(_GENERATED_LABELS_PATH.read_text())
    return _FALLBACK_LABELS


def split_label(disease_code: str) -> tuple[str, str]:
    """'Tomato___late_blight' -> ('Tomato', 'Late Blight')"""
    crop, _, disease = disease_code.partition("___")
    disease_display = disease.replace("_", " ").strip().title() or "Healthy"
    return crop, disease_display


LABELS = load_label_list()
NUM_CLASSES = len(LABELS)

"""Test configuration.

IMPORTANT: env vars must be set before any `app.*` module is imported,
because app.core.config.get_settings() is @lru_cache'd and app.db.session
creates its SQLAlchemy engine at import time. This lets the whole test
suite run against a throwaway SQLite file instead of a real MySQL server,
and avoids ever constructing the real (network-downloading) ImageNet
classifier backbone.
"""
import os
import shutil
import tempfile
from pathlib import Path

_TEST_ROOT = Path(tempfile.gettempdir()) / "agrivision_test"
if _TEST_ROOT.exists():
    shutil.rmtree(_TEST_ROOT, ignore_errors=True)
_TEST_ROOT.mkdir(parents=True, exist_ok=True)

os.environ["DATABASE_URL"] = f"sqlite:///{(_TEST_ROOT / 'test.db').as_posix()}"
os.environ["STORAGE_ROOT"] = str(_TEST_ROOT / "storage")
os.environ["MODEL_CHECKPOINT_PATH"] = str(_TEST_ROOT / "no_checkpoint_here.pt")
os.environ["SEGMENTATION_BACKEND"] = "classical_cv"

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

import app.main as main_module
from app.db.base import Base
from app.db.session import engine
from app.ml.classifier import ClassificationResult
from app.ml.segmentation import ClassicalCVSegmenter
from app.services.inference_service import InferenceService


class _FakeClassifier:
    """Avoids downloading ImageNet weights in tests; everything else in the
    pipeline (preprocessing, segmentation, severity, PDF) runs for real."""

    model_status = "fine_tuned"
    model_version = "test-fake"

    def predict(self, model_input_chw) -> ClassificationResult:
        return ClassificationResult(
            crop_name="Tomato",
            disease_code="Tomato___late_blight",
            disease_display_name="Late Blight",
            confidence=0.87,
            model_status="fine_tuned",
            model_version="test-fake",
        )


def _fake_inference_service_factory(settings):
    service = InferenceService.__new__(InferenceService)
    service.classifier = _FakeClassifier()
    service.segmenter = ClassicalCVSegmenter()
    return service


@pytest.fixture(scope="session", autouse=True)
def _setup_test_database():
    import app.models  # noqa: F401 registers models on Base.metadata

    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(main_module, "InferenceService", _fake_inference_service_factory)
    with TestClient(main_module.app) as test_client:
        yield test_client


def make_synthetic_leaf_jpeg(patch_fraction: float = 0.2) -> bytes:
    """A green square with a brown square patch in one corner, occupying
    roughly `patch_fraction` of the total area — used to sanity-check
    segmentation percentage math without needing a real photo."""
    size = 200
    image = np.zeros((size, size, 3), dtype=np.uint8)
    image[:, :] = (60, 160, 60)  # healthy green

    patch_side = int(size * (patch_fraction ** 0.5))
    image[0:patch_side, 0:patch_side] = (90, 60, 30)  # necrotic brown lesion

    import io

    buffer = io.BytesIO()
    Image.fromarray(image).save(buffer, format="JPEG", quality=95)
    return buffer.getvalue()


def make_non_leaf_jpeg() -> bytes:
    """A flat gray square with no leaf-like green/brown/yellow hues at all —
    used to exercise app/ml/leaf_validity.py's "no clear leaf detected" gate
    without needing a real non-leaf photo."""
    size = 200
    image = np.full((size, size, 3), 128, dtype=np.uint8)  # neutral gray

    import io

    buffer = io.BytesIO()
    Image.fromarray(image).save(buffer, format="JPEG", quality=95)
    return buffer.getvalue()

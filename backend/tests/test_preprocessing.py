import numpy as np

from app.core.constants import MODEL_INPUT_SIZE
from app.ml.preprocessing import (
    decode_and_orient,
    preprocess_for_display,
    preprocess_for_model,
    resize_for_model,
)
from tests.conftest import make_synthetic_leaf_jpeg


def test_decode_and_orient_returns_rgb_array():
    image_bytes = make_synthetic_leaf_jpeg()
    rgb = decode_and_orient(image_bytes)

    assert rgb.dtype == np.uint8
    assert rgb.ndim == 3
    assert rgb.shape[2] == 3


def test_resize_for_model_produces_square_output():
    rgb = np.zeros((80, 200, 3), dtype=np.uint8)
    resized = resize_for_model(rgb, size=MODEL_INPUT_SIZE)

    assert resized.shape == (MODEL_INPUT_SIZE, MODEL_INPUT_SIZE, 3)


def test_preprocess_for_model_output_is_normalized_chw():
    rgb = np.full((300, 300, 3), 128, dtype=np.uint8)
    model_input = preprocess_for_model(rgb)

    assert model_input.shape == (3, MODEL_INPUT_SIZE, MODEL_INPUT_SIZE)
    # ImageNet-normalized values for a mid-gray input should be small in magnitude
    assert np.abs(model_input).max() < 5.0


def test_preprocess_for_display_is_idempotent_on_shape():
    image_bytes = make_synthetic_leaf_jpeg()
    display_image = preprocess_for_display(image_bytes)

    assert display_image.dtype == np.uint8
    assert display_image.shape[2] == 3

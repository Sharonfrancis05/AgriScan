from app.ml.preprocessing import decode_and_orient
from app.ml.segmentation.classical_cv import ClassicalCVSegmenter
from tests.conftest import make_synthetic_leaf_jpeg

_segmenter = ClassicalCVSegmenter()


def test_segmenter_finds_no_lesion_on_a_uniformly_healthy_leaf():
    rgb = decode_and_orient(make_synthetic_leaf_jpeg(patch_fraction=0.0))
    result = _segmenter.segment(rgb)

    assert result.infected_area_pct < 5.0


def test_segmenter_percentage_increases_with_lesion_size():
    small = _segmenter.segment(decode_and_orient(make_synthetic_leaf_jpeg(patch_fraction=0.1)))
    large = _segmenter.segment(decode_and_orient(make_synthetic_leaf_jpeg(patch_fraction=0.4)))

    assert large.infected_area_pct > small.infected_area_pct


def test_segmenter_percentage_is_roughly_proportional_to_known_patch():
    # A known ~20% lesion patch should land in a broad-but-meaningful range —
    # this is a heuristic, not a trained model, so we check order of
    # magnitude rather than an exact percentage (see docs/segmentation_upgrade.md).
    rgb = decode_and_orient(make_synthetic_leaf_jpeg(patch_fraction=0.2))
    result = _segmenter.segment(rgb)

    assert 5.0 <= result.infected_area_pct <= 45.0


def test_segmentation_result_backend_name_is_classical_cv():
    rgb = decode_and_orient(make_synthetic_leaf_jpeg(patch_fraction=0.2))
    result = _segmenter.segment(rgb)

    assert result.backend_name == "classical_cv"
    assert result.leaf_mask.shape == result.lesion_mask.shape

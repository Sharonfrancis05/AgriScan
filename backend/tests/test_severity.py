import pytest

from app.ml.severity import classify_severity


@pytest.mark.parametrize(
    "infected_area_pct,expected",
    [
        (0.0, "Healthy"),
        (2.0, "Healthy"),
        (2.01, "Mild"),
        (10.0, "Mild"),
        (10.01, "Moderate"),
        (25.0, "Moderate"),
        (25.01, "Severe"),
        (50.0, "Severe"),
        (50.01, "Critical"),
        (100.0, "Critical"),
    ],
)
def test_severity_boundaries(infected_area_pct, expected):
    assert classify_severity(infected_area_pct) == expected

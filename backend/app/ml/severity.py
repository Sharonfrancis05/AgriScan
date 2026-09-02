"""Single source of truth mapping % infected leaf area -> severity band.

Thresholds are a simplified 5-band grouping in the spirit of common
agronomic severity scales (e.g. Horsfall-Barratt-style grading). Tunable
here without touching any calling code.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class SeverityBand:
    label: str
    upper_bound_pct: float  # inclusive upper bound; last band has no upper bound


SEVERITY_BANDS: list[SeverityBand] = [
    SeverityBand("Healthy", 2.0),
    SeverityBand("Mild", 10.0),
    SeverityBand("Moderate", 25.0),
    SeverityBand("Severe", 50.0),
    SeverityBand("Critical", float("inf")),
]


def classify_severity(infected_area_pct: float) -> str:
    for band in SEVERITY_BANDS:
        if infected_area_pct <= band.upper_bound_pct:
            return band.label
    return SEVERITY_BANDS[-1].label

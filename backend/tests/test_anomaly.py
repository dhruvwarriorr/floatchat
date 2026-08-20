import pytest

from app.models import Confidence
from app.services.anomaly import confidence_for_count, score_anomaly


@pytest.mark.parametrize(
    ("count", "expected"),
    [
        (1, Confidence.LOW),
        (5, Confidence.LOW),
        (6, Confidence.MEDIUM),
        (20, Confidence.MEDIUM),
        (21, Confidence.HIGH),
    ],
)
def test_confidence_boundaries(count: int, expected: Confidence) -> None:
    assert confidence_for_count(count) is expected


@pytest.mark.parametrize(
    ("current", "expected"),
    [
        (1.49, "normal"),
        (1.5, "mild_positive"),
        (2.49, "mild_positive"),
        (2.5, "strong_positive"),
        (-2.5, "strong_negative"),
    ],
)
def test_z_score_policy_boundaries(current: float, expected: str) -> None:
    result = score_anomaly(current=current, baseline_mean=0, baseline_std=1, profile_count=21)

    assert result is not None
    assert result.label == expected


def test_low_confidence_suppresses_severity() -> None:
    result = score_anomaly(current=3, baseline_mean=0, baseline_std=1, profile_count=5)

    assert result is not None
    assert result.label == "insufficient_data"
    assert result.show_severity is False


def test_zero_standard_deviation_skips_scoring() -> None:
    assert score_anomaly(current=3, baseline_mean=0, baseline_std=0, profile_count=21) is None

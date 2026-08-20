from __future__ import annotations

from dataclasses import dataclass

from app.models import Confidence


@dataclass(frozen=True)
class ScoredAnomaly:
    z_score: float
    label: str
    confidence: Confidence
    provisional: bool
    show_severity: bool


def confidence_for_count(profile_count: int) -> Confidence:
    if profile_count <= 5:
        return Confidence.LOW
    if profile_count <= 20:
        return Confidence.MEDIUM
    return Confidence.HIGH


def score_anomaly(
    *, current: float, baseline_mean: float, baseline_std: float, profile_count: int
) -> ScoredAnomaly | None:
    if baseline_std <= 0 or profile_count <= 0:
        return None

    confidence = confidence_for_count(profile_count)
    z_score = (current - baseline_mean) / baseline_std
    magnitude = abs(z_score)

    if magnitude < 1.5:
        label = "normal"
    elif magnitude < 2.5:
        label = "mild_positive" if z_score > 0 else "mild_negative"
    else:
        label = "strong_positive" if z_score > 0 else "strong_negative"

    if confidence is Confidence.LOW:
        label = "insufficient_data"

    return ScoredAnomaly(
        z_score=z_score,
        label=label,
        confidence=confidence,
        provisional=confidence is Confidence.MEDIUM,
        show_severity=confidence is not Confidence.LOW,
    )

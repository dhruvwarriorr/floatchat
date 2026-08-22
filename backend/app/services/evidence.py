from __future__ import annotations

from dataclasses import dataclass

from app.config import EvidenceGradeThresholds, get_settings
from app.models import EvidenceGrade
from app.services.qc import QCResult


@dataclass(frozen=True)
class GradeResult:
    grade: EvidenceGrade
    reasons: list[str]


def compute_evidence_grade(
    qc_result: QCResult,
    baseline_n: int,
    baseline_std: float,
    thresholds: EvidenceGradeThresholds | None = None,
) -> GradeResult:
    thresholds = thresholds or get_settings().grade_thresholds
    insufficient_reasons: list[str] = []
    if qc_result.valid_profile_count < thresholds.min_valid_profiles:
        insufficient_reasons.append("valid_profiles_below_5")
    if baseline_std <= 0:
        insufficient_reasons.append("baseline_std_zero")

    if (
        not thresholds.reviewed
        or thresholds.min_baseline_n is None
        or thresholds.min_distinct_floats is None
        or thresholds.min_qc_pass_rate is None
    ):
        insufficient_reasons.append("evidence_thresholds_pending_review")
        return GradeResult(EvidenceGrade.INSUFFICIENT, insufficient_reasons)

    if baseline_n < thresholds.min_baseline_n:
        insufficient_reasons.append("baseline_n_below_minimum")
    if insufficient_reasons:
        return GradeResult(EvidenceGrade.INSUFFICIENT, insufficient_reasons)

    indicative_reasons: list[str] = []
    if qc_result.distinct_float_count < thresholds.min_distinct_floats:
        indicative_reasons.append("distinct_floats_below_minimum")
    if qc_result.qc_pass_rate < thresholds.min_qc_pass_rate:
        indicative_reasons.append("qc_pass_rate_below_minimum")
    if indicative_reasons:
        return GradeResult(EvidenceGrade.INDICATIVE, indicative_reasons)

    return GradeResult(EvidenceGrade.SUPPORTED, ["all_grade_conditions_met"])

from __future__ import annotations

from dataclasses import dataclass

from app.config import EvidenceGradeThresholds, get_settings
from app.models import EvidenceGrade
from app.services.qc import QCResult


@dataclass(frozen=True)
class GradeResult:
    grade: EvidenceGrade
    reasons: list[str]
    checks: list[EvidenceCheckResult]


@dataclass(frozen=True)
class EvidenceCheckResult:
    key: str
    label: str
    value: int | float | str | None
    threshold: int | float | str | None
    passed: bool | None
    detail: str


def compute_evidence_grade(
    qc_result: QCResult,
    baseline_n: int,
    baseline_std: float,
    thresholds: EvidenceGradeThresholds | None = None,
) -> GradeResult:
    thresholds = thresholds or get_settings().grade_thresholds
    checks = [
        EvidenceCheckResult(
            key="valid_profile_count",
            label="Valid profile count",
            value=qc_result.valid_profile_count,
            threshold=thresholds.min_valid_profiles,
            passed=qc_result.valid_profile_count >= thresholds.min_valid_profiles,
            detail="At least this many independent profiles must survive quality control.",
        ),
        EvidenceCheckResult(
            key="baseline_observation_count",
            label="Baseline observations",
            value=baseline_n,
            threshold=thresholds.min_baseline_n,
            passed=(
                baseline_n >= thresholds.min_baseline_n
                if thresholds.reviewed and thresholds.min_baseline_n is not None
                else None
            ),
            detail="The production baseline needs enough historical observations for comparison.",
        ),
        EvidenceCheckResult(
            key="distinct_float_count",
            label="Distinct ARGO floats",
            value=qc_result.distinct_float_count,
            threshold=thresholds.min_distinct_floats,
            passed=(
                qc_result.distinct_float_count >= thresholds.min_distinct_floats
                if thresholds.reviewed and thresholds.min_distinct_floats is not None
                else None
            ),
            detail="Multiple physical floats provide more independent confirmation.",
        ),
        EvidenceCheckResult(
            key="qc_pass_rate",
            label="QC pass rate",
            value=qc_result.qc_pass_rate,
            threshold=thresholds.min_qc_pass_rate,
            passed=(
                qc_result.qc_pass_rate >= thresholds.min_qc_pass_rate
                if thresholds.reviewed and thresholds.min_qc_pass_rate is not None
                else None
            ),
            detail="This is the share of retrieved observations retained by the QC policy.",
        ),
        EvidenceCheckResult(
            key="baseline_variability",
            label="Baseline variability",
            value=baseline_std,
            threshold="> 0",
            passed=baseline_std > 0,
            detail="A positive baseline standard deviation is required to divide safely.",
        ),
    ]
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
        return GradeResult(EvidenceGrade.INSUFFICIENT, insufficient_reasons, checks)

    if baseline_n < thresholds.min_baseline_n:
        insufficient_reasons.append("baseline_n_below_minimum")
    if insufficient_reasons:
        return GradeResult(EvidenceGrade.INSUFFICIENT, insufficient_reasons, checks)

    indicative_reasons: list[str] = []
    if qc_result.distinct_float_count < thresholds.min_distinct_floats:
        indicative_reasons.append("distinct_floats_below_minimum")
    if qc_result.qc_pass_rate < thresholds.min_qc_pass_rate:
        indicative_reasons.append("qc_pass_rate_below_minimum")
    if indicative_reasons:
        return GradeResult(EvidenceGrade.INDICATIVE, indicative_reasons, checks)

    return GradeResult(EvidenceGrade.SUPPORTED, ["all_grade_conditions_met"], checks)

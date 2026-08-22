from dataclasses import replace

import pandas as pd

from app.config import EvidenceGradeThresholds
from app.models import EvidenceGrade
from app.services.evidence import compute_evidence_grade
from app.services.qc import QCResult

THRESHOLDS = EvidenceGradeThresholds(
    min_valid_profiles=5,
    min_baseline_n=10,
    min_distinct_floats=2,
    min_qc_pass_rate=0.3,
    coverage_rule="reviewed fixture",
    reviewed=True,
)


def qc_result(**overrides: object) -> QCResult:
    base = QCResult(
        retained=pd.DataFrame(),
        raw_count=10,
        valid_count=8,
        excluded_count=2,
        exclusion_reasons={},
        qc_pass_rate=0.8,
        raw_profile_count=8,
        valid_profile_count=8,
        excluded_profile_count=0,
        distinct_float_count=3,
        data_quality_warning=False,
        qc_rule_applied="fixture",
        value_col="temp_adjusted",
    )
    return replace(base, **overrides)


def test_too_few_profiles_is_insufficient() -> None:
    result = compute_evidence_grade(qc_result(valid_profile_count=4), 20, 1.0, THRESHOLDS)

    assert result.grade is EvidenceGrade.INSUFFICIENT
    assert "valid_profiles_below_5" in result.reasons


def test_small_baseline_and_zero_std_are_insufficient() -> None:
    small = compute_evidence_grade(qc_result(), 9, 1.0, THRESHOLDS)
    zero = compute_evidence_grade(qc_result(), 20, 0.0, THRESHOLDS)

    assert "baseline_n_below_minimum" in small.reasons
    assert "baseline_std_zero" in zero.reasons


def test_limited_float_coverage_is_indicative() -> None:
    result = compute_evidence_grade(qc_result(distinct_float_count=1), 20, 1.0, THRESHOLDS)

    assert result.grade is EvidenceGrade.INDICATIVE
    assert "distinct_floats_below_minimum" in result.reasons


def test_all_reviewed_conditions_pass_is_supported() -> None:
    result = compute_evidence_grade(qc_result(), 20, 1.0, THRESHOLDS)

    assert result.grade is EvidenceGrade.SUPPORTED
    assert result.reasons == ["all_grade_conditions_met"]


def test_unreviewed_thresholds_fail_closed() -> None:
    unreviewed = EvidenceGradeThresholds(
        min_baseline_n=None,
        min_distinct_floats=None,
        min_qc_pass_rate=None,
        coverage_rule=None,
        reviewed=False,
    )
    result = compute_evidence_grade(qc_result(), 20, 1.0, unreviewed)

    assert result.grade is EvidenceGrade.INSUFFICIENT
    assert "evidence_thresholds_pending_review" in result.reasons

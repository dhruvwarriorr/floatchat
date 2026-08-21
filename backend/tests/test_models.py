import pytest
from pydantic import ValidationError

from app.models import ChatResponse, EvidenceGrade, EvidencePanel


def test_rev_b_evidence_grade_values_are_stable() -> None:
    assert [grade.value for grade in EvidenceGrade] == [
        "Insufficient",
        "Indicative",
        "Supported",
    ]


def test_evidence_panel_rejects_invalid_qc_pass_rate() -> None:
    with pytest.raises(ValidationError):
        EvidencePanel(
            raw_profile_count=10,
            valid_profile_count=9,
            excluded_profile_count=1,
            distinct_float_count=3,
            qc_pass_rate=1.1,
            qc_rule="synthetic contract test",
            current_period_summary="synthetic contract test",
        )


def test_chat_response_requires_rev_b_trust_fields() -> None:
    required = set(ChatResponse.model_json_schema()["required"])

    assert {
        "evidence_grade",
        "evidence_grade_reasons",
        "evidence_panel",
        "data_quality_warning",
    } <= required

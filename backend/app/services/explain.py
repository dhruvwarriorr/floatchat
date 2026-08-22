from __future__ import annotations

from typing import Any

from app.models import EvidencePanel, Parameter, QueryParams
from app.services.anomaly import AnomalyScoreResult
from app.services.evidence import GradeResult
from app.services.qc import QCResult

SHALLOW_PROXY_CAVEAT = (
    "Values represent the shallowest QC-passed ARGO float measurement from 0–10 dbar, "
    "not satellite-derived sea-surface temperature."
)


def compose_evidence_panel(
    qc_result: QCResult,
    agg_data: dict[str, object],
    anomaly_result: AnomalyScoreResult | None,
    baseline: dict[str, Any] | None,
    grade_result: GradeResult,
    params: QueryParams,
    manifest_version: str,
    artifact_path: str | None = None,
    artifact_sha256: str | None = None,
) -> EvidencePanel:
    unit = str(agg_data.get("unit", ""))
    current_value = agg_data.get("current_value")
    value_summary = (
        f"; representative value: {float(current_value):.2f} {unit}"
        if current_value is not None
        else "; no QC-passed aggregate could be computed"
    )
    current_summary = (
        f"{qc_result.valid_profile_count} QC-passed profiles from "
        f"{qc_result.distinct_float_count} floats{value_summary}"
    )

    baseline_summary = None
    score_summary = None
    if anomaly_result is not None:
        baseline_summary = (
            f"Production baseline ({anomaly_result.baseline_period}): "
            f"{anomaly_result.baseline_mean:.2f} ± {anomaly_result.baseline_std:.2f} "
            f"{unit} (n={anomaly_result.baseline_n})"
        )
        score_summary = f"z = {anomaly_result.z_score:+.2f} ({anomaly_result.label})"
    elif baseline is not None:
        baseline_summary = (
            f"Production baseline for calendar month {int(baseline['calendar_month'])} "
            f"({int(baseline['year_min'])}–{int(baseline['year_max'])}): "
            f"{float(baseline['mean']):.2f} ± {float(baseline['std']):.2f} {unit} "
            f"(n={int(baseline['n'])})"
        )
    if anomaly_result is None and params.include_anomaly:
        score_summary = f"No z-score emitted; evidence grade is {grade_result.grade.value}."

    if params.location.region_id:
        selection_summary = (
            f"{params.location.label} region; {params.date_from} through {params.date_to}"
        )
    else:
        selection_summary = (
            f"Within {params.location.radius_km:g} km of {params.location.label}; "
            f"{params.date_from} through {params.date_to}"
        )

    trace = agg_data.get("trace") if isinstance(agg_data.get("trace"), dict) else {}
    return EvidencePanel(
        raw_profile_count=qc_result.raw_profile_count,
        valid_profile_count=qc_result.valid_profile_count,
        excluded_profile_count=qc_result.excluded_profile_count,
        raw_observation_count=qc_result.raw_count,
        valid_observation_count=qc_result.valid_count,
        excluded_observation_count=qc_result.excluded_count,
        distinct_float_count=qc_result.distinct_float_count,
        qc_pass_rate=qc_result.qc_pass_rate,
        qc_rule=qc_result.qc_rule_applied,
        exclusion_reasons=qc_result.exclusion_reasons,
        current_period_summary=current_summary,
        baseline_summary=baseline_summary,
        score_summary=score_summary,
        source_version=manifest_version,
        selection_summary=selection_summary,
        aggregation_method=str(agg_data.get("aggregation_method", "")),
        proxy_caveat=(
            SHALLOW_PROXY_CAVEAT if params.parameter is Parameter.SHALLOW_SST_PROXY else None
        ),
        artifact_path=artifact_path,
        artifact_sha256=artifact_sha256,
        contributing_profile_ids=[str(value) for value in trace.get("profile_ids", [])],
        contributing_float_ids=[str(value) for value in trace.get("float_ids", [])],
        source_record_sample=[str(value) for value in trace.get("source_records", [])],
        trace_sample_truncated=bool(trace.get("truncated", False)),
    )

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
    selection_disclosure: str | None = None,
) -> EvidencePanel:
    unit = str(agg_data.get("unit", ""))
    current_value = agg_data.get("current_value")
    value_summary = (
        f"; representative value: {float(current_value):.2f} {unit}"
        if current_value is not None
        else "; no QC-passed aggregate could be computed"
    )
    profile_word = "profile" if qc_result.valid_profile_count == 1 else "profiles"
    float_word = "float" if qc_result.distinct_float_count == 1 else "floats"
    current_summary = (
        f"{qc_result.valid_profile_count} QC-passed {profile_word} from "
        f"{qc_result.distinct_float_count} {float_word}{value_summary}"
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

    recurring_filter = ""
    if params.calendar_month:
        recurring_filter = f"; calendar month {params.calendar_month} only"
    elif params.season:
        recurring_filter = f"; {params.season.value} months only"
    if params.location.region_id:
        selection_summary = (
            f"{params.location.label} region centred at "
            f"{params.location.latitude:.2f}°, {params.location.longitude:.2f}°; "
            f"{params.date_from} through {params.date_to}{recurring_filter}"
        )
    else:
        latitude = params.location.latitude or 0.0
        longitude = params.location.longitude or 0.0
        coordinates = (
            f"{abs(latitude):.{params.location.coordinate_precision}f}°"
            f"{'N' if latitude >= 0 else 'S'}, "
            f"{abs(longitude):.{params.location.coordinate_precision}f}°"
            f"{'E' if longitude >= 0 else 'W'}"
        )
        anchor_basis = (
            "the user's requested coordinate"
            if "°" in params.location.label
            else "the application gazetteer's sea-facing search coordinate"
        )
        selection_summary = (
            f"Within {params.location.radius_km:g} km of {params.location.label} at "
            f"{coordinates}; {params.date_from} through {params.date_to}{recurring_filter}. "
            f"The anchor is {anchor_basis}; it marks the search centre, not an observation"
        )
    if selection_disclosure:
        selection_summary = f"{selection_summary}. {selection_disclosure}"

    trace = agg_data.get("trace") if isinstance(agg_data.get("trace"), dict) else {}
    bins = agg_data.get("bins") if isinstance(agg_data.get("bins"), list) else []
    depth_bins_used = [str(item["depth_bin"]) for item in bins if "depth_bin" in item]
    counts_per_bin = {
        str(item["depth_bin"]): int(item.get("profile_count", 0))
        for item in bins
        if "depth_bin" in item
    }
    float_positions: list[dict[str, object]] = []
    retained = qc_result.retained
    if not retained.empty and {"platform_number", "profile_id", "latitude", "longitude"} <= set(
        retained.columns
    ):
        grouped_positions = (
            retained.dropna(subset=["latitude", "longitude"])
            .groupby("platform_number", as_index=False)
            .agg(
                latitude=("latitude", "median"),
                longitude=("longitude", "median"),
                profile_count=("profile_id", "nunique"),
            )
            .sort_values(["profile_count", "platform_number"], ascending=[False, True])
            .head(50)
        )
        float_positions = [
            {
                "float_id": str(row.platform_number),
                "latitude": float(row.latitude),
                "longitude": float(row.longitude),
                "profile_count": int(row.profile_count),
            }
            for row in grouped_positions.itertuples(index=False)
        ]
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
        depth_bins_used=depth_bins_used,
        aggregation_counts_per_bin=counts_per_bin,
        baseline_grid_cell=baseline.get("grid_bounds") if baseline else None,
        baseline_selection_id=str(baseline["selection_id"]) if baseline else None,
        baseline_month_used=int(baseline["calendar_month"]) if baseline else None,
        baseline_distinct_float_count=(
            int(baseline.get("distinct_float_count", 0)) if baseline else None
        ),
        evidence_checks=[
            {
                "key": check.key,
                "label": check.label,
                "value": check.value,
                "threshold": check.threshold,
                "passed": check.passed,
                "detail": check.detail,
            }
            for check in grade_result.checks
        ],
        proxy_caveat=(
            SHALLOW_PROXY_CAVEAT if params.parameter is Parameter.SHALLOW_SST_PROXY else None
        ),
        artifact_path=artifact_path,
        artifact_sha256=artifact_sha256,
        contributing_profile_ids=[str(value) for value in trace.get("profile_ids", [])],
        contributing_float_ids=[str(value) for value in trace.get("float_ids", [])],
        source_record_sample=[str(value) for value in trace.get("source_records", [])],
        float_positions=float_positions,
        trace_sample_truncated=bool(trace.get("truncated", False)),
    )

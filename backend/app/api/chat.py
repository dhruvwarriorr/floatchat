from __future__ import annotations

import math
from calendar import month_abbr
from dataclasses import dataclass
from datetime import date

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.models import (
    AnomalyResult,
    ChatRequest,
    ChatResponse,
    DataSufficiency,
    ErrorDetail,
    ErrorQueryContext,
    ErrorResponse,
    ErrorType,
    EvidenceGrade,
    Parameter,
    ParameterResult,
    QueryParams,
    QueryType,
)
from app.services.aggregation import (
    aggregate,
    compute_current_mean,
    compute_supplementary_views,
)
from app.services.anomaly import (
    baseline_parameter_name,
    get_baseline_for_month,
    load_production_baseline,
    score_anomaly,
)
from app.services.data import (
    DataRepository,
    DataUnavailable,
    NoDataFound,
    apply_recurring_period_filter,
)
from app.services.evidence import compute_evidence_grade
from app.services.explain import SHALLOW_PROXY_CAVEAT, compose_evidence_panel
from app.services.parser import REGION_BOXES, UnsupportedQuery, parse_query
from app.services.parser_policy import MAX_RADIUS_KM
from app.services.qc import apply_qc_filter

router = APIRouter(tags=["chat"])


@dataclass(frozen=True)
class RetrievalDetails:
    requested_radius_km: float | None
    actual_radius_km: float | None
    radius_expanded: bool = False


AUTO_EXPANSION_RADII_KM = (500.0, 750.0)


def error_response(
    status_code: int,
    error_type: ErrorType,
    message: str,
    suggestion: str | None = None,
    *,
    understanding: str | None = None,
    understood: ErrorQueryContext | None = None,
    searched: str | None = None,
    records_found: int | None = None,
    nearest_available_km: float | None = None,
    suggested_query: str | None = None,
) -> JSONResponse:
    payload = ErrorResponse(
        error=ErrorDetail(
            type=error_type,
            message=message,
            suggestion=suggestion,
            understanding=understanding,
            understood=understood,
            searched=searched,
            records_found=records_found,
            nearest_available_km=nearest_available_km,
            suggested_query=suggested_query,
        )
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump(mode="json"))


def _retrieve(repository: DataRepository, params: QueryParams, parameter: Parameter | None = None):
    if not params.date_from or not params.date_to:
        raise UnsupportedQuery("The query did not produce a usable date range.")
    location = params.location
    if location.region_id:
        bounds = REGION_BOXES.get(location.region_id)
        if bounds is None:
            raise UnsupportedQuery("The named region is not supported by the retrieval policy.")
        return repository.get_region_records(
            *bounds,
            params.date_from,
            params.date_to,
            parameter or params.parameter,
        )
    if location.latitude is None or location.longitude is None:
        raise UnsupportedQuery("The query did not produce a usable location.")
    return repository.get_records(
        location.latitude,
        location.longitude,
        location.radius_km,
        params.date_from,
        params.date_to,
        parameter or params.parameter,
    )


def _apply_query_filters(records, params: QueryParams):
    return apply_recurring_period_filter(
        records,
        calendar_month=params.calendar_month,
        season=params.season,
    )


def _retrieve_with_auto_expansion(
    repository: DataRepository, params: QueryParams, parameter: Parameter
):
    """Retrieve a point selection, widening only an implicit radius when empty."""

    location = params.location
    requested_radius = None if location.region_id else location.radius_km
    details = RetrievalDetails(
        requested_radius_km=requested_radius,
        actual_radius_km=requested_radius,
    )
    records = _apply_query_filters(_retrieve(repository, params, parameter), params)
    if not records.empty or location.region_id or location.radius_explicit:
        return records, params, details

    for expanded_radius in AUTO_EXPANSION_RADII_KM:
        if expanded_radius <= location.radius_km:
            continue
        expanded_location = location.model_copy(update={"radius_km": expanded_radius})
        expanded_params = params.model_copy(update={"location": expanded_location})
        records = _apply_query_filters(
            _retrieve(repository, expanded_params, parameter), expanded_params
        )
        if not records.empty:
            return records, expanded_params, RetrievalDetails(
                requested_radius_km=requested_radius,
                actual_radius_km=expanded_radius,
                radius_expanded=True,
            )

    return records, params, details


def _baseline_month(params: QueryParams, agg_data: dict[str, object]) -> int:
    if params.calendar_month:
        return params.calendar_month
    if params.month:
        return params.month
    if params.query_type is QueryType.TIME_SERIES:
        series = agg_data.get("series")
        if isinstance(series, list) and series:
            month = str(series[-1].get("month", ""))
            if len(month) >= 7:
                return int(month[5:7])
    return date.fromisoformat(params.date_to or "2026-12-31").month


def _location_detail(params: QueryParams) -> str:
    def coordinate(value: float, positive: str, negative: str, precision: int = 2) -> str:
        hemisphere = positive if value >= 0 else negative
        return f"{abs(value):.{precision}f}°{hemisphere}"

    if (
        not params.location.region_id
        and params.location.latitude is not None
        and params.location.longitude is not None
    ):
        latitude = params.location.latitude
        longitude = params.location.longitude
        precision = params.location.coordinate_precision
        location_detail = (
            f"{params.location.label} "
            f"({abs(latitude):.{precision}f}°{'N' if latitude >= 0 else 'S'}, "
            f"{abs(longitude):.{precision}f}°{'E' if longitude >= 0 else 'W'}, "
            f"{params.location.radius_km:g} km radius)"
        )
        return location_detail
    bounds = params.location.bounds
    if bounds:
        return (
            f"{params.location.label} (centre "
            f"{coordinate(params.location.latitude, 'N', 'S')}, "
            f"{coordinate(params.location.longitude, 'E', 'W')}; bounds "
            f"{coordinate(bounds.south, 'N', 'S', 0)} to "
            f"{coordinate(bounds.north, 'N', 'S', 0)}, "
            f"{coordinate(bounds.west, 'E', 'W', 0)} to "
            f"{coordinate(bounds.east, 'E', 'W', 0)})"
        )
    return params.location.label


def _summary(params: QueryParams, agg_data: dict[str, object], grade: EvidenceGrade) -> str:
    unit = str(agg_data.get("unit", ""))
    current = agg_data.get("current_value")
    result_name = params.query_type.value.replace("_", " ")
    location_detail = _location_detail(params)
    if current is None:
        return (
            f"Matching records were found for {location_detail}, but no QC-passed "
            f"{result_name} value could be calculated. Evidence is {grade.value.lower()}."
        )
    return (
        f"The QC-passed {result_name} result for {location_detail} has a representative "
        f"value of {float(current):.2f} {unit}. Evidence is {grade.value.lower()}."
    )


def _interpreted_title(params: QueryParams) -> str:
    """Return a compact title that describes the accepted question, not its result."""

    if len(params.parameters) > 1:
        parameter_name = "Temperature & salinity"
    elif params.parameter is Parameter.SHALLOW_SST_PROXY:
        parameter_name = "Shallow SST proxy"
    elif params.parameter is Parameter.SALINITY:
        parameter_name = "Salinity"
    else:
        parameter_name = "Temperature"

    qualifier = {
        QueryType.PROFILE: " profile",
        QueryType.TIME_SERIES: " trend",
        QueryType.REGIONAL_AVERAGE: " average",
    }[params.query_type]
    preposition = "across" if params.location.region_id else "near"

    date_part = ""
    if params.date_from and params.date_to:
        year_from, year_to = params.date_from[:4], params.date_to[:4]
        if params.calendar_month:
            month = month_abbr[params.calendar_month]
            date_part = f", each {month} {year_from}–{year_to}"
        elif params.season and year_from != year_to:
            date_part = f", {params.season.value} {year_from}–{year_to}"
        elif params.season:
            date_part = f", {params.season.value} {year_from}"
        elif params.date_from[:7] == params.date_to[:7]:
            month = month_abbr[int(params.date_from[5:7])]
            date_part = f", {month} {year_from}"
        elif year_from == year_to:
            date_part = f", {year_from}"
        elif int(year_to) - int(year_from) <= 20:
            date_part = f", {year_from}–{year_to}"

    return f"{parameter_name}{qualifier} {preposition} {params.location.label}{date_part}"


def _retrieval_disclosure(
    params: QueryParams,
    details: RetrievalDetails,
    nearest_observation_km: float | None,
) -> str:
    if params.location.region_id or details.actual_radius_km is None:
        return ""
    if details.radius_expanded:
        text = (
            f"Data was retrieved within {details.actual_radius_km:g} km of the query anchor "
            f"(expanded from {details.requested_radius_km:g} km because no observations "
            "were available closer)."
        )
    else:
        text = f"Data was retrieved within {details.actual_radius_km:g} km of the query anchor."
    if nearest_observation_km is not None:
        text += (
            f" The nearest observation is {nearest_observation_km:.0f} km from "
            "the query anchor."
        )
    return text


def _answer_explanation(
    params: QueryParams,
    agg_data: dict[str, object],
    source: str,
    retrieval_disclosure: str,
) -> str:
    selection = (
        f"the {_location_detail(params)} named-region bounds"
        if params.location.region_id
        else f"the exact point selection {_location_detail(params)}"
    )
    recurring_filter = ""
    if params.calendar_month:
        recurring_filter = f", then kept only calendar month {params.calendar_month}"
    elif params.season:
        recurring_filter = f", then kept only {params.season.value} months"
    explanation = (
        f"Source: {source}. Records from {params.date_from} through {params.date_to} were "
        f"selected using {selection}{recurring_filter}, passed through the declared ARGO "
        f"QC/data-mode rule, "
        f"and aggregated as: {agg_data.get('aggregation_method', 'documented aggregation')}."
    )
    if retrieval_disclosure:
        explanation = f"{explanation} {retrieval_disclosure}"
    if params.parameter.value == "shallow_sst_proxy":
        explanation = f"{explanation} {SHALLOW_PROXY_CAVEAT}"
    return explanation


def _anomaly_model(anomaly_result):
    if anomaly_result is None:
        return None
    return AnomalyResult(
        z_score=anomaly_result.z_score,
        label=anomaly_result.label,
        current_value=anomaly_result.current_value,
        baseline_mean=anomaly_result.baseline_mean,
        baseline_std=anomaly_result.baseline_std,
        baseline_period=anomaly_result.baseline_period,
        baseline_n=anomaly_result.baseline_n,
        explanation=anomaly_result.explanation,
    )


def _error_context(params: QueryParams) -> ErrorQueryContext:
    return ErrorQueryContext(
        location_label=params.location.label,
        latitude=params.location.latitude,
        longitude=params.location.longitude,
        region_id=params.location.region_id,
        radius_km=params.location.radius_km,
        date_from=params.date_from or "",
        date_to=params.date_to or "",
        calendar_month=params.calendar_month,
        season=params.season,
        parameters=params.parameters,
        query_type=params.query_type,
    )


def _parameter_words(params: QueryParams) -> str:
    labels = {
        Parameter.TEMPERATURE: "temperature",
        Parameter.SALINITY: "salinity",
        Parameter.SHALLOW_SST_PROXY: "shallow-water temperature",
    }
    return " and ".join(labels[parameter] for parameter in params.parameters)


def _searched_summary(params: QueryParams) -> str:
    temporal = f"from {params.date_from} through {params.date_to}"
    if params.calendar_month:
        temporal += f", keeping only {month_abbr[params.calendar_month]} observations"
    elif params.season:
        temporal += f", keeping only {params.season.value} months"
    if params.location.region_id:
        return f"The {params.location.label} regional bounds, {temporal}."
    return f"{_location_detail(params)}, {temporal}."


def _suggested_query(params: QueryParams, radius_km: float) -> str:
    query = f"{_parameter_words(params)} near {params.location.label} within {radius_km:g} km"
    if params.calendar_month:
        query += f" every {month_abbr[params.calendar_month]}"
    elif params.season:
        query += f" during {params.season.value}"
    if params.date_from and params.date_to:
        query += f" from {params.date_from[:4]} to {params.date_to[:4]}"
    return query


def _no_data_response(
    repository: DataRepository,
    params: QueryParams,
    parameter: Parameter,
) -> JSONResponse:
    context = _error_context(params)
    searched = _searched_summary(params)
    if params.location.region_id:
        return error_response(
            404,
            ErrorType.NO_DATA,
            f"No ARGO observations matched the understood {params.location.label} selection.",
            "Try the Arabian Sea, another supported period, or a point inside the "
            "installed coverage.",
            understanding=f"The query resolved to {_location_detail(params)}.",
            understood=context,
            searched=searched,
            records_found=0,
            suggested_query="temperature across the Arabian Sea",
        )

    current_radius = params.location.radius_km
    probe_radius = min(
        MAX_RADIUS_KM,
        max(500.0, current_radius * 1.5, current_radius + 250.0),
    )
    nearest_distance: float | None = None
    if probe_radius > current_radius:
        probe_location = params.location.model_copy(update={"radius_km": probe_radius})
        probe_params = params.model_copy(update={"location": probe_location})
        probe_records = _apply_query_filters(
            _retrieve(repository, probe_params, parameter),
            params,
        )
        if not probe_records.empty and "distance_km" in probe_records:
            nearest_distance = float(probe_records["distance_km"].min())

    if nearest_distance is not None:
        suggested_radius = min(
            MAX_RADIUS_KM,
            math.ceil((nearest_distance + 25.0) / 50.0) * 50.0,
        )
        suggested = _suggested_query(params, suggested_radius)
        return error_response(
            404,
            ErrorType.NO_DATA,
            f"No observations were found within {current_radius:g} km of "
            f"{params.location.label}. The nearest matching ARGO data is approximately "
            f"{nearest_distance:.0f} km away.",
            f'Try "{suggested}".',
            understanding=f"The query resolved to {_location_detail(params)}.",
            understood=context,
            searched=searched,
            records_found=0,
            nearest_available_km=round(nearest_distance, 1),
            suggested_query=suggested,
        )

    fallback = "temperature across the Arabian Sea"
    return error_response(
        404,
        ErrorType.NO_DATA,
        f"No ARGO observations were found near {params.location.label} in the requested "
        f"period, including a diagnostic probe out to {probe_radius:g} km.",
        f'Try another period or a covered selection such as "{fallback}".',
        understanding=f"The query resolved to {_location_detail(params)}.",
        understood=context,
        searched=searched,
        records_found=0,
        suggested_query=fallback,
    )


def _build_parameter_result(
    repository: DataRepository,
    raw_records,
    params: QueryParams,
    parameter: Parameter,
    source: str,
    retrieval_details: RetrievalDetails,
) -> ParameterResult:
    parameter_params = params.model_copy(update={"parameter": parameter, "parameters": [parameter]})
    qc_result = apply_qc_filter(raw_records, parameter)
    agg_data = aggregate(qc_result, params.query_type, parameter)
    baseline_df = load_production_baseline(repository.data_dir / "baselines")
    baseline_parameter = baseline_parameter_name(parameter, params.query_type)
    baseline = get_baseline_for_month(
        baseline_df,
        baseline_parameter,
        _baseline_month(parameter_params, agg_data),
        latitude=params.location.latitude,
        longitude=params.location.longitude,
        region_id=params.location.region_id,
    )
    baseline_n = int(baseline["n"]) if baseline else 0
    baseline_std = float(baseline["std"]) if baseline else 0.0
    thresholds = repository.get_grade_thresholds()
    grade_result = compute_evidence_grade(qc_result, baseline_n, baseline_std, thresholds)
    nearest_observation_km: float | None = None
    if not params.location.region_id and "distance_km" in qc_result.retained:
        distances = qc_result.retained["distance_km"].astype(float)
        if not distances.empty and math.isfinite(float(distances.min())):
            nearest_observation_km = float(distances.min())
    disclosure = _retrieval_disclosure(params, retrieval_details, nearest_observation_km)
    current_value = compute_current_mean(agg_data, params.query_type)
    anomaly_result = None
    # The Z-score is computed whenever evidence permits and a baseline exists.
    # ``include_anomaly`` only influences summary emphasis downstream, not whether
    # the score is produced.
    if (
        grade_result.grade is not EvidenceGrade.INSUFFICIENT
        and baseline is not None
        and current_value is not None
    ):
        anomaly_result = score_anomaly(current_value, baseline, baseline_parameter)
    artifact_path, artifact_sha256 = repository.get_profile_artifact_info()
    evidence_panel = compose_evidence_panel(
        qc_result,
        agg_data,
        anomaly_result,
        baseline,
        grade_result,
        parameter_params,
        repository.get_manifest_version(),
        artifact_path,
        artifact_sha256,
        selection_disclosure=disclosure,
    )
    coverage = (
        params.location.label
        if params.location.region_id
        else f"Within {params.location.radius_km:g} km"
    )
    quality_warning = qc_result.data_quality_warning or (
        thresholds.reviewed
        and thresholds.min_qc_pass_rate is not None
        and qc_result.qc_pass_rate < thresholds.min_qc_pass_rate
    )
    # Also compute the other supported aggregation types so the UI can offer
    # every available view of the same QC-passed data (best effort).
    secondary_views: dict[str, object] = {}
    for alternate_type in (
        QueryType.PROFILE,
        QueryType.TIME_SERIES,
        QueryType.REGIONAL_AVERAGE,
    ):
        if alternate_type is params.query_type:
            continue
        try:
            # Secondary views are illustrative and never render per-row traces,
            # so skip the expensive source-record tracing to keep latency low.
            alternate_agg = aggregate(qc_result, alternate_type, parameter, with_trace=False)
        except Exception:
            continue
        if alternate_agg.get("current_value") is not None:
            secondary_views[alternate_type.value] = alternate_agg
    paired_records = None
    try:
        paired_parameter = (
            Parameter.SALINITY
            if parameter in {Parameter.TEMPERATURE, Parameter.SHALLOW_SST_PROXY}
            else Parameter.TEMPERATURE
        )
        # T-S and density views require rows that passed the declared adjusted
        # QC rule for both measurements. Re-filtering the already-retained frame
        # keeps rejected values out of supplementary calculations.
        paired_records = apply_qc_filter(qc_result.retained, paired_parameter).retained
    except (KeyError, ValueError):
        paired_records = None
    supplementary_data = compute_supplementary_views(
        qc_result.retained,
        parameter,
        baseline_df,
        qc_result.value_col,
        paired_records,
        latitude=params.location.latitude,
        longitude=params.location.longitude,
        region_id=params.location.region_id,
    )
    return ParameterResult(
        parameter=parameter,
        summary=(
            f"{_summary(parameter_params, agg_data, grade_result.grade)} {disclosure}"
            if disclosure
            else _summary(parameter_params, agg_data, grade_result.grade)
        ),
        data=agg_data,
        anomaly=_anomaly_model(anomaly_result),
        evidence_grade=grade_result.grade,
        evidence_grade_reasons=grade_result.reasons,
        evidence_panel=evidence_panel,
        data_quality_warning=quality_warning,
        answer_explanation=_answer_explanation(parameter_params, agg_data, source, disclosure),
        data_sufficiency=DataSufficiency(
            profile_count=qc_result.valid_profile_count,
            coverage=coverage,
            coverage_radius_km=retrieval_details.actual_radius_km,
            requested_radius_km=retrieval_details.requested_radius_km,
            actual_radius_km=retrieval_details.actual_radius_km,
            radius_expanded=retrieval_details.radius_expanded,
            nearest_observation_km=nearest_observation_km,
        ),
        secondary_views=secondary_views,
        supplementary_data=supplementary_data,
    )


@router.post("/chat")
def chat(request: ChatRequest) -> JSONResponse:
    try:
        params = parse_query(request.query)
    except UnsupportedQuery as exc:
        return error_response(
            422,
            ErrorType.PARSE_ERROR,
            str(exc),
            "Ask about temperature or salinity at an Indian Ocean location; dates are optional.",
            understanding="No safe structured Indian Ocean selection could be formed.",
        )

    repository = DataRepository(get_settings().data_dir)
    try:
        retrieval_parameter = Parameter.ALL if len(params.parameters) > 1 else params.parameters[0]
        raw_records, params, retrieval_details = _retrieve_with_auto_expansion(
            repository, params, retrieval_parameter
        )
        if raw_records.empty:
            return _no_data_response(repository, params, retrieval_parameter)
        version = repository.get_manifest_version()
        source = f"{repository.get_source_name()} • dataset {version}"
        results = {
            parameter.value: _build_parameter_result(
                repository, raw_records, params, parameter, source, retrieval_details
            )
            for parameter in params.parameters
        }
        primary = results[params.parameters[0].value]
        summary = primary.summary
        if len(results) > 1:
            summary = (
                f"Temperature and salinity were analysed independently for "
                f"{_location_detail(params)}; switch the chart to inspect either result."
            )
            disclosure = _retrieval_disclosure(
                params,
                retrieval_details,
                primary.data_sufficiency.nearest_observation_km,
            )
            if disclosure:
                summary = f"{summary} {disclosure}"
        response = ChatResponse(
            interpreted_title=_interpreted_title(params),
            summary=summary,
            query_type=params.query_type,
            params=params,
            data=primary.data,
            anomaly=primary.anomaly,
            evidence_grade=primary.evidence_grade,
            evidence_grade_reasons=primary.evidence_grade_reasons,
            evidence_panel=primary.evidence_panel,
            data_quality_warning=any(value.data_quality_warning for value in results.values()),
            answer_explanation=primary.answer_explanation,
            data_sufficiency=primary.data_sufficiency,
            parser_used=params.parser_used,
            source=source,
            results_by_parameter=results,
            secondary_views=primary.secondary_views,
            supplementary_data=primary.supplementary_data,
        )
        return JSONResponse(status_code=200, content=response.model_dump(mode="json"))
    except NoDataFound:
        return _no_data_response(repository, params, retrieval_parameter)
    except UnsupportedQuery as exc:
        return error_response(
            422,
            ErrorType.PARSE_ERROR,
            str(exc),
            "Rephrase the location or date.",
            understanding=f"The query resolved to {_location_detail(params)}.",
            understood=_error_context(params),
            searched=_searched_summary(params),
        )
    except DataUnavailable:
        return error_response(
            503,
            ErrorType.GENERAL_ERROR,
            "The scientific dataset is not ready for queries yet.",
            "Run the documented preprocessing and baseline commands, then try again.",
            understanding=f"The query resolved to {_location_detail(params)}.",
            understood=_error_context(params),
            searched=_searched_summary(params),
        )
    except Exception:
        return error_response(
            500,
            ErrorType.GENERAL_ERROR,
            "The request could not be completed safely.",
            "Please retry or rephrase the question.",
            understanding=f"The query resolved to {_location_detail(params)}.",
            understood=_error_context(params),
            searched=_searched_summary(params),
        )

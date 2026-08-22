from __future__ import annotations

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
from app.services.data import DataRepository, DataUnavailable, NoDataFound
from app.services.evidence import compute_evidence_grade
from app.services.explain import SHALLOW_PROXY_CAVEAT, compose_evidence_panel
from app.services.parser import REGION_BOXES, UnsupportedQuery, parse_query
from app.services.qc import apply_qc_filter

router = APIRouter(tags=["chat"])


def error_response(
    status_code: int,
    error_type: ErrorType,
    message: str,
    suggestion: str | None = None,
) -> JSONResponse:
    payload = ErrorResponse(
        error=ErrorDetail(type=error_type, message=message, suggestion=suggestion)
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


def _baseline_month(params: QueryParams, agg_data: dict[str, object]) -> int:
    if params.month:
        return params.month
    if params.query_type is QueryType.TIME_SERIES:
        series = agg_data.get("series")
        if isinstance(series, list) and series:
            month = str(series[-1].get("month", ""))
            if len(month) >= 7:
                return int(month[5:7])
    return date.fromisoformat(params.date_to or "2026-12-31").month


def _summary(params: QueryParams, agg_data: dict[str, object], grade: EvidenceGrade) -> str:
    unit = str(agg_data.get("unit", ""))
    current = agg_data.get("current_value")
    result_name = params.query_type.value.replace("_", " ")
    if current is None:
        return (
            f"Matching records were found for {params.location.label}, but no QC-passed "
            f"{result_name} value could be calculated. Evidence is {grade.value.lower()}."
        )
    return (
        f"The QC-passed {result_name} result for {params.location.label} has a representative "
        f"value of {float(current):.2f} {unit}. Evidence is {grade.value.lower()}."
    )


def _answer_explanation(params: QueryParams, agg_data: dict[str, object], source: str) -> str:
    selection = (
        f"the {params.location.label} named region"
        if params.location.region_id
        else f"a {params.location.radius_km:g} km radius around {params.location.label}"
    )
    explanation = (
        f"Source: {source}. Records from {params.date_from} through {params.date_to} were "
        f"selected using {selection}, passed through the declared ARGO QC/data-mode rule, "
        f"and aggregated as: {agg_data.get('aggregation_method', 'documented aggregation')}."
    )
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


def _build_parameter_result(
    repository: DataRepository,
    raw_records,
    params: QueryParams,
    parameter: Parameter,
    source: str,
) -> ParameterResult:
    parameter_params = params.model_copy(
        update={"parameter": parameter, "parameters": [parameter]}
    )
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
            alternate_agg = aggregate(qc_result, alternate_type, parameter)
        except Exception:
            continue
        if alternate_agg.get("current_value") is not None:
            secondary_views[alternate_type.value] = alternate_agg
    supplementary_data = compute_supplementary_views(
        qc_result.retained,
        parameter,
        baseline_df,
        qc_result.value_col,
        latitude=params.location.latitude,
        longitude=params.location.longitude,
        region_id=params.location.region_id,
    )
    return ParameterResult(
        parameter=parameter,
        summary=_summary(parameter_params, agg_data, grade_result.grade),
        data=agg_data,
        anomaly=_anomaly_model(anomaly_result),
        evidence_grade=grade_result.grade,
        evidence_grade_reasons=grade_result.reasons,
        evidence_panel=evidence_panel,
        data_quality_warning=quality_warning,
        answer_explanation=_answer_explanation(parameter_params, agg_data, source),
        data_sufficiency=DataSufficiency(
            profile_count=qc_result.valid_profile_count,
            coverage=coverage,
            coverage_radius_km=None if params.location.region_id else params.location.radius_km,
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
            "Include an Indian Ocean location or coordinates, temperature/salinity, and a date.",
        )

    repository = DataRepository(get_settings().data_dir)
    try:
        retrieval_parameter = Parameter.ALL if len(params.parameters) > 1 else params.parameters[0]
        raw_records = _retrieve(repository, params, retrieval_parameter)
        if raw_records.empty:
            raise NoDataFound
        version = repository.get_manifest_version()
        source = f"{repository.get_source_name()} • dataset {version}"
        results = {
            parameter.value: _build_parameter_result(
                repository, raw_records, params, parameter, source
            )
            for parameter in params.parameters
        }
        primary = results[params.parameters[0].value]
        summary = primary.summary
        if len(results) > 1:
            summary = (
                f"Temperature and salinity were analysed independently for "
                f"{params.location.label}; switch the chart to inspect either result."
            )
        response = ChatResponse(
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
        return error_response(
            404,
            ErrorType.NO_DATA,
            "No observations in the installed Arabian Sea ARGO subset match that "
            "location and date range.",
            "Try a wider radius, another period, or a location within the Arabian Sea coverage.",
        )
    except UnsupportedQuery as exc:
        return error_response(
            422,
            ErrorType.PARSE_ERROR,
            str(exc),
            "Rephrase the location or date.",
        )
    except DataUnavailable:
        return error_response(
            503,
            ErrorType.GENERAL_ERROR,
            "The scientific dataset is not ready for queries yet.",
            "Run the documented preprocessing and baseline commands, then try again.",
        )
    except Exception:
        return error_response(
            500,
            ErrorType.GENERAL_ERROR,
            "The request could not be completed safely.",
            "Please retry or rephrase the question.",
        )

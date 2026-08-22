from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class QueryType(StrEnum):
    PROFILE = "profile"
    REGIONAL_AVERAGE = "regional_average"
    TIME_SERIES = "time_series"


class Parameter(StrEnum):
    TEMPERATURE = "temperature"
    SALINITY = "salinity"
    SHALLOW_SST_PROXY = "shallow_sst_proxy"
    ALL = "all"


class ParserUsed(StrEnum):
    LLM = "llm"
    RULE_BASED = "rule_based"


class Confidence(StrEnum):
    """Legacy illustrative/profile-count tier used by the current anomaly scaffold."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class EvidenceGrade(StrEnum):
    INSUFFICIENT = "Insufficient"
    INDICATIVE = "Indicative"
    SUPPORTED = "Supported"


class ErrorType(StrEnum):
    PARSE_ERROR = "parse_error"
    NO_DATA = "no_data"
    GENERAL_ERROR = "general_error"


class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def reject_blank_query(self) -> ChatRequest:
        if not self.query.strip():
            raise ValueError("query must contain non-whitespace text")
        return self


class GeographicBounds(BaseModel):
    """Canonical selection rectangle for a named region.

    Populated from the backend ``REGION_BOXES`` source of truth so the frontend
    map never re-derives or drifts from the scientific selection bounds.
    """

    south: float = Field(ge=-90, le=90)
    west: float = Field(ge=-180, le=180)
    north: float = Field(ge=-90, le=90)
    east: float = Field(ge=-180, le=180)

    @model_validator(mode="after")
    def validate_extent(self) -> GeographicBounds:
        if self.south >= self.north:
            raise ValueError("south must be less than north")
        if self.west >= self.east:
            raise ValueError("west must be less than east")
        return self


class QueryLocation(BaseModel):
    label: str
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    region_id: str | None = None
    radius_km: float = Field(default=100.0, ge=1.0, le=2000.0)
    bounds: GeographicBounds | None = None
    coordinate_precision: int = Field(default=2, ge=0, le=4)

    @model_validator(mode="after")
    def require_coordinates_or_region(self) -> QueryLocation:
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("location coordinates must be supplied as a complete pair")
        has_coordinates = self.latitude is not None and self.longitude is not None
        if not has_coordinates:
            raise ValueError("location requires a display centre coordinate pair")
        if self.region_id and self.bounds is None:
            raise ValueError("named-region locations require canonical bounds")
        if not self.region_id and self.bounds is not None:
            raise ValueError("point locations cannot carry regional bounds")
        return self


class QueryParams(BaseModel):
    query_type: QueryType
    parameter: Parameter
    parameters: list[Parameter] = Field(default_factory=list, min_length=1, max_length=2)
    location: QueryLocation
    year_start: int | None = Field(default=None, ge=2000, le=2100)
    year_end: int | None = Field(default=None, ge=2000, le=2100)
    month: int | None = Field(default=None, ge=1, le=12)
    anomaly_requested: bool = False
    date_from: str | None = None
    date_to: str | None = None
    include_anomaly: bool = False
    parser_used: ParserUsed

    @field_validator("date_from", "date_to")
    @classmethod
    def validate_iso_date(cls, value: str | None) -> str | None:
        if value is None:
            return None
        from datetime import date

        date.fromisoformat(value)
        return value

    @model_validator(mode="after")
    def validate_year_order(self) -> QueryParams:
        if self.year_start and self.year_end and self.year_start > self.year_end:
            raise ValueError("year_start cannot be later than year_end")
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from cannot be later than date_to")
        if self.include_anomaly != self.anomaly_requested:
            enabled = self.include_anomaly or self.anomaly_requested
            self.include_anomaly = enabled
            self.anomaly_requested = enabled
        if not self.parameters:
            self.parameters = (
                [Parameter.TEMPERATURE, Parameter.SALINITY]
                if self.parameter is Parameter.ALL
                else [self.parameter]
            )
        deduplicated = list(dict.fromkeys(self.parameters))
        if Parameter.ALL in deduplicated:
            deduplicated = [Parameter.TEMPERATURE, Parameter.SALINITY]
        self.parameters = deduplicated
        self.parameter = Parameter.ALL if len(deduplicated) > 1 else deduplicated[0]
        return self


class DataSufficiency(BaseModel):
    profile_count: int = Field(ge=0)
    coverage: str
    coverage_radius_km: float | None = Field(default=None, ge=0)


class EvidencePanel(BaseModel):
    raw_profile_count: int = Field(ge=0)
    valid_profile_count: int = Field(ge=0)
    excluded_profile_count: int = Field(ge=0)
    raw_observation_count: int = Field(default=0, ge=0)
    valid_observation_count: int = Field(default=0, ge=0)
    excluded_observation_count: int = Field(default=0, ge=0)
    distinct_float_count: int = Field(ge=0)
    qc_pass_rate: float = Field(ge=0, le=1)
    qc_rule: str
    exclusion_reasons: dict[str, int] = Field(default_factory=dict)
    current_period_summary: str
    baseline_summary: str | None = None
    score_summary: str | None = None
    source_version: str | None = None
    selection_summary: str | None = None
    aggregation_method: str | None = None
    proxy_caveat: str | None = None
    artifact_path: str | None = None
    artifact_sha256: str | None = None
    contributing_profile_ids: list[str] = Field(default_factory=list)
    contributing_float_ids: list[str] = Field(default_factory=list)
    source_record_sample: list[str] = Field(default_factory=list)
    trace_sample_truncated: bool = False


class AnomalyResult(BaseModel):
    z_score: float
    label: str
    current_value: float
    baseline_mean: float
    baseline_std: float = Field(gt=0)
    baseline_period: str
    baseline_n: int = Field(gt=0)
    explanation: str


class ParameterResult(BaseModel):
    parameter: Parameter
    summary: str
    data: dict[str, Any]
    anomaly: AnomalyResult | None = None
    evidence_grade: EvidenceGrade
    evidence_grade_reasons: list[str] = Field(min_length=1)
    evidence_panel: EvidencePanel
    data_quality_warning: bool
    answer_explanation: str
    data_sufficiency: DataSufficiency
    secondary_views: dict[str, Any] = Field(default_factory=dict)
    supplementary_data: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    summary: str
    query_type: QueryType
    params: QueryParams
    data: dict[str, Any]
    anomaly: AnomalyResult | None = None
    evidence_grade: EvidenceGrade
    evidence_grade_reasons: list[str] = Field(min_length=1)
    evidence_panel: EvidencePanel
    data_quality_warning: bool
    answer_explanation: str
    data_sufficiency: DataSufficiency
    parser_used: ParserUsed
    source: str
    results_by_parameter: dict[str, ParameterResult] = Field(default_factory=dict)
    secondary_views: dict[str, Any] = Field(default_factory=dict)
    supplementary_data: dict[str, Any] = Field(default_factory=dict)


class ErrorDetail(BaseModel):
    type: ErrorType
    message: str
    suggestion: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail

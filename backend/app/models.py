from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class QueryType(StrEnum):
    PROFILE = "profile"
    REGIONAL_AVERAGE = "regional_average"
    TIME_SERIES = "time_series"


class Parameter(StrEnum):
    TEMPERATURE = "temperature"
    SALINITY = "salinity"
    SHALLOW_SST_PROXY = "shallow_sst_proxy"


class ParserUsed(StrEnum):
    LLM = "llm"
    RULE_BASED = "rule_based"


class Confidence(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


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


class QueryLocation(BaseModel):
    label: str
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    region_id: str | None = None


class QueryParams(BaseModel):
    query_type: QueryType
    parameter: Parameter
    location: QueryLocation
    year_start: int | None = Field(default=None, ge=2000, le=2100)
    year_end: int | None = Field(default=None, ge=2000, le=2100)
    month: int | None = Field(default=None, ge=1, le=12)
    anomaly_requested: bool = False
    parser_used: ParserUsed

    @model_validator(mode="after")
    def validate_year_order(self) -> QueryParams:
        if self.year_start and self.year_end and self.year_start > self.year_end:
            raise ValueError("year_start cannot be later than year_end")
        return self


class DataSufficiency(BaseModel):
    profile_count: int = Field(ge=0)
    coverage: str
    confidence: Confidence


class AnomalyResult(BaseModel):
    z_score: float
    label: str
    baseline_mean: float
    baseline_std: float = Field(gt=0)
    baseline_period: str
    provisional: bool


class ChatResponse(BaseModel):
    summary: str
    query_type: QueryType
    params: QueryParams
    data: list[dict[str, Any]]
    anomaly: AnomalyResult | None = None
    answer_explanation: str
    data_sufficiency: DataSufficiency
    parser_used: ParserUsed
    source: str


class ErrorDetail(BaseModel):
    type: ErrorType
    message: str
    suggestion: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail

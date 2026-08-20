from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.models import ChatRequest, ErrorDetail, ErrorResponse, ErrorType
from app.services.data import DataRepository, DataUnavailable
from app.services.parser import UnsupportedQuery, parse_rule_based

router = APIRouter(tags=["chat"])


def error_response(
    status_code: int, error_type: ErrorType, message: str, suggestion: str | None = None
) -> JSONResponse:
    payload = ErrorResponse(
        error=ErrorDetail(type=error_type, message=message, suggestion=suggestion)
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump(mode="json"))


@router.post("/chat")
def chat(request: ChatRequest) -> JSONResponse:
    try:
        params = parse_rule_based(request.query)
    except UnsupportedQuery:
        return error_response(
            422,
            ErrorType.PARSE_ERROR,
            "I could not map that question to a supported ocean-data query.",
            "Include a supported location, parameter, and year or year range.",
        )

    repository = DataRepository(get_settings().data_dir)
    try:
        repository.query(params)
    except DataUnavailable:
        return error_response(
            503,
            ErrorType.GENERAL_ERROR,
            "The scientific dataset is not ready for queries yet.",
            "Try again after the versioned ARGO subset and baselines are installed.",
        )

    return error_response(
        500,
        ErrorType.GENERAL_ERROR,
        "The request could not be completed safely.",
        "Please retry or rephrase the question.",
    )

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.services.data import DataRepository

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
def live() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
def ready() -> JSONResponse:
    repository = DataRepository(get_settings().data_dir)
    is_ready, reason = repository.readiness()
    return JSONResponse(
        status_code=200 if is_ready else 503,
        content={"status": "ready" if is_ready else "not_ready", "reason": reason},
    )

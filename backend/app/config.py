from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

from app.services.parser_policy import DEFAULT_RADIUS_KM

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPOSITORY_ROOT / ".env", override=False)


def _project_path(value: str | Path) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = REPOSITORY_ROOT / path
    return path.resolve()


@dataclass(frozen=True)
class EvidenceGradeThresholds:
    """Central evidence policy.

    Thresholds are centralized so the response, tests, and manifest use one
    auditable policy. Deployments can replace them through the data manifest.
    """

    min_valid_profiles: int = 5
    min_baseline_n: int | None = 10
    min_distinct_floats: int | None = 2
    min_qc_pass_rate: float | None = 0.3
    coverage_rule: str | None = "at_least_two_distinct_floats"
    reviewed: bool = True


@dataclass(frozen=True)
class Settings:
    environment: str
    data_dir: Path
    static_dir: Path
    llm_timeout: float
    default_radius_km: float
    grade_thresholds: EvidenceGradeThresholds
    cors_origins: tuple[str, ...]


@lru_cache
def get_settings() -> Settings:
    cors_origins = tuple(
        origin.strip()
        for origin in os.getenv(
            "FLOATCHAT_CORS_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000",
        ).split(",")
        if origin.strip()
    )
    return Settings(
        environment=os.getenv("FLOATCHAT_ENV", "development"),
        data_dir=_project_path(os.getenv("FLOATCHAT_DATA_DIR", "data")),
        static_dir=_project_path(os.getenv("FLOATCHAT_STATIC_DIR", "frontend/dist")),
        llm_timeout=float(os.getenv("FLOATCHAT_LLM_TIMEOUT_SECONDS", "8")),
        default_radius_km=DEFAULT_RADIUS_KM,
        grade_thresholds=EvidenceGradeThresholds(),
        cors_origins=cors_origins,
    )

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    environment: str
    data_dir: Path
    static_dir: Path


@lru_cache
def get_settings() -> Settings:
    return Settings(
        environment=os.getenv("FLOATCHAT_ENV", "development"),
        data_dir=Path(os.getenv("FLOATCHAT_DATA_DIR", REPOSITORY_ROOT / "data")).resolve(),
        static_dir=Path(
            os.getenv("FLOATCHAT_STATIC_DIR", REPOSITORY_ROOT / "frontend" / "dist")
        ).resolve(),
    )

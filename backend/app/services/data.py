from __future__ import annotations

import json
from pathlib import Path

from app.models import QueryParams


class DataUnavailable(RuntimeError):
    """Raised until a validated query-ready dataset is installed."""


class DataRepository:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.manifest_path = data_dir / "manifest.json"

    def readiness(self) -> tuple[bool, str]:
        if not self.manifest_path.is_file():
            return False, "data manifest is missing"

        try:
            manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return False, "data manifest is unreadable"

        if manifest.get("status") != "ready":
            return False, "data manifest is not marked ready"

        artifacts = manifest.get("artifacts", [])
        if not artifacts:
            return False, "data manifest has no artifacts"

        for artifact in artifacts:
            relative_path = artifact.get("path")
            if not relative_path or not (self.data_dir / relative_path).is_file():
                return False, "a declared data artifact is missing"

        return True, "query-ready artifacts are present"

    def query(self, _params: QueryParams) -> list[dict[str, object]]:
        ready, reason = self.readiness()
        if not ready:
            raise DataUnavailable(reason)

        raise DataUnavailable(
            "A manifest is present, but scientific repository queries are not implemented yet."
        )

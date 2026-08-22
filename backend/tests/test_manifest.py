import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def test_generated_manifest_matches_schema_and_artifact_hashes() -> None:
    manifest_path = ROOT / "data" / "manifest.json"
    if not manifest_path.is_file():
        pytest.skip("scientific artifacts have not been generated")

    schema = json.loads((ROOT / "data" / "manifest.schema.json").read_text())
    manifest = json.loads(manifest_path.read_text())
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(manifest)

    for artifact in manifest["artifacts"]:
        artifact_path = (ROOT / "data" / artifact["path"]).resolve()
        artifact_path.relative_to((ROOT / "data").resolve())
        assert artifact_path.is_file()
        assert artifact_path.stat().st_size == artifact["size_bytes"]
        assert sha256_file(artifact_path) == artifact["sha256"]

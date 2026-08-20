"""Compare accepted frontend files with their blobs in the current Git HEAD."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def git_output(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    head_paths = git_output("ls-tree", "-r", "--name-only", "HEAD").splitlines()
    already_structured = "frontend/package.json" in head_paths
    ignored_legacy_paths = {".gitignore"}
    mismatches: list[str] = []

    for head_path in head_paths:
        if already_structured:
            if not head_path.startswith("frontend/"):
                continue
            target = ROOT / head_path
        else:
            if head_path in ignored_legacy_paths:
                continue
            target = ROOT / "frontend" / head_path

        expected = subprocess.run(
            ["git", "show", f"HEAD:{head_path}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        ).stdout

        if not target.is_file() or digest(target.read_bytes()) != digest(expected):
            mismatches.append(str(target.relative_to(ROOT)))

    if mismatches:
        print("Frontend boundary mismatch:")
        for path in mismatches:
            print(f"- {path}")
        return 1

    print("Frontend files match the accepted Git blobs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

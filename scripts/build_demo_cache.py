"""Capture sanitized API outputs for the three rehearsed demo paths."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from httpx import ASGITransport, AsyncClient

ROOT = Path(__file__).resolve().parents[1]

QUERIES = {
    "profile_mumbai_apr2024.json": (
        "Show temperature profile near Mumbai in April 2024"
    ),
    "timeseries_chennai_2015_2025.json": (
        "Plot SST time series near Chennai from 2015-2025 and tell me if it is unusual"
    ),
    "regional_bob_salinity_2023.json": (
        "Show average salinity in the Bay of Bengal in 2023"
    ),
    "mumbai_profile_july2024.json": (
        "Show temperature profile near Mumbai in July 2024"
    ),
    "mumbai_sst_timeseries_2015_2024.json": (
        "Plot SST time series at 19N, 72.8E from 2015-2024 and tell me if it is unusual"
    ),
    "bay_of_bengal_salinity_2023.json": (
        "Show average salinity in the Bay of Bengal in 2023"
    ),
    "profile_10n70e_jul2024.json": (
        "Show temperature profile at 10N 70E within 150 km in July 2024"
    ),
    "timeseries_10n70e_2015_2024.json": (
        "Plot SST time series at 10N 70E within 150 km from 2015-2024 "
        "and tell me if it is unusual"
    ),
    "regional_arabian_salinity_2023.json": (
        "Show average salinity in the Arabian Sea in 2023"
    ),
}


async def capture(data_dir: Path, output_dir: Path) -> None:
    os.environ["FLOATCHAT_DATA_DIR"] = str(data_dir)
    for key in (
        "GEMINI_API_KEY",
        "FLOATCHAT_LLM_API_KEY",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
    ):
        os.environ[key] = ""
    sys.path.insert(0, str(ROOT / "backend"))
    from app.config import get_settings
    from app.main import create_app

    get_settings.cache_clear()
    app = create_app()
    transport = ASGITransport(app=app)
    output_dir.mkdir(parents=True, exist_ok=True)
    async with AsyncClient(
        transport=transport, base_url="http://cache.local"
    ) as client:
        for filename, query in QUERIES.items():
            response = await client.post("/chat", json={"query": query})
            payload = response.json()
            if "error" not in payload:
                payload["source"] = f"{payload['source']} (demo cache)"
                payload["answer_explanation"] = (
                    "Cached demo response captured from the local API. "
                    f"{payload['answer_explanation']}"
                )
            serialized = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
            forbidden = [str(ROOT), "sk-", "api_key", "traceback"]
            if any(value.lower() in serialized.lower() for value in forbidden):
                raise RuntimeError(
                    f"Refusing to cache an unsafe response for {filename}"
                )
            (output_dir / filename).write_text(serialized, encoding="utf-8")
            print(f"{filename}: HTTP {response.status_code}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument(
        "--output-dir", type=Path, default=ROOT / "demo" / "cached_responses"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    asyncio.run(capture(args.data_dir.resolve(), args.output_dir.resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

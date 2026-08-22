"""Measure deterministic and optional-provider parser behavior on a frozen prompt set."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import statistics
import sys
import time
from contextlib import nullcontext
from pathlib import Path
from typing import Any
from unittest.mock import patch

from httpx import ASGITransport, AsyncClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.main import app
from app.services.parser import UnsupportedQuery, parse_query


def percentile_95(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, int(0.95 * len(ordered) + 0.999999) - 1)]


def matches_expected(parsed: Any, expected: dict[str, Any]) -> bool:
    actual = parsed.model_dump(mode="json")
    checks = {
        "query_type": actual["query_type"],
        "parameter": actual["parameter"],
        "location": actual["location"]["label"],
        "date_from": actual["date_from"],
        "date_to": actual["date_to"],
        "include_anomaly": actual["include_anomaly"],
        "radius_km": actual["location"]["radius_km"],
    }
    return all(checks.get(key) == value for key, value in expected.items())


def run_mode(
    fixtures: list[dict[str, Any]],
    mode: str,
    repetitions: int,
) -> dict[str, Any]:
    original_environment = {
        "FLOATCHAT_LLM_API_KEY": os.environ.get("FLOATCHAT_LLM_API_KEY")
    }
    if mode == "disabled":
        for key in original_environment:
            os.environ.pop(key, None)
        provider_context = nullcontext()
    elif mode == "simulated_failure":
        os.environ["FLOATCHAT_LLM_API_KEY"] = "test-key-never-sent"
        provider_context = patch(
            "app.services.parser.parse_llm",
            side_effect=UnsupportedQuery("simulated provider failure"),
        )
    elif mode == "enabled":
        if not any(original_environment.values()):
            return {
                "mode": mode,
                "status": "skipped",
                "reason": "no provider key configured",
            }
        provider_context = nullcontext()
    else:
        raise ValueError(f"Unknown mode: {mode}")

    details: list[dict[str, Any]] = []
    latencies: list[float] = []
    correct = 0
    invalid_outputs = 0
    llm_used = 0
    fallback_used = 0
    total_runs = len(fixtures) * repetitions
    try:
        with provider_context:
            for fixture in fixtures:
                fixture_correct = True
                outcomes: list[str] = []
                for _ in range(repetitions):
                    started = time.perf_counter()
                    try:
                        parsed = parse_query(fixture["query"])
                        elapsed = (time.perf_counter() - started) * 1000
                        latencies.append(elapsed)
                        expected_error = fixture.get("expected_error")
                        provider_used = parsed.parser_used.value
                        llm_used += int(provider_used == "llm")
                        fallback_used += int(provider_used == "rule_based")
                        accepted = (
                            not expected_error
                            and matches_expected(parsed, fixture.get("expected", {}))
                            and (mode != "enabled" or provider_used == "llm")
                        )
                        outcomes.append(
                            f"{'correct' if accepted else 'unexpected_success'}:{provider_used}"
                        )
                    except UnsupportedQuery:
                        elapsed = (time.perf_counter() - started) * 1000
                        latencies.append(elapsed)
                        accepted = fixture.get("expected_error") == "UnsupportedQuery"
                        outcomes.append(
                            "expected_error" if accepted else "unexpected_error"
                        )
                    except Exception as exc:  # noqa: BLE001 - report invalid output unchanged
                        elapsed = (time.perf_counter() - started) * 1000
                        latencies.append(elapsed)
                        invalid_outputs += 1
                        accepted = False
                        outcomes.append(type(exc).__name__)
                    fixture_correct &= accepted
                    correct += int(accepted)
                details.append(
                    {
                        "id": fixture["id"],
                        "correct_all_repetitions": fixture_correct,
                        "outcomes": outcomes,
                    }
                )
    finally:
        for key, value in original_environment.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    return {
        "mode": mode,
        "status": "completed",
        "fixture_count": len(fixtures),
        "repetitions": repetitions,
        "run_count": total_runs,
        "correct_count": correct,
        "success_rate": correct / total_runs if total_runs else None,
        "invalid_output_count": invalid_outputs,
        "invalid_output_rate": invalid_outputs / total_runs if total_runs else None,
        "llm_used_count": llm_used,
        "rule_based_used_count": fallback_used,
        "mean_latency_ms": statistics.fmean(latencies) if latencies else None,
        "p95_latency_ms": percentile_95(latencies),
        "details": details,
    }


async def _post_api(query: str) -> tuple[int, dict[str, Any], float]:
    transport = ASGITransport(app=app)
    started = time.perf_counter()
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/chat", json={"query": query})
    elapsed = (time.perf_counter() - started) * 1000
    return response.status_code, response.json(), elapsed


def run_api_scenarios(repetitions: int) -> dict[str, Any]:
    profile_path = ROOT / "data" / "processed" / "argo_profiles.parquet"
    if not profile_path.is_file():
        return {
            "status": "skipped",
            "reason": "query-ready local data artifact is absent",
        }

    provider_keys = ("FLOATCHAT_LLM_API_KEY",)
    provider_environment = {key: os.environ.get(key) for key in provider_keys}
    for key in provider_keys:
        os.environ.pop(key, None)

    scenarios = [
        {
            "id": "in_coverage",
            "query": "Show temperature profile at 10N 70E within 150 km in July 2024",
            "expected_status": 200,
            "check": lambda body: (
                body.get("evidence_panel", {}).get("valid_profile_count", 0) >= 5
            ),
        },
        {
            "id": "sparse_data",
            "query": "Show temperature profile at 10N 70E within 75 km in July 2024",
            "expected_status": 200,
            "check": lambda body: (
                body.get("evidence_panel", {}).get("valid_profile_count", 5) < 5
                and "valid_profiles_below_5" in body.get("evidence_grade_reasons", [])
            ),
        },
        {
            "id": "no_data",
            "query": "Average salinity in the Bay of Bengal during 2023",
            "expected_status": 404,
            "check": lambda body: body.get("error", {}).get("type") == "no_data",
        },
        {
            "id": "malformed_date",
            "query": "Temperature profile near Mumbai in 1999",
            "expected_status": 422,
            "check": lambda body: body.get("error", {}).get("type") == "parse_error",
        },
    ]
    details: list[dict[str, Any]] = []
    latencies: list[float] = []
    correct = 0
    try:
        for scenario in scenarios:
            outcomes: list[str] = []
            for _ in range(repetitions):
                status, body, elapsed = asyncio.run(_post_api(scenario["query"]))
                latencies.append(elapsed)
                safe = all(
                    token not in json.dumps(body).lower()
                    for token in ("traceback", "/users/", "authorization", "api_key")
                )
                accepted = (
                    status == scenario["expected_status"]
                    and scenario["check"](body)
                    and safe
                )
                correct += int(accepted)
                outcomes.append("correct" if accepted else f"unexpected_status_{status}")
            details.append({"id": scenario["id"], "outcomes": outcomes})

        os.environ["FLOATCHAT_LLM_API_KEY"] = "test-key-never-sent"
        with patch(
            "app.services.parser.parse_llm",
            side_effect=UnsupportedQuery("simulated provider failure"),
        ):
            status, body, elapsed = asyncio.run(_post_api(scenarios[0]["query"]))
        latencies.append(elapsed)
        fallback_ok = status == 200 and body.get("parser_used") == "rule_based"
        correct += int(fallback_ok)
        details.append(
            {
                "id": "simulated_provider_failure_fallback",
                "outcomes": [
                    "correct" if fallback_ok else f"unexpected_status_{status}"
                ],
            }
        )
    finally:
        for key, value in provider_environment.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    total_runs = len(scenarios) * repetitions + 1
    return {
        "status": "completed",
        "scenario_count": len(scenarios) + 1,
        "run_count": total_runs,
        "correct_count": correct,
        "success_rate": correct / total_runs,
        "mean_latency_ms": statistics.fmean(latencies),
        "p95_latency_ms": percentile_95(latencies),
        "details": details,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixtures",
        type=Path,
        default=ROOT / "evaluation" / "fixtures" / "parser_queries.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "evaluation" / "results" / "parser_reliability.json",
    )
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument(
        "--max-live-requests",
        type=int,
        default=50,
        help="Hard cap for enabled-provider calls; does not count local-only modes.",
    )
    parser.add_argument("--skip-api", action="store_true")
    parser.add_argument(
        "--modes",
        nargs="+",
        choices=["disabled", "simulated_failure", "enabled"],
        default=["disabled", "simulated_failure", "enabled"],
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    fixtures = json.loads(args.fixtures.read_text(encoding="utf-8"))
    if not 20 <= len(fixtures) <= 30:
        raise ValueError("The frozen reliability suite must contain 20–30 prompts")
    provider_configured = bool(os.environ.get("FLOATCHAT_LLM_API_KEY"))
    projected_live_requests = (
        len(fixtures) * args.repetitions
        if "enabled" in args.modes and provider_configured
        else 0
    )
    if projected_live_requests > args.max_live_requests:
        raise ValueError(
            f"Enabled mode would make {projected_live_requests} calls; "
            f"cap is {args.max_live_requests}."
        )
    mode_results = [run_mode(fixtures, mode, args.repetitions) for mode in args.modes]
    enabled_result = next(
        (result for result in mode_results if result.get("mode") == "enabled"),
        None,
    )
    live_requests = (
        int(enabled_result.get("run_count", 0))
        if enabled_result and enabled_result.get("status") == "completed"
        else 0
    )
    results = {
        "status": "generated_not_reviewed",
        "fixture_path": str(args.fixtures.relative_to(ROOT)),
        "python": sys.version,
        "results": mode_results,
        "live_provider_request_count": live_requests,
        "live_provider_request_cap": args.max_live_requests,
        "api_scenarios": (
            {"status": "skipped_by_cli"}
            if args.skip_api
            else run_api_scenarios(args.repetitions)
        ),
        "claim_gate": (
            "Generated metrics are not pitch evidence until reviewed and entered unchanged in "
            "docs/evidence/evidence-log.csv."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

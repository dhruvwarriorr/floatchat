"""Compare three anomaly methods on the same frozen, scientifically reviewed cases."""

from __future__ import annotations

import argparse
import csv
import json
import math
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
POSITIVE = "upper_ocean_anomaly"
NEGATIVE = "normal_ocean_state"
MEASUREMENT = "measurement_quality_problem"
AMBIGUOUS = "ambiguous_excluded"
REQUIRED_COLUMNS = {
    "case_id",
    "label",
    "current_value",
    "regional_mean",
    "regional_std",
    "unfiltered_mean",
    "unfiltered_std",
    "qc_current",
    "production_mean",
    "production_std",
    "evidence_grade",
    "eligible",
    "dataset_version",
    "label_reference",
}


def _number(row: dict[str, str], key: str) -> float | None:
    try:
        value = float(row[key])
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def _z_decision(
    current: float | None, mean: float | None, std: float | None
) -> bool | None:
    if current is None or mean is None or std is None or std <= 0:
        return None
    return abs((current - mean) / std) >= 1.5


def regional_method(row: dict[str, str]) -> bool | None:
    return _z_decision(
        _number(row, "current_value"),
        _number(row, "regional_mean"),
        _number(row, "regional_std"),
    )


def unfiltered_method(row: dict[str, str]) -> bool | None:
    return _z_decision(
        _number(row, "current_value"),
        _number(row, "unfiltered_mean"),
        _number(row, "unfiltered_std"),
    )


def full_pipeline_method(row: dict[str, str]) -> bool | None:
    if row["evidence_grade"] == "Insufficient":
        return None
    return _z_decision(
        _number(row, "qc_current"),
        _number(row, "production_mean"),
        _number(row, "production_std"),
    )


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def evaluate(
    rows: list[dict[str, str]], method: Callable[[dict[str, str]], bool | None]
) -> dict[str, Any]:
    eligible = [
        row
        for row in rows
        if row["eligible"].lower() in {"1", "true", "yes"} and row["label"] != AMBIGUOUS
    ]
    covered_binary = 0
    tp = fp = tn = fn = 0
    measurement_results = {"rejected": 0, "falsely_alerted": 0, "uncovered": 0}
    elapsed: list[float] = []
    for row in eligible:
        started = time.perf_counter()
        decision = method(row)
        elapsed.append((time.perf_counter() - started) * 1000)
        if row["label"] == MEASUREMENT:
            if decision is None:
                measurement_results["uncovered"] += 1
            elif decision:
                measurement_results["falsely_alerted"] += 1
            else:
                measurement_results["rejected"] += 1
            continue
        if decision is None:
            continue
        covered_binary += 1
        actual_positive = row["label"] == POSITIVE
        if decision and actual_positive:
            tp += 1
        elif decision and not actual_positive:
            fp += 1
        elif not decision and actual_positive:
            fn += 1
        else:
            tn += 1
    precision = _ratio(tp, tp + fp)
    recall = _ratio(tp, tp + fn)
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision is not None and recall is not None and precision + recall > 0
        else None
    )
    return {
        "eligible_cases": len(eligible),
        "covered_binary_cases": covered_binary,
        "query_coverage": _ratio(
            covered_binary,
            len([row for row in eligible if row["label"] in {POSITIVE, NEGATIVE}]),
        ),
        "confusion": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_alert_rate": _ratio(fp, fp + tn),
        "measurement_quality_cases": measurement_results,
        "mean_response_time_ms": sum(elapsed) / len(elapsed) if elapsed else None,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cases",
        type=Path,
        default=ROOT / "evaluation" / "fixtures" / "anomaly_cases.csv",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "evaluation" / "results" / "method_comparison.json",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    with args.cases.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if set(reader.fieldnames or []) != REQUIRED_COLUMNS:
            raise SystemExit(
                "The anomaly fixture columns do not match the frozen evaluation schema"
            )
        rows = list(reader)
    if not rows:
        raise SystemExit(
            "No reviewed anomaly cases exist. Add labels and references before generating metrics."
        )
    report = {
        "status": "generated_not_reviewed",
        "case_count": len(rows),
        "dataset_versions": sorted({row["dataset_version"] for row in rows}),
        "methods": {
            "regional_average": evaluate(rows, regional_method),
            "unfiltered_z_score": evaluate(rows, unfiltered_method),
            "qc_filtered_evidence_graded": evaluate(rows, full_pipeline_method),
        },
        "claim_gate": (
            "Do not quote these metrics until the cases, labels, references, and report are "
            "reviewed and logged in docs/evidence/evidence-log.csv."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

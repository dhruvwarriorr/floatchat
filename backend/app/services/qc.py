from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from app.models import Parameter

QC_RULE = (
    'position_qc="1"; data_mode in {"A","D"}; selected adjusted QC="1"; '
    "selected adjusted value present"
)


@dataclass
class QCResult:
    """Auditable output of the mandatory data-quality boundary."""

    retained: pd.DataFrame
    raw_count: int
    valid_count: int
    excluded_count: int
    exclusion_reasons: dict[str, int]
    qc_pass_rate: float
    raw_profile_count: int
    valid_profile_count: int
    excluded_profile_count: int
    distinct_float_count: int
    data_quality_warning: bool
    qc_rule_applied: str
    value_col: str


def _parameter_columns(parameter: Parameter | str) -> tuple[str, str]:
    value = parameter.value if isinstance(parameter, Parameter) else str(parameter)
    if value in {Parameter.TEMPERATURE.value, Parameter.SHALLOW_SST_PROXY.value}:
        return "temp_adjusted", "temp_adjusted_qc"
    if value == Parameter.SALINITY.value:
        return "psal_adjusted", "psal_adjusted_qc"
    raise ValueError(f"Unsupported QC parameter: {value}")


def _profile_count(frame: pd.DataFrame) -> int:
    return int(frame["profile_id"].nunique()) if "profile_id" in frame else 0


def apply_qc_filter(df: pd.DataFrame, parameter: Parameter | str) -> QCResult:
    value_col, qc_col = _parameter_columns(parameter)
    required = {"position_qc", "data_mode", qc_col, value_col, "profile_id", "platform_number"}
    missing = required - set(df.columns)
    if missing and not df.empty:
        raise ValueError("QC input is missing required audit columns")

    raw_count = len(df)
    raw_profile_count = _profile_count(df)
    if df.empty:
        return QCResult(
            retained=df.copy(),
            raw_count=0,
            valid_count=0,
            excluded_count=0,
            exclusion_reasons={},
            qc_pass_rate=0.0,
            raw_profile_count=0,
            valid_profile_count=0,
            excluded_profile_count=0,
            distinct_float_count=0,
            data_quality_warning=True,
            qc_rule_applied=QC_RULE,
            value_col=value_col,
        )

    position = df["position_qc"].astype("string").str.strip()
    mode = df["data_mode"].astype("string").str.strip().str.upper()
    adjusted_qc = df[qc_col].astype("string").str.strip()
    adjusted_value = pd.to_numeric(df[value_col], errors="coerce")

    remaining = pd.Series(True, index=df.index)
    reasons: dict[str, int] = {}
    checks = [
        ("position_qc_not_1", position.eq("1")),
        ("real_time_mode_excluded", mode.isin(["A", "D"])),
        ("adjusted_qc_not_1", adjusted_qc.eq("1")),
        ("null_adjusted_value", adjusted_value.notna()),
    ]
    for reason, accepted in checks:
        rejected_here = remaining & ~accepted.fillna(False)
        count = int(rejected_here.sum())
        if count:
            reasons[reason] = count
        remaining &= accepted.fillna(False)

    retained = df.loc[remaining].copy()
    retained[value_col] = adjusted_value.loc[remaining].astype(float)
    valid_count = len(retained)
    valid_profile_count = _profile_count(retained)
    valid_profile_ids = set(retained["profile_id"].astype(str))
    raw_profile_ids = set(df["profile_id"].astype(str))
    distinct_float_count = int(retained["platform_number"].astype(str).nunique())

    return QCResult(
        retained=retained,
        raw_count=raw_count,
        valid_count=valid_count,
        excluded_count=raw_count - valid_count,
        exclusion_reasons=reasons,
        qc_pass_rate=(valid_count / raw_count) if raw_count else 0.0,
        raw_profile_count=raw_profile_count,
        valid_profile_count=valid_profile_count,
        excluded_profile_count=len(raw_profile_ids - valid_profile_ids),
        distinct_float_count=distinct_float_count,
        data_quality_warning=valid_profile_count < 5,
        qc_rule_applied=QC_RULE,
        value_col=value_col,
    )

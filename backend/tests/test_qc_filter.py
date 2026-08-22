import pandas as pd

from app.services.qc import apply_qc_filter


def frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "profile_id": "1:1",
                "platform_number": "1",
                "position_qc": "1",
                "data_mode": "D",
                "temp_adjusted_qc": "1",
                "temp_adjusted": 28.0,
            },
            {
                "profile_id": "2:1",
                "platform_number": "2",
                "position_qc": "4",
                "data_mode": "D",
                "temp_adjusted_qc": "1",
                "temp_adjusted": 90.0,
            },
            {
                "profile_id": "3:1",
                "platform_number": "3",
                "position_qc": "1",
                "data_mode": "R",
                "temp_adjusted_qc": "1",
                "temp_adjusted": 80.0,
            },
            {
                "profile_id": "4:1",
                "platform_number": "4",
                "position_qc": "1",
                "data_mode": "A",
                "temp_adjusted_qc": "4",
                "temp_adjusted": 70.0,
            },
            {
                "profile_id": "5:1",
                "platform_number": "5",
                "position_qc": "1",
                "data_mode": "A",
                "temp_adjusted_qc": "1",
                "temp_adjusted": None,
            },
        ]
    )


def test_filter_is_auditable_and_rejected_extremes_do_not_survive() -> None:
    result = apply_qc_filter(frame(), "temperature")

    assert result.valid_count == 1
    assert result.excluded_count == 4
    assert result.retained["temp_adjusted"].tolist() == [28.0]
    assert result.exclusion_reasons == {
        "position_qc_not_1": 1,
        "real_time_mode_excluded": 1,
        "adjusted_qc_not_1": 1,
        "null_adjusted_value": 1,
    }
    assert result.data_quality_warning is True


def test_empty_frame_returns_warning_and_zero_counts() -> None:
    result = apply_qc_filter(pd.DataFrame(), "salinity")

    assert result.retained.empty
    assert result.raw_count == 0
    assert result.qc_pass_rate == 0
    assert result.data_quality_warning is True

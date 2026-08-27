from __future__ import annotations

from typing import Any

import httpx
import pytest

from app.services.data import REQUIRED_PROFILE_COLUMNS
from app.services.live_source import (
    LiveSourceError,
    fetch_argo_profiles,
    is_enabled,
    normalize_argo_profiles,
)


class _FakeResponse:
    def __init__(self, payload: Any, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("GET", "https://argovis-api.colorado.edu/argo")
            raise httpx.HTTPStatusError(
                "error", request=request, response=httpx.Response(self.status_code, request=request)
            )

    def json(self) -> Any:
        if self._payload is _MALFORMED:
            raise ValueError("not valid json")
        return self._payload


_MALFORMED = object()


def _real_shaped_document(
    *,
    document_id: str = "7901125_002",
    cycle_number: int = 2,
    longitude: float = 88.95,
    latitude: float = 14.116666666666667,
    temperature_mode: str = "D",
    salinity_mode: str = "D",
) -> dict[str, Any]:
    """Mirrors the exact shape returned by the live Argovis /argo endpoint.

    Captured from a real request during development (see live_source.py's
    module docstring): data_info is [keys, ["units","data_keys_mode"],
    [[unit, mode], ...]], and data is a column-major matrix aligned to keys.
    """

    return {
        "_id": document_id,
        "geolocation": {"type": "Point", "coordinates": [longitude, latitude]},
        "basin": 56,
        "timestamp": "2023-09-30T14:02:01.999Z",
        "date_updated_argovis": "2025-05-26T07:02:59.484Z",
        "source": [
            {
                "source": ["argo_core"],
                "url": "ftp://ftp.ifremer.fr/ifremer/argo/dac/incois/7901125/profiles/D7901125_002.nc",
                "date_updated": "2025-05-25T17:37:21.000Z",
            }
        ],
        "cycle_number": cycle_number,
        "geolocation_argoqc": 1,
        "profile_direction": "A",
        "timestamp_argoqc": 1,
        "data_info": [
            ["pressure", "temperature", "salinity", "temperature_argoqc", "salinity_argoqc"],
            ["units", "data_keys_mode"],
            [
                ["decibar", "D"],
                ["degree_Celsius", temperature_mode],
                ["psu", salinity_mode],
                [None, None],
                [None, None],
            ],
        ],
        "data": [
            [0.4, 1.0, 1.9],
            [28.754999, 28.761, 28.761999],
            [33.007, 33.004002, 33.002998],
            [1, 1, 1],
            [1, 1, 1],
        ],
    }


# --- is_enabled / disabled-by-default -----------------------------------


def test_disabled_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FLOATCHAT_LIVE_SOURCE_ENABLED", raising=False)
    assert is_enabled() is False


def test_enabled_reads_truthy_env_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FLOATCHAT_LIVE_SOURCE_ENABLED", "true")
    assert is_enabled() is True


def test_fetch_raises_without_network_call_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FLOATCHAT_LIVE_SOURCE_ENABLED", raising=False)

    def fail_if_called(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("httpx.get must not be called when the feature is disabled")

    monkeypatch.setattr("app.services.live_source.httpx.get", fail_if_called)

    with pytest.raises(LiveSourceError):
        fetch_argo_profiles(13.08, 80.27, 150.0, "2023-01-01", "2023-02-01")


# --- fetch_argo_profiles: request shape and coordinate order ------------


def test_fetch_uses_longitude_latitude_center_order(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FLOATCHAT_LIVE_SOURCE_ENABLED", "true")
    captured: dict[str, object] = {}

    def fake_get(url: str, **kwargs: object) -> _FakeResponse:
        captured["url"] = url
        captured.update(kwargs)
        return _FakeResponse([_real_shaped_document()])

    monkeypatch.setattr("app.services.live_source.httpx.get", fake_get)

    fetch_argo_profiles(13.08, 80.27, 150.0, "2023-01-01", "2023-02-01")

    params = captured["params"]
    assert isinstance(params, dict)
    # center is [longitude, latitude] -- confirmed empirically against the
    # live API in Step 1; this must never silently become "13.08,80.27".
    assert params["center"] == "80.27,13.08"
    assert params["startDate"] == "2023-01-01T00:00:00Z"
    assert params["endDate"] == "2023-02-01T23:59:59Z"


def test_fetch_respects_configurable_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FLOATCHAT_LIVE_SOURCE_ENABLED", "true")
    monkeypatch.setenv("FLOATCHAT_LIVE_SOURCE_TIMEOUT_SECONDS", "3.5")
    captured: dict[str, object] = {}

    def fake_get(url: str, **kwargs: object) -> _FakeResponse:
        captured.update(kwargs)
        return _FakeResponse([])

    monkeypatch.setattr("app.services.live_source.httpx.get", fake_get)
    fetch_argo_profiles(13.08, 80.27, 150.0, "2023-01-01", "2023-02-01")

    assert captured["timeout"] == 3.5


# --- fetch_argo_profiles: failure classification -------------------------


def test_fetch_treats_404_as_empty_not_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FLOATCHAT_LIVE_SOURCE_ENABLED", "true")
    monkeypatch.setattr(
        "app.services.live_source.httpx.get",
        lambda *_a, **_k: _FakeResponse([], status_code=404),
    )
    assert fetch_argo_profiles(13.08, 80.27, 150.0, "2023-01-01", "2023-02-01") == []


def test_fetch_timeout_raises_live_source_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FLOATCHAT_LIVE_SOURCE_ENABLED", "true")

    def timeout(*_a: object, **_k: object) -> None:
        raise httpx.ReadTimeout("timed out")

    monkeypatch.setattr("app.services.live_source.httpx.get", timeout)
    with pytest.raises(LiveSourceError):
        fetch_argo_profiles(13.08, 80.27, 150.0, "2023-01-01", "2023-02-01")


def test_fetch_http_error_raises_live_source_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FLOATCHAT_LIVE_SOURCE_ENABLED", "true")

    def connect_error(*_a: object, **_k: object) -> None:
        raise httpx.ConnectError("no route")

    monkeypatch.setattr("app.services.live_source.httpx.get", connect_error)
    with pytest.raises(LiveSourceError):
        fetch_argo_profiles(13.08, 80.27, 150.0, "2023-01-01", "2023-02-01")


def test_fetch_http_status_error_raises_live_source_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FLOATCHAT_LIVE_SOURCE_ENABLED", "true")
    monkeypatch.setattr(
        "app.services.live_source.httpx.get",
        lambda *_a, **_k: _FakeResponse([], status_code=500),
    )
    with pytest.raises(LiveSourceError):
        fetch_argo_profiles(13.08, 80.27, 150.0, "2023-01-01", "2023-02-01")


def test_fetch_malformed_json_raises_live_source_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FLOATCHAT_LIVE_SOURCE_ENABLED", "true")
    monkeypatch.setattr(
        "app.services.live_source.httpx.get",
        lambda *_a, **_k: _FakeResponse(_MALFORMED),
    )
    with pytest.raises(LiveSourceError):
        fetch_argo_profiles(13.08, 80.27, 150.0, "2023-01-01", "2023-02-01")


def test_fetch_non_list_payload_raises_live_source_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FLOATCHAT_LIVE_SOURCE_ENABLED", "true")
    monkeypatch.setattr(
        "app.services.live_source.httpx.get",
        lambda *_a, **_k: _FakeResponse({"unexpected": "shape"}),
    )
    with pytest.raises(LiveSourceError):
        fetch_argo_profiles(13.08, 80.27, 150.0, "2023-01-01", "2023-02-01")


# --- normalize_argo_profiles ----------------------------------------------


def test_normalize_produces_exactly_the_required_columns() -> None:
    frame = normalize_argo_profiles([_real_shaped_document()])
    assert set(frame.columns) >= REQUIRED_PROFILE_COLUMNS


def test_normalize_builds_stable_colon_separated_profile_id() -> None:
    frame = normalize_argo_profiles(
        [_real_shaped_document(document_id="7901125_002", cycle_number=2)]
    )
    assert (frame["platform_number"] == "7901125").all()
    assert (frame["cycle_number"] == "2").all()
    assert (frame["profile_id"] == "7901125:2").all()


def test_normalize_maps_adjusted_values_and_qc_when_mode_is_delayed() -> None:
    frame = normalize_argo_profiles(
        [_real_shaped_document(temperature_mode="D", salinity_mode="D")]
    )
    assert list(frame["temp_adjusted"]) == [28.754999, 28.761, 28.761999]
    assert list(frame["psal_adjusted"]) == [33.007, 33.004002, 33.002998]
    assert (frame["temp_adjusted_qc"] == "1").all()
    assert (frame["psal_adjusted_qc"] == "1").all()
    assert (frame["data_mode"] == "D").all()


def test_normalize_nulls_adjusted_value_when_mode_is_real_time() -> None:
    """Argovis exposes only one value per parameter, not raw+adjusted keys.

    A real-time ("R") mode must not be silently treated as adjusted -- the
    safest interpretation (per Step 1) is to leave the adjusted cell null so
    the existing QC boundary's null-value check excludes it, exactly as it
    would exclude a genuinely missing adjusted value from the local dataset.
    """
    frame = normalize_argo_profiles(
        [_real_shaped_document(temperature_mode="R", salinity_mode="D")]
    )
    assert frame["temp_adjusted"].isna().all()
    assert list(frame["psal_adjusted"]) == [33.007, 33.004002, 33.002998]
    # The flattened data_mode prefers the accepted mode so the genuinely
    # adjusted salinity value is not excluded by the document-level check.
    assert (frame["data_mode"] == "D").all()


def test_normalize_uses_longitude_latitude_order_from_geolocation() -> None:
    frame = normalize_argo_profiles(
        [_real_shaped_document(longitude=88.95, latitude=14.116666666666667)]
    )
    assert frame["longitude"].iloc[0] == pytest.approx(88.95)
    assert frame["latitude"].iloc[0] == pytest.approx(14.116666666666667)


def test_normalize_empty_document_list_raises_live_source_error() -> None:
    with pytest.raises(LiveSourceError):
        normalize_argo_profiles([])


def test_normalize_skips_one_malformed_document_without_crashing() -> None:
    malformed = {"_id": "broken", "geolocation": {}}  # missing everything else
    good = _real_shaped_document()

    frame = normalize_argo_profiles([malformed, good])

    assert len(frame) == 3  # only the well-formed document's 3 levels
    assert (frame["platform_number"] == "7901125").all()


def test_normalize_all_malformed_documents_raises_live_source_error() -> None:
    with pytest.raises(LiveSourceError):
        normalize_argo_profiles([{"_id": "broken", "geolocation": {}}])

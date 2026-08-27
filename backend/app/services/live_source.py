"""Additive, opt-in live fallback against the public Argovis API.

This module is only ever consulted by ``app/api/chat.py`` after the local,
versioned Parquet artifact (``app/services/data.py``) has already been queried
and returned no rows. It never touches the local artifact, QC, aggregation, or
anomaly logic, and it is disabled by default.

Coordinate order (verified empirically against the live API, not assumed):
Argovis's ``center`` query parameter is ``[longitude, latitude]``, matching the
GeoJSON convention used by its ``polygon``/``box`` parameters and by the
``geolocation.coordinates`` field in every response document.

Adjusted-vs-raw values: Argovis exposes only one value per parameter (e.g.
``temperature``), not separate raw/adjusted keys. Provenance instead lives in
each document's ``data_info`` as a per-key ``data_keys_mode`` entry ("R", "A",
or "D" -- Argo's own data-mode convention). A value is only treated as this
project's "adjusted" value when its mode is "A" or "D", mirroring
``qc.py``'s ``accepted_data_modes``; an "R" (real-time, unadjusted) or missing
mode leaves the corresponding ``temp_adjusted``/``psal_adjusted`` cell null
rather than inventing an adjusted value Argovis never provided.

Known limitation: a single Argo profile conventionally shares one data mode
across parameters (confirmed in every live document sampled), but Argovis's
schema does not guarantee this. The flattened ``data_mode`` column prefers
whichever parameter's mode is accepted, so a genuinely present, adjusted value
is never dropped by the QC boundary's mode check; the narrow failure case is a
row whose *requested* parameter was real-time-only while the *other*
parameter on the same profile was adjusted, which would then pass the
document-level mode check without contributing a value (harmless: it is
excluded downstream anyway because that parameter's own adjusted cell is
null).

Region queries: the parsed region's centroid and default radius are used
as-is; a named region's true bounding box is not reconstructed into a
covering circle, so a live top-up for a large region will only sample near
its centroid. This is disclosed via ``live_source_caveat``, not hidden.
"""

from __future__ import annotations

import os
from typing import Any

import httpx
import pandas as pd

from app.services.data import REQUIRED_PROFILE_COLUMNS

ARGOVIS_BASE_URL = "https://argovis-api.colorado.edu"
DEFAULT_TIMEOUT_SECONDS = 8.0

# Argovis's /argo endpoint has no pagination or server-side result cap; bound
# how many documents we convert so a wide live top-up can't blow the request
# timeout or memory budget.
MAX_LIVE_DOCUMENTS = 200

# Matches qc.py's QC_RULE data-mode policy: only real-time-adjusted ("A") or
# delayed-mode ("D") values are treated as this project's "adjusted" value.
ACCEPTED_DATA_MODES = {"A", "D"}

_ARGO_DATA_KEYS = "pressure,temperature,salinity,temperature_argoqc,salinity_argoqc"


class LiveSourceError(RuntimeError):
    """Single exception type for every live-source failure.

    Covers: the feature being disabled, network/timeout errors, non-2xx HTTP
    responses, malformed JSON, and documents missing required fields. The
    /chat handler catches only this type -- no raw httpx or parsing exception
    is ever allowed to escape this module.
    """


def _timeout_seconds() -> float:
    raw = os.getenv("FLOATCHAT_LIVE_SOURCE_TIMEOUT_SECONDS")
    if not raw:
        return DEFAULT_TIMEOUT_SECONDS
    try:
        return float(raw)
    except ValueError:
        return DEFAULT_TIMEOUT_SECONDS


def is_enabled() -> bool:
    return os.getenv("FLOATCHAT_LIVE_SOURCE_ENABLED", "").strip().lower() in {"1", "true", "yes"}


def fetch_argo_profiles(
    latitude: float,
    longitude: float,
    radius_km: float,
    date_from: str,
    date_to: str,
) -> list[dict[str, Any]]:
    """Fetch raw Argovis ``/argo`` documents for a point, radius, and date window.

    Raises ``LiveSourceError`` immediately, before any network call, when the
    feature is disabled. Never lets an ``httpx`` exception or a JSON-decode
    error propagate past this function.
    """
    if not is_enabled():
        raise LiveSourceError(
            "Live-source fallback is disabled (FLOATCHAT_LIVE_SOURCE_ENABLED is not set)."
        )

    params = {
        "startDate": f"{date_from}T00:00:00Z",
        "endDate": f"{date_to}T23:59:59Z",
        # [longitude, latitude] -- confirmed empirically, do not swap this order.
        "center": f"{longitude},{latitude}",
        "radius": f"{radius_km:g}",
        "data": _ARGO_DATA_KEYS,
    }
    try:
        response = httpx.get(f"{ARGOVIS_BASE_URL}/argo", params=params, timeout=_timeout_seconds())
    except httpx.TimeoutException as exc:
        raise LiveSourceError("The live Argo source timed out.") from exc
    except httpx.HTTPError as exc:
        raise LiveSourceError("The live Argo source could not be reached.") from exc

    if response.status_code == 404:
        # Argovis's own "no matching documents" signal, not a real error.
        return []
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise LiveSourceError("The live Argo source returned an HTTP error.") from exc

    try:
        payload = response.json()
    except ValueError as exc:
        raise LiveSourceError("The live Argo source returned malformed JSON.") from exc
    if not isinstance(payload, list):
        raise LiveSourceError("The live Argo source returned an unexpected response shape.")
    return payload[:MAX_LIVE_DOCUMENTS]


def _column(columns: list[list[Any]], key_index: dict[str, int], name: str) -> list[Any] | None:
    index = key_index.get(name)
    return columns[index] if index is not None else None


def _mode(modes_row: list[list[Any]], key_index: dict[str, int], name: str) -> str | None:
    index = key_index.get(name)
    if index is None or index >= len(modes_row):
        return None
    entry = modes_row[index]
    mode = entry[1] if isinstance(entry, list) and len(entry) > 1 else None
    return str(mode) if mode is not None else None


def _rows_from_document(document: dict[str, Any]) -> list[dict[str, Any]]:
    document_id = str(document["_id"])
    platform_number = document_id.rsplit("_", 1)[0]
    cycle_number = str(document["cycle_number"])
    profile_id = f"{platform_number}:{cycle_number}"

    coordinates = document["geolocation"]["coordinates"]
    longitude, latitude = float(coordinates[0]), float(coordinates[1])
    timestamp = document["timestamp"]
    position_qc = str(document.get("geolocation_argoqc", ""))

    data_info = document["data_info"]
    keys: list[str] = data_info[0]
    modes_row: list[list[Any]] = data_info[2]
    columns: list[list[Any]] = document["data"]
    key_index = {key: index for index, key in enumerate(keys)}

    pressures = _column(columns, key_index, "pressure")
    if not pressures:
        return []
    temperatures = _column(columns, key_index, "temperature")
    salinities = _column(columns, key_index, "salinity")
    temp_qc_values = _column(columns, key_index, "temperature_argoqc")
    psal_qc_values = _column(columns, key_index, "salinity_argoqc")
    temperature_mode = _mode(modes_row, key_index, "temperature")
    salinity_mode = _mode(modes_row, key_index, "salinity")

    # Prefer whichever parameter's mode is accepted so a genuinely adjusted
    # value is never excluded by the document-level mode check; see the
    # module docstring's "Known limitation" note.
    if temperature_mode in ACCEPTED_DATA_MODES:
        data_mode = temperature_mode
    elif salinity_mode in ACCEPTED_DATA_MODES:
        data_mode = salinity_mode
    else:
        data_mode = temperature_mode or salinity_mode or ""

    rows: list[dict[str, Any]] = []
    for level, pressure in enumerate(pressures):
        temp_value = temperatures[level] if temperatures and level < len(temperatures) else None
        psal_value = salinities[level] if salinities and level < len(salinities) else None
        temp_qc = temp_qc_values[level] if temp_qc_values and level < len(temp_qc_values) else None
        psal_qc = psal_qc_values[level] if psal_qc_values and level < len(psal_qc_values) else None
        rows.append(
            {
                "platform_number": platform_number,
                "cycle_number": cycle_number,
                "profile_id": profile_id,
                "time": timestamp,
                "latitude": latitude,
                "longitude": longitude,
                "pres": pressure,
                "data_mode": data_mode,
                "position_qc": position_qc,
                "temp_adjusted": (
                    temp_value
                    if temperature_mode in ACCEPTED_DATA_MODES and temp_value is not None
                    else None
                ),
                "temp_adjusted_qc": str(temp_qc) if temp_qc is not None else None,
                "psal_adjusted": (
                    psal_value
                    if salinity_mode in ACCEPTED_DATA_MODES and psal_value is not None
                    else None
                ),
                "psal_adjusted_qc": str(psal_qc) if psal_qc is not None else None,
            }
        )
    return rows


def normalize_argo_profiles(documents: list[dict[str, Any]]) -> pd.DataFrame:
    """Map raw Argovis ``/argo`` documents into the local profile-table contract.

    Produces exactly the columns in ``data.REQUIRED_PROFILE_COLUMNS``. Any one
    malformed document is skipped rather than failing the whole batch; if
    nothing usable remains, raises ``LiveSourceError`` so the caller falls
    back to the existing no-data behavior.
    """
    rows: list[dict[str, Any]] = []
    for document in documents:
        try:
            rows.extend(_rows_from_document(document))
        except (KeyError, TypeError, ValueError, IndexError):
            continue
    if not rows:
        raise LiveSourceError("The live Argo source returned no usable observations.")

    frame = pd.DataFrame(rows)
    missing = REQUIRED_PROFILE_COLUMNS - set(frame.columns)
    if missing:
        raise LiveSourceError("The live Argo source response is missing required fields.")
    return frame

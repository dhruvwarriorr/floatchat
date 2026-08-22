# FloatChat-Lite project handbook

> Runtime handbook, synchronized 22 August 2026

FloatChat-Lite answers natural-language ARGO temperature and salinity questions through a Gemini-first, deterministic-fallback parser and a QC-gated scientific pipeline. The installed artifacts cover the Arabian Sea; unsupported locations receive honest `no_data` responses.

## Working vocabulary

- **QC Filter:** mandatory adjusted A/D, position-QC, parameter-QC, and non-null boundary before aggregation.
- **Data-quality warning:** a factual warning about rejected or thin evidence, separate from anomaly classification.
- **Anomaly screening:** production-baseline Z-score over a QC-passed representative aggregate; not a formal marine-heatwave declaration.
- **Evidence Grade:** `Insufficient`, `Indicative`, or `Supported`, with machine-readable reasons.
- **Evidence panel:** expandable computation transparency including artifact identity and source observation references.
- **Shallow-water proxy:** the shallowest QC-passed 0–10 dbar ARGO observation; not satellite SST.

## Runtime capabilities

- Free-form location/date/parameter parsing, including both parameters.
- Profile, time-series, regional-average, and optional anomaly paths.
- Interactive Leaflet map with exact point/radius or named-region rectangle.
- Temperature, Salinity, and All chart controls with independent units/axes.
- Friendly `parse_error`, `no_data`, and `general_error` responses with no traces or local paths.
- Offline, versioned Parquet data and separate production/validation baselines.
- Per-chart-point profile, float, and source-row trace samples.

## Claim boundary

Automated checks and local reliability reports are engineering evidence, not scientific validation or pitch permission. The three-method evaluation remains blocked until independently reviewed labels and references exist. Provider reliability remains unaccepted until a valid authorized Gemini run is reviewed.

For current commands and measured artifact facts, use the root [README](../README.md). For exact policy and contract details, use [SCIENTIFIC_POLICY.md](SCIENTIFIC_POLICY.md) and [API_CONTRACT.md](API_CONTRACT.md).

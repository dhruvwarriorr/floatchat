# Scientific data boundary

This directory contains versioned scientific artifacts, not application code.

```text
raw/                    Local source NetCDF files; never committed by default
processed/              Query-ready profile tables, normally Parquet
baselines/production/   Baselines used by live responses
baselines/validation/   Independent known-event validation baselines
manifest.schema.json    Required manifest shape
```

Do not put a dataset into service merely because a file exists. A release-ready `manifest.json` must record provenance, licence/access notes, QC policy, spatial and temporal coverage, hashes, build command, and each artifact. The API readiness check accepts only a manifest marked `ready` whose declared files exist.

Raw, processed, and baseline artifacts are ignored by default because they can be large and may have redistribution constraints. Add only deliberately reviewed, hackathon-sized artifacts after confirming source terms.

Production and validation baselines must remain separate. The 2015-2018 validation period described in the project documentation is evidence work, not the baseline for live responses.

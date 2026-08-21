# Scientific data boundary

This directory contains versioned scientific artifacts, not application code.

```text
raw/                    Local source CSV exports; never committed by default
processed/              Query-ready profile tables, normally Parquet
baselines/production/   Baselines used by live responses
baselines/validation/   Independent known-event validation baselines
manifest.schema.json    Required manifest shape
```

Do not put a dataset into service merely because a file exists. A release-ready `manifest.json` must record provenance, licence/access notes, QC policy, spatial and temporal coverage, hashes, build command, and each artifact. The API readiness check accepts only a manifest marked `ready` whose declared files exist.

The prepared profile schema must retain enough ARGO quality metadata to enforce the mandatory data-quality path before anomaly scoring. At minimum, the team must freeze and document observation-level QC flags, raw versus adjusted values, `data_mode`, and the record/profile identity needed to report retained observations and distinct floats. Do not reduce QC to a single undocumented boolean during preprocessing.

Raw CSV exports, processed, and baseline artifacts are ignored by default because they can be large and may have redistribution constraints. Add only deliberately reviewed, hackathon-sized artifacts after confirming source terms. The accepted INCOIS CSV format has a field-name first row and a units second row; preprocessing must skip the units row, preserve identifiers and QC columns as strings, and record the exact source filenames and hashes in the manifest.

Production and validation baselines must remain separate. The 2015-2018 validation period described in the project documentation is evidence work, not the baseline for live responses.

The anomaly service may consume only QC-passed observations. Quantitative comparison fixtures and generated reports belong under `evaluation/`; large or redistribution-sensitive ARGO files remain here.

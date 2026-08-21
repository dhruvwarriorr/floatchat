# Scientific and evaluation scripts

Implement these entrypoints in critical-path order:

1. `preprocess_argo.py`: NetCDF -> validated profile Parquet plus manifest draft.
2. `build_baselines.py`: separate production and validation mean/std/count artifacts.
3. `validate_anomalies.py`: fixed labeled scientific evaluation with exact recorded output; do not call a sparse-profile Z-score result a marine heatwave.
4. `evaluate_methods.py`: compare the regional-average baseline, unfiltered Z-score, and QC-filtered/evidence-graded pipeline.
5. `evaluate_parser.py`: run the frozen 20–30 query parser/reliability set, including LLM-disabled and simulated-failure paths.

Each script must be deterministic for a fixed input, accept explicit input/output paths, fail non-zero on invalid data, and record the dataset version. Do not add a script that prints a pretend success result or silently substitutes illustrative frontend data.

The first implementation checkpoint is a preprocessing command plus one repository query against a manually checked real subset. QC filtering must be testable and auditable before anomaly scoring. LLM integration comes later.

Notebook source, frozen labels/prompts, and generated reports are organized under `evaluation/`; scripts may provide deterministic command-line equivalents used by those notebooks.

# Scientific and evaluation scripts

Implemented entrypoints in critical-path order:

1. `preprocess_argo.py`: INCOIS CSV exports -> validated profile Parquet plus manifest draft.
2. `build_baselines.py`: separate production and validation mean/std/count artifacts.
3. `evaluate_methods.py`: compare the regional-average baseline, unfiltered Z-score, and QC-filtered/evidence-graded pipeline. It fails closed while the reviewed anomaly fixture is empty.
4. `test_parser_reliability.py`: run the frozen 24-query parser suite with LLM-disabled, simulated-failure, and optionally enabled modes.
5. `build_demo_cache.py`: capture sanitized live API outcomes and label them as recorded demo cache.

Each script must be deterministic for a fixed input, accept explicit input/output paths, fail non-zero on invalid data, and record the dataset version. Do not add a script that prints a pretend success result or silently substitutes illustrative frontend data.

The local artifacts and code paths are implemented. Manual scientific review, grade-threshold approval, anomaly labels, provider-enabled evidence, projector checks, and rehearsal remain human acceptance gates.

Notebook source, frozen labels/prompts, and generated reports are organized under `evaluation/`; scripts may provide deterministic command-line equivalents used by those notebooks.

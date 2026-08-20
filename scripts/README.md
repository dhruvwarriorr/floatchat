# Scientific and evaluation scripts

Implement these entrypoints in critical-path order:

1. `preprocess_argo.py`: NetCDF -> validated profile Parquet plus manifest draft.
2. `build_baselines.py`: separate production and validation mean/std/count artifacts.
3. `validate_heatwave.py`: fixed known-event evaluation with exact recorded output.
4. `evaluate_parser.py`: run the frozen labeled query set and emit measured results.

Each script must be deterministic for a fixed input, accept explicit input/output paths, fail non-zero on invalid data, and record the dataset version. Do not add a script that prints a pretend success result or silently substitutes illustrative frontend data.

The first implementation checkpoint is a preprocessing command plus one repository query against a manually checked real subset. LLM integration comes later.

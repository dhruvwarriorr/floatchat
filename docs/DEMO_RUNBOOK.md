# FloatChat-Lite demo runbook

> Status: planned; no release/reliability evidence is recorded.

## Release gate

- [ ] Reviewed manifest, QC-retaining profiles, and separate baselines exist.
- [ ] Runtime order QC → anomaly → evidence grade → panel is tested.
- [ ] Target success and typed error responses render in the frontend.
- [ ] Three-method comparison and parser/API reliability reports are reviewed/logged.
- [ ] Container/local, complete cached fallback, projector/recovery, and rehearsal checks are recorded.

## Result inspection

For every anomaly result verify:

- source/version, dates, region/radius, parser;
- QC rule and data mode;
- raw/valid/excluded counts, distinct floats, QC pass rate;
- data-quality warning, if applicable;
- current aggregate and production baseline mean/std/`n`;
- z-score/label without marine-heatwave overclaim;
- evidence grade and explicit reasons; and
- shallow-water proxy caveat.

## Quantitative claim inspection

- Confirm labels, subset, denominators, method versions, confusion counts, precision/recall/F1/false-alert/coverage/response-time report.
- Confirm reliability test includes 20–30 paraphrases, model explicitly disabled, invalid output/fallback, average/p95 latency, no/sparse data, malformed date, and simulated failure.
- Match every displayed number to an evidence-log row and report artifact.

## Recovery

1. Provider failure → deterministic parser with visible disclosure.
2. Remote failure → verified local container.
3. Runtime/data failure → sanitized cached response preserving QC/grade/provenance fields.
4. Only illustrative UI available → explicitly state that no real-data or validation claim is being demonstrated.

Never hide rejected/thin data, edit metrics, or describe illustrative/cached output as live.

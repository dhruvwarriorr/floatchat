# 48-hour execution plan

The data path is the critical path. Keep the final two hours protected for verification and rehearsal.

## H0-H4: freeze and prepare

- Freeze three pinned queries, response contract, region definitions, ownership, and evidence log.
- Prepare a small, reviewable ARGO subset and inspect adjusted values plus QC flags.
- Build deterministic NetCDF-to-Parquet preprocessing and separate baseline artifacts.
- Build UI states against a contract fixture in parallel, without changing the accepted visual design.

Gate: at H4, use a smaller pre-vetted real subset if ingestion is not query-ready. Do not substitute unlabeled illustrative values.

## H4-H9: prove data and response shapes

- Make one real profile query work from a script and through HTTP.
- Implement repository filters and z-score boundary tests.
- Freeze backend models and frontend fixtures together.
- Render profile/time-series confidence outcomes at laptop/projector size.

Gate: a real profile query and mock contract states must both work.

## H9-H15: parse and integrate

- Add one structured-output LLM parser behind a short timeout only after the deterministic grammar works.
- Force timeout/malformed output and verify rule-based fallback.
- Connect real data, anomaly, explanation, and the frontend.
- Verify source, proxy caveat, profile count, radius/region, confidence, and parser disclosure.

Gate: profile and time-series/anomaly work end-to-end even when the LLM is unavailable.

## H15-H19: freeze and measure

- Add regional average only if the two core flows are stable.
- Run the frozen parser evaluation and scientific validation.
- Record exact outputs; remove unsupported claims.
- Freeze features at H17.

Gate: evidence log contains observed results or the pitch omits those claims.

## H19-H24: release and rehearse

- Build the one-container release, run health and pinned-query smoke checks.
- Capture sanitized cached JSON and screenshots; test offline opening.
- Run failure paths on the actual presentation setup.
- Complete short repeated demos, timed presentation practice, and release freeze.

Gate: live/local and cached paths work, the final build is frozen, and failures have a named mitigation.

## Scope cut order

1. Drop broad regional coverage.
2. Drop map interactivity; keep a static location marker.
3. Drop regional-average KPI.
4. Narrow free-form grammar and use the disclosed rule parser.

Never cut evidence, confidence disclosure, safe errors, or rehearsal time to preserve a feature.

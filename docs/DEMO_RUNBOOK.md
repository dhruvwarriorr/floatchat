# FloatChat-Lite demo runbook

> Status: 🟠 Planned; no rehearsal or release evidence is recorded
> Last synchronized: 21 August 2026

The repository is not demo-ready for real-data claims. The current frontend is an illustrative local experience, `/health/ready` is expected to fail without data, and `/chat` cannot return a successful response. Use this runbook only after the release gate below passes.

## Release gate

- [ ] A reviewed ARGO subset, separate production/validation baselines, and a `ready` manifest exist.
- [ ] Repository queries and `POST /chat` return validated real responses.
- [ ] The frontend uses the API contract rather than `oceanResponses.ts`.
- [ ] `make check` and the container smoke test pass for the release build.
- [ ] Real-data provenance, parser failure, typed errors, and scientific validation are recorded in `evidence/evidence-log.csv`.
- [ ] Sanitized cached responses/screenshots exist under `demo/`.

## Before deployment

1. Confirm `data/manifest.json` is marked `ready`, declared paths exist, hashes match, and provenance/QC notes were reviewed. The current readiness endpoint checks only status and file existence, so hash/schema checks need a separate command until implemented.
2. Confirm no secret appears under `frontend/`, `demo/`, tracked files, screenshots, logs, or cached JSON.
3. Run `make check`; record the exact build identifier and result in the evidence log.
4. Run `make container`, start the image, and exercise liveness, readiness, the pinned queries, `parse_error`, `no_data`, and a forced internal/provider failure.
5. Confirm every real success states source/version, aggregation, dates, selection radius/region, profile count, confidence, parser, and the shallow-water proxy caveat when applicable.

## Before judging

- Use the exact laptop, browser, resolution, projector, and network planned for the session.
- Verify `/health/live` and `/health/ready`; readiness does not prove scientific validity.
- Keep the sanitized cached fallback open separately and clearly label it recorded/cached.
- Run the pinned flows once and check the result against the reviewed fixture.
- Assign presenter, demo operator, timekeeper, and Q&A owner.

## Recovery order

1. If the optional LLM fails, continue with the deterministic parser and show `parser_used=rule_based`.
2. If remote hosting fails, run the verified one-container build on the presentation machine.
3. If the runtime/data path fails, show sanitized cached JSON/screenshots and describe the recorded workflow.
4. If the cached fallback is also unavailable, show the illustrative frontend only with an explicit non-real-data disclosure.

Never edit outputs, hide low confidence, or describe cached/illustrative values as live, validated, or production-ready.

## Freeze rule

After the final rehearsal, change only release blockers: crashes, incorrect data, unreadable output, secret/identity exposure, or unsupported claims. Re-run affected checks and append new evidence after each fix.

# Demo runbook

## Before deployment

- Confirm `data/manifest.json` is marked ready and artifact hashes match.
- Confirm no secret appears under `frontend/`, `demo/`, tracked files, screenshots, or cached JSON.
- Run `make check` and record the output/build identifier in the evidence log.
- Build the container and run liveness, readiness, and the three pinned queries.
- Force one parser/provider failure and one no-data case.

## Before judging

- Use the exact laptop, browser, resolution, projector, and network planned for the session.
- Start or warm the service and check `/health/live` plus `/health/ready`.
- Open the live/local app and a separate sanitized cached fallback tab.
- Run the three pinned questions once; verify source, method, confidence, and parser disclosure.
- Assign presenter, demo operator, timekeeper, and Q&A owner.

## Recovery order

1. If the LLM fails, continue with the deterministic parser and show the disclosure.
2. If hosting fails, use the one-container build on the presentation machine.
3. If the runtime/data path fails, show sanitized cached JSON/screenshots and explain the verified workflow.
4. Never edit outputs, hide low confidence, or describe cached/illustrative data as live.

## Freeze rule

After the final rehearsal, change only release blockers: crashes, wrong data, unreadable output, secret/identity exposure, or unsupported claims. Re-run the affected checks and update the evidence log after every blocker fix.

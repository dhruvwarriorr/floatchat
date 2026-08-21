# FloatChat-Lite delivery phases

> Last synchronized: 21 August 2026

This document groups work into dependency-ordered phases. It is a status view, not evidence that a person is actively working on an item. See the [detailed roadmap](FloatChat-Lite_Detailed_Project_Roadmap.md) for priorities and the [todo](todo.md) for the executable checklist.

## Phase summary

| Phase | Goal | Status | Exit state |
| --- | --- | --- | --- |
| 0. Foundation | Repository boundaries, accepted UI, API safety scaffold | 🟡 Partial | UI and backend checks exist; no scientific success path. |
| 1. Scientific data | Reproducible reviewed ARGO subset and separate baselines | 🔴 Blocked | Ready manifest, reviewed Parquet, production and validation artifacts. |
| 2. Repository and contract | Real profile/time-series through validated API | 🔴 Blocked by Phase 1 | Success/no-data contract fixtures and tests. |
| 3. UI integration | Accepted interface uses `/chat` | 🔴 Blocked by Phase 2 | Real success and typed errors render without redesign. |
| 4. Optional parser and regional breadth | Provider adapter; regional average only if stable | 🟠 Planned | Forced fallback and any optional third flow are evidenced. |
| 5. Evidence and release | Scientific validation, deployment, cache, projector QA, rehearsal | 🟠 Planned | Live/local and cached release paths are recorded and frozen. |

## Phase 0: foundation

### Completed

- Repository separated into `frontend/`, `backend/`, `data/`, `scripts/`, `deploy/`, `demo/`, and `docs/`.
- Accepted illustrative frontend implements four local response flows with Recharts, static map context, confidence, explanation, loading/error/reset states, and local assets.
- FastAPI defines typed request/response/error models, liveness/readiness endpoints, a deterministic pinned parser, safe parse/data-unavailable errors, and isolated anomaly policy.
- Unit/static checks, CI workflow, one-container recipe, manifest schema, and evidence boundary exist.

### Incomplete

- `POST /chat` has no success or `no_data` path.
- Frontend/backend response models diverge.
- Container and browser acceptance are not recorded.

### Exit decision

Treat the foundation as partial, not a completed product phase. Begin with scientific data; do not expand UI or provider scope.

## Phase 1: scientific data

### Goal

Create a small, versioned, licensed/provenanced, query-ready ARGO subset and separate serving/validation baselines.

### Work

1. Freeze source/access/licence, subset, pinned coverage, region/radius rules, QC policy, adjusted/raw precedence, pressure/depth handling, and shallow-water cutoff.
2. Implement deterministic preprocessing with explicit paths and validation.
3. Manually inspect representative profiles and record the review.
4. Build production and validation baselines separately.
5. Validate the manifest schema, hashes, coverage, and artifact kinds.

### Dependencies

Access to the selected ARGO source and team decisions above.

### Exit criteria

- `data/manifest.json` is reviewed and marked ready.
- Profile and baseline artifacts exist, match hashes, and can be rebuilt.
- A script can answer one manually checked profile query.
- Negative validation outcomes are retained rather than edited.

## Phase 2: repository and contract

### Goal

Return validated real profile and time-series responses through HTTP.

### Work

1. Implement schema-aware Parquet access and spatial/time/depth filters.
2. Implement profile, time-series, and data-sufficiency calculations.
3. Connect production-baseline anomaly scoring and explanation templates.
4. Emit `200 ChatResponse`, `404 no_data`, and safe failures.
5. Freeze real fixtures and resolve contract duplication/data variants.

### Dependencies

Phase 1.

### Exit criteria

Profile and time-series/anomaly work through `/chat` using the deterministic parser. Success, no-data, zero-std, sparse-data, and trace-safety tests pass.

## Phase 3: accepted UI integration

### Goal

Replace local illustrative resolution with a typed API adapter while preserving the accepted interface.

### Work

- Reconcile `OceanResponse` and `ChatResponse` through frozen fixtures/adaptation.
- Render real metadata, parser disclosure, and typed error states.
- Preserve Recharts, static Bhuvan map context, component layout, copy boundaries, and interactions.
- Test keyboard, narrow-screen, and projector behaviour.

### Dependencies

Phase 2.

### Exit criteria

The two core pinned flows render real reviewed data end-to-end, and illustrative values cannot be mistaken for live responses.

## Phase 4: optional parser and regional breadth

### Goal

Add only optional scope that does not threaten the core.

### Work

- Implement one structured-output LLM adapter behind a short timeout and deterministic fallback.
- Run a labelled parser evaluation and forced failures.
- Add regional average only if data coverage and the core flows are stable.

### Dependencies

Phase 3 and a confirmed provider/secret/quota decision.

### Exit criteria

Missing provider configuration, timeout, malformed output, and quota failure still support pinned deterministic queries with disclosure. Regional average is either evidenced or explicitly cut.

## Phase 5: evidence and release

### Goal

Produce a truthful, reproducible, presentation-ready release.

### Work

- Run scientific validation and parser evaluation; record exact results.
- Build and smoke-test the one-container release.
- Capture sanitized cached JSON/screenshots with provenance.
- Test browser, projector, offline switch, and failure recovery.
- Rehearse and record actual pass/failure counts; freeze the build.

### Dependencies

Phases 1–3; Phase 4 only for optional claims/features.

### Exit criteria

The release meets the [demo runbook](DEMO_RUNBOOK.md), and every claimed result traces to the evidence log.

## Long-term scope

Only after Phase 5: evaluate multilingual access, other ocean-data domains, multi-turn interaction, authentication, database storage, mobile/WhatsApp, or scaling based on verified need. None is scheduled.

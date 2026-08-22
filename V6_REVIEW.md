# FloatChat-Lite v6 — implementation and verification review

> Reviewed against `codex_prompt_v6_llm_map_improvements.md` and the targeted
> `codex_prompt_v6.md` fixes on 22 August 2026.
> This report describes the current working tree. It does not imply a commit,
> deployment, successful provider-enabled acceptance, scientific validation, or projector acceptance.

## Outcome

The implementable v6 code paths are present and the follow-up hardening pass fixed
the main blank-screen risks, tightened parser authority, made the scientific
visualisations easier to read, and reduced parser configuration to one optional
server-side key. The targeted follow-up adds query-specific result titles, a
full-width anomaly card, Arabian Sea coastal aliases, explicit point coordinates,
balanced chart rows, and responsive Hovmöller labels. `make check` passes with
254 backend tests and 16 frontend tests.

The remaining gates are external or evidence-based: no browser runtime was
available for the required desktop/mobile/projector visual pass, the configured
provider did not produce a successful accepted LLM parse during the live smoke
check, and the installed exports do not cover all three original pinned selections.
Those limits are not relabelled as successful acceptance.

## Prompt cross-check

| Prompt area | Current implementation | Verification |
| --- | --- | --- |
| Part 0 baseline | Parquet retrieval, haversine/bounds selection, mandatory QC, three aggregations, production-baseline Z-score, evidence grading/panel, typed errors, CORS, Leaflet, chart parameter controls, adapter, suggestions, and provenance are present. The manifest reports 14,413,526 processed observations, 77,172 profiles, 531 floats, and Arabian-Sea-focused coverage—not complete Indian Ocean coverage. | Source/tests/manifest inspected; readiness returned `200`. |
| Part 1 typography | Projector-facing body, input, chart axes/tooltips, metadata, chart summaries, errors, map labels, evidence text, and supplementary chart copy were enlarged. The former global 1180 px minimum width was removed and responsive breakpoints were added. | Frontend lint/build/static checks pass; visual projector check remains open. |
| Part 2 parser | Unicode NFKC normalisation, deterministic hints, one optional constrained provider call, exact-schema validation, semantic cross-checks, canonical geography, bounded radius/date policy, classified safe fallback, and policy-generated prompt/examples are implemented. The gazetteer now covers the requested Arabian Sea coastal states, cities, and aliases, including an LLM state-name rule and Gujarat example. Bare “warming” and “cooling” wording is temporal/anomaly intent. Provider output cannot override deterministic known geography or contradictory intent. | All gazetteer aliases and the 25 requested additions are parser-tested; 30/30 deterministic and 30/30 forced-provider-failure fixture outcomes were generated, not reviewed as pitch evidence. Provider-enabled success was not established. |
| Part 3 all graphs | Primary aggregation remains first; every supported alternate aggregation is returned as `secondary_views` on a best-effort basis. Each secondary chart states what it shows and how it was grouped. | API response contained both alternate views for the point and regional smoke queries. |
| Part 4 map | Region bounds come only from the backend. Point radius and region rectangles are mutually exclusive; Leaflet fits actual geometry, invalidates on resize, supports reduced motion/reset/tile failure, and exposes a text equivalent. Explicit coordinate precision is preserved up to four decimals. | Geometry/format helper tests and static component checks pass. Browser resize/visual acceptance remains open. |
| Part 5 Z-score | Scoring is attempted for every successful parameter result after QC and evidence grading, regardless of wording. Insufficient evidence, missing baseline, or zero baseline standard deviation still suppresses the score honestly. | Backend response/test assertions cover always-on and suppressed states. |
| Part 6 transparency | “Computation Transparency” opens with a plain-language retrieval/QC/current-period/baseline/score narrative. Dataset IDs, artifact hash/path, source rows, profiles, floats, exclusions, and the trace table are under collapsed “Data Source.” | Frontend contract checks pass. |
| Part 7 science views | T-S, simplified density, OHC, SVG Hovmöller, seasonal cycle, year-over-year, anomaly trend, and time-series baseline bands are implemented best-effort. T-S and density use only rows passing both temperature and salinity QC rules. The Hovmöller view measures its container, reserves pressure-label space, thins dates by pixel spacing, and scrolls long timelines; density ticks are rounded for readability. | Aggregation, heatmap-layout, and live API payload checks pass. |
| Part 8 layout | The result order is interpreted query/disclosures, insight, primary chart plus map, full-width anomaly context, evidence grade, secondary views, supplementary views, transparency, then data source. Primary graphs flex to their grid height; supplementary cards use count-aware balanced rows and the Hovmöller card spans the full row. | Source and automated layout-contract checks pass; pixel-level browser acceptance remains open. |
| Part 9 scope | No listed v6 feature was intentionally cut. No fake float trajectories or observation heatmaps were added. | Source inspected. |
| Part 10 definition of done | Code-level items and same-origin end-to-end HTTP flow pass. Visual/projector acceptance, provider success, and full pinned-selection data coverage remain explicitly open. | See checks and limits below. |

## Reliability and blank-screen hardening

- The frontend now uses the current origin by default. Vite proxies `/chat` and
  `/health` to FastAPI during development, avoiding a hard-coded localhost URL,
  mixed-content failure, and deployment-origin drift.
- Result rendering has an error boundary, so a chart/map/lazy-render exception
  produces a friendly error state rather than an empty blue page.
- The response header consumes `interpreted_title` while the insight banner keeps
  the computed `summary`, preventing a result sentence from being duplicated as
  the query title.
- Heatmap width and date-label density are pure, tested calculations; environments
  without `ResizeObserver` fall back to window-resize measurement.
- The map handles environments without `ResizeObserver` and refits when the card
  size changes. The UI no longer forces a desktop-only 1180 px document width.
- A live request sent through the Vite development origin returned `200`, proving
  the frontend reached FastAPI through the same-origin proxy.
- A 2501 km query returned the safe typed `422 parse_error`; an uncovered Goa
  query returned the safe typed `404 no_data`, without a traceback.

## One-key parser configuration

`.env.example` exposes only `FLOATCHAT_LLM_API_KEY`. `LLM_PROVIDER` and
`LLM_MODEL` select the compatible provider/model; provider-specific key aliases
are no longer read by the parser or supporting reliability/cache scripts. The key
remains server-only and must never use a `VITE_` prefix.

## Checks performed

```text
make check
  frontend eslint: passed
  frontend TypeScript/Vite production build: passed
  frontend tests: 16 passed
  backend ruff: passed
  backend tests: 254 passed

FLOATCHAT_LLM_API_KEY= python scripts/test_parser_reliability.py ...
  deterministic disabled mode: 30/30 expected outcomes
  simulated provider failure: 30/30 expected outcomes
  API scenarios: 5/5 expected outcomes
  provider-enabled mode: skipped because no key was supplied to this run
  status: generated_not_reviewed

Live same-origin smoke checks through Vite
  GET /: 200
  GET /health/ready: 200 ready
  Kerala point profile: 200 with query-specific title, coordinates/radius in the
    summary, canonical map coordinates, and supplementary/Hovmöller payloads
  Arabian Sea warming trend: 200 Supported with query-specific title and canonical bounds
  Gujarat, Mumbai, Goa, Ratnagiri, and Karwar: parser accepted; current artifact returned 404 no_data
  out-of-range radius: 422 parse_error
  uncovered Goa selection: 404 no_data

Container check
  make container: blocked before build because the local Docker daemon/socket was unavailable
```

## Honest remaining limits

- The in-app browser reported that no browser runtime was available. Automated
  checks and HTTP smoke tests are complete, but desktop, narrow-mobile,
  projector/full-screen, tile-failure, and pixel-level visual acceptance still
  require a browser/human pass.
- The Dockerfile was not container-accepted in this run because no Docker daemon
  was available at the local socket; this is separate from the passing app build.
- Provider calls seen during the live API smoke check fell back safely. This is
  not evidence of successful Gemini/OpenAI/Anthropic structured parsing.
- The installed data is an Arabian-Sea-focused export. Its manifest records zero
  coverage for the original Mumbai-50-km and Bay-of-Bengal pinned selections.
  Those queries correctly return `no_data`; adding reviewed exports is a data
  acquisition task and must not be simulated in UI fixtures.
- The density equation and OHC view are transparent simplified visual aids with
  displayed caveats. They are not independent scientific validation.
- Generated reliability metrics remain outside `docs/evidence/evidence-log.csv`
  until reviewed and recorded unchanged.

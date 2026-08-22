# FloatChat-Lite v6 — Implementation Review

**Branch:** `v6-llm-map-improvements` (4 commits ahead of `main`)
**Status:** Backend `ruff` clean · **183** pytest passing · parser reliability **30/30** · Frontend TypeScript build clean · `eslint` clean · **9** contract tests passing

A plain-language walkthrough of the v6 upgrade — a smarter query parser, richer charts, a precise map, an always-on anomaly score, and a reorganized results panel — plus how it was tested and what remains open.

---

## The short version

FloatChat-Lite lets you ask plain-English questions about Indian Ocean temperature and salinity (from ARGO floats) and get an explained, evidence-graded answer. The v6 prompt asked for a set of **incremental improvements — not a rebuild.** The work touched both the Python backend (how questions are understood and data is crunched) and the React frontend (how results are shown).

Everything landed on `v6-llm-map-improvements` across four commits. The pre-existing local edits to `data/` were left untouched.

| Commit | Summary |
|---|---|
| `987a843` | **Backend v6** — new parser policy module, refactored parser, secondary/supplementary data, always-on z-score, expanded tests |
| `273f16b` | **Frontend v6** — bigger type, new chart components, geometry-driven map, reorganized transparency panel |
| `0451b96` | **Dev launch config** — so the app can be relaunched easily |
| `8e5b4d7` | **Performance fix** — cut the heaviest query from ~39s to ~14s |

**At a glance:** 8 feature areas delivered (Parts 1–8) · 7 new scientific chart types · 3 new files · heaviest query latency 39s → 14s.

---

## What changed, feature by feature

### 1. Bigger, projector-friendly text
Raised font sizes across the interface — body copy, chart axes and tooltips, metric values, labels, the map, and error messages — so the app is legible on a projector from across a room.
> **Why:** the original sizes (10–13px) were fine on a laptop but unreadable in a demo room.

### 2. A sturdier query parser
Rebuilt how questions are understood. All the rules — supported regions, place names, date handling, seasons, radius, intent words — now live in one shared `parser_policy` module used by **both** the AI planner and the deterministic fallback. Word-boundary matching stops false hits (e.g. "salt" inside "basalt"). Failures from the optional AI model are now sorted into clear categories (timeout, auth error, bad JSON, schema/semantic violation) and always fall back safely to the rule-based parser.
> **Why:** casual questions like *"how's the water near Goa?"* should parse reliably, while the AI is kept as a constrained planner — never an authority on geography, dates, or whether data exists.

### 3. Every chart, not just one
A single question now returns **all** the ways to view the same QC-passed data. The backend computes the other aggregation types (depth profile, time series, regional average) alongside the one you asked for, and the UI shows them as "Additional visualizations."
> **Why:** the queried view is shown first and largest; the rest follow as supporting context, nothing hidden.

### 4. A precise, honest map
The map now draws exactly what the backend selected. Region rectangles come from the backend's canonical bounds (a duplicated, drift-prone table in the frontend was removed). The viewport fits the actual geometry — a radius circle for point queries, the region box for regions — with a "Reset view" control, a screen-reader text description, and reduced-motion support.
> **Why:** a higher zoom number isn't precision. Correct coordinates, real radius-to-kilometres, and canonical bounds are.

### 5. The anomaly score is always shown
The Z-score (how far a reading sits from the historical baseline, in standard deviations) is now computed whenever the evidence allows — not only when the question explicitly asked "is this unusual?". When there isn't enough data, the card stays visible but shows an honest "assessment unavailable" note.
> **Why:** the context is useful on every answer; the flag now only affects wording emphasis, not whether the number exists.

### 6. A clearer results panel
The "Computation Transparency" section now opens with a **plain-English narrative** (*"Searched the Arabian Sea… found 1,965 raw profiles; 1,228 passed quality control…"*) instead of a wall of raw numbers. The technical identifiers — float IDs, profile IDs, source rows, dataset hash — moved into a collapsed "Data Source" section.
> **Why:** lead with the story a person can read; keep the audit trail one click away.

### 7. Seven new scientific charts
Added a **T–S diagram**, **density profile**, **ocean-heat-content** card, a **Hovmöller** depth–time heatmap, **seasonal cycle** (with a ±1σ band), **year-over-year** overlay, and an **anomaly-trend** line — plus a confidence-interval band on the main time-series chart. Each is best-effort: it appears only when the data supports it.
> **Why:** these are the visualizations oceanographers actually reach for; the Hovmöller heatmap especially reads at a glance.

### 8. A deliberate reading order
Each answer now flows most-important to most-technical: interpreted question → plain insight → primary chart + map + anomaly card → evidence grade → secondary charts → supplementary science → transparency narrative → collapsed data source.
> **Why:** the thing you asked for is first and biggest; everything else is layered support.

---

## Where the changes live

| File | Type | What changed |
|---|---|---|
| `backend/app/services/parser_policy.py` | new | Single source of truth for parsing rules + generated AI prompt |
| `backend/app/services/parser.py` | rewrite | Word-boundary helpers, classified failures, semantic validation, relative/seasonal dates |
| `backend/app/services/aggregation.py` | edit | Seven supplementary views + the with-trace performance flag |
| `backend/app/api/chat.py` | edit | Always-on Z-score, secondary views, supplementary data |
| `backend/app/models.py` | edit | Geographic bounds + new response fields |
| `backend/tests/test_parser.py` | edit | 30+ paraphrases, 10 unsupported, provider-failure classification |
| `evaluation/fixtures/parser_queries.json` | edit | Frozen reliability fixture grown to 30 prompts |
| `frontend/src/components/SecondaryCharts.tsx` | new | Renders the other aggregation types |
| `frontend/src/components/SupplementaryCharts.tsx` | new | The seven scientific charts |
| `frontend/src/utils/geo.ts` | new | Pure coordinate/radius formatting helpers |
| `frontend/src/components/OceanMap.tsx` | rewrite | Geometry-fit viewport, reset control, accessibility |
| `frontend/src/components/ExplanationPanel.tsx` | rewrite | Narrative transparency + collapsed Data Source |
| `frontend/src/components/StatusCard.tsx` | edit | Always renders; muted when no score |
| `frontend/src/components/Charts.tsx` | edit | Larger axes, confidence-interval band |
| `frontend/src/globals.css` | edit | Font-size increases + new component styles |
| `frontend/src/api/adapter.ts` | edit | Backend-bounds passthrough, CI-band math, removed drift table |
| `frontend/src/api/chatApi.ts`, `types/ocean.ts` | edit | New contract fields (bounds, secondary/supplementary) |
| `frontend/src/components/ResultView.tsx` | edit | Wires the new chart sections into the layout order |
| `frontend/tests/rendered-html.test.mjs` | edit | Updated for the reorganized panel + new charts |

---

## How it was verified

- **Backend:** `ruff` clean, **183** pytest tests passing, parser reliability suite **30/30**.
- **Frontend:** TypeScript build clean, `eslint` clean, **9** contract tests passing.
- **End-to-end:** ran the live API + dev server and drove a real query through the running app, confirming every new section rendered — secondary charts, all supplementary views, the narrative transparency panel, the collapsed Data Source, the always-on Z-score, and the map with backend-derived bounds.

### Performance, before → after the fix

| Query | Before | After |
|---|---|---|
| Point profile (10N 70E, 150 km) | ~3 s | **1.5 s** |
| SST time-series (10 years) | ~23 s | **10.5 s** |
| Arabian Sea regional average | ~39 s | **14 s** |

The new "additional views" were paying the full cost of building a per-row audit trail they never display. Turning that trail off for the secondary charts (the primary answer keeps its full trace) removed most of the slowdown.

---

## Deliberate deviations & limits (the honest bits)

- **Parser test fixture kept at 30, not 38+.** The prompt asked to grow the frozen fixture to 30+ supported and 8+ unsupported prompts. The repo's own reliability script hard-caps that fixture at 20–30 (an evidence-integrity guard). Rather than break it, the fixture sits at the maximum **30**, and the full ≥30-supported / ≥10-unsupported coverage lives in the **unit tests** instead.
- **Live check was DOM-based, not a screenshot.** The browser pane wasn't compositing frames on this machine, so end-to-end verification read the live page's accessibility tree and text rather than capturing a picture. Content and structure were confirmed present; a pixel-level visual pass and the projector/mobile size checks are still worth a human eye.
- **Some supplementary charts are conditional.** By design, the T–S diagram and density profile need both temperature and salinity columns (so they appear on multi-parameter queries), and year-over-year needs two or more years. A single-year, single-parameter question won't show all seven — this is expected best-effort behavior, not a bug.
- **The data is still Arabian-Sea-only.** Unchanged from before v6: the installed dataset covers the Arabian Sea, so Mumbai / Chennai / Bay-of-Bengal queries still correctly return an honest "no data." That's a dataset limitation, not something this work altered.

---

## Still open (not done — and why)

- **Regional queries take ~14 s.** The remaining cost is the quality-control filter plus the primary aggregation over ~900k observations — the real answer. Cutting it further means downsampling the supplementary charts or moving them off the request path; left as a follow-up rather than touching the audited QC boundary.
- **Scientific anomaly labels remain empty.** The v6 prompt didn't ask for them, so the reviewed anomaly ground-truth (and therefore precision/recall numbers) is still unpopulated, exactly as before.
- **The Gemini AI key is still unset.** The parser architecture is ready for it, but with no key the deterministic fallback handles everything — which is the safe, intended default.

---

*Latency figures are warm-cache measurements on the local dataset. Backend and frontend checks green; pre-existing `data/` edits left untouched.*

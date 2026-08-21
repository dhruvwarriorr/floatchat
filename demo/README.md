# Demo fallback package

- `cached/`: sanitized successful response JSON and any minimal offline viewer artifacts.
- `screenshots/`: projector-sized captures for the pinned flows and failure states.

Both directories are ignored except for their placeholders. Deliberately add only reviewed, credential-free release artifacts when the team freezes a demo build. Every cached response must state its dataset/build version and whether it came from a live, local, or recorded run.

Rev. B responses must also preserve the data-quality warning, evidence grade, QC rule, valid/excluded counts, distinct-float count, baseline `n`, and provenance panel. A cached response that omits these fields cannot support an anomaly or reliability claim.

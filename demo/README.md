# Demo fallback package

- `cached_responses/`: generated sanitized API JSON from `scripts/build_demo_cache.py`.
- `cached/`: retained legacy cache boundary.
- `screenshots/`: projector-sized captures for the pinned flows and failure states.

Cache and screenshot directories are ignored except for their placeholders. Current generated cache files include complete measured Arabian-Sea responses and honest typed `no_data` records for prescribed examples outside the installed Arabian-Sea coverage. They are labelled as demo cache, are not a release claim, and must be regenerated after any data/contract change.

Rev. B responses must also preserve the data-quality warning, evidence grade, QC rule, valid/excluded counts, distinct-float count, baseline `n`, and provenance panel. A cached response that omits these fields cannot support an anomaly or reliability claim.

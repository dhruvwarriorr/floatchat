# Evidence and claim gate

> Current status: no observed result rows are recorded as of 21 August 2026.

`evidence-log.csv` is the source of truth for results that may support demo, release, or pitch claims. Its empty data section means parser accuracy, scientific validation, container deployment, live-data integration, projector checks, cached fallback acceptance, and rehearsal counts are **not verified**.

Add a row only after running the stated command or method against the recorded dataset/build. Record:

- date and owner;
- claim or test;
- exact command or method;
- dataset version or build identifier;
- observed result, including negative results;
- whether the result is allowed in the pitch; and
- a small evidence artifact path when applicable.

Automated lint/build/unit-test success is useful engineering evidence but does not prove scientific validity, provider reliability, projector acceptance, deployment health, or rehearsal success.

Store small sanitized text reports here. Keep scientific artifacts under `data/`, visual captures under `demo/screenshots/`, and secrets/private data out of the repository. Never edit an observed number to improve a claim.

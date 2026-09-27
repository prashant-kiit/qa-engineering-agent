# Agile Plan — Agentic QA Engineer (SaaS)

> Phase 0 detailed and executable now. Phases 1–7 are re-planned to this level of detail each
> iteration, against the current app state + `META_PLAN.md`. `META_PLAN.md` is the fixed north star;
> this is the living working-detail. `DESIGN.md` remains the architecture source of truth.

## Task 0 (do first): record post-v1 scope in `DESIGN.md §15`
Add to `DESIGN.md §15`:
> **Explicitly post-v1 (not in first SaaS release):** (a) target-app auth beyond Basic Auth —
> SSO/MFA; (b) data residency & retention policy per tenant tier. All other §15 items are
> implemented in-phase; only their fine detail / eval-driven choice is deferred.

## Phase 0 — Testbed & scaffolding
**Goal:** a real shop app to test + a reliability measurement harness + repo scaffolding, all
reproducible with one command.

### B1. Repo scaffolding
Create the `DESIGN.md §13` directory tree with placeholders; Phase 0 fills `reference_app/`,
`eval/`, and root tooling. Representative paths:

```
reference_app/{backend,frontend}/   agent_config/  connectors/  reliability/
runner/  eval/  control_plane/{api,orchestration,stores,frontend}/  sandbox/
```

- Root tooling: Python env (`uv` or `poetry`) for backend/eval; Node + Playwright for frontend/tests;
  a `Makefile`/`justfile` with `dev`, `test`, `eval`, `release` targets.
- Extend the existing `.gitignore` for `.venv/`, `node_modules/`, `*.db`, Playwright artifacts.

### B2. Reference shop app — `reference_app/` (FastAPI + React + SQLite)
- **Backend (`reference_app/backend/`):** Basic Auth (username/password), products, cart,
  add-to-cart, checkout → create order, get order, order-total calc. FastAPI auto-serves
  `/openapi.json` (the spec the agent grounds API tests on). Seed data: products + one test account.
- **Frontend (`reference_app/frontend/`, React + Vite):** login, product list, cart, checkout,
  order-confirmation — talks to the backend.
- **Run:** `make dev` starts API + UI with seeded SQLite.

### B3. BRD + release convention
- `reference_app/BRD.md` — **freeform** description of intended shop behavior.
- Release convention: a `version` marker + tagging so a "release" bundles code + BRD and yields a
  diff (used by Phase 1 Case 1 / Phase 4 change-detection). Document in `reference_app/README.md`.

### B4. `eval/` injected-bug harness — the reliability gate
- **Bug injection:** buggy variants via env-flag/patch set. Ship ≥3 known bugs, e.g. (a) checkout
  total miscalculation, (b) cart quantity not updating, (c) auth check bypass on an order endpoint.
- **Scorer (`eval/score.py`):** given a suite run against **clean vs each buggy** variant, compute
  **bug-catch rate**, **false-positive rate**, **flake** (re-run consistency), and an
  **assertion-meaningfulness** audit.
- **Baseline:** a small **hand-written** Playwright suite so the harness is provably runnable before
  any agent exists (agent plugs in at Phase 1).

### B5. Playwright TS project
- `playwright.config.ts` + `tests/` targeting the reference app; one hand-written **smoke test**
  (login → add to cart → checkout), **green on clean**, **red on a buggy variant** — validates the
  runner end-to-end.

### Phase 0 acceptance
- `make dev` runs API + UI; `/openapi.json` served; seed data + test account; `BRD.md` exists.
- `make test` runs the Playwright smoke test green on clean.
- `make eval` injects ≥3 bugs and prints catch / false-positive / flake / assertion metrics.

## Verification
- **Phase 0:** run `make dev`; curl key endpoints + load UI; run `make test` (green on clean, red on
  a buggy variant); run `make eval` and inspect the metrics table.
- **Later phases:** gated by the `eval/` metrics (see `META_PLAN.md` gates). Phase 3+ additionally
  verified by a real E2B run — inspect the PR, checkpoints, secret-free logs, and egress denials.

## Agile revise loop
After each phase, re-plan the next phase to this level of detail against the **current app state +
`META_PLAN.md`**. Update `DESIGN.md` if a phase forces an architecture change.

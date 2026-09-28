# Agile Plan — Agentic QA Engineer (SaaS)

> Phase 0 detailed and executable now. Phases 1–7 are re-planned to this level of detail each
> iteration, against the current app state + `META_PLAN.md`. `META_PLAN.md` is the fixed north star;
> this is the living working-detail. `DESIGN.md` remains the architecture source of truth.

## Conflicts / deviations for human review
- **None.** Current repo (docs + harness + units 0–5 done: doc note + scaffold/tooling +
  FastAPI/SQLite shop backend + React/Vite shop frontend + BRD/release convention + Playwright TS
  smoke) is consistent with `META_PLAN.md` Phase 0 and `DESIGN.md`. Proceeding to the **final** unit
  6 (`p0-eval-harness`). The `eval/` harness lands in the `DESIGN.md §13` top-level `eval/` dir; the
  reference app under `reference_app/` stays **pristine** (the bug catalog is a non-invasive
  launcher-overlay, exactly like the unit-5 `SMOKE_FAULT`/`smoke_backend.py` pattern), so §13 and §9
  are not contradicted.
- **Scope fold (recorded, not a deviation):** the Phase 0 **exit gate** requires `make dev` to run
  API + UI and `make eval` to inject ≥3 bugs and print metrics. `make dev` and `make eval` are still
  root-`Makefile` placeholders. Unit 5's spec explicitly deferred real `make dev` wiring to "a small
  follow-on at the exit gate." As the last Phase 0 unit before the exit gate, **unit 6 folds in the
  `make dev` clean-app launcher wiring and the `make eval` wiring** so the exit gate passes on
  landing. This is additive Makefile wiring reusing the already-pinned launch commands — it does not
  contradict `META_PLAN.md`/`DESIGN.md`.

## Task 0 (do first): record post-v1 scope in `DESIGN.md §15`
Add to `DESIGN.md §15`:
> **Explicitly post-v1 (not in first SaaS release):** (a) target-app auth beyond Basic Auth —
> SSO/MFA; (b) data residency & retention policy per tenant tier. All other §15 items are
> implemented in-phase; only their fine detail / eval-driven choice is deferred.

**Status:** DONE (unit `p0-design-note`, commit `50bf25a`). Note present in `DESIGN.md §15`.

## Phase 0 — Testbed & scaffolding  — LOCKED for this iteration (2026-09-28, re-confirmed at unit 6)

**Current app state:** repo contains docs (`DESIGN.md`, `META_PLAN.md`, this file, `CLAUDE.md`),
harness config (`.harness/`, `.claude/`), `.gitignore`, `LICENSE`, and Phase-0 units 0–5 **done**:
- **Unit 0 (`p0-design-note`) — `done`** (commit `50bf25a`): the post-v1 note is present in
  `DESIGN.md §15`.
- **Unit 1 (`p0-scaffold`) — `done`** (commit `d958ac6`): the full `DESIGN.md §13` directory tree
  with placeholders, a root `uv` project manifest (`pyproject.toml`), a root `Makefile` with
  `dev`/`test`/`test-smoke-buggy`/`e2e-deps`/`eval`/`release` + `help` targets, and the extended
  `.gitignore`.
- **Unit 2 (`p0-shop-backend`) — `done`** (commit `0ea16c8`): a runnable **FastAPI + SQLite** shop
  backend at `reference_app/backend/app.py`, importable as `reference_app.backend.app:app` and
  servable on `http://127.0.0.1:8000`. HTTP Basic Auth (`testuser`/`testpass`), a fixed 5-product
  seed catalog (stable ids/prices), a per-user cart with **cumulative** add-to-cart, checkout→order,
  order retrieval, correct order-total (`total = Σ price × quantity`), auth required on every order
  endpoint, and an auto-served `/openapi.json`. Contract in `.harness/tasks/p0-shop-backend.md`;
  launch/seed docs in `reference_app/backend/README.md`.
- **Unit 3 (`p0-shop-frontend`) — `done`** (commit `ba4d349`): a **React + Vite** SPA at
  `reference_app/frontend/` with five views (login, product list, cart, checkout, order
  confirmation) driving the backend over Basic Auth; stable `data-testid` DOM contract documented in
  `reference_app/frontend/README.md`. Vite dev server default `http://127.0.0.1:5173`;
  `VITE_API_BASE_URL` default `http://127.0.0.1:8000`.
- **Unit 4 (`p0-brd-release`) — `done`** (commit `4a63635`): `reference_app/BRD.md` (freeform
  intended behavior), `reference_app/README.md` (release convention: version marker + git tag
  scheme), and `reference_app/VERSION`.
- **Unit 5 (`p0-playwright-smoke`) — `done`** (commit `e07dccd`): a **TypeScript Playwright** project
  at `reference_app/e2e/` (`playwright.config.ts` + `tests/smoke.spec.ts` + dedicated `package.json`
  + `tsconfig.json` + `README.md`) with one UI smoke (login → add to cart → checkout, load-bearing
  `order-total == cart-total` assertion). **Green on clean, red under the single `SMOKE_FAULT=1`
  toggle.** Wired into `make test` (idempotent deps + Chromium install, clean-app run, exit-code
  propagated) and `make test-smoke-buggy` (the red-on-buggy demo). The reference backend is launched
  for the browser run via a **non-invasive launcher overlay** at `reference_app/e2e/smoke_backend.py`
  that imports the clean backend unchanged, adds launch-time CORS, and overlays exactly one fault
  under `SMOKE_FAULT=1` — the clean source stays pristine.

**Still missing (the final unit):** the `eval/` injected-bug harness — the ≥3-bug catalog, the
`eval/score.py` scorer, and the baseline suite the scorer runs — plus wiring `make eval` (and the
clean-app `make dev` launcher) so the Phase 0 exit gate passes. Active unit: **6
(`p0-eval-harness`)** — deps `p0-playwright-smoke` and `p0-shop-backend` are both `done` (**met**).

**Environment note (informs, does not override META_PLAN/DESIGN):** the dev machine has `uv` and GNU
`make`; Node + `npm`/`npx` + a Playwright-installed Chromium are available (unit 5). Test artifacts
are **TypeScript Playwright** (`DESIGN.md §12`) — the unit-6 baseline suite is authored in the same
TS-Playwright toolchain (UI + Playwright API tests), reusing the `reference_app/e2e/` project.
**Unit-6 pattern reuse:** the ≥3-bug catalog is implemented as a **non-invasive backend
launcher-overlay** modelled on `reference_app/e2e/smoke_backend.py` (import the clean backend
unchanged; add launch-time CORS; apply exactly one selected fault via an env toggle), living under
`eval/` so the clean reference app is never modified. Making `make dev` a real clean-app launcher and
wiring `make eval` are folded into unit 6 (they satisfy the exit gate); the launch commands are those
already pinned in the unit-5 config.

**Locked ordered units** (source of truth: `.harness/backlog.md`; scope: B1–B5 below):

| # | id | Depends on | Status |
|---|----|-----------|--------|
| 0 | `p0-design-note` | — | done |
| 1 | `p0-scaffold` | — | done |
| 2 | `p0-shop-backend` | `p0-scaffold` | done |
| 3 | `p0-shop-frontend` | `p0-shop-backend` | done |
| 4 | `p0-brd-release` | `p0-shop-backend` | done |
| 5 | `p0-playwright-smoke` | `p0-shop-frontend` | done |
| 6 | `p0-eval-harness` | `p0-playwright-smoke`, `p0-shop-backend` | **active (spec-ready)** |

**Goal:** a real shop app to test + a reliability measurement harness + repo scaffolding, all
reproducible with one command.

### B1. Repo scaffolding — **DONE (unit 1, `p0-scaffold`)**
Create the `DESIGN.md §13` directory tree with placeholders; Phase 0 fills `reference_app/`,
`eval/`, and root tooling. Representative paths:

```
reference_app/{backend,frontend}/   agent_config/  connectors/  reliability/
runner/  eval/  control_plane/{api,orchestration,stores,frontend}/  sandbox/
```

- Root tooling: Python env (`uv`) for backend/eval; Node + Playwright for frontend/tests; a
  `Makefile` with `dev`, `test`, `eval`, `release` targets.
- Extend `.gitignore` for `.venv/`, `node_modules/`, `*.db`, Playwright artifacts.

### B2. Reference shop app — `reference_app/` (FastAPI + React + SQLite) — **DONE (units 2 + 3)**
- **Backend (`reference_app/backend/`):** Basic Auth, products, cart, add-to-cart, checkout → order,
  get order, order-total calc, auto `/openapi.json`, seed data. **Unit 2 (`p0-shop-backend`) —
  DONE.**
- **Frontend (`reference_app/frontend/`, React + Vite):** login, product list, cart, checkout,
  order-confirmation. **Unit 3 (`p0-shop-frontend`) — DONE.**
- **Run:** `make dev` starts API + UI with seeded SQLite. **Real `make dev` wiring is folded into
  unit 6** (exit-gate follow-on); the launch commands are the ones pinned in the unit-5 config.

### B3. BRD + release convention — **DONE (unit 4, `p0-brd-release`)**
- `reference_app/BRD.md` (freeform intended behavior), release convention (version marker + git tag
  scheme) documented in `reference_app/README.md`, `reference_app/VERSION`. Building the
  diff/hashing tooling is Phase 4, out of scope.

### B4. `eval/` injected-bug harness — the reliability gate  — **ACTIVE (unit 6, `p0-eval-harness`)**
- **Bug injection:** buggy variants of the reference app via an env-flag/variant-selector, built on
  the non-invasive launcher-overlay pattern (like `reference_app/e2e/smoke_backend.py`) so the clean
  app stays pristine. Ship **≥3 known bugs**: (a) checkout-total miscalculation, (b) cart quantity
  not updating (add-to-cart quantity bug), (c) auth-check bypass on an order endpoint.
- **Scorer (`eval/score.py`):** given the baseline suite run against **clean vs each buggy** variant
  (with re-runs), compute and print **bug-catch rate**, **false-positive rate**, **flake** (re-run
  consistency), and an **assertion-meaningfulness** audit, with pinned, testable metric definitions.
- **Baseline:** a small **hand-written** TS-Playwright suite (UI + API), reusing the unit-5
  `reference_app/e2e/` project, that the scorer runs — proving the harness is runnable before any
  agent exists (the agent plugs in at Phase 1). Passes on clean; catches each injected bug.
- **`make eval`:** wires it all — runs the scorer across the ≥3 bugs + clean and prints the metrics
  table; the Phase-0 exit-gate command. **Also fold in `make dev`** (clean-app API+UI launcher) so
  the full exit gate passes.
- Full contract in `.harness/tasks/p0-eval-harness.md`.

### B5. Playwright TS project — **DONE (unit 5, `p0-playwright-smoke`)**
- A **TypeScript Playwright** project at `reference_app/e2e/` (`playwright.config.ts`,
  `tests/smoke.spec.ts`, dedicated `package.json`). One UI smoke (login → add to cart → checkout,
  meaningful `order-total == cart-total` assertion), **green on clean, red under `SMOKE_FAULT=1`**,
  launched via `webServer` (backend via `smoke_backend:app` + Vite frontend). Wired into `make test`
  (+ `make test-smoke-buggy`). Contract in `.harness/tasks/p0-playwright-smoke.md`.

### Phase 0 acceptance (exit gate)
- `make dev` runs API + UI; `/openapi.json` served; seed data + test account; `BRD.md` exists.
  *(`/openapi.json` + seed + `BRD.md` present since units 2/4; the `make dev` launcher itself is
  wired by unit 6.)*
- `make test` runs the Playwright smoke test green on clean. *(Unit 5 — satisfied.)*
- `make eval` injects ≥3 bugs and prints catch / false-positive / flake / assertion metrics.
  *(Unit 6 — the final unit.)*

## Verification
- **Phase 0:** run `make dev`; curl key endpoints + load UI; run `make test` (green on clean, red on
  a buggy variant); run `make eval` and inspect the metrics table.
- **Later phases:** gated by the `eval/` metrics (see `META_PLAN.md` gates). Phase 3+ additionally
  verified by a real E2B run — inspect the PR, checkpoints, secret-free logs, and egress denials.

## Agile revise loop
After each phase, re-plan the next phase to this level of detail against the **current app state +
`META_PLAN.md`**. Update `DESIGN.md` if a phase forces an architecture change.

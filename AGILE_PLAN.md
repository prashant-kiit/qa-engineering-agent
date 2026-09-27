# Agile Plan — Agentic QA Engineer (SaaS)

> Phase 0 detailed and executable now. Phases 1–7 are re-planned to this level of detail each
> iteration, against the current app state + `META_PLAN.md`. `META_PLAN.md` is the fixed north star;
> this is the living working-detail. `DESIGN.md` remains the architecture source of truth.

## Conflicts / deviations for human review
- **None.** Current repo (docs + harness + units 0–3 done: doc note + scaffold/tooling +
  FastAPI/SQLite shop backend + React/Vite shop frontend) is consistent with `META_PLAN.md`
  Phase 0 and `DESIGN.md`. Proceeding to unit 4 (`p0-brd-release`).

## Task 0 (do first): record post-v1 scope in `DESIGN.md §15`
Add to `DESIGN.md §15`:
> **Explicitly post-v1 (not in first SaaS release):** (a) target-app auth beyond Basic Auth —
> SSO/MFA; (b) data residency & retention policy per tenant tier. All other §15 items are
> implemented in-phase; only their fine detail / eval-driven choice is deferred.

**Status:** DONE (unit `p0-design-note`, commit `50bf25a`). Note present in `DESIGN.md §15`.

## Phase 0 — Testbed & scaffolding  — LOCKED for this iteration (2026-09-27, re-confirmed at unit 4)

**Current app state:** repo contains docs (`DESIGN.md`, `META_PLAN.md`, this file, `CLAUDE.md`),
harness config (`.harness/`, `.claude/`), `.gitignore`, `LICENSE`. **Unit 0 (`p0-design-note`) is
`done`** — the post-v1 note is present in `DESIGN.md §15` (commit `50bf25a`). **Unit 1
(`p0-scaffold`) is `done`** — the full `DESIGN.md §13` directory tree with placeholders, a root `uv`
project manifest (`pyproject.toml`), a root `Makefile` with placeholder `dev`/`test`/`eval`/`release`
+ `help` targets, and the extended `.gitignore` are all present (commit `d958ac6`). **Unit 2
(`p0-shop-backend`) is `done`** — a runnable **FastAPI + SQLite** shop backend lives at
`reference_app/backend/app.py`, importable as `reference_app.backend.app:app` and servable on
`http://127.0.0.1:8000` (commit `0ea16c8`). It implements HTTP Basic Auth (`testuser`/`testpass`), a
**fixed 5-product seed catalog**, a per-user cart with cumulative add-to-cart, checkout→order, order
retrieval, correct order-total, and an auto-served `/openapi.json` (routes `/products`, `/cart`,
`/cart/items`, `/checkout`, `/orders/{id}`). The backend API contract is fully specified in
`.harness/tasks/p0-shop-backend.md`; the launch entrypoints + seed are documented in
`reference_app/backend/README.md`. **Unit 3 (`p0-shop-frontend`) is `done`** — a **React + Vite**
single-page UI lives at `reference_app/frontend/` with five views (login, product list, cart,
checkout, order-confirmation) that drive the backend over Basic Auth; verified at the
component/integration level (Vitest with backend stubbed) plus a passing production build (commit
`ba4d349`, branch `harness/p0-shop-frontend`). The UI contract + scripts are documented in
`reference_app/frontend/README.md`. **Still missing:** no `BRD.md`, no `reference_app/README.md` /
release convention, no Playwright project, no `eval/` logic. Active unit: **4 (`p0-brd-release`)** —
dep `p0-shop-backend` is `done` (met). Remaining units 5–6 build the Playwright smoke and the
`eval/` harness on top of it.

**Environment note (informs, does not override META_PLAN/DESIGN):** the dev machine has `uv` and GNU
`make` available; Node + `npx` are available for the frontend and later Playwright units. The Phase 0
frontend stack is **React + Vite** (per `DESIGN.md §12` and B2 below). The BRD + release convention
(B3, this unit) is **documentation + a documented convention + a version marker only** — building the
content-hashing / diff *tooling* is explicitly Phase 4 (`META_PLAN.md` Phase 4) and is out of Phase 0
scope. The full browser E2E smoke against a live app is a **separate later unit (5)**.

**Locked ordered units** (source of truth: `.harness/backlog.md`; scope: B1–B5 below):

| # | id | Depends on | Status |
|---|----|-----------|--------|
| 0 | `p0-design-note` | — | done |
| 1 | `p0-scaffold` | — | done |
| 2 | `p0-shop-backend` | `p0-scaffold` | done |
| 3 | `p0-shop-frontend` | `p0-shop-backend` | done |
| 4 | `p0-brd-release` | `p0-shop-backend` | **active** |
| 5 | `p0-playwright-smoke` | `p0-shop-frontend` | todo |
| 6 | `p0-eval-harness` | `p0-playwright-smoke`, `p0-shop-backend` | todo |

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
  **This is unit 2 (`p0-shop-backend`) — DONE.**
- **Frontend (`reference_app/frontend/`, React + Vite):** login, product list, cart, checkout,
  order-confirmation — talks to the backend (Basic Auth; routes/shapes per
  `.harness/tasks/p0-shop-backend.md`). **This is unit 3 (`p0-shop-frontend`) — DONE.** Its
  acceptance was verified at the **component/integration level** (Vite test tooling with backend
  calls stubbed) plus a **production build succeeding** — NOT via Playwright or a live backend
  (those belong to unit 5).
- **Run:** `make dev` starts API + UI with seeded SQLite.

### B3. BRD + release convention — **ACTIVE (unit 4, `p0-brd-release`)**
- `reference_app/BRD.md` — **freeform** description of intended shop behavior (the human-readable
  intended behavior that Phase 1 Case 1 / Phase 4 change-detection diff against). Must cover the
  shop's key flows in prose: auth, products, cart, checkout, orders, and order-total.
- Release convention: a **version marker** + a **git tag scheme** so a "release" bundles code + BRD
  and yields a diff (consumed by Phase 1 Case 1 / Phase 4 change-detection). **Documented in
  `reference_app/README.md`** (create it).
- **Docs + a documented convention + a version marker only** — building the diff/hashing tooling
  itself is Phase 4, out of scope here.

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

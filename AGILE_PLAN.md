# Agile Plan — Agentic QA Engineer (SaaS)

> Phase 0 detailed and executable now. Phases 1–7 are re-planned to this level of detail each
> iteration, against the current app state + `META_PLAN.md`. `META_PLAN.md` is the fixed north star;
> this is the living working-detail. `DESIGN.md` remains the architecture source of truth.

## Conflicts / deviations for human review
- **None.** Current repo (docs + harness + units 0–4 done: doc note + scaffold/tooling +
  FastAPI/SQLite shop backend + React/Vite shop frontend + BRD/release convention) is consistent with
  `META_PLAN.md` Phase 0 and `DESIGN.md`. Proceeding to unit 5 (`p0-playwright-smoke`). The Playwright
  project is placed at `reference_app/e2e/` — a sub-directory of the `DESIGN.md §13` `reference_app/`
  dir, so no new top-level dir is introduced and §13 is not contradicted.

## Task 0 (do first): record post-v1 scope in `DESIGN.md §15`
Add to `DESIGN.md §15`:
> **Explicitly post-v1 (not in first SaaS release):** (a) target-app auth beyond Basic Auth —
> SSO/MFA; (b) data residency & retention policy per tenant tier. All other §15 items are
> implemented in-phase; only their fine detail / eval-driven choice is deferred.

**Status:** DONE (unit `p0-design-note`, commit `50bf25a`). Note present in `DESIGN.md §15`.

## Phase 0 — Testbed & scaffolding  — LOCKED for this iteration (2026-09-28, re-confirmed at unit 5)

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
`ba4d349`). The UI contract, scripts (`dev`/`build`/`test`), Vite dev server (default
`http://127.0.0.1:5173`), `VITE_API_BASE_URL` (default `http://127.0.0.1:8000`), and the stable
`data-testid` DOM contract are documented in `reference_app/frontend/README.md` and the view sources.
**Unit 4 (`p0-brd-release`) is `done`** — `reference_app/BRD.md` (freeform intended behavior),
`reference_app/README.md` (release convention: version marker + git tag scheme), and
`reference_app/VERSION` are present (commit `4a63635`). **Still missing:** no Playwright project, no
`eval/` logic; the root `Makefile` `test`/`eval`/`dev` targets are still placeholders. Active unit:
**5 (`p0-playwright-smoke`)** — dep `p0-shop-frontend` is `done` (met). Remaining after: unit 6
(`p0-eval-harness`) builds the injected-bug harness + scorer on top of the smoke.

**Environment note (informs, does not override META_PLAN/DESIGN):** the dev machine has `uv` and GNU
`make` available; Node + `npm`/`npx` are available for the frontend and the Playwright unit. The
Phase 0 frontend stack is **React + Vite** (per `DESIGN.md §12`). Test artifacts are **TypeScript
Playwright** (`DESIGN.md §12`). For unit 5, the Playwright project is a dedicated Node project under
`reference_app/e2e/` (its own `package.json` declaring `@playwright/test`), kept separate from the
frontend's Vitest toolchain and from the root bash `tests/` suites to avoid collisions. The full
≥3-bug injection catalog + `eval/score.py` scorer remains **unit 6**, out of unit-5 scope; unit 5
ships exactly one deliberately-faulty variant (a single `SMOKE_FAULT` toggle) purely to demonstrate
the smoke goes red. Making `make dev` a real app-launcher is not required by unit 5 (the launch
commands pinned in the unit-5 spec may be reused for it at the Phase 0 exit gate).

**Locked ordered units** (source of truth: `.harness/backlog.md`; scope: B1–B5 below):

| # | id | Depends on | Status |
|---|----|-----------|--------|
| 0 | `p0-design-note` | — | done |
| 1 | `p0-scaffold` | — | done |
| 2 | `p0-shop-backend` | `p0-scaffold` | done |
| 3 | `p0-shop-frontend` | `p0-shop-backend` | done |
| 4 | `p0-brd-release` | `p0-shop-backend` | done |
| 5 | `p0-playwright-smoke` | `p0-shop-frontend` | **active (spec-ready)** |
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
- **Run:** `make dev` starts API + UI with seeded SQLite. (Real `make dev` wiring is a small
  follow-on at the exit gate; the exact launch commands are pinned in the unit-5 spec.)

### B3. BRD + release convention — **DONE (unit 4, `p0-brd-release`)**
- `reference_app/BRD.md` — **freeform** description of intended shop behavior (the human-readable
  intended behavior that Phase 1 Case 1 / Phase 4 change-detection diff against). Covers the shop's
  key flows in prose: auth, products, cart, checkout, orders, and order-total.
- Release convention: a **version marker** (`reference_app/VERSION`) + a **git tag scheme** so a
  "release" bundles code + BRD and yields a diff, documented in `reference_app/README.md`.
- Docs + a documented convention + a version marker only — building the diff/hashing tooling itself
  is Phase 4, out of scope.

### B4. `eval/` injected-bug harness — the reliability gate  (unit 6, `p0-eval-harness`, NOT YET)
- **Bug injection:** buggy variants via env-flag/patch set. Ship ≥3 known bugs, e.g. (a) checkout
  total miscalculation, (b) cart quantity not updating, (c) auth check bypass on an order endpoint.
- **Scorer (`eval/score.py`):** given a suite run against **clean vs each buggy** variant, compute
  **bug-catch rate**, **false-positive rate**, **flake** (re-run consistency), and an
  **assertion-meaningfulness** audit.
- **Baseline:** a small **hand-written** Playwright suite so the harness is provably runnable before
  any agent exists (agent plugs in at Phase 1) — builds on the unit-5 smoke project.

### B5. Playwright TS project — **ACTIVE (unit 5, `p0-playwright-smoke`)**
- A **TypeScript Playwright** project rooted at **`reference_app/e2e/`**:
  `reference_app/e2e/playwright.config.ts` + `reference_app/e2e/tests/smoke.spec.ts` +
  `reference_app/e2e/package.json` (dedicated `@playwright/test` project). Path chosen to avoid
  collision with the root bash `tests/` suites and the frontend Vitest `src/__tests__`.
- **One hand-written smoke test** through the browser UI: login (`testuser`/`testpass`) → add to
  cart → view cart → checkout → assert the **order confirmation** with a **meaningful order-total
  assertion** (order-total equals the pre-checkout cart total).
- **Green on clean**, **red on a faulty variant.** The faulty variant is a **single documented
  toggle `SMOKE_FAULT`** that surfaces a wrong order total, making the smoke's order-total assertion
  fail (non-zero exit). Exactly one fault — the ≥3-bug catalog + scorer are deferred to unit 6 (B4).
- **App launch:** Playwright `webServer` starts the backend
  (`uv run uvicorn reference_app.backend.app:app --host 127.0.0.1 --port 8000`) and the frontend
  (`npm run dev`, `127.0.0.1:5173`, `VITE_API_BASE_URL=http://127.0.0.1:8000`); `baseURL` =
  `http://127.0.0.1:5173`; browser = Chromium.
- **`make test`** (root Makefile) idempotently installs the e2e deps + Chromium, runs the smoke
  against the clean app, and propagates the exit code. Full contract in
  `.harness/tasks/p0-playwright-smoke.md`.

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

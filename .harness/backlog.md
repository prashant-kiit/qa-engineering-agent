# Backlog — Phase 0 (Testbed & scaffolding)

Ordered units of work for the TDD harness. The **TPM** picks the top unit whose deps are `done`,
writes its spec to `.harness/tasks/<id>.md`, and the `/tdd` cycle proceeds.

**Status lifecycle:** `todo` → `spec-ready` (TPM wrote spec) → `in-progress` → `done`.
Source of truth for scope: `AGILE_PLAN.md` (Phase 0, B1–B5) and `DESIGN.md`.

| # | id | Unit | Depends on | Status |
|---|----|------|-----------|--------|
| 0 | `p0-design-note` | Doc-only: add the post-v1 note to `DESIGN.md §15` (SSO/MFA auth; data residency/retention). No test cycle — acceptance = text present. | — | done |
| 1 | `p0-scaffold` | Repo dir tree per `DESIGN.md §13` + root tooling: Python env (uv/poetry), Node + Playwright, `Makefile`/`justfile` (`dev`/`test`/`eval`/`release`), extend `.gitignore` (`.venv/`, `node_modules/`, `*.db`, Playwright artifacts). | — | spec-ready |
| 2 | `p0-shop-backend` | `reference_app/backend/` FastAPI + SQLite shop API: Basic Auth (user/pass), products, cart, add-to-cart, checkout→order, get-order, order-total calc; seed data (products + test account); auto `/openapi.json`. | `p0-scaffold` | todo |
| 3 | `p0-shop-frontend` | `reference_app/frontend/` React + Vite UI: login, product list, cart, checkout, order-confirmation; talks to the backend. | `p0-shop-backend` | todo |
| 4 | `p0-brd-release` | `reference_app/BRD.md` (freeform intended behavior) + release convention (version marker + tag + diff) documented in `reference_app/README.md`. | `p0-shop-backend` | todo |
| 5 | `p0-playwright-smoke` | Playwright TS project (`playwright.config.ts` + `tests/`) + one smoke test (login → add to cart → checkout): green on clean app, red on a buggy variant. | `p0-shop-frontend` | todo |
| 6 | `p0-eval-harness` | `eval/`: bug injection (≥3 known bugs — checkout-total miscalc, cart-qty bug, order-endpoint auth bypass) + `eval/score.py` (catch rate / false-positive / flake / assertion-meaningfulness) + a baseline hand-written suite proving the harness runs. | `p0-playwright-smoke`, `p0-shop-backend` | todo |

### Phase 0 exit gate (from `AGILE_PLAN.md`)
- `make dev` runs API + UI; `/openapi.json` served; seed data + test account; `BRD.md` exists.
- `make test` runs the Playwright smoke test green on clean.
- `make eval` injects ≥3 bugs and prints catch / false-positive / flake / assertion metrics.

> Notes: `p0-design-note` and `p0-scaffold`/`p0-brd-release` are infra/doc units — the Tester encodes
> their acceptance as presence/smoke checks (files exist, `make` targets succeed) rather than unit
> tests. Code units (`p0-shop-backend` onward) follow full red→green TDD.

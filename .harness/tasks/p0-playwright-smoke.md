# Task: `p0-playwright-smoke` — Playwright TS smoke project (login → add-to-cart → checkout)

## Title
Hand-written **TypeScript Playwright** E2E project + one **smoke test** that drives the reference
shop end-to-end (login → add to cart → checkout) and asserts the order confirmation — **green on the
clean app**, **red on a defined faulty variant** — wired so `make test` runs it against the clean app.

## Context (plan item)
- **AGILE_PLAN.md → Phase 0 → B5** ("Playwright TS project"): `playwright.config.ts` + a `tests/`
  location targeting the reference app; one hand-written smoke test (login → add to cart → checkout),
  **green on clean, red on a buggy variant** — validates the runner end-to-end.
- **Backlog unit 5** (`p0-playwright-smoke`), deps: `p0-shop-frontend` (**done**).
- **DESIGN.md §12**: test artifacts are **TypeScript Playwright** (`playwright test`).
- This unit produces the runnable Playwright harness that **unit 6 (`p0-eval-harness`)** builds on.
  It is the first true red→green TDD code unit of the E2E layer.

**Given app state (contracts to target — do NOT re-derive):**
- Backend: FastAPI + SQLite, binding import `reference_app.backend.app:app`; HTTP server default
  `http://127.0.0.1:8000` (override `SHOP_HOST`/`SHOP_PORT`); Basic Auth `testuser`/`testpass`;
  fixed 5-product seed catalog (stable ids + prices); DB reseeds on each fresh process. Endpoints:
  `GET /products`, `GET /cart`, `POST /cart/items {product_id, quantity}`, `POST /checkout`,
  `GET /orders/{id}`, `GET /openapi.json` (only route without auth). Invariant: `total` = Σ over line
  items of `price × quantity`. (Source: `reference_app/backend/README.md`,
  `.harness/tasks/p0-shop-backend.md`.)
- Frontend: React + Vite SPA at `reference_app/frontend/`. `npm run dev` starts the Vite dev server
  (default `http://127.0.0.1:5173`). Backend base URL resolved from `VITE_API_BASE_URL`, default
  `http://127.0.0.1:8000`. Existing scripts: `dev`, `build`, `test` (Vitest). (Source:
  `reference_app/frontend/README.md`, `package.json`.)
- **Stable DOM contract already present in the UI** (the smoke selects on these — they exist today):
  - Login: `[data-testid="login-username"]`, `[data-testid="login-password"]`,
    `[data-testid="login-submit"]`, `[data-testid="login-error"]`.
  - Navigation buttons by text: **"Products"**, **"Cart"**, **"Checkout"**.
  - Products: `[data-testid="product-item"]`, `[data-testid="add-to-cart"]`,
    `[data-testid="cart-count"]`.
  - Cart: `[data-testid="cart-line"]`, `[data-testid="cart-total"]`, `[data-testid="cart-checkout"]`.
  - Checkout: `[data-testid="checkout-submit"]`, `[data-testid="checkout-error"]`.
  - Order confirmation: heading text **"Order confirmed"**, `[data-testid="order-id"]`,
    `[data-testid="order-total"]`.

## Scope

### In scope
1. A self-contained **TypeScript Playwright project** rooted at `reference_app/e2e/`:
   - `reference_app/e2e/playwright.config.ts` — the Playwright config.
   - `reference_app/e2e/package.json` — a dedicated Node project declaring the `@playwright/test`
     dependency (kept separate from the frontend's Vitest toolchain to avoid version clashes).
   - `reference_app/e2e/tests/smoke.spec.ts` — the single smoke spec.
   - Any minimal supporting files the project needs (e.g. a `tsconfig.json`, a short README, a
     `.gitignore` entry for Playwright artifacts if not already covered).
2. **One smoke test** exercising the full happy path through the **browser UI** against the running
   reference app: login → add a product to cart → view cart → proceed to checkout → place order →
   assert the **order confirmation**, including a **meaningful assertion on the order total**.
3. **Clean-app green:** the smoke passes (process exit 0) against the clean, correct app.
4. **Buggy-variant red:** a **single, documented, self-contained toggle/mechanism** that produces a
   faulty variant of the app-under-test in which the smoke **fails** (non-zero exit) on its
   order-confirmation assertion — demonstrating the runner catches a real defect.
5. **`make test` wiring:** the root `make test` target runs the Playwright smoke against the clean
   app, ensuring prerequisites (project deps + browser binary) are present, and exits non-zero on
   failure. Replaces the current placeholder `test` target.
6. App launch for the test: the Playwright config **starts both servers itself** (backend + frontend)
   via Playwright's `webServer` support, so the test is one-command reproducible.

### Out of scope (defer)
- **The ≥3-bug catalog, the bug-injection patch-set/framework, and `eval/score.py` (catch rate /
  false-positive / flake / assertion-meaningfulness scoring) — these are unit 6 (`p0-eval-harness`).**
  Unit 5 ships **exactly one** deliberately-faulty variant, purely to demonstrate the smoke goes red;
  it must NOT build a catalog, a scorer, or a generalized injection harness.
- Adding a second/third browser project, cross-browser matrices, visual/snapshot testing, API-only
  test suites, CI wiring beyond `make test`.
- Any change to the clean behavior of the backend or frontend. The clean app must behave **exactly**
  as today; the faulty variant must be reachable **only** via the documented toggle and must leave the
  default (untoggled) path byte-for-byte unchanged.
- Making `make dev` real (the standalone app-launcher target) — not required by this unit; the launch
  commands pinned below may be reused for it later at the Phase 0 exit gate.

## Acceptance criteria (enumerated, testable)

1. **Project + config present and valid.** `reference_app/e2e/playwright.config.ts` exists and is a
   valid Playwright config: running the Playwright CLI in `reference_app/e2e/` (e.g. `list`/dry
   discovery) resolves the config and discovers the smoke spec without config errors. `testDir`
   resolves to `reference_app/e2e/tests`.
2. **Smoke spec exists at the pinned path.** `reference_app/e2e/tests/smoke.spec.ts` exists and
   contains exactly one E2E smoke test covering the full flow below.
3. **Smoke drives the full UI flow.** The test, running in a real browser against the running app:
   a. loads the app at the configured `baseURL`;
   b. logs in via `login-username`=`testuser`, `login-password`=`testpass`, `login-submit`, and
      confirms it reached the authenticated shop (product list visible; no `login-error`);
   c. adds a product to the cart via `add-to-cart` and confirms `cart-count` reflects the add
      (becomes `1`);
   d. navigates to the cart (nav **"Cart"**), confirms at least one `cart-line` is shown and reads
      `cart-total` as a positive number;
   e. proceeds to checkout (`cart-checkout`) and places the order (`checkout-submit`).
4. **Meaningful order-confirmation assertions.** After placing the order the test asserts:
   a. the **"Order confirmed"** heading is visible;
   b. `order-id` is present and non-empty (a created order identifier);
   c. `order-total` is a positive number and **equals** the cart total observed pre-checkout in
      step 3d (i.e. enforces the backend invariant `total = Σ price × quantity`). This equality is the
      load-bearing correctness assertion.
   These are real assertions on app-produced values — not mere presence-of-page checks.
5. **Green on clean.** Against the clean app, the smoke passes and the Playwright run exits **0**.
6. **Red on the faulty variant.** With the documented buggy-variant toggle enabled (see Interfaces),
   running the **same** smoke spec fails **at least the order-total assertion** and the Playwright run
   exits **non-zero**. The failure is a genuine assertion failure on wrong app output (not an infra
   error, timeout, or missing-server error).
7. **Toggle is minimal + isolated.** The faulty variant is produced by exactly one documented toggle
   introducing exactly one fault (a wrong order total surfaced at the order confirmation). With the
   toggle **unset**, the app behaves identically to today and the smoke is green (criterion 5). No
   bug catalog / scorer / injection framework is introduced.
8. **`make test` runs the clean smoke.** From the repo root, `make test`:
   a. ensures the e2e project's Node deps and the required browser binary are installed (idempotent —
      succeeds on a machine that has not pre-installed them, and is a no-op when already present);
   b. launches the reference app (backend + frontend) as needed and runs the smoke against the clean
      app;
   c. exits **0** when the smoke passes and **non-zero** when it fails.
9. **One-command reproducibility.** No manual server-starting or DB-seeding step is required before
   `make test`; the Playwright `webServer` config brings the app up and the backend reseeds on start.
10. **Red demonstration is reproducible via a single documented command.** There is one documented
    command (a `make` target and/or an npm script in `reference_app/e2e/package.json`, plus the
    toggle) that runs the smoke against the faulty variant and is expected to exit non-zero; it is
    clearly labelled as the "red on buggy" demonstration so its non-zero exit is understood as success
    of the demonstration.
11. **No collision with existing suites.** The new files live only under `reference_app/e2e/` (plus
    the root `Makefile` `test` target and, if needed, root `.gitignore`). They do **not** live in or
    alter the root bash suites under `tests/` or the frontend Vitest suites under
    `reference_app/frontend/src/__tests__`, and do not change clean backend/frontend source behavior.

## Interfaces / contracts (pin these precisely)

### Paths
- Playwright config: **`reference_app/e2e/playwright.config.ts`**
- Smoke spec: **`reference_app/e2e/tests/smoke.spec.ts`**
- E2E Node project manifest: **`reference_app/e2e/package.json`** (declares `@playwright/test`)
- Optional supporting: `reference_app/e2e/tsconfig.json`, `reference_app/e2e/README.md`

### App launch (Playwright `webServer` — start both, reuse if already up)
- **Backend:** command `uv run uvicorn reference_app.backend.app:app --host 127.0.0.1 --port 8000`
  run from the **repo root**; readiness probed at `http://127.0.0.1:8000/openapi.json`.
- **Frontend:** command `npm run dev` run from `reference_app/frontend/` (Vite dev server), pinned to
  host `127.0.0.1` and port **`5173`** with env `VITE_API_BASE_URL=http://127.0.0.1:8000`; readiness
  probed at `http://127.0.0.1:5173`.
  - Acceptable alternative if the developer prefers a production-like target: build then serve the
    Vite preview on a pinned port, provided `baseURL` and readiness are updated to match. The dev
    server on 5173 is the default contract.
- **`baseURL`** = the frontend origin (`http://127.0.0.1:5173` for the default contract). The smoke
  navigates relative to `baseURL`.
- `reuseExistingServer` should be enabled for local runs so an already-running app is reused.

### Browser
- Single browser project: **Chromium** (Playwright's bundled Chromium). The browser binary is
  installed via the Playwright CLI (`playwright install chromium`); `make test` ensures this
  idempotently. Headless by default.

### Seed / auth (targets, not to be re-implemented)
- Credentials `testuser` / `testpass`. Catalog is the fixed 5-product seed with stable prices; the DB
  reseeds on backend start, so the pre-checkout cart total is deterministic for a single added item.

### `make test` behavior (root `Makefile`)
- Replace the placeholder `test` target so it: (1) idempotently installs the `reference_app/e2e`
  Node deps + Chromium browser; (2) runs the Playwright smoke against the **clean** app (via the
  config's `webServer`); (3) propagates the Playwright exit code (0 pass / non-zero fail).

### Buggy-variant toggle + red demonstration
- A **single environment toggle**, name **`SMOKE_FAULT`** (unset or `0` = clean; `1` = faulty),
  governs the faulty variant. When `SMOKE_FAULT=1`, the app-under-test surfaces a **wrong order
  total** at the order confirmation (the order-confirmation `order-total` no longer equals the true
  cart total), causing the smoke's order-total equality assertion (criterion 4c) to fail.
- **Contract:** with `SMOKE_FAULT` unset the clean path is unchanged (smoke green); with
  `SMOKE_FAULT=1` the smoke goes red on the order-total assertion (non-zero exit). Exactly one fault;
  no catalog, no scorer, no generalized injection framework.
- **HOW is the developer's choice** provided the contract holds and the clean default path is
  untouched — acceptable shapes include a guarded fault layer/wrapper the e2e project launches under
  the toggle, or a second Playwright config that targets a faulty variant. Do not modify the clean
  backend/frontend source's default behavior.
- **Documented red command:** provide one command (e.g. a `make` target such as
  `make test-smoke-buggy`, and/or an npm script in `reference_app/e2e/package.json` invoked with
  `SMOKE_FAULT=1`) that runs the same smoke against the faulty variant and is expected to exit
  non-zero, documented in `reference_app/e2e/README.md` as the Phase-0 "red on buggy" demonstration.

## Definition of Done
- All acceptance criteria 1–11 pass.
- The Playwright project, config, smoke spec, and dedicated `package.json` exist under
  `reference_app/e2e/` at the pinned paths; the smoke is green against the clean app and red under
  `SMOKE_FAULT=1`, both reproducible via the documented commands.
- `make test` runs the clean smoke and returns the correct exit code with no manual setup.
- No changes to clean backend/frontend source behavior; no bug catalog / scorer / injection framework
  (those remain for unit 6). No files added to or modified in the root `tests/` bash suites or the
  frontend Vitest suites.
- The Tester can author `reference_app/e2e/tests/smoke.spec.ts` (red first) purely from the pinned
  selectors, paths, ports, launch commands, and the `SMOKE_FAULT` contract above.

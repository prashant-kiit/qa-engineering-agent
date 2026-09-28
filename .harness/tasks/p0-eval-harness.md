# Task: `p0-eval-harness` — `eval/` injected-bug harness, scorer, baseline suite + exit-gate wiring

## Title
The **reliability measurement harness** for the reference shop: a non-invasive **≥3-bug injection
catalog**, a **scorer** (`eval/score.py`) that computes **bug-catch rate / false-positive rate /
flake / assertion-meaningfulness** by running a **baseline hand-written suite** against the clean app
vs each buggy variant, and the `make eval` (+ clean-app `make dev`) wiring that makes the **Phase 0
exit gate** pass — all with the clean reference app left pristine.

## Context (plan item)
- **AGILE_PLAN.md → Phase 0 → B4** ("`eval/` injected-bug harness — the reliability gate") and the
  **Phase 0 exit gate** (`make dev` runs API+UI; `/openapi.json` + seed + `BRD.md` present; `make
  test` green-on-clean; `make eval` injects ≥3 bugs and prints catch / false-positive / flake /
  assertion metrics).
- **Backlog unit 6** (`p0-eval-harness`), deps: `p0-playwright-smoke` (**done**) and
  `p0-shop-backend` (**done**) — both met.
- **DESIGN.md §5 / §9:** "the reliability layer is the product"; the `eval/` injected-bug harness is
  the agent's own regression suite that scores flake rate, assertion meaningfulness, bug-catch rate,
  and false-positive rate against the reference app. **DESIGN.md §13:** `eval/` is the top-level
  home. **DESIGN.md §12:** test artifacts are TypeScript Playwright.
- This is the **last Phase 0 unit**. It measures reliability; **it is NOT the QA agent** (Planner /
  Generator / Verifier / Healer arrive in Phases 1–2). The baseline suite is a **hand-written**
  stand-in that proves the harness runs before any agent exists.

**Given app state (contracts to build on — do NOT re-derive or modify):**
- Clean backend: `reference_app.backend.app:app` (FastAPI + SQLite). Basic Auth
  `testuser`/`testpass`; fixed 5-product seed (stable ids/prices; DB reseeds each fresh process).
  Endpoints `GET /products`, `GET /cart`, `POST /cart/items {product_id, quantity}` (**cumulative**
  add), `POST /checkout`, `GET /orders/{id}`, `GET /openapi.json`. Invariants (from
  `.harness/tasks/p0-shop-backend.md`): order/cart `total = Σ price × quantity`; adding the same
  product again **increments** its quantity; **every** order endpoint requires auth (401 without).
- Non-invasive launcher-overlay pattern (unit 5): `reference_app/e2e/smoke_backend.py` imports the
  clean backend unchanged, adds launch-time `CORSMiddleware` (additive headers only), and — under a
  single env toggle — drops one clean route and re-registers a faulty overlay in its place. The clean
  source (`reference_app/backend/app.py`) is imported verbatim. **Reuse this exact pattern.**
- Playwright project (unit 5) at `reference_app/e2e/`: dedicated `package.json`
  (`@playwright/test`), `tsconfig.json`, `playwright.config.ts` with `webServer` launching the
  backend + Vite frontend, Chromium project, ports **backend 8000 / frontend 5173**, `baseURL`
  `http://127.0.0.1:5173`. Stable `data-testid` DOM contract per `.harness/tasks/p0-shop-frontend.md`
  and `.harness/tasks/p0-playwright-smoke.md`.
- Root `Makefile`: `make test` / `make test-smoke-buggy` / `make e2e-deps` are real; **`make dev` and
  `make eval` are still placeholders** (this unit wires both).

## Scope

### In scope
1. **Bug catalog (≥3 bugs) as a non-invasive launcher overlay under `eval/`.** A backend launcher
   (analogous to `reference_app/e2e/smoke_backend.py`) that imports the clean backend unchanged, adds
   launch-time CORS, and — selected by a **single env variable** — applies **exactly one** fault. It
   ships the three required faults, each producing a **specific, observable wrong behavior**
   (enumerated in Acceptance §Bugs). With the selector at its clean value the launched app behaves
   **identically to the clean backend** (byte-for-byte bodies/status; CORS additive only).
2. **Scorer `eval/score.py`.** A CLI that, using the baseline suite, runs it against the **clean**
   variant and **each buggy** variant with **re-runs**, then computes and prints the **four metrics**
   with the pinned definitions in Acceptance §Metrics, plus an inspectable per-variant / per-test
   breakdown and an assertion-meaningfulness audit. Exits with the pinned semantics.
3. **Baseline hand-written suite.** A small TS-Playwright suite (UI + Playwright API tests) that
   **passes on the clean app** and, as a whole, **catches all three injected bugs** (fails on the
   variant each bug targets). Reuse/extend the unit-5 `reference_app/e2e/` project; it is invokable
   against a chosen variant via the env selector (Acceptance §Baseline). *(This baseline suite is a
   **product deliverable of this unit** — Developer-authored source — distinct from the harness's own
   verification tests that the Tester writes to check this unit's acceptance.)*
4. **`make eval` wiring.** A real root-`Makefile` `eval` target that ensures prerequisites (the e2e
   Node deps + Chromium, as `make test` does), runs `eval/score.py` across the ≥3 bugs + clean, and
   prints the metrics table; propagates the scorer's exit code.
5. **`make dev` wiring (exit-gate fold-in).** Replace the placeholder `dev` target with a real
   launcher that starts the **clean** reference app — backend (`uv run uvicorn
   reference_app.backend.app:app --host 127.0.0.1 --port 8000`) + Vite frontend (`npm run dev`,
   `127.0.0.1:5173`, `VITE_API_BASE_URL=http://127.0.0.1:8000`) — with seeded SQLite, no bug toggle,
   so `/openapi.json` + UI are reachable. (Reuse the unit-5 launch commands.)
6. **Docs:** an `eval/README.md` documenting the bug catalog (each bug's id + observable behavior),
   the env selector + values, how to run the baseline against a variant, and the `eval/score.py`
   CLI + `make eval`.

### Out of scope (defer)
- **The QA agent itself** — Planner / Generator / Verifier / Healer, Playwright MCP, agent-generated
  tests, prompt/sub-agent config (Phases 1–2). This unit ships only the **measurement harness + a
  hand-written baseline**.
- Any **4th+** bug, cross-browser matrices, visual/snapshot testing, CI wiring beyond `make eval` /
  `make dev`, historical trend storage, dashboards, or thresholds beyond the Phase-0 sanity gate.
- **Any change to clean `reference_app/backend/**` or `reference_app/frontend/**` behavior.** The
  clean app must behave exactly as today; every fault is reachable **only** via the `eval/` launcher
  under the selector and must leave the clean (unselected) path unchanged. **No bug toggle may be
  baked into a clean production path.**
- Editing the unit-5 clean smoke's green-on-clean / red-under-`SMOKE_FAULT` behavior, or the
  `reference_app/e2e/smoke_backend.py` overlay. (Adding new eval specs/config to the e2e project is
  fine; the existing smoke + `make test` must stay green.)
- Editing protected files (`DESIGN.md`, `META_PLAN.md`, `AGILE_PLAN.md`, `CLAUDE.md`, `.harness/**`).

## Acceptance criteria (enumerated, testable)

### Bugs — the injected-bug catalog (≥3), each observable and isolated
Let the env selector be **`EVAL_BUG`** with the variant identifiers pinned in Interfaces. The
launched `eval/` backend variant behaves as follows (all other behavior stays clean):

1. **Clean variant (`EVAL_BUG` unset or `none`).** The launched app satisfies **every** clean-backend
   invariant from `.harness/tasks/p0-shop-backend.md`: order/cart `total = Σ price × quantity`;
   adding the same product again **increments** its quantity; `GET /orders/{id}` and `POST /checkout`
   **require auth** (401 without/with-invalid credentials). Response bodies + status codes are
   identical to `reference_app.backend.app:app` (only CORS headers may be added). The baseline suite
   passes against it.
2. **Bug (a) — checkout-total miscalculation (`EVAL_BUG=checkout_total`).** `POST /checkout` returns
   a created order whose **`total` is wrong** — it does **not** equal `Σ price × quantity` for the
   checked-out lines (a deterministic wrong value, never coincidentally equal to the true total).
   Everything else (line items, order id, cart, product prices) stays correct. Observable: the order
   `total` (and the UI order-confirmation `order-total` the frontend renders from it) mismatches the
   true cart total.
3. **Bug (b) — cart quantity not updating (`EVAL_BUG=cart_quantity`).** `POST /cart/items` for a
   product **already in the cart** does **not** accumulate quantity — the reported quantity for that
   product does **not** equal the cumulative amount added (e.g. it stays at the first/last quantity
   instead of summing). Observable: after adding the same product twice (quantity 1 each), `GET /cart`
   reports quantity ≠ 2 for that product and a correspondingly wrong `total`. (The first add of a
   product may still work; the defect is the missing increment on repeat adds.)
4. **Bug (c) — auth-check bypass on an order endpoint (`EVAL_BUG=order_auth_bypass`).**
   `GET /orders/{id}` **no longer enforces authentication** — a request with **missing or invalid**
   Basic credentials returns **HTTP 200** with the order body instead of **401**. Observable: the
   order-retrieval endpoint is reachable without valid credentials (the exact invariant unit 2 flagged
   as a future injected bug).
5. **Faults are isolated + minimal.** Each `EVAL_BUG` value activates **exactly one** of the above
   faults; no value activates a second fault; with `EVAL_BUG` at its clean value **no** fault is
   active (criterion 1). The clean `reference_app/backend/**` and `reference_app/frontend/**` sources
   are unchanged, and the clean app run directly (e.g. via `make dev` / `make test`) shows none of
   these behaviors.

### Baseline — the hand-written suite
6. **Baseline passes on clean.** Run against the clean variant (`EVAL_BUG` unset/`none`), the baseline
   suite passes (process exit 0; zero failing tests). It contains **real, non-vacuous assertions** on
   app-produced values (order total, cart quantity/total, HTTP status), not mere page-presence checks.
7. **Baseline catches every injected bug.** For each buggy variant, running the **same** baseline
   suite against that variant produces **≥1 failing test** (non-zero exit) — the failure is a genuine
   assertion failure on the wrong app behavior (not an infra/timeout/missing-server error):
   - `checkout_total` → the order-total assertion fails;
   - `cart_quantity` → the cart-quantity/total assertion fails;
   - `order_auth_bypass` → the order-endpoint-auth assertion fails (an API-level test, since the UI
     always sends credentials).
8. **Baseline is variant-selectable + documented.** Running the baseline against a given variant is a
   single documented command driven by `EVAL_BUG` (Interfaces §Baseline invocation); with `EVAL_BUG`
   unset/`none` it targets clean. Documented in `eval/README.md`.

### Metrics — `eval/score.py` computes and prints the four metrics (pinned definitions)
Let the scorer run the baseline `R` times (re-runs, `R ≥ 2`, default in Interfaces) against the clean
variant and each of the 3 buggy variants, recording per-run, per-test pass/fail. Define:
- A test **fails on a variant** in a run if that test reports failed in that run.
- A buggy variant is **caught** if, in its scoring run, ≥1 baseline test fails.

9. **Bug-catch rate.** `bug_catch_rate = (# buggy variants caught) / (total # buggy variants)`.
   With the three bugs + a correct baseline this is **1.0**. Printed as a fraction/percentage.
10. **False-positive rate.** Over the clean variant's runs,
    `false_positive_rate = (# baseline tests that fail on the clean variant) / (# baseline tests run
    on clean)` (aggregated across the clean runs — any clean failure counts). A correct baseline on
    the clean app yields **0.0**.
11. **Flake (re-run consistency).** For each (variant, test) pair, run `R` times; the pair is **flaky**
    if its pass/fail verdict is **not identical** across all `R` runs.
    `flake_rate = (# flaky (variant,test) pairs) / (total (variant,test) pairs evaluated)`. A
    deterministic harness yields **0.0**.
12. **Assertion-meaningfulness audit.** A baseline test is **meaningful (discriminating)** if it
    **passes on the clean variant AND fails on ≥1 buggy variant** (its assertions actually detect a
    defect — it is not vacuous/non-discriminating).
    `assertion_meaningfulness_rate = (# meaningful tests) / (# baseline tests)`. The audit **lists**
    any non-meaningful test (passes on clean and on every buggy variant) so a human can inspect. This
    rate is **reported** (a test such as a generic login/happy-path check may legitimately be
    non-discriminating); it is not part of the hard exit gate (criterion 15).
13. **Metrics are printed in an inspectable form.** `eval/score.py` **always** prints a
    human-readable **metrics table** to stdout containing the four metrics (by their pinned names) +
    a per-variant caught/not-caught line + the assertion-meaningfulness audit list. With `--json` it
    **also** emits machine-readable JSON whose `metrics` object carries the keys `bug_catch_rate`,
    `false_positive_rate`, `flake_rate`, `assertion_meaningfulness_rate` (numeric 0..1) plus a
    per-variant / per-test breakdown.

### `make eval` + `make dev` (exit-gate wiring)
14. **`make eval` runs end-to-end.** From the repo root, `make eval`: (a) idempotently ensures the
    e2e Node deps + Chromium are present (as `make test` does; no-op when present); (b) runs
    `eval/score.py` across the ≥3 buggy variants + clean; (c) prints the metrics table (criterion 13).
    No manual server start or DB seeding is required (the harness launches each variant itself).
15. **`make eval` exits sensibly (Phase-0 sanity gate).** `eval/score.py` (and hence `make eval`)
    exits **0** iff the harness ran to completion **and** `bug_catch_rate == 1.0` **and**
    `false_positive_rate == 0.0` **and** `flake_rate == 0.0`; otherwise it exits **non-zero** (the
    harness failed to run, or a bug went uncaught, or the clean app produced a false positive, or
    flake was detected). Metrics are printed **before** exiting, in both cases.
16. **`make dev` runs the clean app.** From the repo root, `make dev` launches the clean reference
    backend + Vite frontend (seeded SQLite, no bug toggle) so `GET /openapi.json` is served on the
    backend and the UI is reachable on the frontend origin. It uses the launch commands / ports from
    Interfaces and does not enable any `EVAL_BUG`/`SMOKE_FAULT` fault.

### No regressions / isolation
17. **Clean app + prior suites stay green.** The clean backend and frontend behave exactly as before;
    `make test` (unit-5 smoke) is still green on clean and `make test-smoke-buggy` still red under
    `SMOKE_FAULT=1`. No `EVAL_BUG` toggle is baked into any clean production path
    (`reference_app/backend/**`, `reference_app/frontend/**`). Any pre-existing Python/Node test
    suites still pass. New harness files live under `eval/` (plus new eval specs/config in
    `reference_app/e2e/` if the baseline reuses that project, and the root `Makefile`
    `eval`/`dev` targets, and root `.gitignore` if new artifacts appear).
18. **Exit gate satisfied on landing.** With this unit merged, all three Phase-0 exit-gate bullets
    hold: `make dev` runs API+UI with `/openapi.json` + seed + `BRD.md` present; `make test` green on
    clean; `make eval` injects ≥3 bugs and prints the four metrics.

## Interfaces / contracts (pin these precisely)

### Paths
- **Scorer (binding):** `eval/score.py` — run from the repo root.
- **Bug-catalog launcher (pinned home + pattern):** under `eval/` (e.g. `eval/buggy_backend.py`),
  exposing an ASGI `app` object and modelled on `reference_app/e2e/smoke_backend.py`: it imports the
  clean backend (`from reference_app.backend import app as backend`) unchanged, reuses
  `backend.app`, adds launch-time `CORSMiddleware` (additive only), and applies the fault selected by
  `EVAL_BUG` by dropping the relevant clean route and re-registering a faulty overlay (as
  `smoke_backend.py` does for `/checkout`). The clean backend source is **not** modified.
- **Baseline suite:** authored in TypeScript Playwright, reusing the `reference_app/e2e/` project
  (its `package.json` / `tsconfig.json`). New eval specs under `reference_app/e2e/tests/` (e.g. an
  `eval/` subfolder) and, if needed, a dedicated Playwright config (e.g.
  `reference_app/e2e/playwright.eval.config.ts`) whose `webServer` launches the `eval/` bug-catalog
  launcher honoring `EVAL_BUG`. The existing `playwright.config.ts` / `smoke.spec.ts` /
  `smoke_backend.py` and `make test` must be left working.
- **Docs:** `eval/README.md`.

### Env selector (binding)
- **`EVAL_BUG`** selects the launched variant. Accepted values (exact strings):
  - unset or **`none`** → **clean** (no fault).
  - **`checkout_total`** → bug (a), checkout-total miscalculation.
  - **`cart_quantity`** → bug (b), cart quantity not updating.
  - **`order_auth_bypass`** → bug (c), auth-check bypass on `GET /orders/{id}`.
  Exactly one fault per value; unknown values may be rejected or treated as clean (developer's choice,
  document it). This is separate from unit-5's `SMOKE_FAULT`; do not overload `SMOKE_FAULT`.

### Bug-catalog launch (reuse the unit-5 command shape)
- Launch the variant like the unit-5 backend, pointing uvicorn at the `eval/` launcher, e.g.
  `uv run uvicorn buggy_backend:app --app-dir eval --host 127.0.0.1 --port 8000`, with `EVAL_BUG`
  passed through in the environment; readiness at `http://127.0.0.1:8000/openapi.json`. Ports:
  backend **8000**, frontend **5173** (same as unit 5). Variants are launched **one at a time**
  (the scorer runs variants sequentially) to avoid port clashes; a fresh backend process per variant
  reseeds the DB.

### Baseline invocation (per variant)
- The baseline suite runs against the variant named by the `EVAL_BUG` environment variable; unset/
  `none` = clean. There is **one documented command** to run it against a given variant (a Playwright
  invocation on the eval config, e.g. `EVAL_BUG=cart_quantity npx playwright test --config
  playwright.eval.config.ts` from `reference_app/e2e/`, exact form the developer's choice) documented
  in `eval/README.md`. `eval/score.py` uses this mechanism to run each variant.
- The baseline includes **UI tests** (driving the frontend for the happy path + cart quantity) and
  **Playwright API tests** (`request` fixture, for the order-endpoint auth check) — DESIGN §12's
  "TS Playwright + API tests".

### `eval/score.py` CLI + output
- **Invocation:** `uv run python eval/score.py` (from repo root). Options (at minimum):
  - `--reruns N` — re-runs per variant for flake (integer, **default `2`**, `N ≥ 2`).
  - `--json` — additionally emit the machine-readable JSON (criterion 13) to stdout.
  - (The developer may add more, e.g. `--variant`/`--out`; document them.)
- **stdout (always):** a human-readable metrics table with the four metrics under their pinned names
  (`bug_catch_rate`, `false_positive_rate`, `flake_rate`, `assertion_meaningfulness_rate`), a
  per-variant caught/not-caught summary, and the meaningfulness audit list.
- **JSON (`--json`):** an object whose `metrics` field carries the four numeric keys (0..1) plus a
  per-variant / per-test breakdown; field names beyond `metrics.*` are the developer's choice but
  documented.
- **Exit code:** per criterion 15 — `0` iff harness completed and `bug_catch_rate == 1.0 &&
  false_positive_rate == 0.0 && flake_rate == 0.0`, else non-zero; metrics printed before exit.

### `make eval` behavior (root `Makefile`)
- Replace the placeholder `eval` target so it: (1) idempotently ensures the `reference_app/e2e` Node
  deps + Chromium (reuse the existing `e2e-deps` prerequisite); (2) runs `uv run python eval/score.py`
  across the ≥3 buggy variants + clean; (3) prints the metrics table; (4) propagates the scorer's
  exit code (criterion 15).

### `make dev` behavior (root `Makefile`)
- Replace the placeholder `dev` target so it starts the **clean** app: backend `uv run uvicorn
  reference_app.backend.app:app --host 127.0.0.1 --port 8000` + frontend `npm run dev` (from
  `reference_app/frontend/`, `127.0.0.1:5173`, `VITE_API_BASE_URL=http://127.0.0.1:8000`), seeded
  SQLite, no fault toggle. Document how it runs both (foreground/background) in `eval/README.md` or
  the `Makefile` `help`. No `EVAL_BUG`/`SMOKE_FAULT` set.

### Determinism / seed (targets, not to re-implement)
- Credentials `testuser`/`testpass`; fixed 5-product seed with stable prices; the backend reseeds on
  each fresh process, so per-variant runs are deterministic and the four metrics are reproducible
  (`flake_rate == 0.0` expected).

## Definition of Done
- All acceptance criteria **1–18** pass.
- `eval/score.py`, the `eval/` bug-catalog launcher (with the three faults selected by `EVAL_BUG`),
  the baseline TS-Playwright suite (UI + API), and `eval/README.md` exist at the pinned paths; the
  clean reference app is unchanged.
- `make eval` runs end-to-end from a clean checkout (deps auto-installed), prints the four metrics,
  and exits per the pinned sanity gate; `make dev` launches the clean API + UI.
- The three Phase-0 exit-gate bullets all hold; `make test` stays green on clean and
  `make test-smoke-buggy` stays red under `SMOKE_FAULT=1`; no clean production path carries an
  `EVAL_BUG` toggle.
- No protected file changed (`DESIGN.md`, `META_PLAN.md`, `AGILE_PLAN.md`, `CLAUDE.md`,
  `.harness/**`). Consistent with `DESIGN.md §5/§9/§12/§13` and `AGILE_PLAN.md` B4 + the exit gate.
- The Tester can, from this spec alone (paths, `EVAL_BUG` values + observable behaviors, the scorer
  CLI/output/exit contract, the baseline invocation, and the `make eval`/`make dev` contracts),
  author the failing verification tests without reading the implementation.

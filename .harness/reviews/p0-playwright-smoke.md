# Review — `p0-playwright-smoke`

**Verdict: APPROVE**

Independent review of the diff vs. spec (`.harness/tasks/p0-playwright-smoke.md`), the Tester-owned
coverage note, and a self-run of every suite. All four axes pass.

## 1. Acceptance — all criteria met
- **C1 (project + config valid):** `reference_app/e2e/playwright.config.ts` present, `testDir: './tests'`
  resolves to `reference_app/e2e/tests`; Playwright discovers exactly one spec. Chromium project, headless.
- **C2/C3 (single smoke, full UI flow):** `tests/smoke.spec.ts` — one test drives goto(baseURL) → login
  (`testuser`/`testpass`, asserts product list visible + no `login-error`) → `add-to-cart` (cart-count → 1)
  → nav "Cart" (≥1 `cart-line`, positive `cart-total`) → `cart-checkout` → `checkout-submit`.
- **C4 (meaningful order-confirmation assertions):** "Order confirmed" heading visible, `order-id`
  non-empty, and the load-bearing `expect(orderTotal).toBeCloseTo(cartTotal, 2)` comparing the confirmation
  order-total to the pre-checkout cart-total (line 88). Real assertions on app-produced values.
- **C5 (green on clean):** confirmed — `npx playwright test` → `1 passed`, CLEAN_EXIT=0.
- **C6 (red on faulty, at the order-total assertion):** confirmed — `SMOKE_FAULT=1 npx playwright test`
  fails at `smoke.spec.ts:88` `toBeCloseTo`, Expected 9.99 / Received 109.99, FAULT_EXIT=1. Genuine
  assertion failure on wrong app output, not infra/timeout.
- **C7 (toggle minimal + isolated):** exactly one fault (checkout response total + 100.0 offset) via the
  single `SMOKE_FAULT` env toggle; clean default path untouched.
- **C8 (`make test`):** confirmed — `make test` from repo root idempotently installs deps+browser
  (`e2e-deps`), runs the clean smoke via the config `webServer`, `1 passed`, MAKE_TEST_EXIT=0.
- **C9 (one-command reproducibility):** `webServer` launches backend + Vite; no manual server/DB step.
- **C10 (documented red command):** `make test-smoke-buggy` / `npm run test:smoke-buggy`, documented in
  `reference_app/e2e/README.md` as the "red on buggy" demo (non-zero exit = success).
- **C11 (no collision):** new files live only under `reference_app/e2e/` (+ root `Makefile`); tracked set
  is clean (node_modules/test-results/__pycache__ gitignored).
- **Deferral honored:** no bug catalog, no scorer, no injection framework — `make eval` still a
  placeholder naming unit 6. Correctly DEFERRED.

## 2. Test integrity — un-gamed
- The load-bearing assertion compares two independently-sourced UI values (pre-checkout cart-total vs.
  confirmation order-total); it is meaningful, not a presence check.
- The fault genuinely alters app output: `smoke_backend.py` drops the clean `POST /checkout` route and
  serves a `buggy_checkout` that runs the real checkout then returns `total + 100.0`. The test itself is
  toggle-agnostic and unchanged between clean/buggy runs — the red comes from real wrong output, not a
  faked failure.
- Tester-owned locator fix (`exact: true` on the "Cart" nav button) is a legitimate strict-mode
  disambiguation; the load-bearing 4c assertion is untouched.

## 3. Scope — confined to unit 5
- Fault mechanism lives in a separate launcher overlay (`smoke_backend.py`) that imports the clean
  backend unchanged; no permanent bug toggle baked into the clean production path. Verified: no
  changes to `reference_app/backend/` or `reference_app/frontend/` source.
- CORS middleware added only in the launcher (additive headers for the browser cross-origin call),
  not in the clean backend.
- Prior-suite adjustments (Tester-owned) verified **gated, not gutted**:
  - Scaffold C6 reworked into C6a (dev/eval/release placeholders still exit 0 + name their unit) and
    C6b (asserts `make test` is wired to the e2e Playwright smoke via `make -n`, without executing it —
    correct, since unit 5 makes `make test` a real heavy run). Always-run checks remain meaningful.
  - BRD C19/C20 and scaffold C10/C11 gated behind opt-in `BRD_DIFF_GUARD=1` / `SCAFFOLD_DIFF_GUARD=1`.
    Spot-checked: under the flags the guards fully execute their hash-compares (C19 still PASSES;
    C10/C11/C20 FAIL only on the TPM's legitimate non-reentrant plan-lock edits to `AGILE_PLAN.md`/
    `.harness/**` — exactly the documented reason for retiring them from the always-run suite). The
    guard logic is intact, confirming gated-not-gutted.

## 4. Quality
- Config correct: `reuseExistingServer: !FAULTY` ensures a fresh backend serves the faulty variant
  (no stale-server contamination); `SMOKE_FAULT` threaded to the backend process env; strictPort Vite.
- Launcher correctly reinserts repo root on `sys.path` so the clean backend package resolves under
  uvicorn `--app-dir`. Non-zero fault offset guarantees the wrong total can never accidentally equal
  truth. No dead code.

## Test runs (self-executed, isolated with teardown between variants)
```
Clean:   npx playwright test                 → 1 passed (2.3s)   CLEAN_EXIT=0
Buggy:   SMOKE_FAULT=1 npx playwright test    → 1 failed at smoke.spec.ts:88
                                                 toBeCloseTo Expected 9.99 / Received 109.99  FAULT_EXIT=1
make test (repo root)                          → 1 passed         MAKE_TEST_EXIT=0
uv run pytest reference_app/backend/tests -q   → 26 passed
npm --prefix reference_app/frontend test       → 17 passed (6 files)
bash tests/scaffold/p0-scaffold.test.sh        → all acceptance checks passed (C10/C11 SKIP)
bash tests/docs/design-note.test.sh            → all acceptance checks passed
bash tests/docs/brd-release.test.sh            → all acceptance checks passed (C19/C20 SKIP)
SCAFFOLD_DIFF_GUARD=1 …/p0-scaffold.test.sh    → guards execute (C10/C11 fail on plan-lock edits) exit 1
BRD_DIFF_GUARD=1 …/brd-release.test.sh         → guards execute (C19 PASS, C20 fail on plan-lock) exit 1
```
All default-invocation suites green; the two gated guards run fully under their opt-in flags.

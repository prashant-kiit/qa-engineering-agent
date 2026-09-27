# Test coverage — `p0-playwright-smoke`

TDD **red** artifacts authored by the Tester. Per project convention the E2E artifact is
**TypeScript Playwright**. Only the test toolchain + smoke spec are authored here; the
`playwright.config.ts` (baseURL/webServer wiring), the `SMOKE_FAULT` fault mechanism, and the
`make test` wiring are the **Developer's** to create (see the spec's Interfaces).

## Files created by the Tester
- `reference_app/e2e/package.json` — dedicated Node project declaring `@playwright/test`
  (kept separate from the frontend Vitest toolchain). Scripts:
  - `test` → `playwright test` (clean run, once config exists).
  - `test:smoke-buggy` → `SMOKE_FAULT=1 playwright test` (the "red on buggy" demonstration command).
  - `install:browser` → `playwright install chromium`.
- `reference_app/e2e/tsconfig.json` — TS config for the e2e project.
- `reference_app/e2e/tests/smoke.spec.ts` — the single smoke test (login → add-to-cart → view cart
  → checkout → order confirmation), with the load-bearing assertion
  `order-total == cart-total (pre-checkout)`.

Toolchain installed: `npm install` in `reference_app/e2e/` (added `@playwright/test`), and
`npx playwright install chromium` (Chromium binary present in the Playwright cache).

## NOT authored here (Developer's, per spec Interfaces)
- `reference_app/e2e/playwright.config.ts` (baseURL = frontend origin `http://127.0.0.1:5173`,
  `webServer` starting backend `uvicorn reference_app.backend.app:app` + frontend `npm run dev`,
  `reuseExistingServer`, Chromium project).
- The `SMOKE_FAULT` fault mechanism (guarded faulty variant surfacing a wrong order total).
- The root `Makefile` `test` target and any `make test-smoke-buggy` target.

## Acceptance criterion → test / verification

| # | Criterion | Covered by | How verified |
|---|-----------|------------|--------------|
| 1 | Project + config present and valid; `testDir` = `tests` | `package.json`, `tsconfig.json` (Tester) + `playwright.config.ts` (Developer) | Once the Developer adds the config, `npx playwright test --list` resolves the config and discovers the spec. Already: `--list` discovers `tests/smoke.spec.ts` (TS compiles). |
| 2 | Smoke spec exists at pinned path, exactly one test | `tests/smoke.spec.ts` | `npx playwright test --list` → `Total: 1 test in 1 file`. |
| 3a | Loads app at `baseURL` | `smoke.spec.ts` `login()` → `page.goto('/')` | Navigates relative to baseURL (wired by Developer config). |
| 3b | Login with `testuser`/`testpass`, reaches shop, no `login-error` | `smoke.spec.ts` `login()` | Fills `login-username`/`login-password`, clicks `login-submit`; asserts `product-item` visible and `login-error` count 0. |
| 3c | Add to cart; `cart-count` becomes 1 | `smoke.spec.ts` | Clicks `add-to-cart`; asserts `cart-count` text matches `\b1\b`. |
| 3d | Navigate to Cart; ≥1 `cart-line`; `cart-total` positive | `smoke.spec.ts` | Clicks the nav "Cart" button via `getByRole('button', { name: 'Cart', exact: true })` (see locator fix below); asserts `cart-line` visible, count ≥ 1; parses `cart-total` > 0. |
| 3e | Proceed to checkout + place order | `smoke.spec.ts` | Clicks `cart-checkout` then `checkout-submit`. |
| 4a | "Order confirmed" heading visible | `smoke.spec.ts` | `getByRole('heading', { name: 'Order confirmed' })` visible; `checkout-error` count 0. |
| 4b | `order-id` present + non-empty | `smoke.spec.ts` | Asserts `order-id` visible and trimmed text length > 0. |
| 4c | `order-total` positive AND equals pre-checkout `cart-total` (load-bearing) | `smoke.spec.ts` | Parses `order-total` > 0 and `toBeCloseTo(cartTotal, 2)`. This is the invariant `total = Σ price × quantity`. |
| 5 | Green on clean | `smoke.spec.ts` | Same spec passes with exit 0 once Developer wires config + `webServer` against the clean app (`SMOKE_FAULT` unset). |
| 6 | Red on faulty variant (order-total assertion fails, non-zero exit) | `smoke.spec.ts` 4c + `test:smoke-buggy` script | With `SMOKE_FAULT=1`, the app surfaces a wrong order total → 4c equality assertion fails as a genuine assertion failure → non-zero exit. |
| 7 | Toggle minimal + isolated | Developer (fault mechanism) | Tester's single spec is toggle-agnostic: same spec is green unset, red when set — no bug catalog/scorer in the test. |
| 8 | `make test` runs clean smoke, correct exit code | Developer (`Makefile`) | Runs `playwright test` (this spec) via config `webServer`; propagates exit code. |
| 9 | One-command reproducibility | Developer (config `webServer`) | No manual server start needed once `webServer` is wired; spec uses only `baseURL`-relative nav. |
| 10 | Red demonstration via single documented command | `test:smoke-buggy` npm script (Tester) + `make test-smoke-buggy` (Developer) | `npm run test:smoke-buggy` (= `SMOKE_FAULT=1 playwright test`) runs the same spec against the faulty variant; expected non-zero exit. |
| 11 | No collision with existing suites | file placement | All new files under `reference_app/e2e/` only; no edits to root `tests/` bash suites or `reference_app/frontend/src/__tests__` Vitest suites. |

## Red run output (legitimate red)

Toolchain sanity — TS compiles and exactly one test is discovered:

```
$ npx playwright test --list
Listing tests:
  tests/smoke.spec.ts:49:5 › smoke: login -> add to cart -> checkout, order total equals cart total
Total: 1 test in 1 file
```

Red run (no `playwright.config.ts`, so no `baseURL`/`webServer`; app not launched):

```
$ npx playwright test
Running 1 test using 1 worker

  ✘  1 tests/smoke.spec.ts:49:5 › smoke: login -> add to cart -> checkout, order total equals cart total (69ms)

  1) tests/smoke.spec.ts:49:5 › smoke: login -> add to cart -> checkout, order total equals cart total

    Error: page.goto: Protocol error (Page.navigate): Cannot navigate to invalid URL
    Call log:
      - navigating to "/", waiting until "load"

      37 |
      38 | async function login(page: Page): Promise<void> {
    > 39 |   await page.goto('/');
         |              ^
      40 |   await page.getByTestId('login-username').fill(USERNAME);
      41 |   await page.getByTestId('login-password').fill(PASSWORD);
      42 |   await page.getByTestId('login-submit').click();
        at login (.../reference_app/e2e/tests/smoke.spec.ts:39:14)
        at .../reference_app/e2e/tests/smoke.spec.ts:51:9

  1 failed
    tests/smoke.spec.ts:49:5 › smoke: login -> add to cart -> checkout, order total equals cart total

$ echo "PLAYWRIGHT_EXIT=$?"
PLAYWRIGHT_EXIT=1
```

### Why this is a legitimate red (right reason)
- The browser launched and the test **ran** (69ms); the spec is **syntactically sound** — Playwright
  transpiled the TS and discovered exactly one test (`--list` above). The failure is **not** a
  compile/syntax/import error.
- It fails at `page.goto('/')` with "Cannot navigate to invalid URL" precisely because there is **no
  `playwright.config.ts`** wiring a `baseURL` and **no `webServer`** launching the app — i.e. the
  project is not yet wired and the app is not reachable. This is the missing-behavior red the
  Developer will turn green by adding the config + `webServer` against the clean app (criterion 5).
- Non-zero process exit (`PLAYWRIGHT_EXIT=1`) satisfies the "fails non-zero" expectation.

### How green-on-clean and red-on-`SMOKE_FAULT` will be demonstrated (post-Developer)
- **Green on clean:** with the Developer's `playwright.config.ts` (baseURL `http://127.0.0.1:5173`,
  `webServer` starting backend + frontend) and `SMOKE_FAULT` unset, `npx playwright test` /
  `make test` runs this exact spec end-to-end and exits 0 (all assertions incl. 4c pass).
- **Red on buggy:** `npm run test:smoke-buggy` (`SMOKE_FAULT=1 playwright test`) / `make
  test-smoke-buggy` runs the **same** spec against the faulty variant; the wrong order total makes
  assertion **4c** (`order-total` == pre-checkout `cart-total`) fail as a genuine assertion failure,
  exiting non-zero.

## Locator fix (cart-nav disambiguation) — post-Developer, test-only

The step 3d cart navigation originally used `page.getByRole('button', { name: 'Cart' })`. Playwright's
`getByRole` `name` match defaults to **case-insensitive substring**, so `'Cart'` matched the nav
**"Cart"** button AND all five **"Add to cart"** product buttons → a strict-mode violation
("resolved to 6 elements") that failed the smoke before it could reach the load-bearing assertion.

**Fix (test-only, in `smoke.spec.ts`):** added `exact: true` →
`page.getByRole('button', { name: 'Cart', exact: true })`, which targets ONLY the button whose
accessible name is exactly "Cart" (the nav button); the product buttons are named "Add to cart" and no
longer match. Nothing else changed — the load-bearing 4c assertion
(`order-total ≈ pre-checkout cart-total`, `toBeCloseTo(cartTotal, 2)`) is untouched. The spec still
transpiles and discovers exactly one test (`npx playwright test --list` → `Total: 1 test in 1 file`).

## Confirmed green-on-clean / red-on-`SMOKE_FAULT` (Developer wiring now in place)

With the Developer's `playwright.config.ts` (`baseURL` `http://127.0.0.1:5173`, `webServer` starting
backend + frontend) present, the smoke now runs end-to-end. Both outcomes were confirmed after the
locator fix:

- **Green on clean** — `cd reference_app/e2e && npx playwright test` (exit 0, stable across repeated runs):
```
  ✓  1 [chromium] › tests/smoke.spec.ts:49:5 › smoke: login -> add to cart -> checkout, order total equals cart total (579ms)

  1 passed (2.3s)
CLEAN_SMOKE_EXIT=0
```

- **Red on buggy** — `cd reference_app/e2e && SMOKE_FAULT=1 npx playwright test` (exit 1). The failure
  is a genuine assertion failure on the wrong app-produced order total (not an infra/timeout error),
  at the load-bearing 4c assertion (`smoke.spec.ts:88`):
```
    Error: expect(received).toBeCloseTo(expected, precision)
    Expected: 9.99
    Received: 109.99
    Expected precision:    2
    Expected difference: < 0.005
    Received difference:   100
      86 |   const orderTotal = parseMoney(await page.getByTestId('order-total').textContent());
      87 |   expect(orderTotal).toBeGreaterThan(0);
    > 88 |   expect(orderTotal).toBeCloseTo(cartTotal, 2);
  1 failed
FAULT_EXIT=1
```
The Playwright `webServer` auto-starts the backend (`uvicorn`) + frontend (`vite`) for both runs; no
manual server start is required.

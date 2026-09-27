# Review: p0-shop-frontend

**Verdict: APPROVE**

Independent review of the reference-shop frontend (React + Vite) against the spec
(`.harness/tasks/p0-shop-frontend.md`), the Tester's binding contract
(`.harness/tasks/p0-shop-frontend.tests.md`), and the working-tree diff.

## 1. Acceptance — all 17 criteria met
- **Build & health (1–2):** `build` = `tsc --noEmit && vite build` exits 0 and emits a bundle;
  `test` = `vitest run` runs the suite non-interactively with non-zero-on-failure. Both verified below.
- **Login (3–5):** `LoginView` renders `login-username`/`login-password`/`login-submit`; on submit it
  issues an authenticated `GET /cart` carrying `Authorization: Basic base64(user:pass)` derived from the
  entered creds and calls `onLogin(creds)` on success; on stubbed 401 it renders `login-error` and does
  not call `onLogin`. Credentials are captured from the form, never hard-coded (`LoginView.tsx:24-34`).
- **Product list (6–9):** `ProductListView` fetches `GET /products` with Basic auth, renders one
  `product-item` per product with name + price, each with an `add-to-cart` control that POSTs
  `/cart/items { product_id, quantity: 1 }` with Basic auth, and reflects the add via `cart-count`.
- **Cart (10–12):** `CartView` fetches `GET /cart`, renders `cart-line` per item + `cart-total`
  (exact `39.48` from stub), a distinct `cart-empty` state with no phantom lines, and a `cart-checkout`
  control.
- **Checkout → confirmation (13–15):** `CheckoutView` POSTs `/checkout` with Basic auth; on success
  renders `OrderConfirmationView` showing `order-id` (4242) + `order-total` (39.48); on stubbed 400 it
  shows `checkout-error` and renders no `order-id` (no fabricated order).
- **Wiring/config (16–17):** `src/config.ts` exports `API_BASE_URL` resolved from `VITE_API_BASE_URL`,
  defaulting to `http://127.0.0.1:8000`. All five views are barrel-exported from `src/views` and mount
  in isolation with stubbed `fetch`. README documents install/dev/build/test, the config var + default,
  and the per-view export points/props.

## 2. Test integrity — meaningful and un-gamed
- 17 tests across 6 files match the Tester's contract in `p0-shop-frontend.tests.md` exactly (import
  surface `src/views` + `src/config`, props, and every `data-testid`).
- Assertions are behavioral and pinned: exact totals (`39.48`), exact order id (`4242`), literal
  `Authorization: Basic` header equality, request-body `product_id`/`quantity>=1`, empty-cart with zero
  phantom lines, and the negative "no fabricated order on 400" check. Not gameable by trivial stubs.
- Toolchain/config owned by the Tester (`package.json` scripts/deps, `vitest.config.ts`, `tsconfig.json`,
  `src/test/setup.ts`, `src/test/helpers.ts`) is consistent with the tests.md manifest; the developer
  implemented only source under `src/` (config.ts, api.ts, views/*, App.tsx, main.tsx) plus `index.html`,
  `vite-env.d.ts`, and `README.md`. No test file was weakened or modified.

## 3. Scope — clean, no creep
- Frontend-only. No changes under `reference_app/backend/**` (git status confirms only
  `reference_app/frontend/**` untracked). No BRD/release docs, no Playwright project, no bug-injection
  toggles. No protected-file edits by the developer.
- `AGILE_PLAN.md` and `.harness/backlog.md` edits are TPM plan-lock artifacts (status flips 2→done,
  3→active/spec-ready, plan re-confirmation), part of the cycle's plan-lock step — not developer source.

## 4. Quality
- Simple, idiomatic React; views own their own fetches; `App.tsx` only holds captured creds + current
  screen. Basic Auth handled reasonably for a reference app (per `DESIGN.md §12`) — creds flow from the
  login form, never hard-coded (spec + `DESIGN.md §11` respected). Loading/empty/error states present.
  No dead code (`CartView.onCheckout` is optional and wired by `App.tsx`).

## Test runs (all green)
```
# npm --prefix reference_app/frontend test
 Test Files  6 passed (6)
      Tests  17 passed (17)

# npm --prefix reference_app/frontend run build
 ✓ built in 249ms   (BUILD_EXIT=0)

# uv run pytest reference_app/backend/tests -q
 26 passed, 1 warning in 0.25s

# bash tests/scaffold/p0-scaffold.test.sh
 RESULT: all acceptance checks passed

# bash tests/docs/design-note.test.sh
 RESULT: all acceptance checks passed
```

Prior units stay green; the new suite and build pass. Approved.

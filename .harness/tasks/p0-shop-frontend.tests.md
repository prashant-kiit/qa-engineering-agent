# Tests: p0-shop-frontend (TDD red)

Component/integration suite for the reference-shop **frontend** (React + Vite). All backend HTTP
calls are **stubbed** via a mocked global `fetch` — no live backend, no Playwright (E2E smoke is
unit 5). Toolchain: **Vitest + @testing-library/react + jsdom** (Tester-owned setup).

## Toolchain / files created (Tester-owned)
- `reference_app/frontend/package.json` — deps + binding scripts `dev`, `build` (`tsc --noEmit && vite build`), `test` (`vitest run`).
- `reference_app/frontend/vitest.config.ts` — jsdom environment, React plugin, setup file, globals.
- `reference_app/frontend/tsconfig.json` — TS/JSX config used by `build`.
- `reference_app/frontend/src/test/setup.ts` — jest-dom matchers + per-test cleanup/unstub.
- `reference_app/frontend/src/test/helpers.ts` — fetch-stub router, Basic-auth header builder, header/body extractors.
- Test files under `reference_app/frontend/src/__tests__/`: `toolchain.test.ts`, `config.test.ts`,
  `login.test.tsx`, `productList.test.tsx`, `cart.test.tsx`, `checkout.test.tsx`.

## Binding contract the Developer must implement to (Tester-defined; HOW-neutral, tests target it)
Exact component/file names were left to the Developer by the spec, but tests must call a concrete
surface. The following import surface, props, and DOM `data-testid`s are the target the tests drive:

- **Barrel export** `src/views` (i.e. `src/views/index.ts`) re-exporting the five views:
  `LoginView`, `ProductListView`, `CartView`, `CheckoutView`, `OrderConfirmationView`.
- **Config** `src/config.ts` → `export const API_BASE_URL: string` resolved from `VITE_API_BASE_URL`,
  defaulting to `http://127.0.0.1:8000`.
- **HTTP layer:** views use the global `fetch` API (so tests can stub it) and send HTTP **Basic**
  `Authorization` headers derived from the login credentials.
- **Props:**
  - `LoginView { onLogin(creds) }`
  - `ProductListView { credentials }`
  - `CartView { credentials }`
  - `CheckoutView { credentials }`
  - `OrderConfirmationView { order: { id, total, items } }`
- **DOM testids:** `login-username`, `login-password`, `login-submit`, `login-error`;
  `product-item` (per product, contains name+price), `add-to-cart` (within each), `cart-count`;
  `cart-line` (per line), `cart-total`, `cart-empty`, `cart-checkout`;
  `checkout-submit`, `checkout-error`, `order-id`, `order-total`.

## Acceptance criterion → covering test(s)

| # | Criterion | Test(s) |
|---|---|---|
| 1 | `build` script exists & compiles a bundle | `package.json` `build` = `tsc --noEmit && vite build` (Developer makes it pass; not run red at test time) |
| 2 | `test` script runs the suite, non-zero on failure | `toolchain.test.ts` (proves Vitest+jsdom collect/execute); the red run below shows non-zero exit |
| 3 | Login renders username/password/submit | `login.test.tsx` › "renders username, password, and submit controls" |
| 4 | Login captures creds → authenticated Basic-auth fetch | `login.test.tsx` › "captures entered credentials and issues an authenticated Basic-auth request" |
| 5 | 401 → auth-failure shown, does not proceed | `login.test.tsx` › "shows an auth-failure indication on 401 and does not proceed" |
| 6 | Product list renders name+price per product | `productList.test.tsx` › "renders one entry per product with name and price" |
| 7 | Catalog fetched from `GET /products` w/ Basic auth | `productList.test.tsx` › "fetches the catalog from GET /products with Basic auth" |
| 8 | add-to-cart POSTs `/cart/items` {product_id, quantity>=1} | `productList.test.tsx` › "add-to-cart POSTs /cart/items with the product_id and a positive quantity" |
| 9 | UI reflects added item | `productList.test.tsx` › "reflects the added item after a successful add" |
| 10 | Cart renders line items + total from `GET /cart` | `cart.test.tsx` › "renders each line item and the cart total" (exact total `39.48`) |
| 11 | Empty cart state, no phantom lines | `cart.test.tsx` › "renders a clear empty-cart state with no phantom lines" |
| 12 | Proceed-to-checkout control | `cart.test.tsx` › "exposes a proceed-to-checkout control" |
| 13 | Checkout POSTs `/checkout` w/ Basic auth | `checkout.test.tsx` › "POSTs /checkout with Basic auth when activated" |
| 14 | Success → order-confirmation shows returned id + total | `checkout.test.tsx` › "renders the order-confirmation..." + "OrderConfirmationView displays the order id and total" (exact `4242` / `39.48`) |
| 15 | Failure (400) → error shown, no fabricated order | `checkout.test.tsx` › "surfaces an error and shows no fabricated order when checkout fails" |
| 16 | API base URL configurable, defaults to documented URL | `config.test.ts` › "exports a configuration point that defaults to the documented backend URL" |
| 17 | Each view importable/renderable in isolation | rendering assertions across `login`/`productList`/`cart`/`checkout` tests + `OrderConfirmationView` isolation test |

## Red run output (`npm test` in `reference_app/frontend/`)

```
 ✓ src/__tests__/toolchain.test.ts (2 tests) 3ms
 FAIL  src/__tests__/cart.test.tsx [ src/__tests__/cart.test.tsx ]
Error: Failed to resolve import "../views" from "src/__tests__/cart.test.tsx". Does the file exist?
 FAIL  src/__tests__/checkout.test.tsx [ src/__tests__/checkout.test.tsx ]
Error: Failed to resolve import "../views" from "src/__tests__/checkout.test.tsx". Does the file exist?
 FAIL  src/__tests__/config.test.ts [ src/__tests__/config.test.ts ]
Error: Failed to resolve import "../config" from "src/__tests__/config.test.ts". Does the file exist?
 FAIL  src/__tests__/login.test.tsx [ src/__tests__/login.test.tsx ]
Error: Failed to resolve import "../views" from "src/__tests__/login.test.tsx". Does the file exist?
 FAIL  src/__tests__/productList.test.tsx [ src/__tests__/productList.test.tsx ]
Error: Failed to resolve import "../views" from "src/__tests__/productList.test.tsx". Does the file exist?

 Test Files  5 failed | 1 passed (6)
      Tests  2 passed (2)
```

## Legitimacy of the red
- The failures are **missing-module** errors for the spec's export points (`src/views`, `src/config`)
  — i.e. no implementation exists yet, the correct TDD-red reason.
- The **toolchain itself runs**: `toolchain.test.ts` (2 tests) passes green, confirming Vitest,
  jsdom, jest-dom matchers, and the React/TSX transform all execute. So the red suites will exercise
  real behavioral assertions once the views/config module are implemented.
- No implementation source was written or read.

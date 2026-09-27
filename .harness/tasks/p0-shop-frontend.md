# Task: p0-shop-frontend

## Title
Reference shop **frontend** — React + Vite UI (login, product list, cart, checkout,
order-confirmation) talking to the shop backend over HTTP Basic Auth.

## Context
- Plan item: `AGILE_PLAN.md` → Phase 0, **B2. Reference shop app — frontend**; backlog unit
  **#3 (`p0-shop-frontend`)**.
- Depends on: **`p0-shop-backend`** (done) — the FastAPI + SQLite shop API is runnable and its
  **contract is binding**, specified in `.harness/tasks/p0-shop-backend.md` and
  `reference_app/backend/README.md`. This unit builds the UI that drives that API.
- Source of truth: `DESIGN.md §9` (reference app = shop; mutable UI + API), `DESIGN.md §12`
  (frontend = **React** control/reference planes; target-app auth = **Basic Auth**), `AGILE_PLAN.md`
  B2, and the backend contract in `.harness/tasks/p0-shop-backend.md`.
- This is the **clean reference UI only** — the human-facing surface the later Playwright E2E smoke
  (unit 5) will drive end-to-end, and part of what `make dev` launches.

### Backend contract this UI consumes (binding — from `p0-shop-backend`)
- **Auth:** HTTP Basic Auth on every endpoint below. Seeded account: username **`testuser`**,
  password **`testpass`**. Missing/invalid credentials → **HTTP 401** (`WWW-Authenticate: Basic`).
- **Base URL (default):** `http://127.0.0.1:8000` (see Interfaces § API base URL for how this UI
  must make it configurable).
- **Endpoints + shapes** (field names binding; ids are integers per the seed):
  | Method | Path | Request body | Success response |
  |---|---|---|---|
  | `GET`  | `/products` | — | `200`, JSON array of `{ id, name, price }` (seed = **5** products) |
  | `GET`  | `/cart` | — | `200`, `{ items: [ { product_id, quantity } ], total }`; empty = `{ items: [], total: 0 }` |
  | `POST` | `/cart/items` | `{ product_id, quantity }` | `200/201`; updated cart is retrievable via `GET /cart` (add is cumulative) |
  | `POST` | `/checkout` | — | `200/201`, created order `{ id, items: [ { product_id, quantity } ], total }`; then cart is emptied |
  | `GET`  | `/orders/{id}` | — | `200`, same order shape as checkout |
- `total` everywhere = Σ over lines of `price × quantity`. Checkout on an empty cart → client error
  (e.g. `400`).

## Scope
**In scope**
1. A **React + Vite** single-page application under `reference_app/frontend/` presenting the shop
   as **five user-facing views/screens**: **login**, **product list**, **cart**, **checkout**, and
   **order-confirmation**.
2. **Login** captures a username + password and establishes the credentials used to make
   **authenticated** requests to the backend (HTTP Basic Auth) for all subsequent data.
3. **Product list** fetches and renders the catalog from `GET /products`, with an **add-to-cart**
   action per product that issues `POST /cart/items`.
4. **Cart** view fetches/reflects the current cart (`GET /cart`), listing line items (product +
   quantity) and the cart **total**, with an action to proceed to checkout.
5. **Checkout** issues `POST /checkout`, and on success **navigates to the order-confirmation view**
   which shows the returned **order id** and **order total**.
6. Sensible **loading / empty / error** states for the network-driven views (at minimum: an empty
   cart state, and a visible auth-failure/error indication when a request fails or credentials are
   rejected).
7. The frontend is a **buildable, testable Vite project** with `package.json` npm scripts
   (`dev`, `build`, `test` — see Interfaces) and **component export points** that allow each view to
   be imported and rendered in a component/integration test with the backend **stubbed**.
8. An **API-base-URL configuration** mechanism (see Interfaces) so the UI can point at the backend
   without code edits (env var and/or a dev proxy), defaulting to the backend's documented base URL.
9. A short `reference_app/frontend/README.md` documenting how to install, run (`dev`), build
   (`build`), and test (`test`) the UI, and how the API base URL is configured.

**Out of scope**
- The **Playwright E2E smoke** (login→add-to-cart→checkout against the live running app) — unit 5
  (`p0-playwright-smoke`). **This unit's acceptance MUST NOT depend on Playwright, a browser
  automation run, or a live/running backend.** All acceptance is verifiable via component/integration
  tests with backend calls **stubbed/mocked**, plus a successful production build.
- Any **backend** changes — the backend is fixed (`p0-shop-backend`, done). Do not modify
  `reference_app/backend/**`.
- The **BRD** / release/versioning docs — unit 4 (`p0-brd-release`).
- **Bug injection / buggy variants / eval scorer** — unit 6. Ship the **clean** UI only; no
  bug-toggle flags.
- Wiring the real `make dev` / `make test` target bodies beyond what this unit documents for itself
  (the combined app launch + Playwright wiring are units 3→5 concerns; this unit need only provide
  its own `dev`/`build`/`test` npm scripts and document them).
- Any control-plane, multi-tenancy, secrets-vault, styling-polish, or accessibility-beyond-basics
  concerns — later phases.
- Editing `DESIGN.md`, `META_PLAN.md`, `AGILE_PLAN.md`, `CLAUDE.md`, or anything under `.harness/`.

## Acceptance criteria (enumerated, testable)
Verifiable via **component/integration tests** that render exported components/views in an emulated
DOM with the backend HTTP calls **stubbed** (the test supplies canned responses matching the
contract above), plus a **production build** step. **No Playwright and no live backend required.**

**Build & project health**
1. Running the project's **build** script (`build`, see Interfaces) completes **successfully**
   (non-zero exit on failure) and emits a production bundle — i.e. the app compiles with no build
   errors.
2. Running the project's **test** script (`test`, see Interfaces) executes the component/integration
   suite and reports pass/fail with a non-zero exit on failure. (The Tester authors those tests;
   this criterion is that the script exists and runs the suite.)

**Login view**
3. The **login view** renders its key elements: a username input, a password input, and a submit
   control.
4. Submitting the login form with entered credentials causes the app to **capture** those
   credentials and use them to perform an **authenticated request** to the backend (i.e. a
   subsequent data fetch is made carrying HTTP Basic credentials derived from the entered
   username/password). Verified by observing the stubbed request received the expected
   `Authorization: Basic` header (or equivalent captured credential state) for the entered values.
5. When the backend rejects credentials (stubbed **401**), the UI surfaces a visible
   **authentication-failure** indication and does **not** proceed to the authenticated area.

**Product list view**
6. Given a stubbed `GET /products` returning a catalog array, the **product list view** renders one
   entry per product showing at least the product **name** and **price**.
7. The product list view issues its catalog request to **`GET /products`** with the authenticated
   credentials (verified via the stub).
8. Each product entry exposes an **add-to-cart** control; activating it issues a
   **`POST /cart/items`** request whose body carries the correct **`product_id`** and a positive
   **`quantity`** for that product (verified via the stub).
9. After a successful add-to-cart, the UI **reflects** that the item was added (e.g. a cart
   count/indicator updates, or the cart view subsequently shows the item) — the add is not silently
   dropped.

**Cart view**
10. Given a stubbed `GET /cart` returning line items + total, the **cart view** renders each line
    item (identifiable by its product and quantity) and displays the cart **total** consistent with
    the stubbed response.
11. Given a stubbed **empty** cart (`{ items: [], total: 0 }`), the cart view renders a clear
    **empty-cart** state (and does not display phantom line items).
12. The cart view exposes a control to **proceed to checkout**.

**Checkout → order-confirmation**
13. Activating checkout issues a **`POST /checkout`** request with the authenticated credentials
    (verified via the stub).
14. On a successful stubbed checkout response (`{ id, items, total }`), the app **navigates to /
    renders the order-confirmation view**, which displays the returned **order id** and the order
    **total**.
15. When checkout fails (stubbed client error, e.g. empty-cart **400**), the UI surfaces a visible
    **error** state and does **not** navigate to a confirmation showing a fabricated order.

**Wiring / configurability**
16. The API base URL the UI targets is **configurable** without editing component source (via the
    env-var and/or dev-proxy mechanism in Interfaces) and **defaults** to the backend's documented
    base URL (`http://127.0.0.1:8000`). Verified by inspecting the configuration point (e.g. the
    env-var/config module) rather than a live call.
17. Each of the five views is **importable as an exported component** (see Interfaces § Component
    export points) so it can be rendered in isolation by a test; rendering a view in a test does not
    require a real network or a running backend.

## Interfaces / contracts
> The Tester writes component/integration tests against **these contracts** without seeing the
> implementation internals. Script names, the config mechanism, the backend routes/shapes (above),
> and the existence of per-view importable component export points are **binding**. Exact component
> names, file layout, state-management approach, styling, and routing library are the developer's
> choice (HOW) and are **not** prescribed here — tests must target behavior and documented export
> points, not internal structure.

### Project location & tooling
- All frontend code lives under **`reference_app/frontend/`**. It is a **React + Vite** project with
  its own `package.json`. Node dependencies install under `reference_app/frontend/node_modules/`
  (already git-ignored via `node_modules/`).
- Component/integration testing uses a **Vite-native test runner with an emulated DOM and a React
  component-rendering/testing library** (developer's specific choice), driven by the `test` script.

### npm scripts (binding names in `reference_app/frontend/package.json`)
| Script | Purpose |
|---|---|
| `dev`   | Start the Vite dev server for local development (used by `make dev` later). |
| `build` | Produce the production bundle; **non-zero exit on any build/compile error** (criterion 1). |
| `test`  | Run the component/integration test suite once (CI-style, non-interactive), **non-zero exit on failure** (criterion 2). |

- The exact invocation (e.g. `npm run build` / `npm run test`, or the package-manager equivalent)
  and any single-run flags must be documented in `reference_app/frontend/README.md` so the Tester
  and reviewer can run them without reading the code.

### API base URL configuration
- The UI must resolve the backend base URL from a **build/runtime configuration point** — a Vite
  environment variable (e.g. a `VITE_`-prefixed var) **and/or** a Vite dev-server proxy — such that
  the target backend can be changed **without editing component source**.
- The **default** (when nothing is overridden) must be the backend's documented base URL
  **`http://127.0.0.1:8000`**.
- Document the variable name / proxy config and the default in `reference_app/frontend/README.md`.

### Backend routes each view calls (binding — shapes in Context above)
| View | Calls | With |
|---|---|---|
| Login | establishes credentials; triggers first authenticated fetch | HTTP Basic (`testuser`/`testpass` for the seeded account) |
| Product list | `GET /products`; `POST /cart/items` `{ product_id, quantity }` | Basic auth |
| Cart | `GET /cart` | Basic auth |
| Checkout | `POST /checkout` | Basic auth |
| Order-confirmation | renders `{ id, total }` from the checkout response (or `GET /orders/{id}`) | Basic auth |

- All authenticated requests carry the credentials captured at login as an HTTP **Basic**
  `Authorization` header. Credentials must **never** be hard-coded into components (they come from
  the login form).

### Component export points (binding that they exist; names are the developer's choice)
- Each of the **five views** (login, product list, cart, checkout, order-confirmation) must be
  **importable** from the frontend source as a rendarable React component, so a test can mount it in
  isolation with stubbed backend responses. The developer documents the import path / export name
  for each view in `reference_app/frontend/README.md` (or an index/barrel export) so the Tester can
  import them without inspecting implementation internals.
- Network access must be **stubbable** in tests (e.g. the HTTP layer is mockable via the test
  runner's module/fetch mocking) so no real backend is contacted during `test`.

### Documentation
- `reference_app/frontend/README.md` documents: install command, the `dev`/`build`/`test` scripts
  and how to run them, the API-base-URL config variable + default, and the per-view component export
  points/import paths for testing.

## Definition of Done
- All acceptance criteria **1–17** are satisfied.
- A **React + Vite** app lives under `reference_app/frontend/` with a `package.json` exposing
  `dev`, `build`, and `test` scripts; `build` succeeds and `test` runs the component/integration
  suite.
- The five views (login, product list, cart, checkout, order-confirmation) render their key
  elements and drive the backend contract (routes/shapes above) over HTTP Basic Auth, with the API
  base URL configurable (default `http://127.0.0.1:8000`).
- Each view is importable/renderable in isolation with the backend stubbed; no test requires a live
  backend or Playwright.
- `reference_app/frontend/README.md` documents run/build/test, the API-base-URL config, and the
  per-view export points.
- **Clean UI only** — no bug-injection toggles, no backend edits, no BRD/release docs, no Playwright
  project (later units).
- No protected file changed (`DESIGN.md`, `META_PLAN.md`, `AGILE_PLAN.md`, `CLAUDE.md`,
  `.harness/**`, `reference_app/backend/**`).
- Consistent with `DESIGN.md §9/§12` and `AGILE_PLAN.md` B2; unblocks unit 5 (`p0-playwright-smoke`).

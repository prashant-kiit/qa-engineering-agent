# Task: p0-shop-backend

## Title
Reference shop **backend** — FastAPI + SQLite API (Basic Auth, products, cart, checkout → order,
order-total, seed data, auto `/openapi.json`)

## Context
- Plan item: `AGILE_PLAN.md` → Phase 0, **B2. Reference shop app — backend**; backlog unit
  **#2 (`p0-shop-backend`)**.
- Depends on: **`p0-scaffold`** (done) — the `reference_app/backend/` directory + root `uv`
  manifest (`pyproject.toml`) + `Makefile` skeleton already exist. Blocks units 3
  (`p0-shop-frontend`), 4 (`p0-brd-release`), and 6 (`p0-eval-harness`).
- Source of truth: `DESIGN.md §9` (reference app = shop: cart, checkout, orders, auth; mutable UI +
  API), `DESIGN.md §12` (stack: FastAPI backend, SQLite, auto-OpenAPI, Basic Auth from vault), and
  `AGILE_PLAN.md` B2.
- This is the **clean, correct backend + seed data only.** It is the system-under-test the later
  Playwright suite (unit 5) and the `eval/` bug-injection harness (unit 6) run against.

## Scope
**In scope**
1. A runnable **FastAPI HTTP API service** under `reference_app/backend/` implementing the shop
   domain: authentication (HTTP Basic), product listing, a per-user cart with add-to-cart, checkout
   that creates an order, order retrieval, and correct order-total calculation.
2. **SQLite persistence** with **deterministic seed data**: a fixed catalog of products and (at
   least) one known test account, created/seeded on startup so a fresh run is immediately testable.
3. **Auto-served OpenAPI**: FastAPI exposes a machine-readable OpenAPI document at `/openapi.json`
   describing the endpoints below (this is the schema the QA agent will ground API tests on later).
4. A **documented, deterministic way to launch the app for tests** — both a stable HTTP host/port
   for black-box tests **and** an importable ASGI application object for in-process testing (see
   Interfaces § Launch — the import path is **binding**).

**Out of scope**
- The **frontend** (React + Vite UI) — unit 3 (`p0-shop-frontend`).
- The **BRD** and release/versioning convention — unit 4 (`p0-brd-release`).
- **Bug injection / buggy variants / scorer** — unit 6 (`p0-eval-harness`). Ship the **clean**
  backend only; do **not** add bug-toggle env flags in this unit.
- The Playwright test project and `make test`/`make dev` target bodies beyond what this unit needs
  to be launchable — units 3/5 own those. (Wiring `make dev` to start the backend is acceptable but
  not required by this unit's acceptance.)
- Any control-plane, multi-tenancy, secrets-vault, or egress concerns — later phases.
- Editing `DESIGN.md`, `META_PLAN.md`, `AGILE_PLAN.md`, `CLAUDE.md`, or anything under `.harness/`.

## Acceptance criteria (enumerated, testable)
All criteria are verifiable **externally** against the running/importable API (HTTP requests +
response inspection) or the served OpenAPI document — no knowledge of the implementation required.

**Auth**
1. A request to a protected endpoint with **no credentials** is rejected with **HTTP 401**.
2. A request to a protected endpoint with **wrong username or password** is rejected with
   **HTTP 401**.
3. A request with the **seeded valid credentials** (see Interfaces) is accepted (**not** 401/403)
   and returns the endpoint's normal success response.
4. The 401 responses advertise HTTP Basic (a `WWW-Authenticate: Basic ...` response header is
   present) so the scheme is discoverable.

**Products**
5. `GET /products` with valid auth returns **HTTP 200** and a JSON **array** of products; the array
   is **non-empty** and matches the seeded catalog **count**.
6. Each product object contains at least the fields **`id`**, **`name`**, and **`price`**, with
   `price` a non-negative number and `id` unique across the list.

**Cart + add-to-cart**
7. `GET /cart` with valid auth for a fresh/empty account returns **HTTP 200** with an **empty**
   items collection and a **total of 0**.
8. `POST /cart/items` with valid auth and a body referencing a **valid product id** and a positive
   **quantity** returns success (**HTTP 200 or 201**) and the cart subsequently reflects that item
   with the requested quantity.
9. Adding the **same product** again increases that line's quantity such that the cart's reported
   quantity for that product equals the **cumulative** quantity added (no silent drop) — i.e.
   add-to-cart is cumulative-by-increment, not overwrite-to-1.
10. `POST /cart/items` referencing a **non-existent product id** is rejected with a **client-error
    status** (**HTTP 404** for unknown product, or **HTTP 422** for a malformed/invalid body) and
    does **not** add an item to the cart.
11. The **cart total** equals the sum over line items of `product.price × quantity` (exact, using
    the seeded prices).

**Checkout → order**
12. `POST /checkout` with valid auth on a **non-empty** cart returns success (**HTTP 200 or 201**)
    and a **created order** payload that includes an **order `id`** and an order **`total`**.
13. The created order's **`total` equals the cart total** at checkout time (= Σ `price × quantity`),
    proving order-total correctness.
14. After a successful checkout the user's **cart is emptied** (a subsequent `GET /cart` shows no
    items and total 0).
15. `POST /checkout` on an **empty** cart is rejected with a **client-error status** (e.g. **HTTP
    400 or 409**) and does **not** create an order.

**Get order**
16. `GET /orders/{id}` with valid auth for an **existing** order id returns **HTTP 200** and the
    order, whose `id` and `total` match the order returned at checkout (criterion 12/13). The order
    payload identifies its **line items** (product id + quantity per line).
17. `GET /orders/{id}` for a **non-existent** order id returns **HTTP 404**.
18. **Every** order endpoint (`GET /orders/{id}` and `POST /checkout`) requires auth: called with no
    / invalid credentials it returns **HTTP 401** (i.e. no auth-bypass on order endpoints — the
    invariant unit 6 will later inject a bug against).

**Seed data**
19. On a fresh database the seeded **product catalog** is present and stable (same product
    ids/prices across restarts of a freshly-seeded DB), and the seeded **test account** can
    authenticate (criterion 3).

**OpenAPI**
20. `GET /openapi.json` returns **HTTP 200** and a valid JSON OpenAPI document (has an `openapi`
    version string and a `paths` object). This endpoint requires **no** auth.
21. The OpenAPI `paths` document the shop routes exercised above — at minimum entries for
    `/products`, `/cart`, `/cart/items`, `/checkout`, and `/orders/{id}` (path templated).

**Launchability**
22. The app is launchable deterministically for tests via **both** documented entrypoints
    (Interfaces § Launch): the ASGI import path `reference_app.backend.app:app` and a stable HTTP
    host/port. Once up, it serves all of the above. Repeated fresh-start runs are reproducible
    (deterministic seed).

## Interfaces / contracts
> The Tester writes API tests against **this contract** without seeing the implementation. Field
> names, methods, paths, status codes, credentials, and the ASGI import path below are **binding**.
> Where a criterion permits a small set of acceptable status codes (e.g. "200 or 201"), the
> implementation picks one and it must be consistent.

### Auth scheme
- **HTTP Basic Auth** on all endpoints below **except** `GET /openapi.json` and any auto-generated
  docs endpoint. Missing/invalid credentials → **401** with a `WWW-Authenticate: Basic` header.
- **Seeded test account (binding — exactly these values):**
  - username: **`testuser`**
  - password: **`testpass`**
- (The developer may add more seeded accounts, but this one must exist and authenticate.)

### Base URL / paths
- All application routes are served under the service root (no version prefix for Phase 0).
- Endpoints (exact method + path):
  | Method | Path | Auth | Purpose |
  |---|---|---|---|
  | `GET`  | `/products` | Basic | List seeded products |
  | `GET`  | `/cart` | Basic | Current user's cart (items + total) |
  | `POST` | `/cart/items` | Basic | Add a product+quantity to the cart |
  | `POST` | `/checkout` | Basic | Create an order from the current cart, empty the cart |
  | `GET`  | `/orders/{id}` | Basic | Retrieve a previously created order |
  | `GET`  | `/openapi.json` | none | Auto-generated OpenAPI schema |

### Request / response shapes (field names binding; extra fields allowed)
- **Product** (element of `GET /products` array, and referenced by order lines):
  `{ "id": <int|str>, "name": <str>, "price": <number ≥ 0> }`. Choose one id type and keep it
  consistent across products, cart, and orders.
- **`GET /cart`** →
  `{ "items": [ { "product_id": <id>, "quantity": <int ≥ 1>, ... } ], "total": <number> }`.
  An empty cart → `{ "items": [], "total": 0 }`.
- **`POST /cart/items`** request body → `{ "product_id": <id>, "quantity": <int ≥ 1> }`.
  Success → the updated cart (same shape as `GET /cart`) or a 200/201 acknowledgment from which the
  updated cart state is retrievable via `GET /cart`.
- **`POST /checkout`** → **created order**:
  `{ "id": <id>, "items": [ { "product_id": <id>, "quantity": <int> } ... ], "total": <number> }`.
- **`GET /orders/{id}`** → the same **order** shape as the checkout response.
- **`total`** everywhere = Σ over lines of `product.price × quantity`. Use a numeric representation
  that yields exact expected values for the seeded prices (the Tester will assert exact equality).

### Cart scoping
- The cart is **per authenticated user** (keyed off the Basic-Auth identity). Actions by `testuser`
  affect only `testuser`'s cart. (A single test account is sufficient for this unit.)

### Persistence & seed
- **SQLite** database. Seed on startup with a **fixed** product catalog (stable ids + prices) and
  the `testuser`/`testpass` account. The DB file location is the developer's choice but must be
  **git-ignored** (`*.db` is already ignored) and must not require manual setup before tests.
- A **fresh** start (no pre-existing DB, or a reset one) must reproduce the same seed
  deterministically.

### Launch (for tests) — both mechanisms required
- **In-process ASGI (primary for API tests):** the FastAPI application object is importable at the
  **binding** path **`reference_app.backend.app:app`** — i.e. `from reference_app.backend.app import app`
  yields the ASGI app the Tester drives via an ASGI/HTTP test client without binding a port.
  Importing the app must trigger (or make trivially available) the deterministic seed so an
  in-process test starts against seeded data. The package must be importable from the repo root
  under the root `uv` project.
- **HTTP:** a documented command/target that starts the API on a **stable localhost host+port**
  (developer picks the port; document it in `reference_app/backend/README.md` and/or the `make dev`
  body) so black-box HTTP tests can hit `http://<host>:<port>`.
- Both the exact run command and the import path **must be documented** in
  `reference_app/backend/README.md` so the Tester can start the app without reading the
  implementation.

## Definition of Done
- All acceptance criteria **1–22** are satisfied against the running/importable app.
- The backend lives under `reference_app/backend/`; the ASGI app is importable at
  `reference_app.backend.app:app`; SQLite seed (products + `testuser`/`testpass`) is automatic;
  `/openapi.json` is served and documents the shop routes.
- The launch entrypoints (ASGI import path + HTTP host/port) and the seeded credentials are
  documented in `reference_app/backend/README.md` so tests are runnable without inspecting the code.
- Python dependencies needed by the backend are declared via the root `uv` project (`pyproject.toml`)
  so a `uv`-managed environment can run it; DB files remain git-ignored.
- **Clean backend only** — no bug-injection toggles, no frontend, no BRD/release docs (later units).
- No protected file changed (`DESIGN.md`, `META_PLAN.md`, `AGILE_PLAN.md`, `CLAUDE.md`,
  `.harness/**`).
- Consistent with `DESIGN.md §9/§12` and `AGILE_PLAN.md` B2; unblocks units 3, 4, and 6.
</content>
</invoke>

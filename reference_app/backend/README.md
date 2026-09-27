# Reference Shop — Backend (FastAPI + SQLite)

The clean, correct shop API used as the system-under-test for the QA agent's Playwright /
API suites. Provides HTTP Basic Auth, a seeded product catalog, a per-user cart, checkout →
order creation, and order retrieval, with an auto-generated OpenAPI document.

## Launch

Two deterministic entrypoints (both documented here so tests can run without reading the code):

### 1. In-process ASGI (primary for API tests) — binding import path

```python
from reference_app.backend.app import app  # ASGI application object
```

The **binding** import path is `reference_app.backend.app:app`. Importing the module
(re)creates and reseeds the SQLite database, so an in-process test starts against fresh,
deterministic seed data. Drive it with the FastAPI/Starlette `TestClient` (no port needed):

```python
from fastapi.testclient import TestClient
from reference_app.backend.app import app

with TestClient(app) as client:
    client.get("/products", auth=("testuser", "testpass"))
```

### 2. HTTP server (black-box tests) — stable host/port

Runs on **`http://127.0.0.1:8000`** by default (override with `SHOP_HOST` / `SHOP_PORT`):

```bash
uv run uvicorn reference_app.backend.app:app --host 127.0.0.1 --port 8000
# or, equivalently:
uv run python -m reference_app.backend.app
```

Then hit `http://127.0.0.1:8000/products`, `/cart`, `/cart/items`, `/checkout`,
`/orders/{id}`, and `/openapi.json`.

## Seeded credentials

HTTP Basic Auth is required on every endpoint **except** `/openapi.json`.

| username   | password   |
|------------|------------|
| `testuser` | `testpass` |

Missing or invalid credentials return **HTTP 401** with a `WWW-Authenticate: Basic` header.

## Endpoints

| Method | Path            | Auth  | Purpose                                          |
|--------|-----------------|-------|--------------------------------------------------|
| `GET`  | `/products`     | Basic | List the seeded catalog                          |
| `GET`  | `/cart`         | Basic | Current user's cart (`items` + `total`)          |
| `POST` | `/cart/items`   | Basic | Add `{product_id, quantity}` (cumulative add)    |
| `POST` | `/checkout`     | Basic | Create an order from the cart, then empty it     |
| `GET`  | `/orders/{id}`  | Basic | Retrieve a previously created order              |
| `GET`  | `/openapi.json` | none  | Auto-generated OpenAPI schema                    |

- `total` everywhere = Σ over line items of `price × quantity` using the seeded prices.
- Checkout on an empty cart is rejected with **HTTP 400**.

## Persistence & seed

SQLite database at `reference_app/backend/shop.db` (git-ignored via `*.db`). It is reset and
reseeded on every fresh process/import with a fixed product catalog (stable ids + prices) and
the `testuser` / `testpass` account, so repeated fresh-start runs are reproducible. No manual
setup is required before running tests.

## Test

```bash
uv run pytest reference_app/backend/tests -q
```

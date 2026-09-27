# Tests — p0-shop-backend (TDD red)

Test-first acceptance suite for the reference-shop **backend** (FastAPI + SQLite).
Written from `.harness/tasks/p0-shop-backend.md` **without** reading any implementation
(none exists yet — `reference_app/backend/` holds only `.gitkeep`).

## Framework & wiring
- **pytest** driving the app **in-process** via the FastAPI/Starlette `TestClient`
  (httpx-backed), against the **binding** ASGI import path `reference_app.backend.app:app`.
- Test-only deps declared in the root `uv` project (`pyproject.toml` `[dependency-groups].dev`:
  `pytest`, `httpx`, `fastapi`, `uvicorn`) + `[tool.pytest.ini_options]` (`pythonpath=["."]`,
  `testpaths=["reference_app/backend/tests"]`). Runnable with `uv run pytest`.
- Seeded Basic-Auth account used exactly as pinned by the spec: `testuser` / `testpass`.
- **Exact totals**: expected order/cart totals are computed as Σ `price × quantity` using the
  prices returned by `GET /products` (the served seed), then asserted for equality — so the
  suite pins total-correctness against the actual seeded prices without inventing numbers.
- **Isolation**: the `client` fixture reloads the app module (re-triggering the deterministic
  seed) and drains any residual cart via checkout, making cart-state tests order-independent.

## Test files
- `reference_app/backend/tests/conftest.py` — fixtures (`app_obj`, `client`), auth constants,
  helpers (`get_products`, `expected_total`, `find_absent_product_id`, `find_absent_order_id`,
  `cart_qty_for`).
- `reference_app/backend/tests/test_shop_backend.py` — the 26 acceptance tests below.

## Acceptance criterion → test(s)

| # | Criterion | Test(s) |
|---|---|---|
| 1 | No credentials → 401 | `test_c1_no_credentials_rejected_401` (params `/products`, `/cart`) |
| 2 | Wrong user/password → 401 | `test_c2_wrong_credentials_rejected_401` (wrong-pass, wrong-user) |
| 3 | Seeded valid creds accepted (not 401/403) | `test_c3_valid_seeded_credentials_accepted` |
| 4 | 401 advertises `WWW-Authenticate: Basic` | `test_c4_401_advertises_basic_scheme` |
| 5 | `GET /products` → 200, non-empty array, count coherent/stable | `test_c5_products_returns_nonempty_array`, `test_c5_products_count_stable_across_fresh_seed` |
| 6 | Product has `id`/`name`/`price`, price ≥ 0, unique ids | `test_c6_product_fields_and_invariants` |
| 7 | Fresh `GET /cart` → empty items, total 0 | `test_c7_fresh_cart_empty_total_zero` |
| 8 | Add valid product+qty → success, cart reflects qty | `test_c8_add_item_reflected_with_quantity` |
| 9 | Repeat add is cumulative (2+3=5, not overwrite-to-1) | `test_c9_repeat_add_is_cumulative` |
| 10 | Add unknown product → 404/422 and no cart mutation | `test_c10_add_unknown_product_rejected_and_no_mutation` |
| 11 | Cart total == Σ price×qty (exact, seeded prices) | `test_c11_cart_total_equals_sum_price_times_qty` |
| 12 | Checkout non-empty cart → 200/201 order with `id` + `total` | `test_c12_checkout_creates_order_with_id_and_total` |
| 13 | Order `total` == cart total at checkout | `test_c13_order_total_equals_cart_total` |
| 14 | Cart emptied after checkout | `test_c14_cart_emptied_after_checkout` |
| 15 | Checkout empty cart → 400/409, no order | `test_c15_checkout_empty_cart_rejected` |
| 16 | `GET /orders/{id}` existing → 200, matches checkout, has line items | `test_c16_get_order_matches_checkout_and_has_lines` |
| 17 | `GET /orders/{id}` non-existent → 404 | `test_c17_get_nonexistent_order_404` |
| 18 | Order endpoints require auth (no bypass) → 401 | `test_c18_order_endpoints_require_auth` |
| 19 | Seed products (ids/prices) deterministic + account authenticates | `test_c19_seed_products_and_account_deterministic` |
| 20 | `GET /openapi.json` → 200 valid doc, public | `test_c20_openapi_served_without_auth` |
| 21 | OpenAPI documents `/products`,`/cart`,`/cart/items`,`/checkout`,`/orders/{id}` | `test_c21_openapi_documents_shop_routes` |
| 22 | Launchable via binding ASGI path; fresh start serves full API | `test_c22_binding_asgi_import_path`, `test_c22_fresh_start_serves_full_api` |

All 22 criteria are covered (26 tests total; C1/C2/C5/C22 have multiple tests).

## Red run (before implementation)

```
$ uv run pytest reference_app/backend/tests -q

    """Import (or reload) the binding ASGI module so a fresh deterministic seed runs."""
>       import reference_app.backend.app as app_module  # binding import path
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       ModuleNotFoundError: No module named 'reference_app.backend.app'

reference_app/backend/tests/conftest.py:32: ModuleNotFoundError
=========================== short test summary info ============================
ERROR reference_app/backend/tests/test_shop_backend.py::test_c1_no_credentials_rejected_401[/products]
... (26 ERRORs — one per test) ...
ERROR reference_app/backend/tests/test_shop_backend.py::test_c22_fresh_start_serves_full_api
1 warning, 26 errors in 0.06s
```

- `--collect-only` reports **26 tests collected** — the suite has no syntax/scaffolding
  errors; every test fails purely because the system-under-test module does not exist yet
  (`reference_app.backend.app`). This is legitimate TDD red ("no implementation").
- The lone warning is a benign Starlette deprecation notice from `fastapi.testclient`; it
  does not affect the run.

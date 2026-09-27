# Acceptance suite for unit `p0-shop-backend` (TDD red — written before implementation).
#
# Each test maps to an enumerated acceptance criterion (C1..C22) in
# .harness/tasks/p0-shop-backend.md. Tests are behavioral and black-box: they drive the
# app via its binding ASGI import path (reference_app.backend.app:app) using an in-process
# HTTP test client, and assert against the pinned contract only (no implementation reading).
#
# Run:  uv run pytest reference_app/backend/tests -q

import importlib

import pytest

from conftest import (
    PROTECTED_GET,
    VALID_AUTH,
    WRONG_AUTH,
    WRONG_USER,
    cart_qty_for,
    expected_total,
    find_absent_order_id,
    find_absent_product_id,
    get_products,
    product_price,
)

CREATED_OK = (200, 201)  # spec allows either for create-style success
CLIENT_ERR_ADD = (404, 422)  # C10: unknown product OR malformed body
CLIENT_ERR_CHECKOUT = (400, 409)  # C15: empty-cart checkout rejection


# --------------------------------------------------------------------------- Auth (C1-C4)

@pytest.mark.parametrize("path", PROTECTED_GET)
def test_c1_no_credentials_rejected_401(client, path):
    """C1: protected endpoint with no credentials -> 401."""
    r = client.get(path)
    assert r.status_code == 401, f"{path} without creds should be 401, got {r.status_code}"


@pytest.mark.parametrize("bad", [WRONG_AUTH, WRONG_USER])
def test_c2_wrong_credentials_rejected_401(client, bad):
    """C2: wrong username or password -> 401."""
    r = client.get("/products", auth=bad)
    assert r.status_code == 401, f"wrong creds {bad[0]} should be 401, got {r.status_code}"


def test_c3_valid_seeded_credentials_accepted(client):
    """C3: seeded testuser/testpass is accepted (not 401/403) with a normal success response."""
    r = client.get("/products", auth=VALID_AUTH)
    assert r.status_code not in (401, 403), f"valid creds must be accepted, got {r.status_code}"
    assert r.status_code == 200


def test_c4_401_advertises_basic_scheme(client):
    """C4: 401 responses carry a `WWW-Authenticate: Basic ...` header."""
    r = client.get("/products")
    assert r.status_code == 401
    header = r.headers.get("www-authenticate", "")
    assert header.lower().startswith("basic"), (
        f"401 must advertise Basic auth via WWW-Authenticate, got {header!r}"
    )


# ----------------------------------------------------------------------- Products (C5-C6)

def test_c5_products_returns_nonempty_array(client):
    """C5: GET /products (valid auth) -> 200 and a non-empty JSON array matching the seeded count."""
    r = client.get("/products", auth=VALID_AUTH)
    assert r.status_code == 200
    products = r.json()
    assert isinstance(products, list), "GET /products must return a JSON array"
    assert len(products) > 0, "seeded catalog must be non-empty"
    ids = [p["id"] for p in products]
    # count coherence: the array count equals the number of distinct seeded products
    assert len(ids) == len(set(ids)) == len(products)


def test_c5_products_count_stable_across_fresh_seed(client):
    """C5/C19: the seeded catalog count is stable across a fresh reseed."""
    first = len(get_products(client))
    module = importlib.reload(importlib.import_module("reference_app.backend.app"))
    from fastapi.testclient import TestClient

    with TestClient(module.app) as c2:
        second = len(get_products(c2))
    assert first == second, "seeded product count must be deterministic across fresh starts"


def test_c6_product_fields_and_invariants(client):
    """C6: each product has id, name, price; price >= 0 number; ids unique."""
    products = get_products(client)
    seen = set()
    for p in products:
        assert {"id", "name", "price"} <= set(p.keys()), f"missing required fields: {p}"
        assert isinstance(p["name"], str) and p["name"] != ""
        assert isinstance(p["price"], (int, float)) and not isinstance(p["price"], bool)
        assert p["price"] >= 0, f"price must be non-negative: {p}"
        assert p["id"] not in seen, f"duplicate product id {p['id']!r}"
        seen.add(p["id"])


# ----------------------------------------------------------------- Cart / add (C7-C11)

def test_c7_fresh_cart_empty_total_zero(client):
    """C7: GET /cart on a fresh/empty account -> 200, empty items, total 0."""
    r = client.get("/cart", auth=VALID_AUTH)
    assert r.status_code == 200
    cart = r.json()
    assert cart.get("items") == [], f"fresh cart must be empty, got {cart.get('items')!r}"
    assert cart.get("total") == 0, f"empty-cart total must be 0, got {cart.get('total')!r}"


def test_c8_add_item_reflected_with_quantity(client):
    """C8: POST /cart/items (valid product + qty) succeeds and the cart reflects that quantity."""
    products = get_products(client)
    pid = products[0]["id"]
    r = client.post("/cart/items", json={"product_id": pid, "quantity": 2}, auth=VALID_AUTH)
    assert r.status_code in CREATED_OK, f"add-to-cart should be 200/201, got {r.status_code}"
    cart = client.get("/cart", auth=VALID_AUTH).json()
    assert cart_qty_for(cart, pid) == 2, f"cart should reflect quantity 2 for {pid}, got {cart}"


def test_c9_repeat_add_is_cumulative(client):
    """C9: adding the same product again accumulates quantity (increment, not overwrite-to-1)."""
    products = get_products(client)
    pid = products[0]["id"]
    client.post("/cart/items", json={"product_id": pid, "quantity": 2}, auth=VALID_AUTH)
    client.post("/cart/items", json={"product_id": pid, "quantity": 3}, auth=VALID_AUTH)
    cart = client.get("/cart", auth=VALID_AUTH).json()
    assert cart_qty_for(cart, pid) == 5, (
        f"repeat add must be cumulative (2+3=5), got {cart_qty_for(cart, pid)} in {cart}"
    )


def test_c10_add_unknown_product_rejected_and_no_mutation(client):
    """C10: POST /cart/items with a non-existent product id -> client error and cart unchanged."""
    products = get_products(client)
    absent = find_absent_product_id(products)
    before = client.get("/cart", auth=VALID_AUTH).json()
    r = client.post("/cart/items", json={"product_id": absent, "quantity": 1}, auth=VALID_AUTH)
    assert r.status_code in CLIENT_ERR_ADD, (
        f"unknown product must be rejected (404/422), got {r.status_code}"
    )
    after = client.get("/cart", auth=VALID_AUTH).json()
    assert after.get("items") == before.get("items"), "rejected add must not mutate the cart"
    assert cart_qty_for(after, absent) == 0


def test_c11_cart_total_equals_sum_price_times_qty(client):
    """C11: cart total == Σ product.price × quantity (exact, seeded prices)."""
    products = get_products(client)
    a, b = products[0]["id"], products[min(1, len(products) - 1)]["id"]
    client.post("/cart/items", json={"product_id": a, "quantity": 2}, auth=VALID_AUTH)
    if b != a:
        client.post("/cart/items", json={"product_id": b, "quantity": 3}, auth=VALID_AUTH)
        lines = [(a, 2), (b, 3)]
    else:
        client.post("/cart/items", json={"product_id": a, "quantity": 3}, auth=VALID_AUTH)
        lines = [(a, 5)]
    cart = client.get("/cart", auth=VALID_AUTH).json()
    exp = expected_total(products, lines)
    assert cart["total"] == pytest.approx(exp), f"cart total should be {exp}, got {cart['total']}"


# ------------------------------------------------------------ Checkout -> order (C12-C15)

def _add_known_cart(client):
    """Add a deterministic set of lines; return (products, lines, expected_total)."""
    products = get_products(client)
    pid = products[0]["id"]
    client.post("/cart/items", json={"product_id": pid, "quantity": 2}, auth=VALID_AUTH)
    lines = [(pid, 2)]
    return products, lines, expected_total(products, lines)


def test_c12_checkout_creates_order_with_id_and_total(client):
    """C12: POST /checkout on a non-empty cart -> 200/201 with an order id and total."""
    _add_known_cart(client)
    r = client.post("/checkout", auth=VALID_AUTH)
    assert r.status_code in CREATED_OK, f"checkout should be 200/201, got {r.status_code}"
    order = r.json()
    assert "id" in order and order["id"] is not None, "created order must include an id"
    assert "total" in order, "created order must include a total"


def test_c13_order_total_equals_cart_total(client):
    """C13: created order total == cart total at checkout (= Σ price × quantity)."""
    _, _, exp = _add_known_cart(client)
    order = client.post("/checkout", auth=VALID_AUTH).json()
    assert order["total"] == pytest.approx(exp), (
        f"order total should equal cart total {exp}, got {order['total']}"
    )


def test_c14_cart_emptied_after_checkout(client):
    """C14: after a successful checkout GET /cart shows no items and total 0."""
    _add_known_cart(client)
    client.post("/checkout", auth=VALID_AUTH)
    cart = client.get("/cart", auth=VALID_AUTH).json()
    assert cart.get("items") == [], f"cart must be emptied after checkout, got {cart}"
    assert cart.get("total") == 0


def test_c15_checkout_empty_cart_rejected(client):
    """C15: POST /checkout on an empty cart -> client error (400/409) and no order created."""
    # `client` fixture guarantees an empty cart.
    r = client.post("/checkout", auth=VALID_AUTH)
    assert r.status_code in CLIENT_ERR_CHECKOUT, (
        f"empty-cart checkout must be rejected (400/409), got {r.status_code}"
    )


# ------------------------------------------------------------------ Get order (C16-C18)

def test_c16_get_order_matches_checkout_and_has_lines(client):
    """C16: GET /orders/{id} returns the order; id/total match checkout; lines identify product+qty."""
    products, _, exp = _add_known_cart(client)
    pid = products[0]["id"]
    created = client.post("/checkout", auth=VALID_AUTH).json()
    oid = created["id"]
    r = client.get(f"/orders/{oid}", auth=VALID_AUTH)
    assert r.status_code == 200, f"existing order should be 200, got {r.status_code}"
    order = r.json()
    assert order["id"] == oid
    assert order["total"] == pytest.approx(exp)
    assert isinstance(order.get("items"), list) and len(order["items"]) >= 1
    for line in order["items"]:
        assert "product_id" in line and "quantity" in line
    assert cart_qty_for(order, pid) == 2, "order line items must record product id + quantity"


def test_c17_get_nonexistent_order_404(client):
    """C17: GET /orders/{id} for a non-existent id -> 404."""
    products = get_products(client)
    absent = find_absent_order_id(products)
    r = client.get(f"/orders/{absent}", auth=VALID_AUTH)
    assert r.status_code == 404, f"unknown order id should be 404, got {r.status_code}"


def test_c18_order_endpoints_require_auth(client):
    """C18: /checkout and /orders/{id} reject missing/invalid creds with 401 (no auth-bypass)."""
    products = get_products(client)
    absent = find_absent_order_id(products)

    assert client.post("/checkout").status_code == 401, "checkout must require auth"
    assert client.post("/checkout", auth=WRONG_AUTH).status_code == 401

    assert client.get(f"/orders/{absent}").status_code == 401, "get-order must require auth"
    assert client.get(f"/orders/{absent}", auth=WRONG_AUTH).status_code == 401


# -------------------------------------------------------------------- Seed data (C19)

def test_c19_seed_products_and_account_deterministic(client):
    """C19: seeded catalog (ids/prices) is stable across a fresh reseed and testuser authenticates."""
    first = {p["id"]: p["price"] for p in get_products(client)}

    module = importlib.reload(importlib.import_module("reference_app.backend.app"))
    from fastapi.testclient import TestClient

    with TestClient(module.app) as c2:
        # seeded account still authenticates against a freshly-seeded DB (ties to C3)
        assert c2.get("/products", auth=VALID_AUTH).status_code == 200
        second = {p["id"]: p["price"] for p in get_products(c2)}

    assert first == second, "seed must reproduce identical product ids/prices across fresh starts"


# ---------------------------------------------------------------------- OpenAPI (C20-C21)

def test_c20_openapi_served_without_auth(client):
    """C20: GET /openapi.json -> 200 valid OpenAPI doc (openapi version + paths), no auth needed."""
    r = client.get("/openapi.json")  # deliberately no credentials
    assert r.status_code == 200, f"/openapi.json must be public, got {r.status_code}"
    doc = r.json()
    assert isinstance(doc.get("openapi"), str) and doc["openapi"], "missing openapi version string"
    assert isinstance(doc.get("paths"), dict), "OpenAPI doc must have a paths object"


def test_c21_openapi_documents_shop_routes(client):
    """C21: OpenAPI paths document /products, /cart, /cart/items, /checkout, /orders/{id}."""
    doc = client.get("/openapi.json").json()
    paths = doc.get("paths", {})
    for required in ["/products", "/cart", "/cart/items", "/checkout"]:
        assert required in paths, f"OpenAPI must document {required}; paths: {sorted(paths)}"
    # order route is path-templated; accept any single-parameter template name
    assert any(p.startswith("/orders/{") and p.endswith("}") for p in paths), (
        f"OpenAPI must document a templated /orders/{{id}} route; paths: {sorted(paths)}"
    )


# ------------------------------------------------------------------ Launchability (C22)

def test_c22_binding_asgi_import_path(app_obj):
    """C22: app is importable at the binding path reference_app.backend.app:app (ASGI callable)."""
    import reference_app.backend.app as module

    assert module.app is app_obj
    # ASGI apps are callable (Starlette/FastAPI instances qualify).
    assert callable(app_obj), "the exported `app` must be an ASGI application object"


def test_c22_fresh_start_serves_full_api(client):
    """C22: once up, a freshly-seeded app serves the full documented surface end-to-end."""
    products = get_products(client)
    pid = products[0]["id"]
    assert client.post(
        "/cart/items", json={"product_id": pid, "quantity": 1}, auth=VALID_AUTH
    ).status_code in CREATED_OK
    order = client.post("/checkout", auth=VALID_AUTH).json()
    got = client.get(f"/orders/{order['id']}", auth=VALID_AUTH)
    assert got.status_code == 200
    assert client.get("/openapi.json").status_code == 200

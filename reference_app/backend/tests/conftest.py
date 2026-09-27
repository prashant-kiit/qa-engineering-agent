# Shared fixtures/helpers for the p0-shop-backend acceptance suite (TDD red).
#
# The Tester drives the app WITHOUT reading its implementation, against the binding
# contract in .harness/tasks/p0-shop-backend.md:
#   - ASGI import path (binding):   reference_app.backend.app:app
#   - Seeded Basic-Auth account:    testuser / testpass
#
# Isolation: each test reloads the app module (re-triggering the deterministic seed)
# and drains any residual cart via checkout, so cart-state tests are order-independent
# regardless of whether the DB is in-memory or a file.

import importlib

import pytest

# NOTE: fastapi provides starlette's TestClient (sync, httpx-backed). Importing it here
# is fine once the dev group is installed; the app import below is what is expected to
# fail (no implementation yet) — the legitimate TDD-red reason.
from fastapi.testclient import TestClient

# Binding seeded credentials (exact values per spec Interfaces § Auth scheme).
VALID_AUTH = ("testuser", "testpass")
WRONG_AUTH = ("testuser", "wrongpass")
WRONG_USER = ("nosuchuser", "testpass")

# Endpoints requiring Basic auth (spec Base URL / paths table).
PROTECTED_GET = ["/products", "/cart"]


def _import_app_module():
    """Import (or reload) the binding ASGI module so a fresh deterministic seed runs."""
    import reference_app.backend.app as app_module  # binding import path

    return importlib.reload(app_module)


@pytest.fixture
def app_obj():
    """The ASGI application object exposed at reference_app.backend.app:app."""
    module = _import_app_module()
    assert hasattr(module, "app"), (
        "reference_app.backend.app must expose an ASGI `app` object "
        "(binding import path `reference_app.backend.app:app`)."
    )
    return module.app


@pytest.fixture
def client(app_obj):
    """A fresh in-process HTTP client bound to the seeded app (entering triggers startup/lifespan)."""
    with TestClient(app_obj) as c:
        _ensure_empty_cart(c)
        yield c


def _ensure_empty_cart(c):
    """Drain testuser's cart so cart-state assertions are independent of prior tests."""
    r = c.get("/cart", auth=VALID_AUTH)
    if r.status_code == 200:
        body = r.json()
        if body.get("items"):
            c.post("/checkout", auth=VALID_AUTH)


def get_products(c):
    r = c.get("/products", auth=VALID_AUTH)
    assert r.status_code == 200, f"/products should return 200 for valid auth, got {r.status_code}"
    return r.json()


def product_price(products, product_id):
    for p in products:
        if p["id"] == product_id:
            return p["price"]
    raise AssertionError(f"product id {product_id!r} not present in catalog")


def expected_total(products, lines):
    """Σ over lines of price × quantity, using the seeded prices from /products.

    `lines` is an iterable of (product_id, quantity).
    """
    return sum(product_price(products, pid) * qty for pid, qty in lines)


def find_absent_product_id(products):
    """Return an id guaranteed NOT to reference any seeded product (int or str schema)."""
    ids = [p["id"] for p in products]
    if all(isinstance(i, int) for i in ids):
        return max(ids) + 100000
    return "definitely-not-a-real-product-id-zzz"


def find_absent_order_id(products):
    """An order id that should not exist on a freshly-seeded DB (no orders yet)."""
    ids = [p["id"] for p in products]
    if all(isinstance(i, int) for i in ids):
        return 987654321
    return "definitely-not-a-real-order-id-zzz"


def cart_qty_for(cart, product_id):
    """Total quantity reported for a product across the cart's line items."""
    return sum(
        item["quantity"] for item in cart.get("items", []) if item["product_id"] == product_id
    )

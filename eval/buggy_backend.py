"""Eval bug-catalog backend launcher — the non-invasive injected-bug overlay.

This module is **not** part of the clean application. It is imported only by the
eval harness (``eval/score.py`` / the ``playwright.eval.config.ts`` ``webServer``)
to launch the reference backend for a **browser / API** end-to-end run under a
single injected fault. It follows the exact pattern of
``reference_app/e2e/smoke_backend.py``:

1. It imports the **clean** backend (``reference_app.backend.app``) unchanged and
   reuses its ASGI ``app`` object. The clean source is never modified.
2. It adds launch-time ``CORSMiddleware`` (additive response headers only) so the
   Vite frontend can call the backend cross-origin with an ``Authorization``
   header. Status codes and JSON bodies stay byte-for-byte identical to clean.
3. Selected by the single ``EVAL_BUG`` environment variable it applies **exactly
   one** fault, by dropping the relevant clean route and re-registering a faulty
   overlay in its place. With ``EVAL_BUG`` unset or ``none`` **no** fault is
   active and the launched app behaves identically to the clean backend.

``EVAL_BUG`` values (exact strings):
  * unset / ``none``     -> clean (no fault)
  * ``checkout_total``   -> ``POST /checkout`` reports a WRONG order total
  * ``cart_quantity``    -> ``POST /cart/items`` does NOT accumulate on repeat add
  * ``order_auth_bypass``-> ``GET /orders/{id}`` no longer enforces authentication

Unknown values are treated as clean (documented in ``eval/README.md``). This is a
separate selector from unit 5's ``SMOKE_FAULT``; the two are never overloaded.

Launch shape (Interfaces):
    uv run uvicorn buggy_backend:app --app-dir eval --host 127.0.0.1 --port 8000
with ``EVAL_BUG`` passed through in the environment.
"""

from __future__ import annotations

import os
import pathlib
import sys

# Make the repo root importable so the clean backend package resolves regardless
# of uvicorn's --app-dir (which points at ``eval`` for this module).
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from fastapi import Depends, HTTPException, status  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from reference_app.backend import app as backend  # noqa: E402

# Reuse the clean ASGI app object unchanged.
app = backend.app

# Launch-time CORS so the browser can call the backend cross-origin. Additive
# headers only; does not alter any endpoint's status code or JSON body.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# The single injected fault selector. Unknown / unset / "none" -> clean.
_EVAL_BUG = os.environ.get("EVAL_BUG", "").strip() or "none"

# Non-zero offset so a wrong checkout total can never accidentally equal the truth.
_FAULT_TOTAL_OFFSET = 100.0


def _drop_route(path: str, method: str) -> None:
    """Remove the clean route matching (path, method) so an overlay can replace it."""
    app.router.routes = [
        route
        for route in app.router.routes
        if not (
            getattr(route, "path", None) == path
            and method in getattr(route, "methods", set())
        )
    ]


# --------------------------------------------------------------------------- faults

if _EVAL_BUG == "checkout_total":
    # Bug (a): POST /checkout returns a created order whose `total` is WRONG.
    # The persisted order/cart maths stay correct (line items, ids, prices, cart
    # total); only the checkout response `total` is offset, so it never equals
    # Σ price × quantity. Everything else stays clean.
    _clean_checkout = backend.checkout
    _drop_route("/checkout", "POST")

    @app.post("/checkout", response_model=backend.Order)
    def buggy_checkout(user: str = Depends(backend.current_user)) -> backend.Order:
        order = _clean_checkout(user=user)
        return backend.Order(
            id=order.id,
            items=order.items,
            total=order.total + _FAULT_TOTAL_OFFSET,
        )

elif _EVAL_BUG == "cart_quantity":
    # Bug (b): POST /cart/items for a product ALREADY in the cart does NOT
    # accumulate quantity — the repeat add is silently ignored, so the reported
    # quantity stays at the first add instead of summing. The first add of a
    # product still works; only the increment-on-repeat is defective.
    _drop_route("/cart/items", "POST")

    @app.post("/cart/items", response_model=backend.Cart)
    def buggy_add_to_cart(
        payload: backend.AddItem, user: str = Depends(backend.current_user)
    ) -> backend.Cart:
        exists = backend._db.execute(
            "SELECT 1 FROM products WHERE id = ?", (payload.product_id,)
        ).fetchone()
        if exists is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Unknown product"
            )

        row = backend._db.execute(
            "SELECT quantity FROM cart_items WHERE username = ? AND product_id = ?",
            (user, payload.product_id),
        ).fetchone()
        if row is None:
            # First add works exactly as clean.
            backend._db.execute(
                "INSERT INTO cart_items (username, product_id, quantity) VALUES (?, ?, ?)",
                (user, payload.product_id, payload.quantity),
            )
            backend._db.commit()
        # BUG: repeat add is a no-op — quantity is NOT incremented.
        return backend._cart_for(user)

elif _EVAL_BUG == "order_auth_bypass":
    # Bug (c): GET /orders/{id} no longer enforces authentication — a request with
    # missing or invalid Basic credentials returns HTTP 200 with the order body
    # instead of 401. Only this endpoint's auth is dropped; all other endpoints
    # (including POST /checkout) still require valid credentials.
    _drop_route("/orders/{order_id}", "GET")

    @app.get("/orders/{order_id}", response_model=backend.Order)
    def buggy_get_order(order_id: int) -> backend.Order:  # no auth dependency
        order = backend._db.execute(
            "SELECT id, total FROM orders WHERE id = ?", (order_id,)
        ).fetchone()
        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
            )
        item_rows = backend._db.execute(
            "SELECT product_id, quantity FROM order_items WHERE order_id = ? ORDER BY product_id",
            (order_id,),
        ).fetchall()
        return backend.Order(
            id=order["id"],
            items=[
                backend.CartLine(product_id=r["product_id"], quantity=r["quantity"])
                for r in item_rows
            ],
            total=order["total"],
        )

# else: _EVAL_BUG in {"none", <unknown>} -> clean app, only CORS added.

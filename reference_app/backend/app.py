"""Reference shop backend — FastAPI + SQLite.

Binding ASGI import path: ``reference_app.backend.app:app``.

A deliberately small, *clean* e-commerce API used as the system-under-test for the
QA agent's Playwright/API suites. On import/startup it (re)creates a SQLite database
and seeds a fixed product catalog plus the ``testuser`` / ``testpass`` account, so a
fresh run is immediately testable and reproducible.

Endpoints (all Basic-Auth except ``/openapi.json``):
    GET  /products      -> seeded catalog
    GET  /cart          -> current user's cart (items + total)
    POST /cart/items    -> add product+quantity (cumulative)
    POST /checkout      -> create an order from the cart, then empty it
    GET  /orders/{id}   -> retrieve a previously created order
"""

from __future__ import annotations

import os
import secrets
import sqlite3
from pathlib import Path
from typing import List

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field

# --------------------------------------------------------------------------- config / seed

# SQLite file lives next to this module; `*.db` is git-ignored. A fresh process resets
# and reseeds it so runs are deterministic (see reseed on import below).
DB_PATH = Path(__file__).with_name("shop.db")

# Binding seeded credentials (exact values per spec).
SEED_USERS = {
    "testuser": "testpass",
}

# Fixed, deterministic catalog: (id, name, price). Stable ids/prices across restarts.
SEED_PRODUCTS = [
    (1, "Aluminum Widget", 9.99),
    (2, "Titanium Gadget", 19.50),
    (3, "Carbon Gizmo", 4.25),
    (4, "Copper Doohickey", 100.00),
    (5, "Silicon Thingamajig", 0.99),
]


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _init_and_seed() -> sqlite3.Connection:
    """Create a fresh schema and load the deterministic seed. Idempotent per process."""
    # Reset the DB file so a fresh import reproduces exactly the seeded state.
    if DB_PATH.exists():
        try:
            DB_PATH.unlink()
        except OSError:
            pass

    conn = _connect()
    conn.executescript(
        """
        CREATE TABLE users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        );
        CREATE TABLE products (
            id    INTEGER PRIMARY KEY,
            name  TEXT NOT NULL,
            price REAL NOT NULL
        );
        CREATE TABLE cart_items (
            username   TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            quantity   INTEGER NOT NULL,
            PRIMARY KEY (username, product_id)
        );
        CREATE TABLE orders (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            total    REAL NOT NULL
        );
        CREATE TABLE order_items (
            order_id   INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity   INTEGER NOT NULL
        );
        """
    )
    conn.executemany(
        "INSERT INTO users (username, password) VALUES (?, ?)",
        list(SEED_USERS.items()),
    )
    conn.executemany(
        "INSERT INTO products (id, name, price) VALUES (?, ?, ?)",
        SEED_PRODUCTS,
    )
    conn.commit()
    return conn


# One shared connection per process, created + seeded at import time so the app is
# immediately testable via the binding ASGI import path.
_db = _init_and_seed()


# --------------------------------------------------------------------------- schemas

class Product(BaseModel):
    id: int
    name: str
    price: float


class CartLine(BaseModel):
    product_id: int
    quantity: int


class Cart(BaseModel):
    items: List[CartLine]
    total: float


class AddItem(BaseModel):
    product_id: int
    quantity: int = Field(ge=1)


class Order(BaseModel):
    id: int
    items: List[CartLine]
    total: float


# --------------------------------------------------------------------------- auth

security = HTTPBasic(auto_error=True)


def current_user(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    """Validate Basic credentials against the seeded users; else 401 (WWW-Authenticate: Basic)."""
    expected = SEED_USERS.get(credentials.username)
    ok = expected is not None and secrets.compare_digest(credentials.password, expected)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


# --------------------------------------------------------------------------- helpers

def _cart_for(username: str) -> Cart:
    rows = _db.execute(
        "SELECT product_id, quantity FROM cart_items WHERE username = ? ORDER BY product_id",
        (username,),
    ).fetchall()
    items = [CartLine(product_id=r["product_id"], quantity=r["quantity"]) for r in rows]
    total = _total_for_lines([(r["product_id"], r["quantity"]) for r in rows])
    return Cart(items=items, total=total)


def _total_for_lines(lines) -> float:
    total = 0.0
    for product_id, quantity in lines:
        row = _db.execute("SELECT price FROM products WHERE id = ?", (product_id,)).fetchone()
        if row is not None:
            total += row["price"] * quantity
    return total


# --------------------------------------------------------------------------- app / routes

app = FastAPI(title="Reference Shop API", version="0.1.0")


@app.get("/products", response_model=List[Product])
def list_products(_: str = Depends(current_user)) -> List[Product]:
    rows = _db.execute("SELECT id, name, price FROM products ORDER BY id").fetchall()
    return [Product(id=r["id"], name=r["name"], price=r["price"]) for r in rows]


@app.get("/cart", response_model=Cart)
def get_cart(user: str = Depends(current_user)) -> Cart:
    return _cart_for(user)


@app.post("/cart/items", response_model=Cart)
def add_to_cart(payload: AddItem, user: str = Depends(current_user)) -> Cart:
    exists = _db.execute(
        "SELECT 1 FROM products WHERE id = ?", (payload.product_id,)
    ).fetchone()
    if exists is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown product")

    row = _db.execute(
        "SELECT quantity FROM cart_items WHERE username = ? AND product_id = ?",
        (user, payload.product_id),
    ).fetchone()
    if row is None:
        _db.execute(
            "INSERT INTO cart_items (username, product_id, quantity) VALUES (?, ?, ?)",
            (user, payload.product_id, payload.quantity),
        )
    else:
        _db.execute(
            "UPDATE cart_items SET quantity = quantity + ? WHERE username = ? AND product_id = ?",
            (payload.quantity, user, payload.product_id),
        )
    _db.commit()
    return _cart_for(user)


@app.post("/checkout", response_model=Order)
def checkout(user: str = Depends(current_user)) -> Order:
    rows = _db.execute(
        "SELECT product_id, quantity FROM cart_items WHERE username = ? ORDER BY product_id",
        (user,),
    ).fetchall()
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot checkout an empty cart"
        )

    lines = [(r["product_id"], r["quantity"]) for r in rows]
    total = _total_for_lines(lines)

    cur = _db.execute(
        "INSERT INTO orders (username, total) VALUES (?, ?)", (user, total)
    )
    order_id = cur.lastrowid
    _db.executemany(
        "INSERT INTO order_items (order_id, product_id, quantity) VALUES (?, ?, ?)",
        [(order_id, pid, qty) for pid, qty in lines],
    )
    # Empty the cart on successful checkout.
    _db.execute("DELETE FROM cart_items WHERE username = ?", (user,))
    _db.commit()

    return Order(
        id=order_id,
        items=[CartLine(product_id=pid, quantity=qty) for pid, qty in lines],
        total=total,
    )


@app.get("/orders/{order_id}", response_model=Order)
def get_order(order_id: int, user: str = Depends(current_user)) -> Order:
    order = _db.execute(
        "SELECT id, total FROM orders WHERE id = ? AND username = ?", (order_id, user)
    ).fetchone()
    if order is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    item_rows = _db.execute(
        "SELECT product_id, quantity FROM order_items WHERE order_id = ? ORDER BY product_id",
        (order_id,),
    ).fetchall()
    return Order(
        id=order["id"],
        items=[CartLine(product_id=r["product_id"], quantity=r["quantity"]) for r in item_rows],
        total=order["total"],
    )


if __name__ == "__main__":  # pragma: no cover - convenience launcher
    import uvicorn

    uvicorn.run(
        "reference_app.backend.app:app",
        host=os.environ.get("SHOP_HOST", "127.0.0.1"),
        port=int(os.environ.get("SHOP_PORT", "8000")),
        reload=False,
    )

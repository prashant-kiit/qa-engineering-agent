"""Phase-0 smoke backend launcher — the app the Playwright ``webServer`` runs.

This module is **not** part of the clean application and is imported only by the
smoke's ``webServer`` (never on the app's normal production path). It exists to
launch the reference backend for a **browser** end-to-end run, which needs two
launch-time concerns the in-process/unit tests do not:

1. **CORS** — the smoke drives the Vite frontend (origin ``http://127.0.0.1:5173``)
   which calls the backend cross-origin (``http://127.0.0.1:8000``) with an
   ``Authorization`` header. That is a non-simple request, so the browser sends a
   CORS preflight. The clean backend ships no CORS middleware (its unit tests are
   in-process / same-origin), so this launcher adds ``CORSMiddleware``. This is
   purely additive response headers — the API's status codes and JSON bodies are
   byte-for-byte identical to the clean app; no business logic changes.

2. **The single ``SMOKE_FAULT`` toggle** — when ``SMOKE_FAULT=1`` this launcher
   overlays **exactly one** fault: the ``POST /checkout`` response reports a
   *wrong* order total (true total + a fixed offset). The persisted order and cart
   maths stay correct, so the pre-checkout ``cart-total`` is still right; only the
   confirmation ``order-total`` (rendered verbatim by the UI from the checkout
   response) is wrong, so the smoke's ``order-total == cart-total`` assertion fails
   and the run goes red. With ``SMOKE_FAULT`` unset the app behaves exactly as the
   clean backend and the smoke is green.

The clean backend source (``reference_app/backend/app.py``) is imported unchanged;
this file is the only place the smoke's launch concerns live.
"""

from __future__ import annotations

import os
import pathlib
import sys

# Make the repo root importable so the clean backend package resolves regardless
# of uvicorn's --app-dir (which points at reference_app/e2e for this module).
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from fastapi import Depends  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from reference_app.backend import app as backend  # noqa: E402

# Reuse the clean ASGI app object unchanged.
app = backend.app

# Launch-time CORS so the browser can call the backend cross-origin. Additive
# headers only; does not alter any endpoint's behavior. Echoes the request origin
# (regex) so credentialed/authorized requests are permitted.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# The single injected fault, active only under SMOKE_FAULT=1. Non-zero offset so
# the wrong total can never accidentally equal the truth.
_FAULT_TOTAL_OFFSET = 100.0
_SMOKE_FAULT = os.environ.get("SMOKE_FAULT", "").strip() == "1"

if _SMOKE_FAULT:
    _clean_checkout = backend.checkout

    # Drop the clean POST /checkout route so the faulty overlay serves instead.
    app.router.routes = [
        route
        for route in app.router.routes
        if not (
            getattr(route, "path", None) == "/checkout"
            and "POST" in getattr(route, "methods", set())
        )
    ]

    @app.post("/checkout", response_model=backend.Order)
    def buggy_checkout(user: str = Depends(backend.current_user)) -> backend.Order:
        """Run the clean checkout, then surface a WRONG total in the response only."""
        order = _clean_checkout(user=user)
        return backend.Order(
            id=order.id,
            items=order.items,
            total=order.total + _FAULT_TOTAL_OFFSET,
        )

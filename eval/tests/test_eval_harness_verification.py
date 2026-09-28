"""Harness-verification tests for unit ``p0-eval-harness`` (TDD red — written BEFORE any
implementation and WITHOUT reading the eval implementation source).

These are the **Tester's own verification tests** — distinct from the Developer's product
deliverables (``eval/buggy_backend.py``, ``eval/score.py``, the baseline TS-Playwright suite,
and the ``make eval`` / ``make dev`` wiring). Each test maps to an enumerated acceptance
criterion (C1..C16) in ``.harness/tasks/p0-eval-harness.md`` and asserts it from the outside:

  * C1-C5   Bug catalog HTTP behavior — launch the ``eval/`` bug-catalog variant per ``EVAL_BUG``
            value (pinned shape: ``uv run uvicorn buggy_backend:app --app-dir eval ...`` with
            ``EVAL_BUG`` in env) and assert observable behavior over HTTP.
  * C6-C8   Baseline behavior — invoke the developer's documented baseline command against each
            variant and assert exit codes (clean -> 0, each buggy variant -> non-zero genuine fail).
  * C9-C13, C15  Scorer contract — run ``eval/score.py --reruns 2 --json`` and assert the four
            metric names, the ``metrics`` JSON object, and the exit-code sanity gate.
  * C14, C16  make wiring — ``make eval`` runs end-to-end + prints metrics + propagates exit;
            ``make dev`` launches the clean app (reachable /openapi.json on 8000 + UI on 5173,
            no fault).

Contracts (binding) come from the task spec + the p0-shop-backend / p0-playwright-smoke specs:
  * Clean backend seed: 5 products, Basic auth testuser/testpass; total = Σ price × quantity;
    repeat add-to-cart increments; every order endpoint requires auth (401 without).
  * Ports: backend 8000, frontend 5173. Launcher home: ``eval/buggy_backend.py`` (ASGI ``app``).
  * ``EVAL_BUG`` values: unset/``none`` (clean), ``checkout_total``, ``cart_quantity``,
    ``order_auth_bypass``.

Run:  uv run pytest eval/tests/test_eval_harness_verification.py -q
"""

from __future__ import annotations

import contextlib
import json
import os
import pathlib
import signal
import subprocess
import time

import httpx
import pytest

# --------------------------------------------------------------------------- constants / paths

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
E2E_DIR = REPO_ROOT / "reference_app" / "e2e"
EVAL_DIR = REPO_ROOT / "eval"

BUGGY_LAUNCHER = EVAL_DIR / "buggy_backend.py"
SCORE_PY = EVAL_DIR / "score.py"
EVAL_PW_CONFIG = E2E_DIR / "playwright.eval.config.ts"  # pinned example config (Interfaces)

VALID_AUTH = ("testuser", "testpass")
INVALID_AUTH = ("testuser", "wrongpass")

BACKEND_PORT = 8000
CLEAN_REF_PORT = 8001  # a directly-launched clean backend, for byte-parity comparison
FRONTEND_PORT = 5173

# The four pinned metric names (criterion 13 / Interfaces).
METRIC_NAMES = (
    "bug_catch_rate",
    "false_positive_rate",
    "flake_rate",
    "assertion_meaningfulness_rate",
)

# EVAL_BUG variant identifiers (Interfaces § Env selector).
BUGGY_VARIANTS = ("checkout_total", "cart_quantity", "order_auth_bypass")


# --------------------------------------------------------------------------- process helpers


def _kill_port(port: int) -> None:
    """Best-effort kill of anything listening on ``port`` so launches are collision-free."""
    try:
        out = subprocess.run(
            ["lsof", "-ti", f"tcp:{port}"], capture_output=True, text=True, timeout=10
        ).stdout.strip()
    except Exception:
        return
    for pid in out.split():
        with contextlib.suppress(Exception):
            os.kill(int(pid), signal.SIGKILL)


def _terminate(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    with contextlib.suppress(Exception):
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    try:
        proc.wait(timeout=10)
    except Exception:
        with contextlib.suppress(Exception):
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)


def _drain(proc: subprocess.Popen) -> str:
    with contextlib.suppress(Exception):
        return proc.communicate(timeout=5)[0] or ""
    return ""


@pytest.fixture(autouse=True, scope="session")
def _clear_ports_at_session_start():
    for p in (BACKEND_PORT, CLEAN_REF_PORT, FRONTEND_PORT):
        _kill_port(p)
    yield


@contextlib.contextmanager
def launch_variant(eval_bug, port: int = BACKEND_PORT):
    """Launch the ``eval/`` bug-catalog variant on ``port`` with ``EVAL_BUG=eval_bug``.

    Uses the pinned launch shape. ``eval_bug=None`` means the selector is UNSET (clean).
    Fails fast with a clear message if the launcher never becomes ready (e.g. because
    ``eval/buggy_backend.py`` does not exist yet — the legitimate TDD-red reason).
    """
    _kill_port(port)
    env = os.environ.copy()
    if eval_bug is None:
        env.pop("EVAL_BUG", None)
    else:
        env["EVAL_BUG"] = eval_bug
    cmd = [
        "uv", "run", "uvicorn", "buggy_backend:app",
        "--app-dir", "eval", "--host", "127.0.0.1", "--port", str(port),
    ]
    proc = subprocess.Popen(
        cmd, cwd=str(REPO_ROOT), env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        start_new_session=True,
    )
    base = f"http://127.0.0.1:{port}"
    try:
        deadline = time.time() + 25
        while time.time() < deadline:
            if proc.poll() is not None:
                raise AssertionError(
                    f"eval bug-catalog launcher (EVAL_BUG={eval_bug!r}) exited before becoming "
                    f"ready — expected {BUGGY_LAUNCHER} to expose an ASGI `app`.\n"
                    f"--- launcher output ---\n{_drain(proc)}"
                )
            try:
                r = httpx.get(f"{base}/openapi.json", timeout=2.0)
                if r.status_code == 200:
                    break
            except Exception:
                pass
            time.sleep(0.4)
        else:
            raise AssertionError(
                f"eval bug-catalog launcher (EVAL_BUG={eval_bug!r}) not ready on {base} within 25s "
                f"(expected {BUGGY_LAUNCHER}). This unit's launcher does not exist yet.\n"
                f"--- launcher output ---\n{_drain(proc)}"
            )
        yield base
    finally:
        _terminate(proc)
        _kill_port(port)


@contextlib.contextmanager
def launch_clean_backend(port: int = CLEAN_REF_PORT):
    """Launch the pristine clean backend directly (for byte-parity comparison)."""
    _kill_port(port)
    cmd = [
        "uv", "run", "uvicorn", "reference_app.backend.app:app",
        "--host", "127.0.0.1", "--port", str(port),
    ]
    proc = subprocess.Popen(
        cmd, cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        start_new_session=True,
    )
    base = f"http://127.0.0.1:{port}"
    try:
        deadline = time.time() + 25
        while time.time() < deadline:
            if proc.poll() is not None:
                raise AssertionError(f"clean backend failed to start:\n{_drain(proc)}")
            try:
                if httpx.get(f"{base}/openapi.json", timeout=2.0).status_code == 200:
                    break
            except Exception:
                pass
            time.sleep(0.4)
        else:
            raise AssertionError(f"clean backend not ready on {base} within 25s:\n{_drain(proc)}")
        yield base
    finally:
        _terminate(proc)
        _kill_port(port)


# --------------------------------------------------------------------------- domain helpers


def _products(base: str) -> list:
    r = httpx.get(f"{base}/products", auth=VALID_AUTH, timeout=10.0)
    assert r.status_code == 200, f"/products should be 200 with valid auth, got {r.status_code}"
    return r.json()


def _price_of(products: list, product_id) -> float:
    for p in products:
        if p["id"] == product_id:
            return p["price"]
    raise AssertionError(f"product id {product_id!r} not in catalog")


def _first_product_id(products: list):
    return products[0]["id"]


def _clear_cart(base: str) -> None:
    """Drain the cart via checkout so cart-state assertions are independent."""
    c = httpx.get(f"{base}/cart", auth=VALID_AUTH, timeout=10.0)
    if c.status_code == 200 and c.json().get("items"):
        httpx.post(f"{base}/checkout", auth=VALID_AUTH, timeout=10.0)


def _add(base: str, product_id, quantity: int):
    return httpx.post(
        f"{base}/cart/items",
        json={"product_id": product_id, "quantity": quantity},
        auth=VALID_AUTH,
        timeout=10.0,
    )


def _cart_qty(cart: dict, product_id) -> int:
    return sum(
        i["quantity"] for i in cart.get("items", []) if i["product_id"] == product_id
    )


def _create_order(base: str, product_id, quantity: int = 1) -> dict:
    _clear_cart(base)
    r = _add(base, product_id, quantity)
    assert r.status_code in (200, 201), f"add-to-cart failed: {r.status_code} {r.text}"
    co = httpx.post(f"{base}/checkout", auth=VALID_AUTH, timeout=10.0)
    assert co.status_code in (200, 201), f"checkout failed: {co.status_code} {co.text}"
    return co.json()


# =========================================================================================
# C1 + C5(clean) — Clean variant (EVAL_BUG unset / none) satisfies every clean invariant
# =========================================================================================


@pytest.mark.parametrize("selector", [None, "none"])
def test_c1_clean_variant_order_total_correct(selector):
    """C1: clean variant — checkout order total == Σ price × quantity."""
    with launch_variant(selector) as base:
        products = _products(base)
        pid = _first_product_id(products)
        order = _create_order(base, pid, quantity=2)
        expected = _price_of(products, pid) * 2
        assert order["total"] == pytest.approx(expected), (
            f"clean variant (EVAL_BUG={selector!r}) order total {order['total']} "
            f"!= Σ price×qty {expected}"
        )


@pytest.mark.parametrize("selector", [None, "none"])
def test_c1_clean_variant_repeat_add_increments(selector):
    """C1: clean variant — adding the same product twice accumulates to quantity 2."""
    with launch_variant(selector) as base:
        products = _products(base)
        pid = _first_product_id(products)
        _clear_cart(base)
        _add(base, pid, 1)
        _add(base, pid, 1)
        cart = httpx.get(f"{base}/cart", auth=VALID_AUTH, timeout=10.0).json()
        assert _cart_qty(cart, pid) == 2, (
            f"clean variant (EVAL_BUG={selector!r}): repeat add should accumulate to qty 2, "
            f"got {_cart_qty(cart, pid)}"
        )


@pytest.mark.parametrize("selector", [None, "none"])
def test_c1_clean_variant_order_requires_auth(selector):
    """C1: clean variant — GET /orders/{id} without credentials returns 401."""
    with launch_variant(selector) as base:
        products = _products(base)
        order = _create_order(base, _first_product_id(products))
        r = httpx.get(f"{base}/orders/{order['id']}", timeout=10.0)  # no creds
        assert r.status_code == 401, (
            f"clean variant (EVAL_BUG={selector!r}): GET /orders/{{id}} without creds "
            f"should be 401, got {r.status_code}"
        )


def test_c1_clean_variant_products_byte_parity_with_clean_backend():
    """C1 (byte-parity, where feasible): the clean eval variant's /products response body is
    byte-for-byte identical to the pristine clean backend launched directly."""
    with launch_variant(None) as eval_base, launch_clean_backend() as clean_base:
        r_eval = httpx.get(f"{eval_base}/products", auth=VALID_AUTH, timeout=10.0)
        r_clean = httpx.get(f"{clean_base}/products", auth=VALID_AUTH, timeout=10.0)
        assert r_eval.status_code == r_clean.status_code == 200
        assert r_eval.text == r_clean.text, (
            "clean eval variant /products body differs from the pristine clean backend "
            "(clean path must be byte-for-byte identical)"
        )


# =========================================================================================
# C2 — checkout_total: order total is WRONG (!= Σ price×qty); other behavior stays clean
# =========================================================================================


def test_c2_checkout_total_order_total_is_wrong():
    """C2: EVAL_BUG=checkout_total — checkout order total does NOT equal Σ price × quantity."""
    with launch_variant("checkout_total") as base:
        products = _products(base)
        pid = _first_product_id(products)
        order = _create_order(base, pid, quantity=2)
        true_total = _price_of(products, pid) * 2
        assert order["total"] != pytest.approx(true_total), (
            f"checkout_total variant should report a WRONG order total, but got the correct "
            f"Σ price×qty = {true_total}"
        )


def test_c2_checkout_total_isolated_cart_and_auth_stay_clean():
    """C2/C5: under checkout_total, repeat-add still increments and order auth stays enforced
    (exactly one fault; the checkout-total fault does not activate a second fault)."""
    with launch_variant("checkout_total") as base:
        products = _products(base)
        pid = _first_product_id(products)
        _clear_cart(base)
        _add(base, pid, 1)
        _add(base, pid, 1)
        cart = httpx.get(f"{base}/cart", auth=VALID_AUTH, timeout=10.0).json()
        assert _cart_qty(cart, pid) == 2, "checkout_total must not break cart-quantity increment"
        order = _create_order(base, pid)
        r = httpx.get(f"{base}/orders/{order['id']}", timeout=10.0)  # no creds
        assert r.status_code == 401, "checkout_total must not bypass order-endpoint auth"


# =========================================================================================
# C3 — cart_quantity: repeat add does NOT accumulate (qty != 2 after adding twice)
# =========================================================================================


def test_c3_cart_quantity_repeat_add_does_not_accumulate():
    """C3: EVAL_BUG=cart_quantity — adding the same product twice does NOT report quantity 2."""
    with launch_variant("cart_quantity") as base:
        products = _products(base)
        pid = _first_product_id(products)
        _clear_cart(base)
        r1 = _add(base, pid, 1)
        assert r1.status_code in (200, 201), f"first add failed: {r1.status_code} {r1.text}"
        _add(base, pid, 1)
        cart = httpx.get(f"{base}/cart", auth=VALID_AUTH, timeout=10.0).json()
        assert _cart_qty(cart, pid) != 2, (
            f"cart_quantity variant should NOT accumulate repeat adds, but reported qty 2 "
            f"for product {pid}"
        )


def test_c3_cart_quantity_isolated_auth_stays_clean():
    """C3/C5: under cart_quantity, the order endpoint still enforces auth (fault isolated)."""
    with launch_variant("cart_quantity") as base:
        products = _products(base)
        order = _create_order(base, _first_product_id(products))
        r = httpx.get(f"{base}/orders/{order['id']}", timeout=10.0)  # no creds
        assert r.status_code == 401, "cart_quantity must not bypass order-endpoint auth"


# =========================================================================================
# C4 — order_auth_bypass: GET /orders/{id} returns 200 with missing/invalid credentials
# =========================================================================================


def test_c4_order_auth_bypass_missing_credentials_returns_200():
    """C4: EVAL_BUG=order_auth_bypass — GET /orders/{id} with NO credentials returns 200."""
    with launch_variant("order_auth_bypass") as base:
        products = _products(base)
        order = _create_order(base, _first_product_id(products))  # creation still uses valid auth
        r = httpx.get(f"{base}/orders/{order['id']}", timeout=10.0)  # no creds
        assert r.status_code == 200, (
            f"order_auth_bypass variant: GET /orders/{{id}} without creds should return 200, "
            f"got {r.status_code}"
        )


def test_c4_order_auth_bypass_invalid_credentials_returns_200():
    """C4: order_auth_bypass — GET /orders/{id} with INVALID credentials returns 200."""
    with launch_variant("order_auth_bypass") as base:
        products = _products(base)
        order = _create_order(base, _first_product_id(products))
        r = httpx.get(f"{base}/orders/{order['id']}", auth=INVALID_AUTH, timeout=10.0)
        assert r.status_code == 200, (
            f"order_auth_bypass variant: GET /orders/{{id}} with invalid creds should return 200, "
            f"got {r.status_code}"
        )


def test_c4_order_auth_bypass_isolated_total_and_cart_stay_clean():
    """C4/C5: under order_auth_bypass, checkout total is correct and repeat-add increments
    (only the order-endpoint auth is faulted — exactly one fault)."""
    with launch_variant("order_auth_bypass") as base:
        products = _products(base)
        pid = _first_product_id(products)
        order = _create_order(base, pid, quantity=2)
        assert order["total"] == pytest.approx(_price_of(products, pid) * 2), (
            "order_auth_bypass must not corrupt the order total"
        )
        _clear_cart(base)
        _add(base, pid, 1)
        _add(base, pid, 1)
        cart = httpx.get(f"{base}/cart", auth=VALID_AUTH, timeout=10.0).json()
        assert _cart_qty(cart, pid) == 2, "order_auth_bypass must not break cart-quantity increment"


# =========================================================================================
# C5 — exactly one fault per value (cross-variant divergence proof)
# =========================================================================================


def test_c5_each_buggy_variant_diverges_from_clean_on_its_own_axis():
    """C5: each EVAL_BUG value activates exactly one distinct, observable fault — verified by
    each buggy variant diverging from clean on precisely its own axis (covered per-variant by
    C2/C3/C4 above; this asserts they are three DISTINCT faults, not aliases)."""
    observations = {}
    for selector in ("none", *BUGGY_VARIANTS):
        with launch_variant(None if selector == "none" else selector) as base:
            products = _products(base)
            pid = _first_product_id(products)
            # total axis
            order = _create_order(base, pid, quantity=2)
            true_total = _price_of(products, pid) * 2
            total_wrong = order["total"] != pytest.approx(true_total)
            # cart-quantity axis
            _clear_cart(base)
            _add(base, pid, 1)
            _add(base, pid, 1)
            cart = httpx.get(f"{base}/cart", auth=VALID_AUTH, timeout=10.0).json()
            qty_wrong = _cart_qty(cart, pid) != 2
            # auth axis
            order2 = _create_order(base, pid)
            auth_bypassed = (
                httpx.get(f"{base}/orders/{order2['id']}", timeout=10.0).status_code == 200
            )
            observations[selector] = (total_wrong, qty_wrong, auth_bypassed)

    assert observations["none"] == (False, False, False), (
        f"clean variant showed a fault: {observations['none']}"
    )
    assert observations["checkout_total"] == (True, False, False), (
        f"checkout_total should fault only the total axis, saw {observations['checkout_total']}"
    )
    assert observations["cart_quantity"] == (False, True, False), (
        f"cart_quantity should fault only the cart-quantity axis, saw {observations['cart_quantity']}"
    )
    assert observations["order_auth_bypass"] == (False, False, True), (
        f"order_auth_bypass should fault only the auth axis, saw {observations['order_auth_bypass']}"
    )


# =========================================================================================
# C6-C8 — baseline suite behavior (invoked, not authored, by the Tester)
# =========================================================================================


def _run_baseline(eval_bug, timeout: int = 300) -> subprocess.CompletedProcess:
    """Run the developer's documented baseline command against the given variant.

    Documented invocation (Interfaces § Baseline invocation): from ``reference_app/e2e/``,
    ``npx playwright test --config playwright.eval.config.ts`` with ``EVAL_BUG`` in env
    (unset/``none`` = clean).
    """
    _kill_port(BACKEND_PORT)
    _kill_port(FRONTEND_PORT)
    env = os.environ.copy()
    if eval_bug in (None, "none"):
        env.pop("EVAL_BUG", None)
    else:
        env["EVAL_BUG"] = eval_bug
    return subprocess.run(
        ["npx", "playwright", "test", "--config", "playwright.eval.config.ts"],
        cwd=str(E2E_DIR), env=env,
        capture_output=True, text=True, timeout=timeout,
    )


def test_c8_baseline_eval_config_exists():
    """C8: the baseline is variant-selectable via a documented Playwright config; the pinned
    eval config must exist so the baseline can target a chosen EVAL_BUG variant."""
    assert EVAL_PW_CONFIG.exists(), (
        f"baseline eval Playwright config missing at {EVAL_PW_CONFIG} — the baseline suite is "
        f"not variant-selectable yet"
    )


def test_c6_baseline_passes_on_clean():
    """C6: the baseline suite passes (exit 0) against the clean variant."""
    assert EVAL_PW_CONFIG.exists(), f"baseline eval config missing at {EVAL_PW_CONFIG}"
    proc = _run_baseline(None)
    assert proc.returncode == 0, (
        f"baseline should PASS on clean (exit 0), got {proc.returncode}\n"
        f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
    )


@pytest.mark.parametrize("variant", BUGGY_VARIANTS)
def test_c7_baseline_catches_each_injected_bug(variant):
    """C7: the SAME baseline suite fails (non-zero, >=1 genuine assertion failure) on each
    buggy variant — and the failure is a real test failure, not an infra/config error."""
    assert EVAL_PW_CONFIG.exists(), f"baseline eval config missing at {EVAL_PW_CONFIG}"
    proc = _run_baseline(variant)
    combined = f"{proc.stdout}\n{proc.stderr}"
    assert proc.returncode != 0, (
        f"baseline should CATCH {variant} (non-zero exit), got 0\n{combined}"
    )
    # The non-zero must be a genuine assertion failure, not a missing-config / no-tests infra error.
    lower = combined.lower()
    assert "failed" in lower, f"expected >=1 failing test for {variant}; output:\n{combined}"
    for infra in ("no tests found", "cannot find", "error: config"):
        assert infra not in lower, (
            f"{variant} baseline failed for an INFRA reason ({infra!r}), not a genuine assertion "
            f"failure:\n{combined}"
        )


# =========================================================================================
# C9-C13, C15 — scorer contract (eval/score.py)
# =========================================================================================


def _extract_metrics_json(text: str):
    """Extract the first JSON object containing a ``metrics`` field from mixed stdout."""
    dec = json.JSONDecoder()
    idx = 0
    while True:
        start = text.find("{", idx)
        if start == -1:
            return None
        try:
            obj, _ = dec.raw_decode(text[start:])
        except json.JSONDecodeError:
            idx = start + 1
            continue
        if isinstance(obj, dict) and "metrics" in obj:
            return obj
        idx = start + 1


@pytest.fixture(scope="session")
def scorer_run():
    """Run ``eval/score.py --reruns 2 --json`` ONCE (slow: launches browsers across variants)
    and share stdout/stderr/exit across the scorer-contract tests."""
    _kill_port(BACKEND_PORT)
    _kill_port(FRONTEND_PORT)
    proc = subprocess.run(
        ["uv", "run", "python", "eval/score.py", "--reruns", "2", "--json"],
        cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=1800,
    )
    return proc


def test_c13_stdout_contains_four_metric_names(scorer_run):
    """C13: score.py always prints a human-readable table containing the four pinned metric names."""
    out = scorer_run.stdout
    missing = [m for m in METRIC_NAMES if m not in out]
    assert not missing, (
        f"scorer stdout missing metric name(s) {missing}. STDOUT:\n{out}\nSTDERR:\n{scorer_run.stderr}"
    )


def test_c13_stdout_has_per_variant_summary_and_audit(scorer_run):
    """C13: the human table includes a per-variant caught/not-caught summary and the
    assertion-meaningfulness audit — verified by each buggy variant id appearing in stdout."""
    out = scorer_run.stdout
    missing = [v for v in BUGGY_VARIANTS if v not in out]
    assert not missing, (
        f"scorer stdout missing per-variant line(s) for {missing}. STDOUT:\n{out}"
    )


def test_c13_json_metrics_object_has_four_numeric_keys(scorer_run):
    """C13: with --json, score.py emits a `metrics` object carrying the four numeric keys (0..1)."""
    obj = _extract_metrics_json(scorer_run.stdout)
    assert obj is not None, (
        f"--json did not emit a JSON object containing `metrics`. STDOUT:\n{scorer_run.stdout}"
    )
    metrics = obj["metrics"]
    for key in METRIC_NAMES:
        assert key in metrics, f"metrics.{key} missing from JSON: {metrics}"
        val = metrics[key]
        assert isinstance(val, (int, float)) and not isinstance(val, bool), (
            f"metrics.{key} must be numeric, got {val!r}"
        )
        assert 0.0 <= float(val) <= 1.0, f"metrics.{key} must be within 0..1, got {val}"


def test_c13_json_has_per_variant_breakdown(scorer_run):
    """C13: the JSON carries a per-variant / per-test breakdown (references the buggy variants)."""
    obj = _extract_metrics_json(scorer_run.stdout)
    assert obj is not None, "no metrics JSON emitted (--json)"
    blob = json.dumps(obj)
    missing = [v for v in BUGGY_VARIANTS if v not in blob]
    assert not missing, f"JSON breakdown missing per-variant entries for {missing}: {blob}"


def test_c9_bug_catch_rate_is_one(scorer_run):
    """C9: with the three bugs + a correct baseline, bug_catch_rate == 1.0."""
    obj = _extract_metrics_json(scorer_run.stdout)
    assert obj is not None, "no metrics JSON emitted (--json)"
    assert float(obj["metrics"]["bug_catch_rate"]) == 1.0, (
        f"bug_catch_rate should be 1.0, got {obj['metrics']['bug_catch_rate']}"
    )


def test_c10_false_positive_rate_is_zero(scorer_run):
    """C10: a correct baseline on the clean app yields false_positive_rate == 0.0."""
    obj = _extract_metrics_json(scorer_run.stdout)
    assert obj is not None, "no metrics JSON emitted (--json)"
    assert float(obj["metrics"]["false_positive_rate"]) == 0.0, (
        f"false_positive_rate should be 0.0, got {obj['metrics']['false_positive_rate']}"
    )


def test_c11_flake_rate_is_zero(scorer_run):
    """C11: a deterministic harness yields flake_rate == 0.0 across re-runs."""
    obj = _extract_metrics_json(scorer_run.stdout)
    assert obj is not None, "no metrics JSON emitted (--json)"
    assert float(obj["metrics"]["flake_rate"]) == 0.0, (
        f"flake_rate should be 0.0, got {obj['metrics']['flake_rate']}"
    )


def test_c12_assertion_meaningfulness_reported(scorer_run):
    """C12: assertion_meaningfulness_rate is reported as a numeric 0..1 value."""
    obj = _extract_metrics_json(scorer_run.stdout)
    assert obj is not None, "no metrics JSON emitted (--json)"
    val = obj["metrics"]["assertion_meaningfulness_rate"]
    assert isinstance(val, (int, float)) and not isinstance(val, bool), (
        f"assertion_meaningfulness_rate must be numeric, got {val!r}"
    )
    assert 0.0 <= float(val) <= 1.0, f"assertion_meaningfulness_rate out of 0..1: {val}"


def test_c15_exit_code_sanity_gate(scorer_run):
    """C15: score.py exits 0 IFF bug_catch_rate==1.0 && false_positive_rate==0.0 && flake_rate==0.0;
    otherwise non-zero. Metrics are printed either way."""
    obj = _extract_metrics_json(scorer_run.stdout)
    assert obj is not None, (
        f"metrics must be printed before exit. STDOUT:\n{scorer_run.stdout}"
    )
    m = obj["metrics"]
    gate = (
        float(m["bug_catch_rate"]) == 1.0
        and float(m["false_positive_rate"]) == 0.0
        and float(m["flake_rate"]) == 0.0
    )
    if gate:
        assert scorer_run.returncode == 0, (
            f"gate satisfied (catch=1,fp=0,flake=0) but scorer exited {scorer_run.returncode}"
        )
    else:
        assert scorer_run.returncode != 0, (
            f"gate NOT satisfied {m} but scorer exited 0"
        )


# =========================================================================================
# C14 — make eval runs end-to-end, prints metrics table, propagates exit code
# =========================================================================================


@pytest.fixture(scope="session")
def make_eval_run():
    """Run ``make eval`` ONCE from the repo root (slow: deps + full scorer)."""
    _kill_port(BACKEND_PORT)
    _kill_port(FRONTEND_PORT)
    proc = subprocess.run(
        ["make", "eval"], cwd=str(REPO_ROOT),
        capture_output=True, text=True, timeout=2400,
    )
    return proc


def test_c14_make_eval_is_not_a_placeholder(make_eval_run):
    """C14: `make eval` must be a real target, not the Phase-0 placeholder stub."""
    combined = f"{make_eval_run.stdout}\n{make_eval_run.stderr}"
    assert "not yet implemented" not in combined.lower(), (
        f"`make eval` is still a placeholder:\n{combined}"
    )


def test_c14_make_eval_prints_metrics_table(make_eval_run):
    """C14: `make eval` runs end-to-end and prints the four-metric table to stdout."""
    out = make_eval_run.stdout
    missing = [m for m in METRIC_NAMES if m not in out]
    assert not missing, (
        f"`make eval` output missing metric name(s) {missing}.\nSTDOUT:\n{out}\n"
        f"STDERR:\n{make_eval_run.stderr}"
    )


def test_c14_make_eval_propagates_exit_code(make_eval_run):
    """C14/C15: `make eval` propagates the scorer's sanity-gate exit code (0 iff catch=1,fp=0,
    flake=0). Verified by cross-checking the printed metrics against the exit code."""
    obj = _extract_metrics_json(make_eval_run.stdout)
    if obj is not None:
        m = obj["metrics"]
        gate = (
            float(m["bug_catch_rate"]) == 1.0
            and float(m["false_positive_rate"]) == 0.0
            and float(m["flake_rate"]) == 0.0
        )
        expected_zero = gate
    else:
        # No parseable metrics -> the harness did not complete -> must be non-zero.
        expected_zero = False
    if expected_zero:
        assert make_eval_run.returncode == 0, (
            f"gate satisfied but `make eval` exited {make_eval_run.returncode}"
        )
    else:
        assert make_eval_run.returncode != 0, (
            f"gate not satisfied / harness incomplete but `make eval` exited 0.\n"
            f"STDOUT:\n{make_eval_run.stdout}"
        )


# =========================================================================================
# C16 — make dev launches the clean app (reachable /openapi.json on 8000 + UI on 5173, no fault)
# =========================================================================================


def test_c16_make_dev_launches_clean_app():
    """C16: `make dev` launches the clean reference backend + Vite frontend so /openapi.json is
    served on 8000 and the UI is reachable on 5173, with NO fault active."""
    _kill_port(BACKEND_PORT)
    _kill_port(FRONTEND_PORT)
    proc = subprocess.Popen(
        ["make", "dev"], cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        start_new_session=True,
    )
    backend_ready = frontend_ready = False
    try:
        deadline = time.time() + 90
        while time.time() < deadline:
            if proc.poll() is not None:
                raise AssertionError(
                    "`make dev` exited without launching the app (placeholder / not wired).\n"
                    f"--- output ---\n{_drain(proc)}"
                )
            if not backend_ready:
                try:
                    if httpx.get(
                        f"http://127.0.0.1:{BACKEND_PORT}/openapi.json", timeout=2.0
                    ).status_code == 200:
                        backend_ready = True
                except Exception:
                    pass
            if not frontend_ready:
                try:
                    if httpx.get(
                        f"http://127.0.0.1:{FRONTEND_PORT}", timeout=2.0
                    ).status_code < 500:
                        frontend_ready = True
                except Exception:
                    pass
            if backend_ready and frontend_ready:
                break
            time.sleep(0.5)

        assert backend_ready, (
            f"`make dev`: backend /openapi.json not reachable on {BACKEND_PORT} within 90s"
        )
        assert frontend_ready, (
            f"`make dev`: frontend UI not reachable on {FRONTEND_PORT} within 90s"
        )
        # No fault active: clean invariant — GET /orders/{id} without creds must be 401.
        base = f"http://127.0.0.1:{BACKEND_PORT}"
        order = _create_order(base, _first_product_id(_products(base)))
        r = httpx.get(f"{base}/orders/{order['id']}", timeout=10.0)  # no creds
        assert r.status_code == 401, (
            f"`make dev` launched with a fault active: order endpoint auth not enforced "
            f"(got {r.status_code}, expected 401)"
        )
    finally:
        _terminate(proc)
        _kill_port(BACKEND_PORT)
        _kill_port(FRONTEND_PORT)

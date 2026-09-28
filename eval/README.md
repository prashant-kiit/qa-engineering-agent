# `eval/` — injected-bug reliability harness

The **reliability measurement harness** for the reference shop (Phase-0 unit
`p0-eval-harness`). It is the QA agent's own regression suite: it injects a small
catalog of **observable bugs** into the reference backend (non-invasively), runs a
hand-written **baseline** TS-Playwright suite against the clean app and each buggy
variant, and scores four reliability metrics. It is **not** the QA agent itself —
the Planner / Generator / Verifier / Healer arrive in Phases 1–2; the baseline is a
hand-written stand-in that proves the harness runs before any agent exists.

The clean reference app (`reference_app/backend/**`, `reference_app/frontend/**`) is
**never modified** — every fault lives in a launch-time overlay.

## Bug catalog (`eval/buggy_backend.py`)

`eval/buggy_backend.py` exposes an ASGI `app`. It imports the clean backend
(`reference_app.backend.app`) unchanged, reuses its `app`, adds launch-time
`CORSMiddleware` (additive headers only), and — selected by the single **`EVAL_BUG`**
environment variable — drops one clean route and re-registers a faulty overlay in its
place. Exactly one fault is active per value.

| `EVAL_BUG` value    | Fault | Observable wrong behavior |
|---------------------|-------|---------------------------|
| unset / `none`      | *(none — clean)* | Behaves byte-for-byte like the clean backend (only CORS headers added). |
| `checkout_total`    | (a) checkout-total miscalculation | `POST /checkout` returns an order whose `total` is a deterministic wrong value (`true total + 100.0`), never equal to `Σ price × quantity`. Line items, ids, prices and the cart total stay correct. |
| `cart_quantity`     | (b) cart quantity not updating | `POST /cart/items` for a product **already in the cart** is a no-op — the repeat add does not accumulate, so `GET /cart` reports the wrong quantity (stays at the first add) and a wrong total. The first add still works. |
| `order_auth_bypass` | (c) auth-check bypass | `GET /orders/{id}` no longer enforces authentication — a request with **missing or invalid** Basic credentials returns HTTP 200 with the order body instead of 401. All other endpoints still require auth. |

Unknown `EVAL_BUG` values are treated as **clean** (no fault). `EVAL_BUG` is separate
from unit-5's `SMOKE_FAULT`; the two are never overloaded.

### Launching a variant directly

```sh
# Clean (no fault):
uv run uvicorn buggy_backend:app --app-dir eval --host 127.0.0.1 --port 8000

# A specific bug:
EVAL_BUG=cart_quantity uv run uvicorn buggy_backend:app --app-dir eval --host 127.0.0.1 --port 8000
```

Readiness: `http://127.0.0.1:8000/openapi.json`. A fresh process reseeds the SQLite
DB, so per-variant runs are deterministic.

## Baseline suite (`reference_app/e2e/tests/eval/`)

A small hand-written TypeScript-Playwright suite (**UI + API** tests) that passes on
the clean app and, as a whole, catches all three bugs:

| Spec | Type | Catches |
|------|------|---------|
| `happy_path.spec.ts`    | UI  | `checkout_total` (order-total != cart-total) |
| `cart_quantity.spec.ts` | UI  | `cart_quantity` (repeat add does not reach qty 2 / price×2) |
| `order_auth.spec.ts`    | API (`request` fixture) | `order_auth_bypass` (`GET /orders/{id}` returns 200 without/with-invalid creds instead of 401) |

The auth check is an **API** test because the UI always sends credentials and so can
never exercise the missing/invalid-credential path.

Its Playwright config `reference_app/e2e/playwright.eval.config.ts` launches the
`eval/` bug-catalog backend (honoring `EVAL_BUG`) + the Vite frontend as its
`webServer`, with a fresh process per run (deterministic reseed).

### Running the baseline against a variant

From `reference_app/e2e/` (one documented command, driven by `EVAL_BUG`):

```sh
# Clean (EVAL_BUG unset/none -> exits 0):
npx playwright test --config playwright.eval.config.ts

# A buggy variant (>=1 genuine assertion failure -> non-zero exit):
EVAL_BUG=checkout_total    npx playwright test --config playwright.eval.config.ts
EVAL_BUG=cart_quantity     npx playwright test --config playwright.eval.config.ts
EVAL_BUG=order_auth_bypass npx playwright test --config playwright.eval.config.ts
```

## Scorer (`eval/score.py`)

Runs the baseline against the clean variant + the three buggy variants, with re-runs,
and computes the four metrics.

```sh
uv run python eval/score.py [--reruns N] [--json]
```

Options:

- `--reruns N` — re-runs per variant for flake detection (integer, **default `2`**, `N ≥ 2`).
- `--json` — additionally emit a machine-readable JSON object to stdout (with a
  `metrics` field carrying the four numeric 0..1 keys and a per-variant / per-test
  breakdown), on top of the always-printed human table.

### Metrics (pinned definitions)

- **`bug_catch_rate`** = (# buggy variants caught) / (# buggy variants). A variant is
  *caught* if ≥1 baseline test fails on it. Expected **1.0**.
- **`false_positive_rate`** = (# baseline tests that fail on clean) / (# baseline tests
  run on clean). Expected **0.0**.
- **`flake_rate`** = (# flaky `(variant, test)` pairs) / (# pairs evaluated). A pair is
  *flaky* if its pass/fail verdict is not identical across all re-runs. Expected **0.0**.
- **`assertion_meaningfulness_rate`** = (# meaningful tests) / (# baseline tests). A
  test is *meaningful* if it passes on clean AND fails on ≥1 buggy variant. Reported
  (with an audit list of any non-meaningful test); **not** part of the hard exit gate.

### Output & exit code

`score.py` **always** prints a human-readable metrics table (the four metrics by their
pinned names, a per-variant caught/not-caught summary, and the meaningfulness audit
list). With `--json` it also prints the JSON object. It exits **0** iff the harness ran
to completion **and** `bug_catch_rate == 1.0` **and** `false_positive_rate == 0.0`
**and** `flake_rate == 0.0`; otherwise it exits non-zero. Metrics are printed before
exiting in either case.

## `make eval` / `make dev`

- **`make eval`** — idempotently ensures the e2e Node deps + Chromium (reuses
  `make e2e-deps`), runs `uv run python eval/score.py --json` across the 3 buggy
  variants + clean, prints the metrics table, and propagates the scorer's exit code
  (the Phase-0 sanity gate). No manual server start or DB seeding is required.
- **`make dev`** — launches the **clean** reference app: the backend
  (`uv run uvicorn reference_app.backend.app:app` on `127.0.0.1:8000`) in the background
  and the Vite frontend (`npm run dev` on `127.0.0.1:5173`, with
  `VITE_API_BASE_URL=http://127.0.0.1:8000`) in the foreground, with seeded SQLite and
  **no** fault toggle. `GET /openapi.json` is served on `:8000` and the UI on `:5173`.
  Ctrl-C stops the frontend and tears the backend down.

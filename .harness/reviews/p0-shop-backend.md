# Review — p0-shop-backend

**Verdict:** APPROVE

## Summary
The clean reference-shop backend (FastAPI + SQLite) meets all 22 binding acceptance criteria.
The contract is honored exactly: routes/methods, `testuser`/`testpass`, the binding ASGI import
path `reference_app.backend.app:app`, and order-total = Σ price×quantity. All three suites are
green. Tests are meaningful and un-gamed; scope is backend-only with no bug-injection toggles.

## Axis 1 — Acceptance (22/22 met)
- **Auth (C1–C4):** `HTTPBasic(auto_error=True)` yields 401 for missing creds; `current_user`
  raises 401 with `WWW-Authenticate: Basic` for wrong user/pass; valid seeded creds accepted.
  Password compared with `secrets.compare_digest`. (`app.py:145-158`)
- **Products (C5–C6):** `GET /products` returns the 5-item seeded catalog, unique int ids,
  `price ≥ 0`. (`app.py:42-48, 187-190`)
- **Cart (C7–C11):** empty cart → `{items: [], total: 0}`; add reflects quantity; repeat add is
  cumulative via `UPDATE quantity = quantity + ?`; unknown product → 404 with no mutation; total
  = Σ price×qty. (`app.py:163-221`)
- **Checkout → order (C12–C15):** creates order with `id`+`total`, total equals cart total,
  empties cart, empty-cart checkout → 400. (`app.py:224-254`)
- **Get order (C16–C18):** `GET /orders/{id}` returns order with line items; non-existent → 404;
  both order endpoints require auth (no bypass) — order lookup also scoped to the owning user.
  (`app.py:257-273`)
- **Seed (C19):** fixed catalog + `testuser`/`testpass`, DB reset+reseeded on import →
  deterministic across fresh starts. (`app.py:37-111`)
- **OpenAPI (C20–C21):** FastAPI auto-serves `/openapi.json` publicly; paths document all shop
  routes including templated `/orders/{order_id}`.
- **Launchability (C22):** importable at the binding path; documented HTTP entrypoint
  (`127.0.0.1:8000`, `SHOP_HOST`/`SHOP_PORT`) in `reference_app/backend/README.md`.

## Axis 2 — Test integrity
- `test_shop_backend.py` (26 tests) and `conftest.py` match the Tester's coverage note exactly
  (test names, criterion mapping). Not weakened: C9 asserts cumulative 2+3=5, C10 asserts
  no-mutation on rejection, totals are computed from the *served* seed prices, C18 asserts
  no-bypass, C20 fetches `/openapi.json` with no creds. Developer did not modify the tests.

## Axis 3 — Scope
- Backend only. No frontend, no BRD, no bug-injection toggles. `SHOP_HOST`/`SHOP_PORT` are launch
  config, not bug flags. `pyproject.toml` adds the dev group (pytest/httpx/fastapi/uvicorn) +
  pytest config needed to run the suite; DB file (`shop.db`) is git-ignored (`git check-ignore`
  confirms) and never staged.
- **Scaffold-guard retirement verified (in-scope harness decision):** `tests/scaffold/p0-scaffold.test.sh`
  default run stays green — the reentrant structural checks (C1/C3 dirs exist & tracked, C4 uv
  parseable, C5 Makefile targets, C8/C9 gitignore) all PASS; C2/C10/C11 now SKIP with a clear
  message. The guards were **not gutted**: `SCAFFOLD_DIFF_GUARD=1` still executes them fully — they
  correctly fire on the repo's legitimate post-scaffold evolution (`.venv`/`.pytest_cache`,
  `AGILE_PLAN.md`/`.harness/backlog.md` edits, new task files), confirming the logic is intact and
  merely gated behind the opt-in flag.

## Axis 4 — Quality / security
- Parameterized SQL throughout (no injection). Constant-time password compare. No auth-bypass on
  order endpoints. Deterministic reseed on import. Simple, readable, no dead code.
- Minor, non-blocking observation: fastapi/uvicorn are declared in the `dev` dependency group
  rather than `[project.dependencies]`. Since `uv run` includes the dev group by default, the app
  is runnable and the suite passes; the DoD ("declared so a uv-managed environment can run it") is
  satisfied. Consider promoting runtime deps to `[project.dependencies]` in a later hardening pass.

## Test runs
```
$ uv run pytest reference_app/backend/tests -q
.......................... (26 passed, 1 warning in 0.21s)   # benign Starlette httpx deprecation

$ bash tests/scaffold/p0-scaffold.test.sh
RESULT: all acceptance checks passed   (C2, C10/C11 SKIP by design; reentrant checks PASS)

$ bash tests/docs/design-note.test.sh
RESULT: all acceptance checks passed

$ SCAFFOLD_DIFF_GUARD=1 bash tests/scaffold/p0-scaffold.test.sh
RESULT: 3 acceptance check(s) failed   (C2/C10/C11 execute and fire on legitimate repo
                                        evolution — confirms guards intact, not gutted)
```

Deploy gate: opened (`p0-shop-backend` written to `.harness/state/APPROVED`).

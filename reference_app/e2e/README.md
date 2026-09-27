# Reference Shop — E2E smoke (TypeScript Playwright)

A self-contained Playwright project holding the Phase-0 end-to-end **smoke** for the
reference shop. The smoke drives the full happy path through the real browser UI:

```
login -> add to cart -> view cart -> checkout -> order confirmation
```

Its load-bearing assertion is that the order-confirmation **`order-total` equals the
`cart-total` read immediately before checkout** (the backend invariant
`total = Σ price × quantity`).

## Layout

| File | Purpose |
|------|---------|
| `playwright.config.ts` | `baseURL` + `webServer` wiring (backend + Vite frontend), Chromium project. |
| `tests/smoke.spec.ts` | The single smoke spec. |
| `smoke_backend.py` | Backend launcher the `webServer` runs: imports the clean backend unchanged, adds launch-time CORS, and overlays the `SMOKE_FAULT` fault when toggled. |
| `package.json` / `tsconfig.json` | Dedicated Node/TS project (separate from the frontend Vitest toolchain). |

## Prerequisites

- Node (for `@playwright/test`) and `uv` (for the Python backend) available on `PATH`.
- Install deps + the Chromium binary (idempotent):

  ```bash
  npm install
  npm run install:browser   # playwright install chromium
  ```

  From the repo root, `make test` does both automatically before running.

## Running

No manual server start or DB seeding is needed — `playwright.config.ts` launches both
servers itself and the backend reseeds on startup.

- **Clean smoke (green):**

  ```bash
  # from reference_app/e2e/
  npx playwright test          # or: npm test
  # from the repo root
  make test
  ```

  Launches the backend via `smoke_backend:app` (the clean backend + launch-time
  CORS, no fault) on `127.0.0.1:8000` and the Vite dev server on `127.0.0.1:5173`
  (`VITE_API_BASE_URL=http://127.0.0.1:8000`, `baseURL=http://127.0.0.1:5173`).
  Exits **0**.

- **Red-on-buggy demonstration (expected to FAIL):**

  ```bash
  # from reference_app/e2e/
  npm run test:smoke-buggy     # = SMOKE_FAULT=1 playwright test
  # from the repo root
  make test-smoke-buggy
  ```

  A **non-zero** exit here is the *success* of the demonstration — it proves the
  runner catches a real defect.

## The `SMOKE_FAULT` mechanism

`SMOKE_FAULT` is a single environment toggle. `playwright.config.ts` passes it
through to the backend process (`smoke_backend:app`):

- **unset / `0`** — `smoke_backend` serves the clean backend unchanged (plus
  launch-time CORS). The clean default path is byte-for-byte unchanged; the smoke
  is green.
- **`1`** — `smoke_backend` overlays **exactly one** fault: the `POST /checkout`
  response reports a **wrong order total** (true total + a fixed offset). The
  persisted order and the cart maths stay correct, so the pre-checkout `cart-total`
  is still right; only the confirmation `order-total` (which the UI renders verbatim
  from the checkout response) is wrong. The smoke's `order-total == cart-total`
  assertion then fails as a genuine assertion failure, turning the run red.

The launcher (`smoke_backend.py`) also adds `CORSMiddleware` for **both** variants
— a browser cross-origin launch concern (the frontend on `:5173` calls the backend
on `:8000` with an `Authorization` header, which triggers a CORS preflight). This
is additive response headers only; the API's status codes and JSON bodies are
identical to the clean backend, and the clean source (`reference_app/backend/app.py`)
is imported unchanged.

The fault is deliberately minimal: one toggle, one fault. It is **not** a bug
catalog, scorer, or injection framework (those are unit 6, `p0-eval-harness`). No
clean backend/frontend source is modified and all new files live under
`reference_app/e2e/`.

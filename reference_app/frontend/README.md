# Reference Shop — Frontend

React + Vite single-page UI for the reference shop. It presents five user-facing
views (login, product list, cart, checkout, order-confirmation) and drives the
shop backend (`reference_app/backend`) over HTTP Basic Auth.

## Install

```bash
cd reference_app/frontend
npm install
```

## Scripts

| Script          | What it does                                                        |
| --------------- | ------------------------------------------------------------------- |
| `npm run dev`   | Start the Vite dev server for local development.                    |
| `npm run build` | Type-check (`tsc --noEmit`) and produce a production bundle. Non-zero exit on any build/compile error. |
| `npm test`      | Run the component/integration suite once (Vitest, CI-style, non-interactive). Non-zero exit on failure. |

Run the suite and build without reading the code:

```bash
npm test          # component/integration tests (backend fully stubbed)
npm run build     # production bundle
```

## API base URL configuration

The backend base URL is resolved in `src/config.ts` from the Vite env var
**`VITE_API_BASE_URL`**, defaulting to **`http://127.0.0.1:8000`** (the backend's
documented base URL). Point the UI at a different backend without editing any
component source:

```bash
VITE_API_BASE_URL="http://localhost:9000" npm run dev
# or add VITE_API_BASE_URL=... to a .env file
```

All authenticated requests carry the credentials captured at login as an HTTP
Basic `Authorization` header; credentials are never hard-coded in components.

## Component export points (for testing)

Each view is importable from the barrel `src/views` and renders in isolation
with the backend stubbed (global `fetch` mocked). No live backend is required.

| View                  | Import                                              | Props                                |
| --------------------- | --------------------------------------------------- | ------------------------------------ |
| Login                 | `import { LoginView } from "./views"`               | `{ onLogin(creds) }`                 |
| Product list          | `import { ProductListView } from "./views"`         | `{ credentials }`                    |
| Cart                  | `import { CartView } from "./views"`                | `{ credentials }`                    |
| Checkout              | `import { CheckoutView } from "./views"`            | `{ credentials }`                    |
| Order confirmation    | `import { OrderConfirmationView } from "./views"`   | `{ order: { id, total, items } }`    |

`credentials` is `{ username, password }`. The API base URL constant is
`import { API_BASE_URL } from "./config"`.

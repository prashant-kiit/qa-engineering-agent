import { defineConfig, devices } from '@playwright/test';
import path from 'path';

/**
 * Playwright config for the eval **baseline** suite (unit `p0-eval-harness`).
 *
 * Distinct from the unit-5 smoke config (`playwright.config.ts`): its `webServer`
 * launches the eval **bug-catalog** backend (`eval/buggy_backend.py`) instead of
 * the smoke launcher, and it honours the single `EVAL_BUG` env selector rather
 * than `SMOKE_FAULT`. The baseline specs live under `tests/eval/`.
 *
 * `EVAL_BUG` chooses the launched variant (passed through to the backend
 * process): unset / "none" -> clean; `checkout_total` / `cart_quantity` /
 * `order_auth_bypass` -> the three injected faults. The baseline suite passes on
 * clean and, as a whole, produces >=1 genuine assertion failure on each buggy
 * variant.
 *
 * A fresh backend process is launched per invocation (reuseExistingServer:false)
 * so each variant reseeds the SQLite DB — this makes the harness deterministic
 * (flake_rate == 0). The eval scorer clears ports 8000 / 5173 between runs.
 */

const REPO_ROOT = path.resolve(__dirname, '..', '..');
const FRONTEND_HOST = '127.0.0.1';
const FRONTEND_PORT = 5173;
const BACKEND_PORT = 8000;
const BACKEND_URL = `http://127.0.0.1:${BACKEND_PORT}`;
const BASE_URL = `http://${FRONTEND_HOST}:${FRONTEND_PORT}`;

// The selected variant (unset / "" -> clean). Passed through to the backend.
const EVAL_BUG = process.env.EVAL_BUG ?? '';

const backendCommand =
  `uv run uvicorn buggy_backend:app --app-dir eval ` +
  `--host 127.0.0.1 --port ${BACKEND_PORT}`;

export default defineConfig({
  testDir: './tests/eval',
  timeout: 60_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [['list']],
  use: {
    baseURL: BASE_URL,
    headless: true,
    trace: 'off',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  // A fresh backend + frontend serve each variant; never reuse a lingering
  // server (the scorer reseeds per variant by launching a fresh process).
  webServer: [
    {
      command: backendCommand,
      cwd: REPO_ROOT,
      url: `${BACKEND_URL}/openapi.json`,
      reuseExistingServer: false,
      timeout: 120_000,
      env: { EVAL_BUG },
      stdout: 'pipe',
      stderr: 'pipe',
    },
    {
      command: `npm run dev -- --host ${FRONTEND_HOST} --port ${FRONTEND_PORT} --strictPort`,
      cwd: path.join(REPO_ROOT, 'reference_app', 'frontend'),
      url: BASE_URL,
      reuseExistingServer: false,
      timeout: 120_000,
      env: { VITE_API_BASE_URL: BACKEND_URL },
      stdout: 'pipe',
      stderr: 'pipe',
    },
  ],
});

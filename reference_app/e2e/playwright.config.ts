import { defineConfig, devices } from '@playwright/test';
import path from 'path';

/**
 * Playwright config for the Phase-0 reference-shop smoke.
 *
 * Brings the whole app up itself via `webServer` (backend + Vite frontend) so the
 * smoke is one-command reproducible — no manual server start or DB seeding.
 *
 * The backend is launched via the smoke launcher `smoke_backend:app`, which imports
 * the clean backend unchanged and adds only launch-time concerns (CORS for the
 * browser cross-origin calls; the SMOKE_FAULT overlay). Clean vs. buggy is governed
 * by the single `SMOKE_FAULT` env toggle, passed through to that backend process:
 *   - unset / "0"  -> clean app; smoke is green.
 *   - "1"          -> the launcher returns a wrong order total; the smoke's
 *                     order-total==cart-total assertion fails and the run exits
 *                     non-zero ("red on buggy").
 */

const REPO_ROOT = path.resolve(__dirname, '..', '..');
const FRONTEND_HOST = '127.0.0.1';
const FRONTEND_PORT = 5173;
const BACKEND_PORT = 8000;
const BACKEND_URL = `http://127.0.0.1:${BACKEND_PORT}`;
const BASE_URL = `http://${FRONTEND_HOST}:${FRONTEND_PORT}`;

const FAULTY = process.env.SMOKE_FAULT === '1';

const backendCommand =
  `uv run uvicorn smoke_backend:app --app-dir reference_app/e2e ` +
  `--host 127.0.0.1 --port ${BACKEND_PORT}`;

export default defineConfig({
  testDir: './tests',
  // The unit-6 eval baseline specs live under `tests/eval/` and run via their own
  // `playwright.eval.config.ts` (which launches the EVAL_BUG bug-catalog backend).
  // Keep the unit-5 smoke scoped to just `smoke.spec.ts` so its green-on-clean /
  // red-under-SMOKE_FAULT behavior and scope are unchanged.
  testIgnore: '**/tests/eval/**',
  timeout: 60_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [['list']],
  use: {
    baseURL: BASE_URL,
    headless: true,
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  // A fresh backend must serve each variant, so the faulty run never reuses a
  // clean server that may be lingering (and vice-versa).
  webServer: [
    {
      command: backendCommand,
      cwd: REPO_ROOT,
      url: `${BACKEND_URL}/openapi.json`,
      reuseExistingServer: !FAULTY,
      timeout: 120_000,
      env: { SMOKE_FAULT: FAULTY ? '1' : '0' },
      stdout: 'pipe',
      stderr: 'pipe',
    },
    {
      command: `npm run dev -- --host ${FRONTEND_HOST} --port ${FRONTEND_PORT} --strictPort`,
      cwd: path.join(REPO_ROOT, 'reference_app', 'frontend'),
      url: BASE_URL,
      reuseExistingServer: !FAULTY,
      timeout: 120_000,
      env: { VITE_API_BASE_URL: BACKEND_URL },
      stdout: 'pipe',
      stderr: 'pipe',
    },
  ],
});

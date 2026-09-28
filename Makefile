# qa-engineering-agent — root task runner (Phase 0 scaffold).

E2E_DIR := reference_app/e2e

.PHONY: help dev test test-smoke-buggy e2e-deps eval release

FRONTEND_DIR := reference_app/frontend
BACKEND_HOST := 127.0.0.1
BACKEND_PORT := 8000
FRONTEND_HOST := 127.0.0.1
FRONTEND_PORT := 5173
BACKEND_URL := http://$(BACKEND_HOST):$(BACKEND_PORT)

help:
	@echo "qa-engineering-agent — available targets:"
	@echo "  dev              run the CLEAN reference shop app locally (backend :8000 + Vite frontend :5173, seeded, no fault)"
	@echo "  test             run the Playwright E2E smoke against the clean reference app (unit 5: p0-playwright-smoke)"
	@echo "  test-smoke-buggy run the SAME smoke against the SMOKE_FAULT variant — expected to FAIL (red-on-buggy demo)"
	@echo "  eval             run the injected-bug eval harness + scorer (unit 6: p0-eval-harness)"
	@echo "  release          produce the BRD / release docs (arrives in unit 4: p0-brd-release)"
	@echo "  help             list available targets (this message)"

# Launch the CLEAN reference app locally: the backend (uvicorn) and the Vite
# frontend, seeded SQLite, NO bug toggle (no EVAL_BUG / SMOKE_FAULT). The backend
# runs in the background; the frontend runs in the foreground so Ctrl-C stops it,
# after which the backend is torn down. /openapi.json is served on :8000 and the
# UI on :5173 (pointed at the backend via VITE_API_BASE_URL).
dev:
	@echo "make dev: launching CLEAN reference app — backend $(BACKEND_URL), frontend http://$(FRONTEND_HOST):$(FRONTEND_PORT)"
	@set -e; \
	uv run uvicorn reference_app.backend.app:app --host $(BACKEND_HOST) --port $(BACKEND_PORT) & \
	BACKEND_PID=$$!; \
	trap "kill $$BACKEND_PID 2>/dev/null || true" EXIT INT TERM; \
	cd $(FRONTEND_DIR) && VITE_API_BASE_URL=$(BACKEND_URL) npm run dev -- --host $(FRONTEND_HOST) --port $(FRONTEND_PORT) --strictPort

# Idempotently install the e2e Node deps and the Chromium browser binary.
# Safe to re-run: npm install is a no-op when up to date; playwright install
# skips an already-present browser.
e2e-deps:
	@cd $(E2E_DIR) && npm install
	@cd $(E2E_DIR) && npm run install:browser

# Clean-app smoke: ensures deps + browser, then runs the Playwright smoke against
# the clean reference app (the config's webServer brings backend+frontend up).
# Propagates the Playwright exit code (0 pass / non-zero fail).
test: e2e-deps
	@cd $(E2E_DIR) && npm test

# Red-on-buggy demonstration: runs the SAME smoke against the SMOKE_FAULT variant
# (a faulty backend overlay that returns a wrong order total). This target is
# EXPECTED to exit non-zero — a passing (green) smoke here would be the failure.
test-smoke-buggy: e2e-deps
	@cd $(E2E_DIR) && npm run test:smoke-buggy

# Injected-bug eval harness: ensures the e2e Node deps + Chromium are present
# (reusing the e2e-deps prerequisite; no-op when already installed), then runs the
# scorer across the 3 buggy variants + clean. The scorer prints the four-metric
# table (and, with --json, a machine-readable object) and its exit code is the
# Phase-0 sanity gate (0 iff catch=1, fp=0, flake=0); `make` propagates it.
eval: e2e-deps
	@uv run python eval/score.py --json

release:
	@echo "make release: not yet implemented — arrives in unit 4 (p0-brd-release)."

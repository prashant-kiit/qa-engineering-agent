# qa-engineering-agent — root task runner (Phase 0 scaffold).

E2E_DIR := reference_app/e2e

.PHONY: help dev test test-smoke-buggy e2e-deps eval release

help:
	@echo "qa-engineering-agent — available targets:"
	@echo "  dev              run the reference shop app locally (arrives in units 2-3: p0-shop-backend / p0-shop-frontend)"
	@echo "  test             run the Playwright E2E smoke against the clean reference app (unit 5: p0-playwright-smoke)"
	@echo "  test-smoke-buggy run the SAME smoke against the SMOKE_FAULT variant — expected to FAIL (red-on-buggy demo)"
	@echo "  eval             run the injected-bug eval harness + scorer (arrives in unit 6: p0-eval-harness)"
	@echo "  release          produce the BRD / release docs (arrives in unit 4: p0-brd-release)"
	@echo "  help             list available targets (this message)"

dev:
	@echo "make dev: not yet implemented — arrives in units 2-3 (p0-shop-backend / p0-shop-frontend / p0-playwright-smoke)."

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

eval:
	@echo "make eval: not yet implemented — arrives in unit 6 (p0-eval-harness)."

release:
	@echo "make release: not yet implemented — arrives in unit 4 (p0-brd-release)."

# qa-engineering-agent — root task runner (Phase 0 scaffold).
# Placeholder targets only. Each prints a "not yet implemented" message naming the
# later Phase 0 unit that will implement real behavior, then exits 0.

.PHONY: help dev test eval release

help:
	@echo "qa-engineering-agent — available targets:"
	@echo "  dev      run the reference shop app locally (arrives in units 2-3: p0-shop-backend / p0-shop-frontend)"
	@echo "  test     run the Playwright E2E + API suite (arrives in unit 5: p0-playwright-smoke)"
	@echo "  eval     run the injected-bug eval harness + scorer (arrives in unit 6: p0-eval-harness)"
	@echo "  release  produce the BRD / release docs (arrives in unit 4: p0-brd-release)"
	@echo "  help     list available targets (this message)"

dev:
	@echo "make dev: not yet implemented — arrives in units 2-3 (p0-shop-backend / p0-shop-frontend / p0-playwright-smoke)."

test:
	@echo "make test: not yet implemented — arrives in units 2-5 (p0-shop-backend / p0-shop-frontend / p0-playwright-smoke)."

eval:
	@echo "make eval: not yet implemented — arrives in unit 6 (p0-eval-harness)."

release:
	@echo "make release: not yet implemented — arrives in unit 4 (p0-brd-release)."

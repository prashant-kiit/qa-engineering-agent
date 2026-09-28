# Review — `p0-eval-harness` (final Phase 0 unit)

**Verdict: APPROVE**

Independent review of the reliability measurement harness (bug-catalog overlay, scorer, baseline
TS-Playwright suite, `make eval` / `make dev` wiring + Phase-0 exit-gate fold-in). All four axes pass
and the full suite is green when I ran it myself.

## 1. Acceptance (criteria 1–18) — met

- **Bugs (C1–C5).** `eval/buggy_backend.py` reuses the clean ASGI app unchanged, adds additive-only
  CORS, and applies exactly one fault per `EVAL_BUG` value by dropping + re-registering a single
  route:
  - `checkout_total` — `POST /checkout` returns `true_total + 100.0` (deterministic wrong value, can
    never coincide with the truth); persisted maths, line items, ids, cart total stay clean.
  - `cart_quantity` — repeat add is a no-op (first add works); `GET /cart` reports qty ≠ 2.
  - `order_auth_bypass` — `GET /orders/{id}` drops the auth dependency → 200 with missing/invalid creds.
  - Clean value (`none`/unset) → byte-parity with the pristine backend (verified by the byte-parity
    test on `/products`).
  Isolation verified by the cross-variant divergence test: `none=(F,F,F)`, `checkout_total=(T,F,F)`,
  `cart_quantity=(F,T,F)`, `order_auth_bypass=(F,F,T)`.
- **Baseline (C6–C8).** Three hand-written specs under `reference_app/e2e/tests/eval/` (2 UI +
  1 Playwright API), non-vacuous assertions on app-produced values (order total, cart qty/total,
  HTTP 401), variant-selectable via `playwright.eval.config.ts` honoring `EVAL_BUG`. Passes on clean;
  each buggy variant yields a genuine assertion failure (not infra).
- **Metrics + gate (C9–C15).** `eval/score.py` computes the four pinned metrics; per-variant
  breakdown shows each bug caught by exactly its discriminating test (`[false,false]`) and every
  other (variant,test) `[true,true]`. `bug_catch_rate=1.0`, `false_positive_rate=0.0`,
  `flake_rate=0.0`, `assertion_meaningfulness_rate=1.0`. Exit 0 iff `catch==1 && fp==0 && flake==0`
  (meaningfulness excluded from the gate, per spec); metrics printed before exit; `--json` emits a
  `metrics` object with four numeric keys + per-variant/per-test breakdown.
- **Wiring (C14/C16).** `make eval` ensures deps, runs the scorer across 3 buggy + clean, prints the
  table, propagates exit (observed exit 0). `make dev` launches the clean app (`/openapi.json` on
  8000 + UI on 5173, 401 enforced, no fault).
- **Exit gate (C17/C18).** All three exit-gate bullets hold; `make test` green-on-clean,
  `make test-smoke-buggy` red under `SMOKE_FAULT=1`.

## 2. Test integrity — sound / un-gamed

- Flake logic genuinely compares pass/fail verdicts across reruns (`len(set(verdicts)) > 1`).
- False-positive uses `failed_any_run` on clean; catch requires a real per-variant failure — the
  scorer cannot report `catch=1.0` without an actual variant failure (confirmed by the per-variant
  `[false,false]` entries mapping each bug to its own discriminating test).
- Pass/fail sourced from Playwright's JSON report (temp file, immune to webServer stdout); infra
  failures raise `RuntimeError` → harness marked incomplete → non-zero gate.
- The Tester's verification file is unchanged (matches the coverage note's C1–C16 mapping; red→green
  transition legitimate). The scaffold-suite edit is the sanctioned Tester-owned prior-suite fix
  (C6a runs only the `release` placeholder; `dev`/`eval`/`test` verified real via `make -n`).

## 3. Scope — clean

- `reference_app/backend/**` and `reference_app/frontend/**` sources have zero working-tree changes;
  the fault lives only in the `eval/` overlay. No `EVAL_BUG` toggle in any clean production path.
- `playwright.config.ts` gained only `testIgnore: '**/tests/eval/**'` (in-scope; keeps unit-5 smoke
  scoped to `smoke.spec.ts`, still 1 passed).
- `AGILE_PLAN.md` / `.harness/backlog.md` / `.harness/tasks/p0-scaffold.tests.md` changes are the
  sanctioned TPM plan-lock + backlog status + Tester scaffold-fix — not developer scope creep.

## 4. Quality — good

Overlay follows the unit-5 pattern faithfully; scorer is robust (deterministic reseed per fresh
process, port clearing, JSON-report source of truth); README documents the catalog, selector,
baseline invocation, scorer CLI, and `make eval`/`make dev`. No dead code observed.

## Test runs (all on my own execution)

```
uv run pytest eval/tests -q               -> 33 passed in 62.44s
make eval                                 -> exit 0; catch=1.000 fp=0.000 flake=0.000 meaningful=1.000
                                             checkout_total/cart_quantity/order_auth_bypass all CAUGHT
uv run pytest reference_app/backend/tests -> 26 passed
npm --prefix reference_app/frontend test  -> 17 passed
cd reference_app/e2e && npx playwright test          -> 1 passed (clean smoke)
make test                                 -> exit 0 (1 passed, green-on-clean)
make test-smoke-buggy                     -> exit 2 (1 failed, red-under-SMOKE_FAULT)
bash tests/scaffold/p0-scaffold.test.sh   -> exit 0 (fast, no hang)
bash tests/docs/design-note.test.sh       -> exit 0
bash tests/docs/brd-release.test.sh       -> exit 0
```

Deploy gate: `p0-eval-harness` written to `.harness/state/APPROVED`.

# Tester coverage — `p0-eval-harness` (TDD red)

Harness-verification tests authored **before** any implementation, from the spec + the
`p0-shop-backend` / `p0-playwright-smoke` contracts only (no eval implementation source read).

These are the **Tester's own verification tests**, deliberately distinct from the Developer's
product deliverables (`eval/buggy_backend.py`, `eval/score.py`, the baseline TS-Playwright suite,
and the `make eval` / `make dev` wiring), which do not exist yet.

## Test file
- `eval/tests/test_eval_harness_verification.py` — Python `pytest` (drives the eval bug-catalog
  variants over HTTP via `httpx` + `subprocess`; invokes the baseline / scorer / make targets as
  black boxes).

## Run command
```
uv run pytest eval/tests/test_eval_harness_verification.py -o addopts="" -o testpaths=""
```
(Ports 8000 / 8001 / 5173 are cleared before each launch; variants launch one at a time.)

## Acceptance criterion → verification test(s)

| Criterion (spec) | Verification test(s) |
|---|---|
| **C1** clean variant (`EVAL_BUG` unset/`none`) satisfies every clean invariant + byte-parity | `test_c1_clean_variant_order_total_correct[None/none]`, `test_c1_clean_variant_repeat_add_increments[None/none]`, `test_c1_clean_variant_order_requires_auth[None/none]`, `test_c1_clean_variant_products_byte_parity_with_clean_backend` |
| **C2** `checkout_total` → order total ≠ Σ price×qty | `test_c2_checkout_total_order_total_is_wrong` |
| **C3** `cart_quantity` → repeat add does not accumulate (qty ≠ 2) | `test_c3_cart_quantity_repeat_add_does_not_accumulate` |
| **C4** `order_auth_bypass` → `GET /orders/{id}` returns 200 without/with-invalid creds | `test_c4_order_auth_bypass_missing_credentials_returns_200`, `test_c4_order_auth_bypass_invalid_credentials_returns_200` |
| **C5** exactly one fault per value; faults isolated + distinct | `test_c2_checkout_total_isolated_cart_and_auth_stay_clean`, `test_c3_cart_quantity_isolated_auth_stays_clean`, `test_c4_order_auth_bypass_isolated_total_and_cart_stay_clean`, `test_c5_each_buggy_variant_diverges_from_clean_on_its_own_axis` |
| **C6** baseline passes on clean (exit 0) | `test_c6_baseline_passes_on_clean` |
| **C7** baseline catches each injected bug (non-zero, genuine assertion fail) | `test_c7_baseline_catches_each_injected_bug[checkout_total/cart_quantity/order_auth_bypass]` |
| **C8** baseline variant-selectable + documented config | `test_c8_baseline_eval_config_exists` |
| **C9** `bug_catch_rate == 1.0` | `test_c9_bug_catch_rate_is_one` |
| **C10** `false_positive_rate == 0.0` | `test_c10_false_positive_rate_is_zero` |
| **C11** `flake_rate == 0.0` | `test_c11_flake_rate_is_zero` |
| **C12** `assertion_meaningfulness_rate` reported (numeric 0..1) | `test_c12_assertion_meaningfulness_reported` |
| **C13** stdout table with 4 metric names + per-variant + audit; `--json` `metrics` object (4 numeric keys) + per-variant breakdown | `test_c13_stdout_contains_four_metric_names`, `test_c13_stdout_has_per_variant_summary_and_audit`, `test_c13_json_metrics_object_has_four_numeric_keys`, `test_c13_json_has_per_variant_breakdown` |
| **C14** `make eval` runs end-to-end, prints metrics table, propagates exit | `test_c14_make_eval_is_not_a_placeholder`, `test_c14_make_eval_prints_metrics_table`, `test_c14_make_eval_propagates_exit_code` |
| **C15** scorer exit 0 iff `catch==1.0 && fp==0.0 && flake==0.0`; metrics printed before exit | `test_c15_exit_code_sanity_gate` (+ `test_c14_make_eval_propagates_exit_code`) |
| **C16** `make dev` launches clean app (`/openapi.json` on 8000 + UI on 5173, no fault) | `test_c16_make_dev_launches_clean_app` |

### Criteria not covered by Tester verification tests (by design)
- **C17 / C18** (no-regressions / exit-gate-on-landing): covered by the *existing* `make test`
  (green-on-clean smoke) and `make test-smoke-buggy` (red under `SMOKE_FAULT=1`) suites, which this
  unit must leave working — the Reviewer re-runs them. Not re-authored here.
- The baseline suite itself (C6/C7 internals) is a **Developer deliverable**; the Tester only
  *invokes* it and asserts exit codes.

## Notes / assumptions
- Bug-catalog variants are launched with the pinned shape
  `uv run uvicorn buggy_backend:app --app-dir eval --host 127.0.0.1 --port 8000`, `EVAL_BUG` in env.
- Baseline invocation uses the spec's pinned example: from `reference_app/e2e/`,
  `npx playwright test --config playwright.eval.config.ts` with `EVAL_BUG` in env
  (unset/`none` = clean). Config path `playwright.eval.config.ts` per Interfaces.
- Scorer run uses `--reruns 2 --json` once (session-scoped) and the four scorer-contract metric
  tests share it; `make eval` is run once (session-scoped). These are slow when green (they launch
  browsers across variants) — expected per the spec.
- `make dev` is checked with a bounded start → poll-readiness (90s) → teardown.

## Red run output (all legitimately failing — files/targets do not exist yet)

```
============================== 33 failed in 8.41s ==============================
```

Failure reasons confirmed to be missing-behavior (not harness syntax/collection errors):

- **C1–C5 (bug catalog):**
  `AssertionError: eval bug-catalog launcher (EVAL_BUG=...) exited before becoming ready — expected .../eval/buggy_backend.py to expose an ASGI 'app'.`
  `ERROR:    Error loading ASGI app. Could not import module "buggy_backend".`
- **C6–C8 (baseline):**
  `AssertionError: baseline eval config missing at .../reference_app/e2e/playwright.eval.config.ts`
- **C9–C13, C15 (scorer):**
  `scorer_run = CompletedProcess(args=['uv','run','python','eval/score.py','--reruns','2','--json'], returncode=2, ...
   can't open file '.../eval/score.py': [Errno 2] No such file or directory)`
  → `missing metric name(s) [...]` / `no metrics JSON emitted (--json)`
- **C14 (make eval):**
  `make eval: not yet implemented — arrives in unit 6 (p0-eval-harness).` (returncode 0)
  → `gate not satisfied / harness incomplete but 'make eval' exited 0`
- **C16 (make dev):**
  `AssertionError: 'make dev' exited without launching the app (placeholder / not wired).`
  `make dev: not yet implemented — arrives in units 2-3 (...).`

Full failing-test list (33):
```
test_c1_clean_variant_order_total_correct[None]
test_c1_clean_variant_order_total_correct[none]
test_c1_clean_variant_repeat_add_increments[None]
test_c1_clean_variant_repeat_add_increments[none]
test_c1_clean_variant_order_requires_auth[None]
test_c1_clean_variant_order_requires_auth[none]
test_c1_clean_variant_products_byte_parity_with_clean_backend
test_c2_checkout_total_order_total_is_wrong
test_c2_checkout_total_isolated_cart_and_auth_stay_clean
test_c3_cart_quantity_repeat_add_does_not_accumulate
test_c3_cart_quantity_isolated_auth_stays_clean
test_c4_order_auth_bypass_missing_credentials_returns_200
test_c4_order_auth_bypass_invalid_credentials_returns_200
test_c4_order_auth_bypass_isolated_total_and_cart_stay_clean
test_c5_each_buggy_variant_diverges_from_clean_on_its_own_axis
test_c8_baseline_eval_config_exists
test_c6_baseline_passes_on_clean
test_c7_baseline_catches_each_injected_bug[checkout_total]
test_c7_baseline_catches_each_injected_bug[cart_quantity]
test_c7_baseline_catches_each_injected_bug[order_auth_bypass]
test_c13_stdout_contains_four_metric_names
test_c13_stdout_has_per_variant_summary_and_audit
test_c13_json_metrics_object_has_four_numeric_keys
test_c13_json_has_per_variant_breakdown
test_c9_bug_catch_rate_is_one
test_c10_false_positive_rate_is_zero
test_c11_flake_rate_is_zero
test_c12_assertion_meaningfulness_reported
test_c15_exit_code_sanity_gate
test_c14_make_eval_is_not_a_placeholder
test_c14_make_eval_prints_metrics_table
test_c14_make_eval_propagates_exit_code
test_c16_make_dev_launches_clean_app
```
</content>
</invoke>

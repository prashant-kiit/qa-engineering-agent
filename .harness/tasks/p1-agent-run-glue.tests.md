# Tests coverage — `p1-agent-run-glue` (TDD red)

Tester artifacts (tests + fixtures only; **no implementation** written):

- `runner/tests/authoring_helpers.py` — **uniquely-named** shared module holding the constants
  (`BRD_SENTINEL`, `BRD_TOKEN`, `CREDENTIAL_REF`, `MCP_CONFIG_REL`, `QA_PROMPT_PATH`,
  `SECRET_SENTINEL`, `SAMPLE_OPENAPI`, `PLANNER_FIELDS`, …), the config factory (`make_config`),
  and the **mock agent-runner** seam substitutes (`RecordingRunner`, `RaisingRunner`). Test code
  imports these via `from authoring_helpers import ...` — NOT `from conftest import ...` — so the
  whole-repo suite can be collected together without the two bare `conftest` modules colliding.
- `runner/tests/conftest.py` — offline **pytest fixtures only** (`sample_openapi`,
  `expected_api_surface`, `clean_brd`, `token_bearing_brd`, `config_factory`, `valid_config`,
  `recording_runner`), delegating to `authoring_helpers`.
- `runner/tests/test_authoring.py` — the acceptance suite (21 test cases incl. the parametrized
  bad-placeholder case).

Run: `uv run pytest runner/tests -q`. No model key, no network, no browser, no real Claude Code / MCP.

## Red confirmation (right reason = missing behavior, not a broken harness)

```
runner/tests/test_authoring.py:21: in <module>
    from runner.authoring import DEFAULT_OUTPUT_DIR, run_authoring
E   ModuleNotFoundError: No module named 'runner.authoring'
=========================== short test summary info ============================
ERROR runner/tests/test_authoring.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.08s
```

The single failure is the import of the **module under test** (`runner.authoring`) — the intended
TDD-red signal. Verified the harness itself is sound and everything *else* resolves:
- `connectors.spec_loader` / `connectors.target_config` imports (before the failing line) succeed.
- `python -m py_compile` on both files: **compile OK** (no syntax errors).
- `conftest` imports cleanly in isolation; the composed unit-1 loader normalizes `SAMPLE_OPENAPI`
  to `title="Reference Shop API"`, ops `[(GET,/cart),(POST,/checkout)]`; the real QA prompt has
  **exactly one** `{{BRD}}` token; the shipped example config exists.
- Regression: `uv run pytest connectors/tests agent_config/tests -q` → **132 passed, 1 skipped**
  (units 1–5 unaffected).

## Acceptance criterion → test(s)

| # | Criterion | Test(s) |
|---|---|---|
| 1 | Loads target config via unit 2; result reflects fields | `test_loads_target_config_via_unit2` |
| 2 | Loads API surface via units 1+2 (`to_dict`), no network | `test_loads_api_surface_via_units_1_and_2` |
| 3a/3b/3d | BRD text present, no `{{BRD}}` residue, template preserved | `test_brd_injected_present_no_residue_and_template_preserved` |
| 3c | Replaced exactly once; token-bearing BRD body not double-substituted | `test_brd_replaced_exactly_once_no_double_substitution` |
| 4 | Deterministic assembly (byte-identical) | `test_deterministic_assembly` |
| 5 | MCP config path referenced (result + invocation) | `test_mcp_config_referenced` |
| 6 | Planner & Generator referenced, distinct + present | `test_planner_and_generator_referenced` |
| 7 | Runner invoked with full invocation bundle (pinned fields) | `test_runner_invoked_with_assembled_invocation` |
| 8 | No hard-coded live call; only injected runner used, offline | `test_no_hardcoded_live_call` |
| 9 | Generated tests written to output dir, byte-exact (nested paths) | `test_generated_tests_written_to_output_dir` |
| 10 | Default output path pinned (constant + None-resolution behavior) | `test_default_output_dir_constant`, `test_default_output_dir_used_when_none` |
| 11 | RunResult shape + values (all pinned attrs) | `test_run_result_shape_and_values` |
| 12 | Invalid/missing config → `TargetConfigError`; no run, no writes | `test_invalid_config_raises_unit2_error` |
| 13 | Spec load failure → `SpecLoadError` unchanged; no run, no writes | `test_spec_load_failure_propagates_unchanged` |
| 14 | Missing/unreadable BRD → named glue error naming the path | `test_missing_brd_raises_named_glue_error` |
| 15 | Bad `{{BRD}}` count (0 or 2) → named glue error; no run, no writes | `test_bad_placeholder_count_raises_named_glue_error` (params: zero-tokens, two-tokens) |
| 16a | Runner raises → surfaced (not swallowed) | `test_runner_exception_is_surfaced` |
| 16b | Runner error status → reflected; no false successful write | `test_runner_error_status_not_reported_as_success` |
| 17 | Secret-safety: sentinel leaks nowhere; only ref name flows | `test_only_credential_reference_flows_through` |
| 18 | Correct home + runnable tests; units 1–5 still pass | whole suite runs via `uv run pytest runner/tests -q`; regression run above |
| 19 | No regressions / no side effects beyond output dir | all tests write only to `tmp_path`; default-path test monkeypatches `DEFAULT_OUTPUT_DIR`; regression run above |

## Naming / seam assumptions the developer MUST honor

These are pinned by the task spec Interfaces section; encoded as binding contract by the tests:

0. **Test-artifact import hygiene (cross-dir collection fix):** shared test constants + the mock
   runners live in `runner/tests/authoring_helpers.py` and are imported as
   `from authoring_helpers import ...`. Do **not** reintroduce `from conftest import ...` — with no
   package `__init__.py`, two bare `conftest` modules (runner/tests + connectors/tests) collide under
   pytest's prepend importmode and break whole-suite collection.
1. **Public import path** `runner.authoring` exposing `run_authoring`, `DEFAULT_OUTPUT_DIR`,
   `AgentRunOutput`, and the `RunResult` type.
2. **Entry point** `run_authoring(config_source, *, agent_runner, output_dir=None, source_type="auto")`.
   `agent_runner` is a **required keyword** with no live default exercised by these tests.
3. **Runner seam is a callable** invoked exactly once as `agent_runner(invocation)`.
4. **Invocation bundle exposes its fields as attributes**: `system_prompt`, `api_surface`,
   `target_url`, `planner_fields`, `mcp_config_path`, `planner_agent`, `generator_agent`,
   `basic_auth_credential_ref`, `output_dir`. (`api_surface` may be the `ApiSurface` or its
   `to_dict()`; test normalizes.)
5. **Runner output type `AgentRunOutput`** importable from `runner.authoring`, constructed as
   `AgentRunOutput(status=<str>, generated_tests=<mapping rel-name→content>)` — the mock returns this
   so the glue's read path is unambiguous.
6. **RunResult attributes** (pinned names): `config`, `system_prompt`, `api_surface`,
   `mcp_config_path`, `planner_agent`, `generator_agent`, `output_dir`, `written_test_paths`,
   `runner_status`. `config` may be a `TargetConfig` or its `to_dict()` (test normalizes via
   `hasattr(cfg,"to_dict")`).
7. **`DEFAULT_OUTPUT_DIR`** value ends with `runner/generated` and is a **module global consulted at
   call time** for the `output_dir=None` default (so `monkeypatch.setattr(authoring,
   "DEFAULT_OUTPUT_DIR", ...)` redirects the default — used to avoid polluting the repo).
8. **QA system-prompt path is a monkeypatchable module-level attribute** whose value ends with
   `qa_system_prompt.md` (criterion-15 test discovers it by scanning module attributes and patches
   it to a bad-token prompt). The developer must keep the prompt path as a module attribute.
9. **Named glue error(s)** are defined in the `runner` package (`type(exc).__module__` starts with
   `"runner"`) and are **not** subclasses of `connectors` `TargetConfigError` / `SpecLoadError`
   (those propagate unchanged). The BRD-missing error message must **contain the BRD path string**.
10. **`generated_tests` mapping keys are relative filenames** written under `output_dir` (nested
    paths like `api/orders.api.spec.ts` supported); `written_test_paths` lists the files written.
11. **Error paths short-circuit before the runner**: on invalid config / spec failure / missing BRD /
    bad placeholder count, the runner is **not** invoked and **no** files are written.

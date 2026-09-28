# Test coverage — `p1-opencode-runner` (TDD red)

Failing acceptance tests for the OpenCode runner adapter, authored from the spec ONLY
(no implementation read). Exercised with an **injected mock command-runner** — no model
key, no network, no browser, no real OpenCode process.

## Files created (tests only)
- `runner/tests/test_opencode_runner.py` — the acceptance suite (criteria 1–19).
- `runner/tests/opencode_helpers.py` — uniquely-named shared helpers (mock command-runner
  `FakeCommandRunner`, `FakeCompleted`, `make_invocation`, surface-collection + argv
  helpers, markers/sentinels, lazy `import_adapter`). NOT named `conftest` — avoids the
  cross-dir `conftest` collision under pytest's prepend importmode (same lesson as unit-6's
  `authoring_helpers`).

Existing unit-6 files (`test_authoring.py`, `conftest.py`, `authoring_helpers.py`) were
**not** modified. `authoring_helpers.make_config` is reused (import) for the through-glue
tests (C1, C10) since its config shape is already proven against the unit-2 loader.

## Criterion → test(s)

| # | Criterion | Test(s) |
|---|-----------|---------|
| 1 | Satisfies unit-6 `AgentRunner` seam (callable, drives through `run_authoring`) | `test_c1_satisfies_agentrunner_seam_through_glue` |
| 2 | Invokes `opencode` binary + non-interactive `run` subcommand | `test_c2_invokes_opencode_binary_in_run_mode` |
| 3 | Selects `openai/gpt-4o-mini`; model is a bumpable knob | `test_c3_selects_gpt4o_mini_model`, `test_c3_model_is_bumpable_config_value` |
| 4 | Wires MCP via governing OpenCode config (`mcp` key, `@playwright/mcp@0.0.41`) | `test_c4_wires_mcp_via_governing_config` (+ `test_c18_connector_config_artifact_shape`) |
| 5 | Delivers BRD-injected system prompt + 7 fields; no `{{BRD}}` re-inject; prompt file untouched | `test_c5_delivers_brd_injected_prompt_and_seven_fields`, `test_c5_does_not_modify_shared_prompt_file` |
| 6 | Points at `target_url` | `test_c6_points_at_target_url` |
| 7 | Planner precedes Generator (both present, distinct) | `test_c7_planner_precedes_generator` |
| 8 | Runs in a workspace distinct from `output_dir` (asserted via `cwd`) | `test_c8_workspace_distinct_from_output_dir` |
| 9 | Captures generated tests into byte-exact, workspace-relative mapping | `test_c9_captures_generated_tests_into_mapping` |
| 10 | End-to-end: glue writes exactly the captured files under `output_dir` | `test_c10_end_to_end_through_glue_writes_files` |
| 11 | Model key in child env only; sentinel absent from argv/prompt/files/output/logs | `test_c11_model_key_injected_into_child_env_only` |
| 12 | Missing model credential → named error before spawn; names ref, no secret | `test_c12_missing_model_credential_raises_named_error` |
| 13 | Target-app auth stays a reference; resolved sentinel absent from every surface | `test_c13_target_auth_stays_reference_only` |
| 14 | Non-zero exit → non-`ok` status + scrubbed detail; not raised | `test_c14_nonzero_exit_yields_nonok_scrubbed_detail`, `test_c14_normal_run_failure_is_not_an_exception` |
| 15 | Exit 0 but no tests → non-`ok` status, empty mapping | `test_c15_no_tests_produced_yields_nonok` |
| 16 | Missing connector config → named error | `test_c16_missing_connector_config_raises_named_error` |
| 17 | Deterministic construction (identical argv modulo temp workspace + config) | `test_c17_deterministic_construction` |
| 18 | Pinned import path/constants/errors + connector config + agent defs at pinned paths | `test_c18_pinned_constants_and_import_path`, `test_c18_connector_config_artifact_shape`, `test_c18_opencode_agent_defs_exist_and_reference_shared_prompt` |
| 19 | No egress / no writes outside the workspace; glue is single writer of `output_dir` | `test_c19_no_egress_no_writes_outside_workspace` |

## Naming / shape assumptions the developer MUST honor (spec leaves latitude here)

1. **Named adapter error = `OpenCodeRunnerError`.** The spec says the error name is the
   developer's choice (example `OpenCodeRunnerError`). The tests pin
   `runner.opencode_runner.OpenCodeRunnerError` as the raised type for C12 and C16, and
   require it to be an `Exception` subclass (C18). If a different name is chosen, these
   tests must be updated with the reviewer's sign-off.
2. **Constructor knobs (keyword):** `command_runner=`, `model=`, `opencode_config_path=`.
   All must have working defaults (default construction possible). Tests inject
   `command_runner=` and override `model=` / `opencode_config_path=`.
3. **Command-runner seam signature:** `command_runner(argv, *, cwd, env, input=None,
   timeout=None) -> CompletedCommand` where `CompletedCommand` exposes `.returncode`,
   `.stdout`, `.stderr` (binding attr names). The adapter routes EVERY OpenCode call
   through this seam.
4. **Module constants (binding names):** `DEFAULT_MODEL == "openai/gpt-4o-mini"`,
   `OPENAI_API_KEY_ENV == "OPENAI_API_KEY"`, `OPENCODE_CONFIG_PATH ==
   "connectors/opencode/opencode.json"`, `OPENCODE_BIN == "opencode"`,
   `PLANNER_AGENT == "qa-planner"`, `GENERATOR_AGENT == "qa-generator"`.
5. **argv shape:** `argv[0]` basename `opencode`; `run` within the first two args; model
   selected via `--model <m>` / `--model=<m>` / `-m <m>`; agents (if two-run form) via
   `--agent <name>`. C7 accepts **either** two ordered `--agent` runs **or** a single
   orchestrator with both roles present in the governing config/message (spec latitude).
6. **Config discovery (C4):** any of `OPENCODE_CONFIG` env → `--config <path>` → an
   `opencode.json` copied into the run workspace cwd is accepted; the resolved config must
   declare `model: openai/gpt-4o-mini`, a top-level `mcp` key, and `@playwright/mcp@0.0.41`.
7. **Workspace ≠ output_dir (C8/C19):** the `cwd` handed to the command-runner must not be
   `invocation.output_dir` and must not be the repo root; the adapter must not write the
   generated tests into `output_dir` itself (the glue is the single writer). If two runs
   share one workspace, the mock writes canned files into each call's `cwd` — the adapter
   is assumed to collect from the workspace it used as `cwd`.
8. **Output capture globs:** the two canned files (`cart.spec.ts`, `orders.api.spec.ts`)
   must match the pinned capture globs; both are returned byte-exact with
   workspace-relative keys. No specific constant name for the globs is asserted.
9. **Agent defs (C18):** `.opencode/agent/qa-planner.md` + `.opencode/agent/qa-generator.md`
   referencing `agent_config/qa_system_prompt.md` is the pinned default; the inline-`agent`
   block in `connectors/opencode/opencode.json` (roles `qa-planner`/`qa-generator`,
   referencing the shared prompt) is accepted as the spec's alternative.
10. **Secret scan excludes the child env.** The model key legitimately lives in the child
    env (C11 requires it there), so env is excluded from the "sentinel must be absent"
    surface set for both C11 and C13.
11. **`planner_fields["depth"]` is a constrained enum.** C1/C10 push the marker dict through
    the real glue, so `depth` must be a valid unit-2 enum value (`{smoke, regression,
    exhaustive}`) — the helper uses `"regression"` (still assertable in the delivered
    surface for C5). The other six fields are unconstrained and keep their `*-MARKER-*`
    sentinels.

## Red run (legitimate — missing adapter module + missing config/agent artifacts)

`uv run pytest runner/tests/test_opencode_runner.py -q` → **24 failed in 0.19s**.
- Adapter tests fail with `ModuleNotFoundError: No module named 'runner.opencode_runner'`
  (lazy `import_adapter()` — the missing implementation).
- `test_c18_connector_config_artifact_shape` fails with
  `AssertionError: missing OpenCode connector config: .../connectors/opencode/opencode.json`.
- `test_c18_opencode_agent_defs_exist_and_reference_shared_prompt` fails with
  `AssertionError: neither .opencode/agent/qa-*.md files nor an inline `agent` block present`.

Combined no-regression run:
`uv run pytest runner/tests connectors/tests agent_config/tests -q`
→ **24 failed, 153 passed, 1 skipped** — the 24 failures are exactly this suite; all
existing unit-1..6 / agent_config tests still pass; no collection collision.

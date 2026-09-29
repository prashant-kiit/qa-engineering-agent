# Tester coverage — `p1-agent-authoring-gate` (Phase 1 EXIT GATE)

**Test file (new, model-free):**
`eval/tests/test_agent_authoring_gate_verification.py`
Runnable via `uv run pytest eval/tests -q` (also intended behind `make authoring-gate`).
Pre-existing Phase-0 suite `eval/tests/test_eval_harness_verification.py` is untouched and still
collects/co-exists (50 tests collected across the dir, no import collision — helpers are local to
the module, no shared `conftest`).

These tests are **deterministic and model-free** (criterion **V8**): they bind to the **committed**
artifacts the one-time live OpenCode run will produce and re-derive the gate. They never call the
live model, never need `OPENAI_API_KEY`, and perform no OpenAI egress. Clean-pass (V2) is bound to
the committed report's clean-variant breakdown rather than re-launching the app+model, per the
task's "prefer binding to the committed report metrics to keep verification deterministic".

## Acceptance criterion → test(s)

| Criterion (spec) | Test(s) |
|---|---|
| **V1** Generated suite present + non-trivial (≥1 `*.spec.ts`/`*.api.spec.ts`, real `expect(...)`, valid/collectable, agent config → `./tests/generated`) | `test_v1_generated_dir_exists_and_has_spec_files`, `test_v1_each_generated_spec_has_real_assertions`, `test_v1_agent_config_exists_and_targets_generated_dir`, `test_v1_generated_suite_is_collectable_by_playwright_list` |
| **V2** Passes on clean (reproduced, model-free) — `false_positive_rate == 0` encoded in committed report | `test_v2_clean_pass_encoded_in_committed_report` |
| **V3** Committed eval report exists + well-formed (valid JSON, 4 pinned metric keys as numbers 0..1, records GENERATED suite + `reruns` + per-variant caught breakdown; `.txt` rendering) | `test_v3_eval_report_json_exists_and_metrics_wellformed`, `test_v3_eval_report_txt_exists`, `test_v3_eval_report_records_generated_suite_and_reruns`, `test_v3_eval_report_has_per_variant_caught_breakdown` |
| **V4** Thresholds met (bound to committed report): `bug_catch_rate > 0.0` (≥1/3), `false_positive_rate == 0.0`, `flake_rate == 0.0`, `assertion_meaningfulness_rate > 0.0` — beats naive floor | `test_v4_bug_catch_rate_beats_naive_floor`, `test_v4_false_positive_rate_is_zero`, `test_v4_flake_rate_is_zero`, `test_v4_assertion_meaningfulness_rate_positive` |
| **V5** Provenance manifest present + stamped fields + secret-free | `test_v5_manifest_exists_and_records_pinned_provenance_fields`, `test_v5_manifest_metrics_beat_thresholds_consistently`, `test_v5_no_secret_leaks_in_committed_artifacts` |
| **V8 / Secret-safety** `.env` gitignored + untracked (key never committed) | `test_v8_env_is_gitignored_and_untracked` |

**Not covered here (by design — belong to the Reviewer / other roles, per the spec's role split):**
- **G1–G6** are the live-run *demonstration* (Developer/orchestrator with the key); the Tester only
  binds to their committed outputs (V1–V5).
- **V6** grounding/meaningfulness audit and independent re-run/re-score is the **Reviewer's** manual
  judgement (V4's `assertion_meaningfulness_rate > 0` gives the objective floor the Reviewer confirms).
- **V7** no-regressions (baseline `make eval`, `make test`, units 1–7 + unit-7 adapter suites,
  unchanged clean app) is enforced by the existing per-unit suites + the reviewer running them; not
  re-implemented here to avoid duplicating slow browser/eval runs.

## Red run (this file, artifacts absent)

```
$ uv run pytest eval/tests/test_agent_authoring_gate_verification.py -q
16 failed, 1 passed in 0.10s
```

All 16 gate assertions fail for the **right reason** — the committed artifacts do not exist yet
(`reference_app/e2e/tests/generated/`, `reference_app/e2e/playwright.agent.config.ts`,
`eval/reports/p1-agent-authoring-gate.eval.json` + `.txt`,
`eval/reports/p1-agent-authoring-gate.run.json`). The one passing test
(`test_v8_env_is_gitignored_and_untracked`) asserts an already-true secret-safety invariant
(`.env` is in `.gitignore` and untracked) that must **remain** true — it is not a shortcut.

Sample failure (representative):
```
provenance manifest missing at .../eval/reports/p1-agent-authoring-gate.run.json —
the one-time live authoring run has not committed this artifact yet
(legitimate TDD-red: the gate's committed outputs are absent).
```

Whole-dir collection is clean (no collision with the Phase-0 module):
```
$ uv run pytest eval/tests -q --co
50 tests collected in 0.04s   (exit 0)
```

## Assumptions the Developer MUST honor (binding contract encoded in the tests)

### Paths (exact)
- Generated tests committed under `reference_app/e2e/tests/generated/` with ≥1 file matching the
  capture globs `*.spec.ts` / `*.test.ts` / `*.api.spec.ts`, each containing ≥1 `expect(...)`.
- `reference_app/e2e/playwright.agent.config.ts` exists and its source matches
  `testDir: './tests/generated'` (single/double quotes accepted).
- `eval/reports/p1-agent-authoring-gate.eval.json` (machine), `.eval.txt` (human, must contain the
  four metric names), `.run.json` (manifest).

### Eval report JSON shape (reuse `eval/score.py`'s `public_report` structure)
- Top-level `metrics` object with **exactly** the four keys `bug_catch_rate`,
  `false_positive_rate`, `flake_rate`, `assertion_meaningfulness_rate`, each a number in `0..1`.
- Top-level `reruns` (int ≥ 2).
- Top-level `variants` object keyed by variant id including `none` and the three buggy variants;
  each buggy variant entry has a `caught` (bool); each entry has a `tests` map of
  `test_id -> [bool per re-run]` (the clean `none` entry's per-test run arrays are what V2 reads —
  every generated test must be `true` on every clean re-run).
- The report must reference the **generated** suite (JSON contains `tests/generated` and/or
  `playwright.agent.config.ts`) and must **not** reference the baseline (`tests/eval` /
  `playwright.eval.config.ts`). If `score.py`'s current `public_report` does not already record the
  scored-suite path, add such a field (any key whose value carries `tests/generated` /
  `playwright.agent.config.ts` satisfies the check).

### Manifest JSON fields (exact key names asserted)
`cli == "opencode"`; a CLI-version field (any of `cli_version`, `opencode_version`, or a `version`
sub-key under a `cli` object); `model == "openai/gpt-4o-mini"`;
`mcp_server == "@playwright/mcp@0.0.41"`; `reference_app_version` (must equal
`reference_app/VERSION` = `0.1.0`); `timestamp` (non-empty ISO-8601 string); `reruns` (int ≥ 2);
`naive_bug_catch_floor == 0.0`; a `metrics` object with the four keys (0..1); `thresholds`;
`generated_suite_path`; `eval_report_path`; `gate_passed == true` (JSON bool).

### Metric semantics (do NOT redefine)
Reuse `eval/score.py`'s four metric definitions verbatim. The gate binds to the **committed report's
values**, NOT to `score.py`'s Phase-0 exit code (which demands `bug_catch == 1.0`; this Phase-1 gate
is *better-than-naive*: `bug_catch_rate > 0.0`, i.e. ≥ 1/3).

### Secret-safety
No token matching `sk-…` or `e2b_…` may appear in any committed generated spec, the eval report
(`.json`/`.txt`), or the manifest. `.env` stays in `.gitignore` and untracked.

---

## AMENDMENT — Adapter headless-execution fix (AF1–AF6, Interpretation #4 concrete)

**Source:** `.harness/tasks/p1-agent-authoring-gate.md` → "Adapter headless-execution fix
(Interpretation #4, concrete)".

**New test file (additive only, mock-only, no live process):**
`runner/tests/test_opencode_runner_headless_fix.py`
**New helper module (additive only, uniquely named, NOT `conftest`):**
`runner/tests/opencode_headless_fix_helpers.py`

These do **not** modify `runner/tests/test_opencode_runner.py`,
`runner/tests/test_opencode_runner_credential_exception.py`, or `runner/tests/opencode_helpers.py`
— they only import (read-only) the existing `opencode_helpers.FakeCommandRunner` /
`import_adapter` / `make_invocation` seam those suites already use. Runnable via
`uv run pytest runner/tests -q`.

### Acceptance criterion → test(s)

| Criterion (spec) | Test(s) |
|---|---|
| **AF1** `--auto` + `--dir <cwd>` on every invocation | `test_af1_every_call_has_auto_and_dir_matching_cwd` |
| **AF2** continue-session flag (`--continue`/`-c`) absent on Planner (1st), present on Generator (2nd) | `test_af2_continue_absent_on_planner_present_on_generator` |
| **AF3 (general)** `OPENCODE_CONFIG` resolves to a single materialized, workspace-local JSON file (never the shipped path); identical across both calls of one run; preserves shipped `model`/`mcp` unchanged; shipped `connectors/opencode/opencode.json` byte-unmodified before/after | `test_af3_config_is_workspace_local_materialized_json` |
| **AF3a** agent-role `{file:...}` refs (`agent.qa-planner.prompt` / `agent.qa-generator.prompt`) resolve, relative to the materialized config's own parent dir, to in-workspace files **byte-identical** to their shipped source (`.opencode/agent/qa-{planner,generator}.md`) | `test_af3a_agent_role_file_refs_are_byte_identical_in_workspace` |
| **AF3b** `instructions` list entries resolve, relative to the materialized config's own parent dir, to an in-workspace file whose content equals **this run's `invocation.system_prompt`** (already BRD-injected, token-free) — **not** a byte-copy of the shipped `agent_config/qa_system_prompt.md` **template** (which still contains the literal, unresolved `{{BRD}}`); the materialized file must never contain `{{BRD}}` | `test_af3b_instructions_resolve_to_injected_system_prompt_not_shipped_template` |
| **AF4** materialized `permission.external_directory == "deny"`, never `"allow"`, across default / model-override / custom-`opencode_config_path` constructor variants | `test_af4_permission_external_directory_is_deny`, `test_af4_external_directory_never_allow_across_constructor_variants` |
| **AF5** mock-only verifiability (no live process, no network, no real key) | Satisfied by construction — every AF1–AF4 test above routes exclusively through the existing injected `opencode_helpers.FakeCommandRunner` (never `mod.default_command_runner`), with only the existing placeholder `MODEL_KEY_SENTINEL` credential (per unit 7's established pattern). No dedicated always-green "methodology" test was added, per the instruction that every new test in this suite must be a legitimate red today. |
| **AF6** no regression to unit 7 / 7.5's pinned behaviors | Verified by running the full pre-existing suites unmodified (`test_opencode_runner.py`, `test_opencode_runner_credential_exception.py`) alongside the new file — see red run below. |

### Naming / design assumptions recorded
- `flag_value(argv, "--dir")` / literal `"--auto"` / literal `"--continue"`/`"-c"` membership checks
  mirror the existing helper style (`model_arg`, `agent_flags_in_order` in `opencode_helpers.py`) —
  accepting both `--flag value` and `--flag=value` forms for `--dir` per that established
  convention; `--auto` and `--continue`/`-c` are checked as bare flags (no value), per the spec's
  own phrasing ("includes `--auto`", "does NOT contain a continue-session flag").
- **CORRECTION (post-authoring, orchestrator-traced spec imprecision — AF3 split into AF3a/AF3b):**
  the original single AF3 test required **every** `instructions`/`{file:...}` reference — including
  the one standing in for `agent_config/qa_system_prompt.md` — to resolve to a **byte-identical**
  workspace copy of its shipped source. The Developer's implementation attempt surfaced a genuine
  structural conflict: the shipped `agent_config/qa_system_prompt.md` is the raw, **unresolved
  TEMPLATE** (it literally contains `{{BRD}}` — verified in
  `test_af3b_instructions_resolve_to_injected_system_prompt_not_shipped_template`'s own premise
  check) and materializing it byte-for-byte into the workspace directly contradicts the
  **frozen, untouched** `test_c5_delivers_brd_injected_prompt_and_seven_fields` (in
  `test_opencode_runner.py`), which scans every file under the workspace (via the shared
  `agent_visible_text` helper) and asserts the literal `{{BRD}}` token is absent. The TPM corrected
  `.harness/tasks/p1-agent-authoring-gate.md`'s AF3 bullet into two: **AF3a** (agent-role
  `{file:...}` refs — legitimately byte-identical, since `.opencode/agent/qa-*.md` never change at
  runtime) and **AF3b** (the `instructions` entry — must resolve to **`invocation.system_prompt`**,
  the already-injected/token-free value the run actually used, never the raw shipped template).
  `test_af3_config_is_workspace_local_materialized_json` was narrowed to only the config-location /
  `model`/`mcp`/shipped-file-unmodified facts; the file-reference-content assertions were split out
  into `test_af3a_...` (byte-identical, unchanged logic) and a new `test_af3b_...` (content ==
  `invocation.system_prompt`, and `{{BRD}}` absent).
- AF3a's file-content comparisons resolve the shipped config's `{file:...}` strings relative to
  **`REPO_ROOT`** (the repo-root-relative convention the shipped `connectors/opencode/opencode.json`
  literally uses today, e.g. `"{file:./.opencode/agent/qa-planner.md}"`). The materialized side is
  resolved relative to the **materialized config file's own parent directory**, per AF3's binding
  text. `{file:...}` reference matching assumes the materialized config mirrors the shipped config's
  JSON *structure* (only path *values* rewritten), so `find_file_refs` can pair them up by identical
  json-path position, in traversal order.
- AF3b's own premise check reads the shipped `agent_config/qa_system_prompt.md` fresh from disk and
  asserts it still contains `{{BRD}}` (anchoring *why* a byte-copy would be wrong), then asserts the
  crafted invocation's `system_prompt` does **not** contain `{{BRD}}` (mirroring the real unit-6 glue
  output), before asserting the materialized instructions file equals `invocation.system_prompt`
  exactly and is itself `{{BRD}}`-free.
- AF4's `test_af4_external_directory_never_allow_across_constructor_variants` requires the key to be
  **present** (not just never `"allow"`), because a silently-absent key would otherwise let the test
  pass vacuously today (no `permission` block exists yet) — that would not be a legitimate red. This
  strengthens, but does not contradict, AF4's literal text ("if the adapter sets the key at all it
  must be `\"deny\"`"): pairing the presence requirement with the negative-invariant framing is the
  only way to make this specific test a genuine red now.
- The custom-`opencode_config_path` variant in AF4's second test uses a **minimal** input config
  (`model` only, no `instructions`/`agent`/`permission`) rather than a full copy of the shipped
  config, to keep that variant's assertions scoped to AF4 (permission handling) without coupling it
  to AF3's file-reference-resolution mechanics for a config file living outside
  `connectors/opencode/`.

### Red run — at authoring time (before any adapter implementation existed)
`uv run pytest runner/tests/test_opencode_runner_headless_fix.py -q`:
```
5 failed in 0.06s (abbreviated; each fails for the missing-mechanism reason, not an import/harness error)

FAILED test_af1_every_call_has_auto_and_dir_matching_cwd
  AssertionError: missing auto-approve-permissions flag in argv: [...] (no --auto, no --dir at all)

FAILED test_af2_continue_absent_on_planner_present_on_generator
  AssertionError: Generator (second) invocation must carry a continue-session flag: [...]
  (current adapter never emits --continue/-c on either call)

FAILED test_af3_config_is_workspace_local_materialized_json (pre-split; now AF3/AF3a/AF3b)
  AssertionError: OPENCODE_CONFIG must point at a materialized workspace-local file, never the
  shipped connectors/opencode/opencode.json path
  assert PosixPath('.../connectors/opencode/opencode.json') != PosixPath('.../connectors/opencode/opencode.json')
  (current _build_env points OPENCODE_CONFIG straight at the resolved shipped path)

FAILED test_af4_permission_external_directory_is_deny
  AssertionError: materialized config is missing a `permission` block
  assert None is not None

FAILED test_af4_external_directory_never_allow_across_constructor_variants
  AssertionError: variant 'default' ({}): materialized config must explicitly set
  permission.external_directory (got permission={})
```
All 58 pre-existing `runner/tests` tests passed unmodified at this point; `58 passed, 5 failed`.

### Re-check after the AF3a/AF3b correction, against the Developer's in-progress implementation
The Developer had begun implementing against the (pre-correction) single AF3 test — an
uncommitted, in-progress `runner/opencode_runner.py` diff was already present in the working tree
by the time the AF3a/AF3b split landed. `uv run pytest runner/tests -q` against that in-progress
state:
```
FAILED runner/tests/test_opencode_runner.py::test_c5_delivers_brd_injected_prompt_and_seven_fields
FAILED runner/tests/test_opencode_runner_headless_fix.py::test_af3b_instructions_resolve_to_injected_system_prompt_not_shipped_template
2 failed, 63 passed in 0.16s
```
- `test_af3b_...` is **red for the right reason** (legitimate, expected): the in-progress
  `_materialize_ref`/`_materialize_config` still copies the shipped
  `agent_config/qa_system_prompt.md` template byte-for-byte for the `instructions` entry, so its
  content is the raw template (containing `{{BRD}}`), not `invocation.system_prompt`.
  `test_af1`/`test_af2`/`test_af3` (general)/`test_af3a`/both `test_af4` tests are already green —
  the Developer's in-progress work already covers those mechanisms correctly.
- **Finding, reported transparently (not caused by, and not fixed by, this Tester pass):**
  `test_c5_delivers_brd_injected_prompt_and_seven_fields` — a **frozen, unmodified, pre-existing**
  unit-7 test — is currently **failing** against that same in-progress implementation, because
  copying the raw `{{BRD}}`-containing template into the workspace (the old, pre-correction AF3
  behavior) lands a file under the workspace that trips `test_c5`'s "`{{BRD}}` absent from every
  workspace file" scan (`agent_visible_text`). This is exactly the conflict the AF3a/AF3b spec
  correction targets. Per this Tester's scope (tests only, no source edits), it is **not** fixed
  here — it is expected to resolve once the Developer updates `_materialize_config` to write
  `invocation.system_prompt` for the `instructions` entry (satisfying the corrected `test_af3b_...`)
  instead of copying the shipped template, which will simultaneously stop placing `{{BRD}}` in the
  workspace and restore `test_c5` to green. `test_c13_target_auth_stays_reference_only` — the other
  test the coordinator asked to confirm — **does** still pass unmodified.

```
$ uv run pytest runner/tests connectors/tests agent_config/tests -q
2 failed, 195 passed, 1 skipped in 2.03s  (same two failures as above; no other regressions)
```
No collision, no regression outside the 5 new legitimate reds — the pre-existing 195 (190 pass + 1
skip, unchanged) collect and pass exactly as before this addition.

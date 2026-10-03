# Review — `p1-agent-authoring-gate` amendment: OpenCode adapter headless-execution fix (AF1–AF6)

**Verdict: APPROVE**

## Scope of this review
Diff under review: `runner/opencode_runner.py` (163 insertions / 15 deletions) on
`harness/build`, plus the Tester's new files `runner/tests/test_opencode_runner_headless_fix.py`
and `runner/tests/opencode_headless_fix_helpers.py`. Spec section: "Adapter headless-execution
fix (Interpretation #4, concrete)" in `.harness/tasks/p1-agent-authoring-gate.md` (AF1–AF6,
including the corrected AF3/AF3a/AF3b split), cross-checked against
`.harness/tasks/p1-agent-authoring-gate.tests.md`'s AMENDMENT/CORRECTION sections.

## 1. Test suite — run myself

```
$ uv run pytest runner/tests -q
65 passed in 0.12s
```
(58 original unit-7/7.5 tests + 7 new AF tests, exactly as expected.)

```
$ uv run pytest runner/tests/test_opencode_runner.py::test_c5_delivers_brd_injected_prompt_and_seven_fields \
                runner/tests/test_opencode_runner.py::test_c13_target_auth_stays_reference_only -v
test_c5_delivers_brd_injected_prompt_and_seven_fields PASSED
test_c13_target_auth_stays_reference_only PASSED
2 passed in 0.04s
```

Both frozen tests individually confirmed green. `git diff runner/tests/test_opencode_runner.py`
and `git diff runner/tests/test_opencode_runner_credential_exception.py` and
`git diff runner/tests/opencode_helpers.py` are all **empty** — none of unit 7's tests or shared
helpers were modified; the amendment is purely additive test-wise.

```
$ uv run pytest runner/tests connectors/tests agent_config/tests -q
197 passed, 1 skipped in 1.87s
```
Matches the expected combined count exactly.

## 2. AF3b correctness — verified independently, not just from the report

Traced the pipeline by hand:
- `connectors/opencode/opencode.json` (read directly): `"instructions": ["agent_config/qa_system_prompt.md"]`
  — a plain relative path (not `{file:...}`) — and `"agent"."qa-planner"/"qa-generator"."prompt"` use
  `"{file:./.opecode/agent/qa-*.md}"` — the `{file:...}` form. The implementation correctly
  distinguishes these two syntaxes (`_materialize_instruction` for the `instructions` list vs.
  `_materialize_file_refs`/`_FILE_REF_RE` for `{file:...}` refs) — this structural split is exactly
  what AF3a/AF3b requires and is not conflated.
- `runner/opencode_runner.py:386-418` `_materialize_config`: for every `instructions` entry it calls
  `_materialize_instruction(entry, workspace, invocation.system_prompt)`, which writes
  `invocation.system_prompt` (not a copy of the shipped file) to the mirrored relative path under the
  workspace (`opencode_runner.py:365-384`). The shipped `agent_config/qa_system_prompt.md` is never
  opened/read for its content anywhere in the diff (only `config_path` — the opencode.json — is read
  for JSON parsing; the `agent_config/qa_system_prompt.md` path is never referenced in
  `opencode_runner.py` at all except transitively as a string value copied unchanged from the JSON).
- Traced `invocation.system_prompt`'s origin in `runner/authoring.py`: `run_authoring` calls
  `_inject_brd(prompt_template, config.brd_path)` (`authoring.py:280`), which replaces the single
  `{{BRD}}` token exactly once (`authoring.py:196-212`, raising `AuthoringError` if the token isn't
  present exactly once) and passes the result into `AuthoringInvocation(system_prompt=system_prompt, ...)`
  (`authoring.py:295,327`). This is structurally guaranteed token-free by the time the adapter ever
  sees it — confirmed by construction, not merely trusted.
- `test_af3b_...` independently re-derives this: it asserts the shipped template still contains
  `{{BRD}}` (premise anchor), asserts the crafted `invocation.system_prompt` used in the test does
  not, then asserts the materialized instructions-file content equals `invocation.system_prompt`
  exactly and is itself `{{BRD}}`-free. This is a genuine, non-circular proof.

Verdict: AF3b's correctness is real, not merely reported.

## 3. AF4 security property — verified directly, unconditional

`_materialize_config` (`opencode_runner.py:403-406`):
```python
permission = dict(materialized.get("permission") or {})
permission["external_directory"] = "deny"
materialized["permission"] = permission
```
This runs unconditionally on every call to `_materialize_config`, which itself runs exactly once per
`__call__` regardless of constructor knobs (`opencode_config_path`, `model`, etc. — none of these
gate or branch around the permission-forcing line). There is no `if`/config-provided override path
that could produce `"allow"` — the shipped config today has no `permission` key at all, and even if
a custom input config declared `permission.external_directory = "allow"`, the line above
unconditionally overwrites it to `"deny"` after `copy.deepcopy(shipped)`. Confirmed by reading the
whole file (no other write path to a `permission` key exists) and by the two dedicated tests
(`test_af4_permission_external_directory_is_deny`, and the negative-invariant
`test_af4_external_directory_never_allow_across_constructor_variants` across default/model-override/
custom-config-path variants, the latter using a minimal input config with no `permission` block of
its own, proving the adapter — not the input file — enforces the deny). All pass.

## 4. AF1/AF2 — verified via `_build_argv` call sites, not just tests

`_build_argv` (`opencode_runner.py:422-439`) unconditionally appends `OPENCODE_AUTO_FLAG` ("--auto")
and `OPENCODE_DIR_FLAG` + `str(workspace)` ("--dir <workspace>") to every argv it builds, then appends
`OPENCODE_CONTINUE_FLAG` ("--continue") only `if continue_session`. The single call site
(`opencode_runner.py:491-495`, inside the `for index, (role_label, agent) in enumerate(runs)` loop)
passes `continue_session=(index > 0)` — `False` for the first (Planner, index 0) call, `True` for the
second (Generator, index 1) call. `workspace` (same value for both calls) is also what's passed as
`cwd=str(workspace)` to the command-runner a few lines later, so `--dir`'s value structurally equals
the call's `cwd` by construction, not by coincidence. Matches AF1/AF2 exactly.

## 5. Shipped-file-untouched — verified

`connectors/opencode/opencode.json` is only ever reached via `_resolve_config_path` → passed into
`_materialize_config(workspace, config_path, invocation)`, where the only operation on `config_path`
is `json.loads(config_path.read_text(...))` (read-only) followed by `copy.deepcopy`. Every
`.write_bytes`/`.write_text` call in the diff targets either `dest` (a workspace-local path built
from `workspace / rel_path`) or `materialized_path` (`workspace / MATERIALIZED_CONFIG_FILENAME`) —
never `config_path` itself. `test_af3_config_is_workspace_local_materialized_json` empirically
confirms byte-identical before/after on the shipped file. Confirmed both by static reading and by
the passing test.

## 6. Scope discipline

```
$ git status --porcelain
 M runner/opencode_runner.py
?? .harness/tasks/p1-agent-authoring-gate.md
?? .harness/tasks/p1-agent-authoring-gate.tests.md
?? eval/tests/test_agent_authoring_gate_verification.py
?? runner/tests/opencode_headless_fix_helpers.py
?? runner/tests/test_opencode_runner_headless_fix.py
```
Only `runner/opencode_runner.py` is modified source; the other untracked files are task/tests
artifacts (spec, tester coverage note, the Tester's new test files) outside this review's code-diff
concern. Confirmed **empty** diffs on all protected/adjacent files: `connectors/opencode/opencode.json`,
`.opencode/**`, `agent_config/**`, `runner/authoring.py`, `runner/tests/test_opencode_runner.py`,
`runner/tests/test_opencode_runner_credential_exception.py`, `runner/tests/opencode_helpers.py`. No
`eval/score.py` or `Makefile` changes in this diff. No scope creep.

## 7. Test adequacy (AF1–AF6, including the corrected split)

The 7 AF tests genuinely exercise AF1–AF6:
- `test_af1_every_call_has_auto_and_dir_matching_cwd` — checks *every* recorded call (not just one),
  and that `--dir`'s value resolves equal to that call's `cwd`, not just "some --dir somewhere."
- `test_af2_continue_absent_on_planner_present_on_generator` — checks absence on first AND presence
  on second (both directions), covering `--continue`/`-c` synonyms.
- `test_af3_config_is_workspace_local_materialized_json` — checks not-the-shipped-path, in-workspace,
  valid JSON, `model`/`mcp` preserved, identical across both calls, AND the shipped-file-unmodified
  negative check, all in one test with real value comparisons against fresh-loaded shipped config
  (not hardcoded expectations that could silently drift).
- `test_af3a_...` — pairs shipped vs. materialized `{file:...}` refs by structural JSON-path position
  (robust to ordering) and does true byte-content comparison, not existence-only.
- `test_af3b_...` — as analyzed above, a genuinely non-circular test with a self-verifying premise
  check.
- `test_af4_permission_external_directory_is_deny` and the negative-invariant variant test — the
  latter explicitly requires the key be *present* (not vacuously passing on an absent key), a
  deliberate strengthening documented in the tests.md CORRECTION notes; this closes the obvious gap
  of a test that could trivially pass if the adapter simply never set the key.
- AF5 (mock-only) is satisfied by construction — every test above routes exclusively through
  `FakeCommandRunner`, confirmed by reading the test file (no `default_command_runner` usage, no
  network, only `MODEL_KEY_SENTINEL`).
- AF6 (no regression) — covered by the full pre-existing suites passing unmodified, verified above.

No meaningful gaps found. The AF3/AF3a/AF3b correction documented in the tests.md is itself sound:
it was necessitated by a genuine structural conflict with the frozen `test_c5` (verified above — the
shipped `agent_config/qa_system_prompt.md` really does contain `{{BRD}}`, and a byte-copy really
would trip `test_c5`'s scan), not a weakening for convenience. The corrected AF3b test is *stricter*
in the sense that matters (content must equal the actual injected prompt, and must be token-free) —
it is not a loophole.

## Conclusion

All of AF1–AF6 hold as implemented, verified independently (not merely trusting the developer's or
tester's narrative). No scope creep, no dead code, no frozen-test modification, no secret leakage in
the diff. Suite is green at every layer requested (`runner/tests`, combined `runner/tests
connectors/tests agent_config/tests`, and the two individually-named frozen tests).

**Verdict: APPROVE**

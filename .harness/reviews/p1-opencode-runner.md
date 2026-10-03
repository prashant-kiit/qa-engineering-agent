# Review — `p1-opencode-runner` (OpenCode runner adapter + connector config)

**Verdict: APPROVE**

Independent review of the OpenCode `AgentRunner` adapter, its connector config, and the
OpenCode-format agent defs against the spec, the Tester's suite, and quality. Read-only on
code; suites run independently.

## Test run (both ways — green)

```
$ uv run pytest runner/tests/test_opencode_runner.py -q
........................                                                 [100%]
24 passed in 0.09s

$ uv run pytest runner/tests connectors/tests agent_config/tests -q
..................................................s..................... [ 40%]
........................................................................ [ 80%]
..................................                                       [100%]
177 passed, 1 skipped in 1.92s
```

24 in the unit suite; 177 passed / 1 skipped across the combined suite with **no collection
error**. Both green, matching the spec's expected counts.

## 1. Acceptance — all 19 criteria met

- **Seam conformance (C1):** `OpenCodeRunner.__call__(invocation) -> AgentRunOutput`, importing
  both types from `runner.authoring`; drives cleanly through `run_authoring(...)`.
- **Invocation (C2–C8):** argv is `["opencode","run",<message>,"--model","openai/gpt-4o-mini",
  "--agent",<agent>]`; two ordered runs, `qa-planner` before `qa-generator` (C7); model is a
  bumpable constructor knob (C3); MCP wired via the shipped config discovered through
  `OPENCODE_CONFIG` (C4); BRD-injected `system_prompt` + all seven `planner_fields` + `target_url`
  delivered in the message with no `{{BRD}}` re-injection and the shared prompt file untouched
  (C5–C6); `cwd` is a per-run temp workspace `!=` `output_dir` (C8).
- **Output capture (C9–C10):** collects glob-matched files byte-exact with workspace-relative
  keys; the glue writes exactly those under `output_dir`.
- **Secret-safety (C11–C13):** model key injected into the child env only (from the
  `OPENAI_API_KEY` reference), scrubbed from detail, and absent from argv/message/workspace/
  output/stdout; missing key raises `OpenCodeRunnerError` *before* any spawn, naming the
  reference not the value; target-app auth flows as `basic_auth_credential_ref` name only.
- **Non-success (C14–C16):** non-zero exit and no-tests-produced both return a non-`"ok"` status
  with scrubbed detail (not raised); missing connector config raises `OpenCodeRunnerError`.
- **Determinism / placement (C17–C19):** identical argv modulo the temp workspace; pinned import
  path, constants, and artifact paths; no writes outside the workspace, glue remains the single
  writer of `output_dir`.

## 2. Test integrity — un-gamed, and the helper fix is clean

- The Developer correctly **STOPPED** on the impossible test rather than editing it: the helper
  had set `planner_fields["depth"]` to an invalid enum value that unit-2's loader rejects *before*
  the adapter runs (C1/C10 push the dict through the real glue). The Tester's fix
  (`opencode_helpers.py:67`, `depth="regression"`) is the minimal correct change — `regression`
  is a valid unit-2 enum — and it does **not** weaken any assertion: C5 still asserts every
  `PLANNER_FIELD_MARKERS` value is delivered, and lowercase `regression` is not a coincidental
  substring of the delivered surfaces (the reliability-rule token is `HEAL_VS_REGRESSION`,
  uppercase, and is not even inlined into the message). Assertion still meaningful.
- Secret scans are strong: distinctive sentinels asserted absent from argv, message, workspace
  files, `AgentRunOutput`, and captured stdout/stderr. The child env is correctly *excluded*
  from the scan (the key legitimately lives there) — a justified, documented exclusion, not a
  loophole.
- The invocation carries unique per-field markers, so C5–C6 genuinely prove delivery rather than
  accepting incidental text.

## 3. Scope — no creep

Developer added exactly: `runner/opencode_runner.py`, `runner/tests/test_opencode_runner.py`,
`runner/tests/opencode_helpers.py`, `connectors/opencode/opencode.json`,
`.opencode/agent/qa-planner.md`, `.opencode/agent/qa-generator.md`. No modification to the
unit-6 glue, units 1–5 artifacts, `.claude/agents/*`, `reference_app/**`, or any protected file.
`AGILE_PLAN.md` + `.harness/backlog.md` edits are the TPM re-plan (expected, not a dev change).

## 4. Quality

- Command-runner seam is a clean injectable `Protocol`; the real `default_command_runner` (the
  only `subprocess` path) is `pragma: no cover` and never reached in tests — no real
  OpenCode/network/browser in the import path.
- Ordering of checks in `__call__` is correct: config existence → credential presence → workspace
  → runs, so both named-error cases fire before any spawn.
- Connector config is valid JSON with `$schema`, `model`, top-level `mcp` (pinned
  `@playwright/mcp@0.0.41`, headless chromium), `instructions` → shared prompt, and inline
  `agent` roles `qa-planner`/`qa-generator` pointing at the `.opencode/agent/*.md` defs which in
  turn reference `agent_config/qa_system_prompt.md`. Portable core shared; only the CLI wrapper
  differs — matches unit-5's intent.
- Public API, constants, seam, and errors are all documented in the module docstring (spec
  permits docstring in lieu of a README).

## Advisory notes for the live gate (unit 8 — NOT blocking, no change requested)

These do not affect the mock-tested contract; verify against the pinned OpenCode version at the
live authoring gate:
1. **Relative paths under a temp cwd.** `opencode.json` uses relative `instructions`
   (`agent_config/qa_system_prompt.md`) and `{file:./.opencode/agent/*.md}`, while the run `cwd`
   is a temp workspace. Confirm OpenCode resolves these relative to the config-file location (or
   copy/materialize them into the workspace) so the prompt/agent defs actually load live.
2. **Prompt via argv positional.** The full BRD-injected system prompt is passed as an argv
   positional; for large BRDs consider stdin to avoid arg-length limits. The seam already
   supports `input=`.
3. **Full `os.environ` inheritance** into the child is standard and fine; just confirms the
   model key is the only *added* secret.

## Deploy gate

Written `p1-opencode-runner` to `.harness/state/APPROVED`.

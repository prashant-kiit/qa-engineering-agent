# Review — `p1-agent-run-glue`

**Verdict:** APPROVE

Independent review of the Phase 1 agent-run glue (`runner/authoring.py`, `runner/__init__.py`)
against the spec, the Tester's suite, and quality. Read-only on code; suite run independently
both ways.

## Test run (both collection modes green)

```
$ uv run pytest runner/tests -q
.....................                                                    [100%]
21 passed in 0.05s

$ uv run pytest runner/tests connectors/tests agent_config/tests -q
..........................s............................................. [ 46%]
........................................................................ [ 93%]
..........                                                               [100%]
153 passed, 1 skipped in 1.81s
```

Both green; **no collection error** under whole-suite collection. The `conftest`-collision fix
is clean: shared constants + mock runners live in the uniquely-named
`runner/tests/authoring_helpers.py`, imported as `from authoring_helpers import ...`; `conftest.py`
exposes only pytest fixtures. No bare `from conftest import ...` remains.

## 1. Acceptance — all 19 criteria met

- **1–2 (config + API surface via units 1+2):** `load_target_config` then `config.load_api_spec()`;
  no re-parsing. Verified by `test_loads_target_config_via_unit2`, `test_loads_api_surface_via_units_1_and_2`.
- **3 (BRD injection exactly once):** `_inject_brd` validates `prompt.count(BRD_TOKEN) == 1` then
  `prompt.replace(BRD_TOKEN, brd_text, 1)` — count-of-1 pre-check + bounded single replace means a
  `{{BRD}}` inside the BRD body is never re-substituted. No residue; template preserved.
- **4 (determinism):** `planner_fields` copied, `api_surface` is the sorted `to_dict()`; no
  nondeterministic content.
- **5–6 (MCP + sub-agents):** `MCP_CONFIG_PATH`, `PLANNER_AGENT`/`GENERATOR_AGENT` referenced in both
  invocation and RunResult; distinct.
- **7–8 (runner seam):** `agent_runner` is a required keyword; invoked exactly once with the full
  `AuthoringInvocation` bundle carrying all nine pinned fields. No hard-coded live call — the module
  imports nothing that talks to Claude Code / MCP / network / browser.
- **9–11 (output + RunResult):** writes each `rel_name` (nested paths supported) under the resolved
  dir; `DEFAULT_OUTPUT_DIR` ends with `runner/generated` and is consulted at call time; RunResult
  exposes all pinned attributes.
- **12–16 (errors):** `TargetConfigError` / `SpecLoadError` propagate unchanged (not caught);
  `AuthoringError` (module `runner`, not a connectors subclass) raised for unreadable BRD (message
  names the path) and bad `{{BRD}}` count — both short-circuit **before** the runner and before any
  write; runner exceptions propagate un-swallowed; error status ⇒ no writes, status surfaced.
- **17 (secret-safety):** only `basic_auth_credential_ref` (the name) flows; `resolve_credential()`
  is never called; `RunResult.__repr__` is secret-free (does not even render the ref). Verified by
  `test_only_credential_reference_flows_through` (env sentinel scanned across prompt, repr,
  invocation blob, written files, and captured stdout/stderr).
- **18–19 (placement / no regression):** code at pinned home `runner/` with import path
  `runner.authoring`; units 1–5 suites unchanged and green.

## 2. Test integrity

Tests are meaningful and un-gamed. Clean three-file split (helpers / fixtures / assertions); the
collision fix relocated shared symbols without weakening any assertion. Error-path tests assert both
the raised type/module **and** the no-invocation / empty-dir side-effects. Secret test scans every
required surface. No test edited to accommodate the implementation.

## 3. Scope

Working-tree additions are limited to `runner/__init__.py`, `runner/authoring.py`, `runner/tests/**`,
the two `p1-agent-run-glue` task files, and a bookkeeping edit to `.harness/backlog.md`. No source
of units 1–5, no `reference_app/**`, and no protected file (`DESIGN.md`, `META_PLAN.md`,
`AGILE_PLAN.md`, `CLAUDE.md`) was modified by this unit. No stray artifacts under `runner/generated/`
(directory does not exist; tests write only to `tmp_path`).

## 4. Quality

- Truly composes units 1–5; no reimplementation.
- Runner seam is a documented `Protocol`; injectable with no live default exercised.
- Docs requirement satisfied via the thorough module docstring + per-class docstrings
  (spec permits "documented module docstring" in lieu of `runner/README.md`).

### Non-blocking observations (no action required)
- `dest = base / rel_name` does not guard against a runner returning an absolute path or `../`
  traversal in `generated_tests` keys. The runner is a trusted seam and the spec does not require
  path-hardening here; worth a guard when the real (unit 7) runner lands.

Deploy gate: `p1-agent-run-glue` written to `.harness/state/APPROVED`.

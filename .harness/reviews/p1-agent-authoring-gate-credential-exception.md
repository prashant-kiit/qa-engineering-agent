# Review — `p1-agent-authoring-gate-credential-exception`

**Final verdict: APPROVE**

(This review went through one CHANGES_REQUESTED round on scope grounds; see
"Round 1" below for the original findings, and "Round 2" for the re-verification
that led to approval. All security-critical findings from Round 1 continued to
hold unchanged and were re-confirmed independently in Round 2.)

## Round 2 — re-verification (final)

The Developer split the diff as requested: reset `runner/opencode_runner.py`,
`eval/score.py`, and `Makefile` to their pre-session state, then re-applied only the
`_compose_message` credential-exposure branch; removed the stray untracked unit-8
files (`runner/authoring_gate.py`, `reference_app/e2e/playwright.agent.config.ts`);
fixed the stale `AuthoringInvocation` docstring.

Independently re-verified, with fresh reads (not trusting the Developer's claims):

- `git diff -- runner/opencode_runner.py` → now **17 lines**, containing **only** the
  `_compose_message` opt-in branch and its docstring update. No
  `_materialize_config`, no `_build_argv`/`--auto`/`--dir`/`--continue` changes, no
  `permission.external_directory` policy, no `run()` reorder. The default (`None`)
  branch is still the original return expression verbatim (just reassigned to
  `message` before an unconditional `return message`) — byte-identical, confirmed.
- `git diff -- eval/score.py Makefile` → **empty**. Confirmed zero changes.
- `runner/authoring_gate.py` and `reference_app/e2e/playwright.agent.config.ts` → no
  longer present (`ls` confirms both missing).
- `runner/authoring.py` diff (24 lines) → unchanged from Round 1's clean review; the
  `AuthoringInvocation` docstring (line ~86) now reads: *"Carries the credential
  **reference name** (`basic_auth_credential_ref`); the resolved value
  (`basic_auth_credential_value`) stays `None` unless the caller explicitly opts in
  via `run_authoring(..., expose_credential_for_exploration=True)` — a narrow,
  documented carve-out (see `runner/README.md`). It never flows into the returned
  `RunResult`."* — accurate, no longer stale. Item 3 resolved.
- `git diff -- runner/tests/test_opencode_runner.py` → still a 0-line diff (byte-
  unmodified).
- `uv run pytest runner/tests -q` → **58 passed**.
- `uv run pytest runner/tests/test_opencode_runner.py::test_c13_target_auth_stays_reference_only -q`
  → **1 passed**.
- `uv run pytest runner/tests connectors/tests agent_config/tests -q` →
  **190 passed, 1 skipped**.
- `git status --porcelain` → tracked changes now limited to `.harness/backlog.md`,
  `AGILE_PLAN.md` (TPM plan-lock/deviation bookkeeping — expected), `runner/authoring.py`,
  `runner/opencode_runner.py`; untracked additions are this unit's own new test files
  (`runner/tests/credential_exception_helpers.py`,
  `runner/tests/test_authoring_credential_exception.py`,
  `runner/tests/test_opencode_runner_credential_exception.py`), `runner/README.md`,
  this review file, this unit's own task spec files, and (harmlessly, since neither
  `eval/score.py` nor any wiring references them) unit 8's still-untracked spec docs
  (`p1-agent-authoring-gate.md`/`.tests.md`) and a leftover
  `eval/tests/test_agent_authoring_gate_verification.py` — none of these are wired
  into anything this unit touches or exercises, and none are part of this unit's
  diff to any tracked file.

All Round 1 action items are resolved:
1. **[dev] resolved** — `_materialize_config`/argv/permission/`run()` changes removed
   from `runner/opencode_runner.py`.
2. **[dev] resolved** — `eval/score.py`/`Makefile` reverted to zero diff.
3. **[dev] resolved** — `AuthoringInvocation` docstring corrected.

Scope is now exactly what the spec calls for: `runner/authoring.py`,
`runner/opencode_runner.py` (credential-exposure branch only), `runner/README.md`,
plus the Tester's new test files. Nothing in `reference_app/**`, `connectors/**`,
`agent_config/**`, or `eval/**` is touched. No protected file (`DESIGN.md`,
`META_PLAN.md`, `CLAUDE.md`, `.harness/**` other than the expected task/review
artifacts) was altered.

## Round 1 findings (for the record — all still hold)

### Test run (independent)

```
$ uv run pytest runner/tests -q
58 passed in 0.13s

$ uv run pytest runner/tests/test_opencode_runner.py::test_c13_target_auth_stays_reference_only -q
1 passed in 0.03s

$ git diff -- runner/tests/test_opencode_runner.py | wc -l
0   # byte-identical

$ uv run pytest runner/tests connectors/tests agent_config/tests -q
190 passed, 1 skipped in 1.86s
```

### Default-off guarantee — verified genuine

- `runner/authoring.py`: `resolve_credential()` is called **only** inside
  `if expose_credential_for_exploration:`. Traced the full return path: `RunResult`'s
  `__slots__`/`__init__` has **no** parameter or slot for
  `basic_auth_credential_value` — structurally impossible for the resolved value to
  reach `RunResult`. Confirmed by `test_opt_in_value_never_exposed_by_run_result`
  (scans `dir(res)`/`repr(res)` for the sentinel value).
- `OpenCodeRunner._compose_message`: the default (`None`) branch is the **original
  return expression verbatim**, only conditionally appended to when
  `credential_value is not None`. Byte-identical — confirmed by direct reading and by
  the unmodified, passing `test_c13_target_auth_stays_reference_only`.
- `AuthoringInvocation.basic_auth_credential_value: Optional[str] = None` appended
  after all 9 existing fields with a default — no reordering, no break to any
  existing keyword-only construction site.

### Exemption's factual basis — verified independently

Grepped the three cited files myself:
- `reference_app/e2e/tests/smoke.spec.ts:23-24` — `USERNAME = 'testuser'`,
  `PASSWORD = 'testpass'`, plaintext.
- `reference_app/e2e/tests/eval/helpers.ts:15-16` — same, plaintext, exported.
- `eval/tests/test_eval_harness_verification.py:53` — `VALID_AUTH = ("testuser",
  "testpass")`, plaintext.

All three confirmed — the fixture value really is already public/committed in
Phase-0 artifacts predating this unit.

`AGILE_PLAN.md` (Conflicts / deviations, 2026-09-29 entry) correctly and explicitly
attributes the decision to an **in-session `AskUserQuestion` tool** use, lists the
three options (a/b/c) the human was asked to choose between, states **the human
chose (a)**, and correctly flags option (b) as deferred (not abandoned) to Phase 2+.
Properly recorded human decision, not agent self-authorization.

### Test adequacy (AC1–AC9)

The 13 new tests (`test_authoring_credential_exception.py`,
`test_opencode_runner_credential_exception.py`) genuinely and directly prove
AC1–AC7: default-preserved (including the untouched `test_c13`), opt-in resolves
and delivers the value only to the invocation, `RunResult` never exposes it
(attribute/repr/full `dir()` scan), `CredentialUnsetError` still propagates with no
run attempted, both Planner/Generator roles receive the value alongside (not
instead of) the reference name, and the `OPENAI_API_KEY` path is unaffected on both
invocations (no cross-talk). No existing test was weakened or modified; the new
tests use a distinctive non-secret sentinel value, never the real
`testuser`/`testpass`. AC8 (full suite green, zero existing test touched) directly
verified. No `[tester]` items.

### README (AC9)

`runner/README.md` accurately documents `expose_credential_for_exploration`,
`basic_auth_credential_value`, the default-off/opt-in behavior, the "why this value
is exempt / why it doesn't generalize" framing (matching the spec and
`AGILE_PLAN.md`), and the documented (non-code-enforced) constraint that only unit
8's live-gate script, for the reference app's fixture account, may pass the flag.

### Original scope finding (now resolved in Round 2)

Round 1 found that `runner/opencode_runner.py`'s diff (146 lines) contained ~125
lines of unrelated unit-8 ("headless-emit fix, spec Interpretation #4") work —
`_materialize_config`, new `--auto`/`--dir`/`--continue` argv flags, a
`permission.external_directory = "deny"` policy, and a `run()` reorder — plus
out-of-scope edits to `eval/score.py`/`Makefile`. None of this was covered by this
unit's tests and all of it was explicitly out of scope per this unit's own spec.
This blocked approval in Round 1 and is fully resolved in Round 2 (see above).

## Files reviewed

- `/Users/prashant/Desktop/Project/qa-engineering-agent/.harness/tasks/p1-agent-authoring-gate-credential-exception.md`
- `/Users/prashant/Desktop/Project/qa-engineering-agent/.harness/tasks/p1-agent-authoring-gate-credential-exception.tests.md`
- `/Users/prashant/Desktop/Project/qa-engineering-agent/AGILE_PLAN.md` (Conflicts / deviations, 2026-09-29 entry; Phase 1 unit table)
- `/Users/prashant/Desktop/Project/qa-engineering-agent/runner/authoring.py` (diff)
- `/Users/prashant/Desktop/Project/qa-engineering-agent/runner/opencode_runner.py` (diff — now scoped to `_compose_message` only)
- `/Users/prashant/Desktop/Project/qa-engineering-agent/runner/README.md` (new)
- `/Users/prashant/Desktop/Project/qa-engineering-agent/runner/tests/test_authoring_credential_exception.py`
- `/Users/prashant/Desktop/Project/qa-engineering-agent/runner/tests/test_opencode_runner_credential_exception.py`
- `/Users/prashant/Desktop/Project/qa-engineering-agent/runner/tests/credential_exception_helpers.py`
- `/Users/prashant/Desktop/Project/qa-engineering-agent/runner/tests/test_opencode_runner.py` (confirmed byte-unmodified)
- `/Users/prashant/Desktop/Project/qa-engineering-agent/eval/score.py`, `/Users/prashant/Desktop/Project/qa-engineering-agent/Makefile` (confirmed zero diff in Round 2)

**Deploy gate:** `p1-agent-authoring-gate-credential-exception` written to
`/Users/prashant/Desktop/Project/qa-engineering-agent/.harness/state/APPROVED`.

# Test coverage — `p1-agent-authoring-gate-credential-exception` (TDD red)

Tester wrote **only new tests** for this unit. No existing test file was modified:
`runner/tests/test_authoring.py` and `runner/tests/test_opencode_runner.py` are
byte-unmodified (verified: `test_c13_target_auth_stays_reference_only` and all other
45 previously-passing `runner/tests` tests still pass, unchanged, below).

## New files

- `runner/tests/credential_exception_helpers.py` — shared helper (uniquely named, not
  `conftest`, per the import-hygiene lesson already recorded in
  `runner/tests/opencode_helpers.py`). Provides `TEST_CREDENTIAL_VALUE` (a distinctive,
  non-secret sentinel — never the real `testuser`/`testpass` fixture) and
  `make_invocation_with_credential_value(output_dir, *, basic_auth_credential_value=None,
  system_prompt=None, target_url=None)`, which constructs an `AuthoringInvocation`
  **directly** (reusing `opencode_helpers`'s constants for the other fields) so it can
  pass the not-yet-existing `basic_auth_credential_value` keyword.
- `runner/tests/test_authoring_credential_exception.py` — unit-6 (`run_authoring` /
  `AuthoringInvocation`) coverage.
- `runner/tests/test_opencode_runner_credential_exception.py` — unit-7
  (`OpenCodeRunner._compose_message` / `__call__`) coverage.

## Criterion -> test map

| AC | Description | Test(s) |
|---|---|---|
| AC1 | Default (`omitted` / `False`) behavior fully preserved | `test_authoring_credential_exception.py::test_omitted_flag_defaults_invocation_value_to_none`, `::test_explicit_false_matches_omitted_default`, `::test_default_path_does_not_call_resolve_credential` |
| AC2 | Opt-in resolves and carries the value; `RunResult` never exposes it | `test_authoring_credential_exception.py::test_opt_in_resolves_credential_onto_invocation`, `::test_opt_in_value_never_exposed_by_run_result` |
| AC3 | Unset credential still raises `CredentialUnsetError`, unchanged | `test_authoring_credential_exception.py::test_opt_in_with_unset_env_var_raises_credential_unset_error` |
| AC4 | `AuthoringInvocation` field additive, optional, keyword-compatible | `test_authoring_credential_exception.py::test_authoring_invocation_gains_optional_credential_value_field`, `::test_existing_keyword_construction_sites_still_work_unmodified` |
| AC5 | `_compose_message` default path byte-identical (pinned by existing `test_c13_target_auth_stays_reference_only`, kept unmodified) | `test_opencode_runner_credential_exception.py::test_explicit_none_message_matches_todays_default_path`; plus the pre-existing, unmodified `runner/tests/test_opencode_runner.py::test_c13_target_auth_stays_reference_only` |
| AC6 | `_compose_message` opt-in path delivers the value for both roles, reference name retained | `test_opencode_runner_credential_exception.py::test_opt_in_value_present_for_both_roles_alongside_reference_name`, `::test_opt_in_value_reaches_full_mock_run_surface` |
| AC7 | No `OPENAI_API_KEY` regression on either path | `test_opencode_runner_credential_exception.py::test_openai_key_handling_unaffected_with_default_invocation`, `::test_openai_key_handling_unaffected_with_opt_in_invocation`; plus the pre-existing, unmodified `test_c11_model_key_injected_into_child_env_only` / `test_c12_missing_model_credential_raises_named_error` |
| AC8 | Full existing suite green, zero existing test modified | Verified directly below (45/45 pre-existing `runner/tests` pass unmodified; `test_c13` explicitly re-run and passing) |
| AC9 | `runner/README.md` documentation | Not test-covered (a documentation criterion); left for Reviewer to check the Developer updated the doc as scoped. |

## Naming / construction assumptions recorded

- `AuthoringInvocation` gains `basic_auth_credential_value: Optional[str] = None`,
  appended after the existing 9 fields (order pinned and asserted in
  `test_authoring_invocation_gains_optional_credential_value_field`).
- `run_authoring` gains keyword-only `expose_credential_for_exploration: bool = False`.
- The opt-in call site is expected to call `config.resolve_credential()` (unit-2,
  unmodified) — asserted indirectly via the resolved value landing on the invocation
  and via `CredentialUnsetError` propagating when the env var is unset.
- `OpenCodeRunner._compose_message`'s opt-in branch is asserted to *retain* the
  existing reference-name sentence (`repr(basic_auth_credential_ref)` substring) while
  *adding* the resolved value — per the spec's "supplemented, not replaced" wording.
- `credential_exception_helpers.make_invocation_with_credential_value` builds the
  invocation directly (not via `opencode_helpers.make_invocation`) specifically so it
  can pass the new field before it exists; this is intentional TDD-red scaffolding, not
  a workaround.

## Red run — new suite (`runner/tests`)

```
$ uv run pytest runner/tests -q
...
13 failed, 45 passed in 0.10s
```

All 13 failures are the new tests, all failing for the **legitimate, missing-feature**
reason — either:

```
TypeError: AuthoringInvocation.__init__() got an unexpected keyword argument
'basic_auth_credential_value'. Did you mean 'basic_auth_credential_ref'?
```

(from `credential_exception_helpers.make_invocation_with_credential_value`, used by
every `test_opencode_runner_credential_exception.py` test and by
`test_existing_keyword_construction_sites_still_work_unmodified` /
`test_opt_in_resolves_credential_onto_invocation` / etc. in the authoring suite), or

```
AttributeError: 'AuthoringInvocation' object has no attribute
'basic_auth_credential_value'
```

(when reading the field off an invocation built by the existing, unmodified
`opencode_helpers.make_invocation` / via `run_authoring`'s current signature), or

```
TypeError: run_authoring() got an unexpected keyword argument
'expose_credential_for_exploration'
```

(for calls that pass the new `run_authoring` parameter directly).

No collection errors, no import errors unrelated to the missing feature, no assertion
failures caused by test-harness bugs.

Full list of the 13 new (red) tests:

```
FAILED runner/tests/test_authoring_credential_exception.py::test_authoring_invocation_gains_optional_credential_value_field
FAILED runner/tests/test_authoring_credential_exception.py::test_existing_keyword_construction_sites_still_work_unmodified
FAILED runner/tests/test_authoring_credential_exception.py::test_omitted_flag_defaults_invocation_value_to_none
FAILED runner/tests/test_authoring_credential_exception.py::test_explicit_false_matches_omitted_default
FAILED runner/tests/test_authoring_credential_exception.py::test_default_path_does_not_call_resolve_credential
FAILED runner/tests/test_authoring_credential_exception.py::test_opt_in_resolves_credential_onto_invocation
FAILED runner/tests/test_authoring_credential_exception.py::test_opt_in_value_never_exposed_by_run_result
FAILED runner/tests/test_authoring_credential_exception.py::test_opt_in_with_unset_env_var_raises_credential_unset_error
FAILED runner/tests/test_opencode_runner_credential_exception.py::test_explicit_none_message_matches_todays_default_path
FAILED runner/tests/test_opencode_runner_credential_exception.py::test_opt_in_value_present_for_both_roles_alongside_reference_name
FAILED runner/tests/test_opencode_runner_credential_exception.py::test_opt_in_value_reaches_full_mock_run_surface
FAILED runner/tests/test_opencode_runner_credential_exception.py::test_openai_key_handling_unaffected_with_default_invocation
FAILED runner/tests/test_opencode_runner_credential_exception.py::test_openai_key_handling_unaffected_with_opt_in_invocation
13 failed, 45 passed in 0.10s
```

## Explicit confirmation: `test_c13_target_auth_stays_reference_only` still passes

```
$ uv run pytest runner/tests/test_opencode_runner.py::test_c13_target_auth_stays_reference_only -q
.                                                                        [100%]
1 passed in 0.03s
```

This test's file (`runner/tests/test_opencode_runner.py`) is **byte-unmodified** by
this unit. It passing, unmodified, in the red state is the direct proof that AC5's
default path is untouched at this stage.

## Regression check — all previously-passing `runner/tests` (45) still pass unmodified

The full `runner/tests -q` run above shows `45 passed` alongside the `13 failed` new
tests — i.e. every test that existed before this unit's tests were added still passes,
unmodified.

## Combined suite — no collection collision / no cross-directory regression

```
$ uv run pytest runner/tests connectors/tests agent_config/tests -q
...
13 failed, 177 passed, 1 skipped in 1.86s
```

Only the same 13 new, legitimately-red tests fail; the `connectors/tests` and
`agent_config/tests` suites are wholly unaffected (no import collisions from the new
uniquely-named `credential_exception_helpers` / test modules).

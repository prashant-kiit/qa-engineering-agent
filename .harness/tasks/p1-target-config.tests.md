# Test coverage — `p1-target-config` (TDD red)

**Test file (new):** `connectors/tests/test_target_config.py`
**Runner:** `uv run pytest connectors/tests -q`
**Status:** legitimately RED — all 53 new tests error at setup with the single right reason
`ModuleNotFoundError: No module named 'connectors.target_config'` (implementation absent).
Unit-1's `connectors/tests/test_spec_loader.py` (24 tests) is untouched and still **passes**.
No fixtures were added to unit-1's `conftest.py`; the new suite is self-contained and reuses
the existing `spec_loader` and `openapi_doc` fixtures for the hand-off tests.

## Naming assumptions the DEVELOPER must honor
The spec (Interfaces) leaves several public names to the developer's choice but requires them
**documented + stable**. The Tester pinned the most natural per the spec; honor these exact names
(or update this note + tests in the review loop if a different name is documented):

| Concept | Pinned name |
|---|---|
| Public module (stable import path) | `connectors.target_config` |
| Loader entry point | `load_target_config(source, source_type="auto") -> TargetConfig` |
| Config object type | `TargetConfig` |
| Named config/validation error | `connectors.target_config.TargetConfigError` |
| Credential-unset error (distinct, NOT a subclass of `TargetConfigError`) | `connectors.target_config.CredentialUnsetError` |
| Spec hand-off (method on the object) | `TargetConfig.load_api_spec() -> connectors.spec_loader.ApiSurface` |
| Credential resolution hand-off (method) | `TargetConfig.resolve_credential() -> str` (secret; returned to caller, never stored) |
| Serialization | `TargetConfig.to_dict() -> dict` (deterministic) + secret-free `__repr__` |
| Example config file | `connectors/examples/reference_app.target.json` |

**Binding (NOT assumptions) — pinned serialized contract keys** (from the spec Model + Seven-Planner
tables): top-level `target_url`, `api_spec_source`, `brd_path`, `basic_auth_credential_ref`,
`planner_fields`; planner `target_scope`, `intent`, `expected_behavior`, `priority_risk`,
`test_data_preconditions`, `out_of_scope_constraints`, `depth`; depth enum
`{smoke, regression, exhaustive}`.

Other test conventions the developer should be aware of:
- The loader accepts a **mapping** and a **file path string** (JSON). Malformed JSON in a file must
  raise `TargetConfigError` (not a raw `json`/`OSError`).
- `resolve_credential()` returns the raw env-var value to the caller; it must NOT be logged or
  stored back on the object.
- Valid-config fixtures point `brd_path` at the real `reference_app/BRD.md` (absolute), so the
  loader may require the BRD path to exist without breaking the happy path.

## Acceptance criterion → test mapping

| # | Criterion | Test(s) |
|---|---|---|
| 1 | Load from mapping | `test_load_from_mapping_returns_object` |
| 2 | Load from JSON file == mapping; load error on bad file | `test_load_from_json_file_equals_mapping`, `test_invalid_json_file_raises_named_error` |
| 3 | Pinned top-level field access | `test_object_exposes_pinned_top_level_fields` |
| 4 | Exactly seven pinned planner fields | `test_seven_planner_fields_exactly`, `test_planner_field_values_roundtrip` |
| 5 | Missing required top-level field → named error (not KeyError) | `test_missing_required_top_level_field_rejected` (×5) |
| 6 | Malformed/wrong-typed/empty field → named error naming the field | `test_malformed_field_rejected_named` (×8) |
| 7 | `depth` enum enforced | `test_depth_enum_accepts_valid` (×3), `test_depth_out_of_set_rejected` (×6) |
| 8 | Each of the seven planner fields required (absent or empty) | `test_each_planner_field_required` (×7), `test_empty_planner_text_field_rejected` (×6) |
| 9 | Only a reference stored; no inlined secret retained | `test_only_reference_is_stored_no_inlined_secret` |
| 10 | Serialization/repr/str/logs show ref name, never the secret | `test_serialization_leaks_no_secret_but_shows_reference` |
| 11 | At-call-time, non-retaining resolution; named unset error | `test_resolution_is_at_call_time_and_non_retaining`, `test_resolve_unset_credential_raises_distinct_named_error` |
| 12 | Delegates to `connectors.spec_loader.load_spec`; same ApiSurface | `test_spec_handoff_delegates_and_matches_unit1`, `test_spec_handoff_calls_load_spec_with_source` |
| 13 | Loader errors propagated unchanged (not rewrapped) | `test_spec_handoff_propagates_loader_error_unchanged`, `test_spec_handoff_propagates_unsupported_error_unchanged` |
| 14 | Example config present + valid + wired values | `test_example_config_present_and_valid` |
| 15 | Example config is secret-free | `test_example_config_is_secret_free` |
| 16 | Deterministic serialization (same input, file==mapping, stable keys) | `test_to_dict_deterministic_same_input`, `test_to_dict_file_equals_mapping_and_stable_keys` |
| 17 | Correct home + runnable tests + unit-1 still green | whole suite under `connectors/tests/`, runs via `uv run pytest connectors/tests -q`; unit-1 verified still 24-pass |
| 18 | No regressions / no secret persisted / no writes | covered indirectly: no test triggers writes; secret-safety tests (10–11) prove no credential persisted/logged; unit-1 API used unchanged via `spec_loader` fixture |

Notes on the two "lenient both-branch" tests (deliberate, to avoid over-constraining developer
choice while still being meaningful):
- Criterion 9 (`test_only_reference_is_stored_no_inlined_secret`): accepts EITHER rejecting an
  inlined-secret config with `TargetConfigError` OR silently not retaining it — but in the accepted
  branch it strictly asserts the sentinel appears nowhere on the object.
- Criterion 2 YAML support is optional per the spec; the suite does not require YAML, and instead
  asserts a malformed JSON file raises the named error.

## Captured RED output
```
$ uv run pytest connectors/tests -q
24 passed, 53 errors in 1.96s

# every new-test error resolves to the single right reason:
$ uv run pytest connectors/tests 2>&1 | grep -Eo "ModuleNotFoundError: No module named '[^']*'" | sort -u
ModuleNotFoundError: No module named 'connectors.target_config'

# unit-1 unaffected:
$ uv run pytest connectors/tests/test_spec_loader.py -q
........................                                                 [100%]
24 passed in 1.68s
```

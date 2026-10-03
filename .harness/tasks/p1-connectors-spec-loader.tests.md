# Test coverage — `p1-connectors-spec-loader` (TDD red)

Tester artifacts (tests only; no implementation written or read):

- `connectors/tests/conftest.py` — fixtures: real OpenAPI doc captured from the clean
  `reference_app.backend.app:app` OpenAPI generator (`openapi_doc`), plus `openapi_json_str`,
  `openapi_file`, an in-thread loopback stub HTTP server `openapi_url`, an `unreachable_url`
  (bound-then-closed ephemeral port), and the `spec_loader` import fixture.
- `connectors/tests/test_spec_loader.py` — 24 tests encoding acceptance criteria 1–19.

Run: `uv run pytest connectors/tests -q`

## Naming assumptions the developer MUST honor

The spec leaves several public names to the developer's choice but requires them documented and
stable. The tests pin the most natural names the spec suggests; the implementation must match these
(or the developer coordinates a change back through the tests):

- Public module import path: **`connectors.spec_loader`** (Interfaces §Paths gives this as the
  example stable path).
- Loader entry point: **`load_spec(source, source_type="auto")`** returning the surface object
  (Interfaces §Public API: one auto-detecting entry point + optional `source_type` hint, `auto`
  default).
- Serialization method: **`surface.to_dict()`** returning a plain JSON-serializable dict
  (Interfaces §Serialization gives `.to_dict()` / `.to_json()`; tests use `.to_dict()`).
- Base load/parse error: **`spec_loader.SpecLoadError`** (Interfaces §Errors example name), used for
  malformed/non-OpenAPI input and unreachable file/URL.
- Unsupported-source error: **`spec_loader.UnsupportedSourceError`** (may be a subclass of
  `SpecLoadError` — tests only require `pytest.raises(UnsupportedSourceError)`).
- `source_type="graphql"` selects the deferred/unsupported GraphQL path (criterion 17). GraphQL is
  the spec's canonical deferred case; the explicit hint forces the unsupported path deterministically.
- Serialized `request_body` nests its resolved schema under key **`"schema"`** (mirrors the pinned
  responses shape `{ schema }`).
- Serialized `responses` map status-code string → **`{ "schema": <resolved> }`**.
- Resolved object schemas expose concrete fields under a **`"properties"`** mapping with **no
  top-level `"$ref"`** (intra-document `$ref` resolved/inlined).
- `operations` serialize sorted by **(path, method)** — the canonical ordering the spec states for
  criterion 13 ("sorted by `path` then `method`").

Surface objects are exercised only through `to_dict()` and the pinned serialized key names; the
in-memory object's own class name / attributes are intentionally NOT asserted (developer's choice).

## Criterion → test mapping

| # | Acceptance criterion | Test(s) |
|---|---|---|
| 1 | Load from in-memory dict | `test_load_from_in_memory_dict` |
| 2 | Load from local file == dict | `test_load_from_local_file_matches_dict` |
| 3 | Load from HTTP(S) URL (stub server) == dict | `test_load_from_http_url_matches_dict` |
| 4 | Load from raw JSON string == dict | `test_load_from_raw_json_string_matches_dict` |
| 5 | Auto-detection; equivalent inputs → equal surfaces | `test_source_kind_autodetection_equivalent` |
| 6 | Document `title` + `version` from `info` | `test_document_metadata` |
| 7 | Exactly the 5 (method, path) ops; method upper-cased; templated path preserved | `test_operations_enumerated_exactly` |
| 8 | Pinned per-operation fields present (list/mapping types) | `test_per_operation_fields_present` |
| 9 | Path param `order_id` surfaced, required, `in=path` | `test_path_parameter_surfaced` |
| 10 | Request-body `$ref`→AddItem resolved (product_id, quantity; no `$ref`) | `test_request_body_schema_resolved` |
| 11 | Response `$ref`→Order resolved (id, items, total reachable) | `test_response_schema_resolved_to_order` |
| 12 | `security_schemes` (HTTPBasic/http) + per-op `security` round-trip fidelity | `test_security_schemes_and_per_operation_security` |
| 13 | JSON-serializable; same input twice → byte-identical; canonical (path, method) order | `test_serialization_is_json_serializable_and_stable`, `test_operations_deterministically_ordered` |
| 14 | Serialized surface equal across dict/file/string/URL | `test_round_trip_equality_across_source_kinds` |
| 15 | Non-OpenAPI object / invalid JSON → named `SpecLoadError` | `test_non_openapi_object_rejected`, `test_malformed_json_string_rejected` |
| 16 | Missing file / unreachable URL → named `SpecLoadError` | `test_missing_file_rejected`, `test_unreachable_url_rejected` |
| 17 | Unsupported (GraphQL) source → named `UnsupportedSourceError`; source-agnostic op shape | `test_unsupported_graphql_source_rejected`, `test_operation_shape_is_source_agnostic` |
| 18 | Correct home + stable public import path exposing API | `test_public_import_path_exposes_api` (whole suite runs under `connectors/tests/` via `uv run pytest connectors/tests -q`) |
| 19 | No network egress for non-URL sources; no file writes on load | `test_no_network_egress_for_non_url_sources`, `test_no_file_writes_on_load` |

Notes on coverage scope:
- Criterion 4's optional YAML-string support is not asserted (the spec makes it optional either way);
  the JSON-string path is asserted firmly.
- Criterion 18's "correct home / runnable" is satisfied structurally by the suite living under
  `connectors/tests/` and importing `connectors.spec_loader`; `test_public_import_path_exposes_api`
  additionally pins the exposed public surface.
- Criterion 19's broader "no regression to Phase 0 suites / protected files" is a harness-level
  guarantee (the tester adds no implementation and does not touch `reference_app/**`); the two
  side-effect containment tests cover the loader-specific "no egress except URL / no writes" clauses.

## Captured red run

`uv run pytest connectors/tests -q` — all 24 tests error at fixture setup with
`ModuleNotFoundError: No module named 'connectors.spec_loader'`, i.e. legitimately red for the RIGHT
reason (missing implementation), not broken scaffolding. The fixtures themselves were verified sound
independently (the real app's OpenAPI doc is captured and the loopback stub server round-trips).

```
ERROR connectors/tests/test_spec_loader.py::test_load_from_in_memory_dict - ModuleNotFoundError: No module named 'connectors.spec_loader'
ERROR connectors/tests/test_spec_loader.py::test_load_from_local_file_matches_dict
ERROR connectors/tests/test_spec_loader.py::test_load_from_http_url_matches_dict
ERROR connectors/tests/test_spec_loader.py::test_load_from_raw_json_string_matches_dict
ERROR connectors/tests/test_spec_loader.py::test_source_kind_autodetection_equivalent
ERROR connectors/tests/test_spec_loader.py::test_document_metadata
ERROR connectors/tests/test_spec_loader.py::test_operations_enumerated_exactly
ERROR connectors/tests/test_spec_loader.py::test_per_operation_fields_present
ERROR connectors/tests/test_spec_loader.py::test_path_parameter_surfaced
ERROR connectors/tests/test_spec_loader.py::test_request_body_schema_resolved
ERROR connectors/tests/test_spec_loader.py::test_response_schema_resolved_to_order
ERROR connectors/tests/test_spec_loader.py::test_security_schemes_and_per_operation_security
ERROR connectors/tests/test_spec_loader.py::test_serialization_is_json_serializable_and_stable
ERROR connectors/tests/test_spec_loader.py::test_operations_deterministically_ordered
ERROR connectors/tests/test_spec_loader.py::test_round_trip_equality_across_source_kinds
ERROR connectors/tests/test_spec_loader.py::test_non_openapi_object_rejected
ERROR connectors/tests/test_spec_loader.py::test_malformed_json_string_rejected
ERROR connectors/tests/test_spec_loader.py::test_missing_file_rejected
ERROR connectors/tests/test_spec_loader.py::test_unreachable_url_rejected
ERROR connectors/tests/test_spec_loader.py::test_unsupported_graphql_source_rejected
ERROR connectors/tests/test_spec_loader.py::test_operation_shape_is_source_agnostic
ERROR connectors/tests/test_spec_loader.py::test_public_import_path_exposes_api
ERROR connectors/tests/test_spec_loader.py::test_no_network_egress_for_non_url_sources
ERROR connectors/tests/test_spec_loader.py::test_no_file_writes_on_load
24 errors in 0.29s
```

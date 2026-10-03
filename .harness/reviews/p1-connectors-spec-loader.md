# Review — `p1-connectors-spec-loader`

**Verdict: APPROVE**

Independent review of the OpenAPI spec loader against the spec, the Tester's suite, and quality.

## Test run (independently executed)

```
$ uv run pytest connectors/tests -q
........................                                                 [100%]
24 passed in 1.74s
```

Phase-0 regression spot-check (no regression):

```
$ uv run pytest reference_app/backend/tests eval/tests -q
...........................................................              [100%]
59 passed, 1 warning in 62.80s
```

(The lone warning is a pre-existing Starlette/httpx deprecation, unrelated to this unit.)

## 1. Acceptance — all criteria 1–19 met

- **1–5 (multi-source + auto-detect + cross-kind equality):** `load_spec` accepts dict, file path,
  HTTP(S) URL, and raw JSON string via `_load_document` auto-detection; dict/file/string/URL forms
  produce equal serialized surfaces (`test_source_kind_autodetection_equivalent`,
  `test_round_trip_equality_across_source_kinds`). Confirmed.
- **6–9 (metadata, exact ops, per-op fields, path param):** `title`/`version` from `info`; exactly
  the 5 (method, path) pairs, method upper-cased, templated `/orders/{order_id}` preserved; pinned
  keys present with correct list/mapping types; `order_id` surfaced as required `in=path`. Confirmed.
- **10–11 (`$ref` resolution):** request body `$ref → AddItem` and response `$ref → Order` are
  inlined so `product_id`/`quantity` and `id`/`items`/`total` read directly off `properties`; no
  dangling `$ref`. `_resolve_refs` is intra-document only (`#/…`) with a path-based cycle guard
  (`seen` frozenset) and leaves external/cyclic refs untouched — total and terminating.
- **12 (security):** `security_schemes` copied verbatim (HTTPBasic, `type: http`); per-op `security`
  is op-declared → doc-level default → `[]`, faithfully round-tripping the fixture.
- **13–14 (determinism + serialization):** `to_dict()` emits operations sorted by `(path, method)`,
  responses sorted by status code, deterministic content-schema selection (prefers
  `application/json`); byte-identical across repeat calls and across source kinds. No timestamps or
  object addresses.
- **15–17 (errors):** non-OpenAPI object, malformed JSON, missing file, and unreachable URL all raise
  `SpecLoadError` (not `KeyError`, not a silent empty surface); `source_type="graphql"` raises
  `UnsupportedSourceError` (a `SpecLoadError` subclass). Operation shape uses only generic keys.
- **18–19 (home, no-regression, side-effects):** code under `connectors/` at the pinned public path
  `connectors.spec_loader`; no network egress for non-URL sources (urlopen reached only on http(s));
  no file writes; no credential handling/logging. `.gitkeep` removed now that real files exist.

## 2. Test integrity

The suite is the Tester's; tests are exercised only through the documented public surface
(`load_spec`, `.to_dict()`, named errors) and pinned serialized keys — not implementation internals.
Assertions are substantive (concrete field sets, exact op-key set, cross-source equality, byte
stability, `pytest.raises` on named errors). No sign of weakening or gaming. The developer honored
the pinned names rather than editing tests.

## 3. Scope

No scope creep. GraphQL correctly deferred to a documented `UnsupportedSourceError` path with a
source-agnostic model. Accepting a `swagger` marker in addition to `openapi` is a minor, harmless
liberalization consistent with "validate it is an OpenAPI document" and not worth blocking.

## 4. Quality

Clean, minimal, well-documented (`connectors/README.md` pins the public API, surface shape, source
kinds, error types, side-effect containment, and the GraphQL-deferred note). `$ref` resolution
deep-copies before inlining so the source document is never mutated. No dead code. No secrets logged
or persisted.

## Protected files

No changes to `reference_app/**` (verified: `git diff HEAD --name-only -- reference_app/` empty), nor
to `DESIGN.md` / `META_PLAN.md` / `CLAUDE.md`. `AGILE_PLAN.md` and `.harness/backlog.md` edits are the
TPM's planning updates (expected), not developer changes.

Deploy gate: unlocked — task id written to `.harness/state/APPROVED`.

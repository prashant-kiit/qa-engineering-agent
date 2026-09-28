# Review — `p1-target-config`

**Verdict: APPROVE**

Independent review of `connectors/target_config.py`, `connectors/examples/reference_app.target.json`,
and the `connectors/README.md` section against the spec, the Tester's suite, and quality.

## Test run (independently executed)

```
$ uv run pytest connectors/tests -q
........................................................................ [ 93%]
.....                                                                    [100%]
77 passed in 1.75s
```
= 24 unit-1 tests + 53 new unit-2 tests (matches the Tester's captured RED count → tests
un-gamed and unmodified).

Phase-0 regression spot-check (no regression):
```
$ uv run pytest reference_app/backend/tests eval/tests -q
59 passed, 1 warning in 62.74s
```

## 1. Acceptance — all criteria 1–18 met
- **1–4 Load/schema:** loads from mapping and JSON file (equal `to_dict`); exposes the five
  pinned top-level fields; `to_dict()["planner_fields"]` carries exactly the seven pinned
  names (dataclass + `_validate_planner` enforce the closed set).
- **5–8 Validation:** missing top-level field → `TargetConfigError` naming the field (never a
  bare `KeyError`); malformed/empty/wrong-typed fields rejected with the field named;
  `depth` constrained to `{smoke, regression, exhaustive}`; each of the seven planner fields
  required and non-empty.
- **9–11 Secret-safety:** frozen dataclass stores only the reference name; `to_dict`/`__repr__`
  emit only pinned keys (no secret surface); `resolve_credential()` reads `os.environ` at call
  time, returns to caller, stores nothing back (frozen), logs nothing; `CredentialUnsetError`
  raised on unset, and it is **not** a subclass of `TargetConfigError` (distinct, as required).
- **12–13 Spec hand-off:** `load_api_spec()` imports the `spec_loader` *module* and calls
  `spec_loader.load_spec(self.api_spec_source)` — dynamic lookup (monkeypatchable), no
  reimplementation; `SpecLoadError`/`UnsupportedSourceError` propagate unchanged.
- **14–15 Example config:** wired to the clean reference app, validates cleanly, seven planner
  fields populated, `depth=regression`; file contains no `testuser`/`testpass`.
- **16–18 Determinism/placement/no-regression:** fixed key ordering → byte-identical repeat
  serialization; code under `connectors/`; unit-1 API untouched; Phase-0 suites green.

## 2. Test integrity
Tests are meaningful (env-var sentinel proof across `to_dict`/`repr`/`str`/`caplog` before and
after resolve; loader-error propagation via real `SpecLoadError` and monkeypatched
`UnsupportedSourceError`; parametrised missing/malformed/enum cases). Test file is new and
unit-1's `test_spec_loader.py` is unmodified. No weakening.

## 3. Scope
Only `connectors/target_config.py`, the example JSON, and a README section added; `.harness/`
task/tests/backlog updates are expected harness artifacts. No MCP/prompt/agent work, no real
vaulting, no spec re-parsing. No protected file (`DESIGN.md`/`META_PLAN.md`/`AGILE_PLAN.md`/
`CLAUDE.md`) and no `reference_app/**` behavior changed.

## 4. Quality — plus the two flagged design choices
- **`brd_path` existence not required (non-empty string only):** acceptable. No acceptance
  criterion tests existence; criterion 6's "at minimum" malformed list excludes `brd_path`; the
  Tester note explicitly makes existence optional ("the loader *may* require the BRD path to
  exist"). Documented in README. Fine for this unit (BRD content handling is Phase 4).
- **Inlined-secret keys ignored (not retained):** acceptable per criterion 9's either-branch.
  The frozen dataclass holds only the five known fields, `to_dict()` emits only pinned keys, and
  `vars(cfg)` carries no extra keys — the sentinel is unreachable. Documented.
- Correct, simple, no dead code (`source_type` is a documented reserved hint per the spec's
  allowed signature). Reuses `connectors.spec_loader` rather than duplicating. Security per
  §11.4 satisfied: reference-only storage, at-call-time resolution, no logging/caching of the
  secret.

Deploy-gate marker written.

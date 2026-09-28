# Task: `p1-target-config` — `connectors/` per-run target config (schema + loader)

## Title
The **per-run target configuration** for `connectors/`: a Python (`uv`) schema + loader that reads
the configuration a single authoring run needs — **target UI URL**, **API-spec source** (consumed by
the unit-1 `connectors.spec_loader`), **BRD source path**, a **Basic-Auth credential *reference***
(an env-var / vault-key **name**, never the secret value — `DESIGN.md §11.4`), and the **seven
structured Planner fields** (`DESIGN.md §6`). It **validates** required fields, raises a **named
error** on missing/invalid config, and is **secret-safe** (no secret value is ever stored on the
object or emitted by its serialization/logging). Ships a concrete **reference-app example config** as
the canonical example. No model key required; testable purely with fixtures.

## Context (plan item)
- **AGILE_PLAN.md → Phase 1 → D2** ("`connectors/` — per-run target config") and the **Phase 1 unit
  table** unit 2. Depends on unit 1 (`p1-connectors-spec-loader`, now **done**, merged commit
  `97f9b53`) — dep met.
- **Backlog unit 2** (`p1-target-config`, status `spec-ready`).
- **DESIGN.md §6** — the structured field set that drives the Planner (the **seven fields** enumerated
  below) plus the freeform, content-hashed **BRD**. This config is the machine-readable carrier of
  those fields for a run.
- **DESIGN.md §11.4** — "target-app login is **Basic Auth (username/password)** stored in the vault
  and injected at **runtime**, egress-scoped, **never in prompts, logs, traces, or artifacts**;
  ephemeral; rotated." → this config may hold only a **reference** to the credential, never the
  secret itself.
- **DESIGN.md §10** — per-app config carries "target URL, API spec, BRD source, repo, secrets,
  memory, test suite, CLI choice, model/tier"; the **per-run target config** here is the local-first,
  single-app slice of that (URL + API-spec source + BRD + credential reference + Planner fields).
- **DESIGN.md §13** — `connectors/  # playwright-mcp config, api-spec loader, per-run target config`
  is the home directory. **§12** — control-plane glue/tooling is **Python** (`uv`); test artifacts
  stay TypeScript Playwright (this is Python tooling the glue consumes, not a test artifact).
- This unit is the **per-run input contract** the later agent-run glue (unit 6) reads. It is **not**
  the spec loader (unit 1, done — this config *points at* a spec and *delegates* loading to it), not
  the MCP config (unit 3), not the prompt/sub-agents/glue/live-run (units 4–7), and **not** a secret
  vault (only the *reference* mechanism lives here).

**Given app state (contracts to build on — do NOT re-derive or modify):**
- **Unit-1 spec loader is present and stable** at import path `connectors.spec_loader`, exposing
  `load_spec(source, source_type="auto") -> ApiSurface`, `ApiSurface` (with `.to_dict()`),
  `SpecLoadError`, and `UnsupportedSourceError` (see `connectors/README.md`). The API-spec-source
  field of this config is exactly a **`source`** that `load_spec` accepts (a URL, file path, raw
  string, or mapping). **This unit does not re-parse specs** — it validates/stores the source and
  offers a documented hand-off to `connectors.spec_loader` (delegation, no duplication).
- **Clean reference app (pristine):** React+Vite UI at `http://127.0.0.1:5173`; FastAPI backend at
  `http://127.0.0.1:8000` serving **OpenAPI 3.1.0** at `GET /openapi.json`; Basic Auth
  `testuser`/`testpass` (the **values** live outside config — the config names an env var, e.g.
  `REF_APP_BASIC_AUTH`, that a runtime would resolve). Freeform BRD at `reference_app/BRD.md`.
- `connectors/` already contains real code (`spec_loader.py`, `__init__.py`, `tests/`, `README.md`).
  This unit **adds** the target-config module + its tests + example config + README section; it must
  not break unit-1's public API or tests.
- Root project uses `uv` (`pyproject.toml`); Phase 0/1 suites run via `uv run pytest <dir> -q`.

## Scope

### In scope
1. **A Python target-config module under `connectors/`** exposing a documented, stable public API
   (see Interfaces) that **loads** a per-run target config from a file (JSON; YAML support
   optional-but-documented) and/or an already-parsed mapping/dict, **validates** it, and returns a
   typed, immutable-ish **target-config object**.
2. **The target-config schema/model** (see Interfaces §Model) with pinned field names carrying:
   - `target_url` — the running target **UI** URL (string).
   - `api_spec_source` — the source the unit-1 loader consumes (URL / file path / raw string /
     mapping). Stored as given; **not** parsed by this unit.
   - `brd_path` — filesystem path to the freeform BRD document.
   - `basic_auth_credential_ref` — the **name** of the env var / vault key that a runtime resolves to
     the Basic-Auth username/password (a **reference**, never the secret).
   - `planner_fields` — the **seven** structured Planner fields (see §Model; names pinned below).
3. **Required-field validation** raising a **named, documented error** (Interfaces §Errors) when a
   required field is missing, empty, wrong-typed, or malformed (e.g. `target_url` not a URL-shaped
   string; `planner_fields` missing one of the seven; `basic_auth_credential_ref` absent/blank).
4. **Secret-safety, provable in tests** (Interfaces §Secret-safety):
   - The object stores only the **reference name**, never a username/password value.
   - The module provides a **documented resolution hand-off** that reads the secret from the
     environment/vault **only at call time** and **does not** retain it on the config object.
   - Serialization (`to_dict()` / `__repr__` / any logging helper) emits the **reference name only**
     and **never** any resolved secret value — so a test can assert that a secret placed in the
     environment never appears in the serialized/`repr`/log output.
5. **A documented hand-off to the unit-1 spec loader**: a method/helper that passes
   `api_spec_source` to `connectors.spec_loader.load_spec(...)` and returns its `ApiSurface`
   (delegation only — this unit adds no spec-parsing logic and re-raises the loader's named errors
   unchanged).
6. **A concrete reference-app example config file** committed under `connectors/` (Interfaces §Paths)
   wired to the clean reference app: `target_url` = `http://127.0.0.1:5173`, `api_spec_source` =
   `http://127.0.0.1:8000/openapi.json`, `brd_path` = `reference_app/BRD.md`,
   `basic_auth_credential_ref` = an env-var name (e.g. `REF_APP_BASIC_AUTH`), and the seven
   `planner_fields` filled with sensible shop-domain values. The example must **load and validate
   cleanly** through the loader and contain **no secret value**.
7. **A test suite** under `connectors/tests/` (pytest) proving the acceptance criteria against
   fixtures + the shipped example config, runnable via `uv run pytest connectors/tests -q`.
8. **Docs**: extend `connectors/README.md` (a new section) documenting the public API, the config
   schema + pinned field names, the seven Planner-field names, the credential-reference (secret-
   safety) rule, required-field validation + error types, the spec-loader hand-off, and the example
   config path.

### Out of scope (defer)
- **Playwright-MCP config** — unit 3.
- **QA system prompt, Planner/Generator sub-agents, agent-run glue, any live agent run** — units 4–7.
- **Re-parsing / normalizing the API spec** — that is unit 1 (`connectors.spec_loader`, done); this
  unit only validates + carries the source and delegates loading.
- **Real secret management / vaulting / rotation / injection plumbing** — only the *reference*
  mechanism (a name the config carries + an at-call-time resolution hand-off) lives here.
- **BRD content parsing / hashing** (hashing is Phase 4); this unit only validates the path exists /
  is a well-formed path per the criteria, not the BRD's contents.
- **Multi-app / multi-tenant config, repo/CLI/model fields** (`DESIGN.md §10` full shape) — later
  phases; the per-run local-first slice only.
- **Any change to the clean `reference_app/**` sources**, to unit-1's `connectors/spec_loader.py`
  public behavior, or to protected files (`DESIGN.md`, `META_PLAN.md`, `AGILE_PLAN.md`, `CLAUDE.md`,
  `.harness/**`).

## Acceptance criteria (enumerated, testable)

### Loading & schema
1. **Load from a mapping/dict.** Given an already-parsed config mapping with all required fields, the
   loader returns a target-config object without error.
2. **Load from a file.** Given a filesystem path to a JSON config file with all required fields, the
   loader reads, parses, and returns an object **equal** to the one produced from the equivalent
   mapping. (YAML file support is optional; if implemented it is documented, else a YAML file yields
   the documented validation/load error.)
3. **Field access.** The returned object exposes, under the pinned names (Interfaces §Model):
   `target_url`, `api_spec_source`, `brd_path`, `basic_auth_credential_ref`, and `planner_fields`
   (carrying all seven sub-fields).
4. **Seven Planner fields present & named.** `planner_fields` exposes **exactly** the seven fields
   with the pinned names (§Model): `target_scope`, `intent`, `expected_behavior`, `priority_risk`,
   `test_data_preconditions`, `out_of_scope_constraints`, `depth` — no more, no fewer. A config
   missing any one of the seven fails validation (criterion 8).

### Validation & named error
5. **Missing required top-level field rejected.** Omitting any required top-level field
   (`target_url`, `api_spec_source`, `brd_path`, `basic_auth_credential_ref`, `planner_fields`)
   raises the module's **named** config error (Interfaces §Errors) — not a bare `KeyError`, not a
   silent default.
6. **Malformed field rejected.** A wrong-typed / empty / malformed field raises the named config
   error, with a message identifying the offending field. At minimum: `target_url` that is not a
   non-empty URL-shaped string; `basic_auth_credential_ref` that is empty/blank/non-string;
   `planner_fields` that is not a mapping of the seven fields.
7. **`depth` constrained.** The `depth` Planner field is validated against a **documented enumerated
   set** (per `DESIGN.md §6`: `smoke` / `regression` / `exhaustive`); a value outside the set raises
   the named config error. (Other Planner fields are free text; empty required Planner text fields
   fail per criterion 8.)
8. **Each of the seven Planner fields required.** A config in which any one of the seven Planner
   fields is absent or empty raises the named config error naming the missing field.

### Secret-safety (credential is a reference only)
9. **Only a reference is stored.** The config object stores `basic_auth_credential_ref` as the
   **name** of an env var / vault key (a string), and provides **no** field holding a username or
   password value. A config that inlines a raw secret (e.g. a `password`/`basic_auth` value field)
   is either rejected by the schema or the value is not retained — the Tester asserts no secret value
   is reachable on the object.
10. **Serialization leaks no secret.** With a secret value present in the environment under the
    referenced name, serializing the object (`to_dict()`), its `repr()`, and any provided
    logging/summary helper output **contain the reference name but never the secret value**. (Tester
    sets an env var to a sentinel secret, then asserts the sentinel appears in **no** serialized/
    repr/log output.)
11. **Resolution is at-call-time and non-retaining.** The documented credential-resolution hand-off
    (Interfaces §Secret-safety) reads the secret from the environment/vault **only when called** and
    the resolved value is **not** stored back on the config object (a subsequent `to_dict()`/`repr()`
    still shows only the reference — re-verifies criterion 10 after a resolve call). If the referenced
    env var / key is unset at resolve time, a **named** error is raised (documented) — distinct from
    the load/validation error.

### Spec-loader hand-off (reuse unit 1, no duplication)
12. **Delegates to `connectors.spec_loader`.** The documented hand-off passes `api_spec_source` to
    `connectors.spec_loader.load_spec(...)` and returns its `ApiSurface`. For the reference example
    config's `api_spec_source`, the returned surface is the same one unit 1 produces for that source
    (Tester may use a mock/stub or the equivalent dict form so no external network is required). This
    unit performs **no** independent spec parsing/normalization.
13. **Loader errors surfaced unchanged.** If `load_spec` raises its named error (`SpecLoadError` /
    `UnsupportedSourceError`), the hand-off propagates it unchanged (not swallowed, not rewrapped
    into the config error) — so spec problems are diagnosable as spec problems.

### Reference-app example config
14. **Example config present & valid.** The committed reference-app example config file (Interfaces
    §Paths) loads and validates cleanly through the loader, yields `target_url` =
    `http://127.0.0.1:5173`, `api_spec_source` = `http://127.0.0.1:8000/openapi.json`, `brd_path`
    pointing at `reference_app/BRD.md`, a non-empty `basic_auth_credential_ref` env-var **name**, and
    all seven Planner fields populated with `depth` in the enumerated set.
15. **Example config is secret-free.** The example config file contains **no** username/password
    value — only the credential **reference name** (asserted against the file contents / loaded
    object).

### Determinism, placement, tests, no-regression
16. **Deterministic serialization.** `to_dict()` uses the pinned key names and stable ordering; the
    **same** input serialized twice yields **identical** output; a file and its equivalent mapping
    serialize equal. No non-deterministic content.
17. **Correct home + runnable tests.** New code lives under `connectors/` with the pinned public
    import path (Interfaces §Paths); tests live under `connectors/tests/` and pass via
    `uv run pytest connectors/tests -q`. Unit-1's existing tests still pass unchanged.
18. **No regressions.** No change to `reference_app/**` behavior, to unit-1's `spec_loader` public
    API, or to any protected file; Phase 0 `make test` / `make eval` / backend pytest still pass. The
    loader performs **no writes**, **no network egress** of its own (network only occurs if the
    spec-loader hand-off in criterion 12 is invoked with a URL source), and **never** logs/persists
    any credential value.

## Interfaces / contracts (pin these precisely)

### Paths
- **Module home (binding):** `connectors/` — importable at a stable path, e.g.
  `connectors.target_config` (exact module filename the developer's choice, but the public import
  path must be documented in `connectors/README.md` and kept stable). Reuse the existing `connectors`
  package (`__init__.py` already present).
- **Tests:** `connectors/tests/` (pytest), runnable as `uv run pytest connectors/tests -q`.
- **Example config (binding path + name):** a committed file under `connectors/`, e.g.
  `connectors/examples/reference_app.target.json` (exact name the developer's choice, documented in
  the README; a JSON file wired to the clean reference app per criteria 14–15).
- **Docs:** a new section in `connectors/README.md`.

### Public API (shape — names/signatures the developer's choice but must be documented & stable)
- A primary loader entry point accepting a **source** (file path or mapping; source-kind hint
  parameter allowed with an `auto`/file default) returning the validated **target-config** object;
  raises the named config error (below) on invalid/missing fields.
- A documented **spec hand-off** (method or function) that returns
  `connectors.spec_loader.load_spec(<api_spec_source>) -> ApiSurface` (criteria 12–13).
- A documented **credential-resolution hand-off** (method or function) that resolves the referenced
  env var / vault key at call time and returns the secret **to the caller only** (never stored),
  raising a named "credential unset" error when absent (criterion 11).
- A `to_dict()` (and safe `__repr__`) that serialize deterministically and secret-free (criteria
  10, 16).

### Model (target config — pinned field names for the JSON/consumer contract)
The config document / serialized object has, at minimum:
- `target_url` (string) — the running target UI URL.
- `api_spec_source` (string | mapping) — a `source` accepted by `connectors.spec_loader.load_spec`.
- `brd_path` (string) — filesystem path to the freeform BRD.
- `basic_auth_credential_ref` (string) — the **name** of the env var / vault key holding the
  Basic-Auth credential. **No** field for the raw username/password.
- `planner_fields` (mapping) — the **seven** Planner fields, with **pinned names** mapped to
  `DESIGN.md §6` (see §Seven-Planner-fields below):

  | pinned name | `DESIGN.md §6` field | notes |
  |---|---|---|
  | `target_scope` | Target scope (feature/flow) | free text |
  | `intent` | Intent / goal | free text |
  | `expected_behavior` | Expected behavior / acceptance criteria | free text |
  | `priority_risk` | Priority / risk areas | free text |
  | `test_data_preconditions` | Test data / preconditions | free text |
  | `out_of_scope_constraints` | Out-of-scope / constraints | free text |
  | `depth` | Depth (smoke / regression / exhaustive) | enumerated: `smoke` \| `regression` \| `exhaustive` |

The in-memory object may use dataclasses/typed objects; the **serialized** form uses the key names
above.

### Errors (named, documented)
- A module-level **config error** (e.g. a `TargetConfigError`-style class; exact name the developer's
  choice, documented) raised for: missing required field (criteria 5, 8), malformed/wrong-typed
  field (criterion 6), and out-of-set `depth` (criterion 7). Messages must name the offending field.
- A distinct named **"credential unset"** error (or documented subclass) for the resolve-time case
  where the referenced env var / vault key is absent (criterion 11) — distinct from the config error.
- Unit-1's `SpecLoadError` / `UnsupportedSourceError` are **propagated unchanged** by the spec
  hand-off (criterion 13), not rewrapped.

### Secret-safety (binding rule, per `DESIGN.md §11.4`)
- The config object and every serialization/`repr`/logging path expose the credential **reference
  name only**; a resolved secret value is **never** stored on the object and **never** appears in
  `to_dict()` / `repr()` / logs. The Tester proves this by placing a sentinel secret in the
  environment and asserting it appears nowhere in the object's serialized/repr/log surfaces, before
  and after invoking the resolution hand-off.

### Seven Planner fields (pinned — source: `DESIGN.md §6`, "Structured field set (drives the Planner)")
`DESIGN.md §6` enumerates exactly seven structured fields (and §6 itself calls them "the seven
fields"). Pinned, in order:
1. **Target scope (feature/flow)** → `target_scope`
2. **Intent / goal** → `intent`
3. **Expected behavior / acceptance criteria** → `expected_behavior`
4. **Priority / risk areas** → `priority_risk`
5. **Test data / preconditions** → `test_data_preconditions`
6. **Out-of-scope / constraints** → `out_of_scope_constraints`
7. **Depth (smoke / regression / exhaustive)** → `depth`

### Fixtures (guidance for the Tester — not implementation)
- Small hand-crafted config mappings/files (valid + each invalid variant: missing field, malformed
  field, out-of-set `depth`, missing a Planner field, inlined-secret attempt) drive the
  validation/error criteria.
- The shipped **reference-app example config** file drives criteria 14–15 and 12.
- The spec hand-off (criterion 12) may use a mock/stub of `connectors.spec_loader.load_spec` or an
  equivalent in-memory `api_spec_source` (dict) so no external network is required.
- The secret-safety criteria (10–11) use an env-var sentinel set in the test environment.

## Definition of Done
- All acceptance criteria **1–18** pass.
- The target-config module (public import path documented + stable), the schema/model with the pinned
  serialized key names (including the seven Planner-field names), required-field validation with the
  named config error, the secret-safe credential-reference handling + at-call-time resolution
  hand-off + named "credential unset" error, the delegating spec-loader hand-off, deterministic
  `to_dict()`, the `connectors/tests/` tests, the committed reference-app example config, and the
  updated `connectors/README.md` section all exist under `connectors/`.
- `uv run pytest connectors/tests -q` is green from a clean checkout under `uv` (unit-1 tests still
  pass unchanged).
- No protected file changed (`DESIGN.md`, `META_PLAN.md`, `AGILE_PLAN.md`, `CLAUDE.md`, `.harness/**`);
  no change to `reference_app/**` behavior or to unit-1's `spec_loader` public API; Phase 0
  `make test` / `make eval` / backend pytest still pass. Consistent with `DESIGN.md §6/§10/§11.4/§12/§13`
  and `AGILE_PLAN.md` D2.
- **Tester-can-author-from-this-alone:** from this spec alone (pinned import path + example config
  path, the config schema with the pinned field names incl. the seven Planner-field names and the
  `depth` enum, required-field validation + named error behavior, the secret-safety rule with the
  env-var-sentinel proof, the deterministic serialization contract, and the spec-loader/credential
  resolution hand-offs), the Tester can author the failing verification tests **without reading the
  implementation**.

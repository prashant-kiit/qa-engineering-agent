# Task: `p1-connectors-spec-loader` — `connectors/` OpenAPI spec loader → normalized API surface

## Title
The **API spec loader** for `connectors/`: a Python (`uv`) module that loads an **OpenAPI** document
from a URL, a local file, or an in-memory object, validates it is an OpenAPI document, and produces a
**normalized, deterministic, JSON-serializable "API surface"** — per-operation method, path,
parameters, request/response schemas (with intra-document `$ref` resolved), and declared security —
that a downstream Generator uses to **ground API assertions in the schema** (`DESIGN.md §5.1`). No
model key required; testable purely with fixtures.

## Context (plan item)
- **AGILE_PLAN.md → Phase 1 → D1** ("`connectors/` — API spec loader") and the **Phase 1 unit table**
  unit 1. First Phase 1 unit; deps = Phase 0 (done) → met.
- **Backlog unit 1** (`p1-connectors-spec-loader`).
- **DESIGN.md §5.1** — grounding: "API assertions grounded in the OpenAPI/GraphQL schema." **§4** —
  the Generator turns the plan into TS Playwright + API tests over "Playwright MCP + API tool
  (OpenAPI/GraphQL)." **§13** — `connectors/  # playwright-mcp config, api-spec loader, per-run
  target config` is the home. **§12** — control-plane glue/tooling is **Python**; test artifacts stay
  TS Playwright (this loader is Python tooling the agent/glue consumes, not a test artifact).
- This unit is the **schema-grounding data source**. It is **not** the agent, not the Planner/
  Generator, not the per-run config, not the MCP config (those are later Phase 1 units). It only
  loads a spec and normalizes it.

**Given app state (contracts to build on — do NOT re-derive or modify):**
- The clean reference backend (`reference_app.backend.app:app`) serves an **OpenAPI 3.1.0** document
  at `GET /openapi.json` (no auth on that endpoint). Its `paths` are `GET /products`, `GET /cart`,
  `POST /cart/items`, `POST /checkout`, `GET /orders/{order_id}`; `components.securitySchemes`
  contains `HTTPBasic`; `components.schemas` contains `Product`, `Cart`, `CartLine`, `Order`,
  `AddItem`, `HTTPValidationError`, `ValidationError`. This document is a valid **real fixture** for
  this unit (the Tester may capture it by importing the backend / hitting `/openapi.json` on the
  clean app; the clean app must not be modified).
- `connectors/` is currently an **empty placeholder** (`.gitkeep` only). This unit creates its first
  real contents.
- Root project uses `uv` (`pyproject.toml`); Phase 0 test suites live in per-area `tests/` dirs
  (e.g. `reference_app/backend/tests`, `eval/tests`) run via `uv run pytest <dir> -q`.

## Scope

### In scope
1. **A Python spec-loader module under `connectors/`** exposing a documented public API (see
   Interfaces) that loads an OpenAPI document from any of: an **HTTP(S) URL**, a **local file path**,
   a **raw string** (JSON; YAML support optional-but-documented), or an **already-parsed mapping/dict**
   — auto-detecting the source kind — and returns a **normalized API surface** object.
2. **The normalized "API surface" model** (see Interfaces §Model) with pinned field names: document
   `title` + `version`; a deterministically-ordered list of **operations** each carrying `method`,
   `path`, `operation_id`, `summary`, `parameters`, `request_body`, `responses`, and declared
   `security`; and the document's `security_schemes`.
3. **Intra-document `$ref` resolution** for request/response body schemas and parameter schemas so a
   consumer can read the concrete field set of `components.schemas` entries (e.g. the `Order` schema's
   fields) without doing its own `$ref` chasing.
4. **Deterministic, JSON-serializable output**: a method that renders the surface to a plain
   dict/JSON with stable key names and stable ordering (same input → byte-stable output), so the
   downstream glue/agent can consume it and tests can assert on it.
5. **Defined error behavior**: loading an unreachable URL / missing file / non-OpenAPI or malformed
   document raises a **named, documented exception** (not a silent empty surface). Unknown/unsupported
   source types (e.g. a GraphQL SDL/introspection source) have **documented** behavior (a named
   "not supported yet" error) — the GraphQL adapter itself is **out of scope** (deferred), but the
   normalized model and loader entry point are shaped to accommodate a future GraphQL adapter.
6. **A test suite** under `connectors/tests/` (pytest) proving the acceptance criteria against
   fixtures, runnable via `uv run pytest connectors/tests -q`.
7. **Docs**: a short `connectors/README.md` (or module docstring section) documenting the public API,
   the normalized-surface shape + key names, accepted source kinds, the error types, and the
   GraphQL-deferred note.

### Out of scope (defer)
- **The GraphQL adapter implementation** (only interface-level accommodation + a documented
  "not supported yet" path here).
- **Per-run target config** (target URL, BRD path, credential refs, the seven Planner fields) — that
  is unit 2 (`p1-target-config`).
- **Playwright-MCP config** — unit 3.
- **The QA system prompt, Planner/Generator sub-agents, agent-run glue, and any live agent run** —
  units 4–7.
- **Generating tests / assertions from the surface** — the loader only *produces the grounding data*;
  the Generator (later, agent-side) consumes it.
- **Live schema-drift detection, spec diffing/versioning/hashing, caching** (hashing/diff is Phase 4).
- **Full OpenAPI validation to spec** (e.g. exhaustive `$ref` cycles across external documents,
  full JSON-Schema validation of instances). Only the normalization + intra-document `$ref`
  resolution described above is required; external `$ref`s (other files/URLs) may be treated as an
  unsupported/documented case.
- **Any change to the clean `reference_app/**` sources**, and to protected files (`DESIGN.md`,
  `META_PLAN.md`, `AGILE_PLAN.md`, `CLAUDE.md`, `.harness/**`).

## Acceptance criteria (enumerated, testable)

### Loading from multiple source kinds
1. **Load from an in-memory dict.** Given an already-parsed OpenAPI 3.x mapping (the reference app's
   `/openapi.json` object is a valid such input), the loader returns an API-surface object without
   error.
2. **Load from a local file.** Given a filesystem path to a JSON file containing an OpenAPI document,
   the loader reads and parses it and returns the same surface it would for the equivalent dict.
3. **Load from an HTTP(S) URL.** Given a URL that serves an OpenAPI JSON document (a local test HTTP
   server / the running clean backend's `http://127.0.0.1:8000/openapi.json` / a mocked HTTP
   response — the Tester's choice), the loader fetches and parses it and returns the equivalent
   surface. (The Tester may use a stub/mock server so the test needs no external network.)
4. **Load from a raw JSON string** yields the equivalent surface. (YAML string support is
   optional; if implemented it is documented, if not, a YAML string produces the documented error.)
5. **Source-kind auto-detection** is documented and correct: the same public entry point accepts all
   supported kinds (or a documented small set of entry points), and equivalent inputs across kinds
   (dict vs file vs string vs URL of the *same* document) produce **equal** normalized surfaces.

### Normalized API surface — shape and content (fixture: the reference OpenAPI document)
6. **Document metadata.** The surface exposes the document `title` and `version` taken from the
   OpenAPI `info` object.
7. **Operations enumerated.** For the reference fixture, the surface enumerates exactly the operations
   for these (method, path) pairs and no phantom ones: `GET /products`, `GET /cart`,
   `POST /cart/items`, `POST /checkout`, `GET /orders/{order_id}`. `method` is normalized to
   upper-case; `path` is the templated path exactly as in the document (`/orders/{order_id}`).
8. **Per-operation fields present.** Each operation exposes, under pinned names (Interfaces §Model):
   `method`, `path`, `operation_id` (the spec's `operationId` or `null`/absent if none), `summary`
   (or `null`), `parameters` (a list — path/query params with `name`, `in`/location, `required`,
   `schema`; empty list when none), `request_body` (present for `POST /cart/items` and `POST
   /checkout` if the spec declares one, else `null`/absent), and `responses` (keyed by status code
   string, each with its response schema when the spec declares content).
9. **Path parameters surfaced.** `GET /orders/{order_id}` exposes a path parameter named `order_id`
   marked required, so a consumer can construct the concrete URL. (Grounding requirement: the
   Generator must be able to see this without parsing the raw path string.)
10. **Request-body schema resolved.** For `POST /cart/items`, the operation's request body schema is
    resolved (intra-document `$ref` to `components.schemas.AddItem` followed) so the consumer can read
    its concrete fields (`product_id`, `quantity`) directly from the surface — not merely a dangling
    `$ref` string.
11. **Response schema resolved.** For `POST /checkout` (and/or `GET /orders/{order_id}`), the success
    response's schema resolves to the `Order` schema with its concrete fields reachable (e.g. the
    order `total` and line items), enabling schema-grounded API assertions.
12. **Security surfaced.** The surface exposes the document's `security_schemes` including
    `HTTPBasic` (its declared type), and each operation exposes its declared `security` requirement
    (the list from the operation or the document-level default; an empty list when the spec declares
    none for that operation). The Tester asserts **round-trip fidelity** to whatever the fixture
    declares — the loader must faithfully reflect the document, not invent or drop security.

### Determinism & serialization
13. **JSON-serializable, stable output.** The surface renders to a plain dict / JSON via a documented
    method (Interfaces §Serialization) using the pinned key names; serializing the **same** input
    twice yields **identical** output (stable operation ordering — e.g. sorted by `path` then
    `method` — and stable key ordering). No non-deterministic content (no timestamps, no object
    addresses).
14. **Round-trip equality across source kinds.** The serialized surface from the dict, file, string,
    and URL forms of the *same* document are **equal** (ties criterion 5 to the serialized form).

### Error behavior
15. **Non-OpenAPI / malformed input rejected.** A JSON object lacking the OpenAPI markers (e.g. no
    `openapi` version field and/or no `paths`), or syntactically invalid JSON, raises the module's
    **named** load error (Interfaces §Errors) — not a silent empty surface, not a bare `KeyError`.
16. **Unreachable source rejected.** A missing file path or an unreachable/failing URL raises the
    module's named load error (distinguishable message), rather than returning an empty/partial
    surface.
17. **Unsupported source documented.** A GraphQL/other unsupported source (or a source-kind the module
    cannot handle) raises a **named, documented** "not supported yet" error, confirming the deferral
    is explicit rather than a crash. (The normalized model + entry point remain shaped so a future
    GraphQL adapter can populate the same surface — verified structurally, e.g. the model does not
    hard-depend on OpenAPI-only fields for its core operation shape.)

### Placement, tests, no-regression
18. **Correct home + runnable tests.** All new code lives under `connectors/` (module + package init
    as needed) with the pinned public import path (Interfaces §Paths); tests live under
    `connectors/tests/` and pass via `uv run pytest connectors/tests -q`. The `connectors/.gitkeep`
    placeholder may be removed once real files exist.
19. **No regressions.** No change to `reference_app/**` behavior or to any protected file; existing
    Phase 0 suites (`make test`, `make eval`, backend pytest) and the clean app are unaffected. The
    loader performs **no writes** and **no network egress except** when explicitly given a URL source
    (criterion 3), and never logs/persists any credentials (it handles specs, not secrets).

## Interfaces / contracts (pin these precisely)

### Paths
- **Module home (binding):** `connectors/` — the loader is importable at a stable path, e.g.
  `connectors.spec_loader` (the exact module filename is the developer's choice, but the public
  import path must be documented in `connectors/README.md` and kept stable). Add package
  `__init__.py` files as needed so `connectors` is importable from the repo root under `uv`.
- **Tests:** `connectors/tests/` (pytest), runnable as `uv run pytest connectors/tests -q`.
- **Docs:** `connectors/README.md` (public API + surface shape + source kinds + error types +
  GraphQL-deferred note).

### Public API (shape — names/signatures are the developer's choice but must be documented & stable)
- A primary loader entry point that accepts a **source** (URL string, file path, raw string, or
  mapping) — with auto-detection — and returns the normalized **API surface** object. A source-type
  hint parameter is allowed (e.g. `source_type="auto"|"openapi"|...`) with `auto` as default.
- The GraphQL path (if a source is identified as GraphQL / unsupported) raises the documented
  "not supported yet" error (criterion 17).

### Model (normalized API surface — pinned field names for JSON/consumer contract)
The serialized surface (criterion 13) is an object with at least:
- `title` (string), `version` (string) — from `info`.
- `security_schemes` — mapping of scheme name → its declared definition (must include `HTTPBasic`
  for the reference fixture).
- `operations` — a **deterministically ordered** list; each operation object has:
  - `method` (upper-case string, e.g. `"GET"`, `"POST"`)
  - `path` (templated path string, e.g. `"/orders/{order_id}"`)
  - `operation_id` (string or null)
  - `summary` (string or null)
  - `parameters` — list of `{ name, in, required, schema }` (empty list when none)
  - `request_body` — object with the resolved schema (and content-type/required if declared) or null
  - `responses` — mapping of status-code string → `{ schema }` (resolved) where the spec declares
    content; may be empty for status codes without content
  - `security` — list of the operation's declared security requirements (empty list when none)

Resolved `schema` values (criteria 10–11) must expose the concrete field set of the referenced
`components.schemas` entry (inlined or otherwise directly readable), not a raw unresolved `$ref`
string. The in-memory object form may use dataclasses/typed objects; the **serialized** form uses the
key names above.

### Errors (named, documented)
- A single module-level base exception for load/parse failures (e.g. a `SpecLoadError`-style class;
  exact name the developer's choice, documented), used for: malformed/non-OpenAPI input (criterion
  15) and unreachable file/URL (criterion 16). Messages must distinguish the cases enough for a human
  to diagnose.
- A distinct named error (or a documented subclass/flag) for the **unsupported-source** case
  (criterion 17).

### Serialization
- A documented method to render the surface to a plain JSON-serializable dict (e.g. `.to_dict()` /
  `.to_json()`), deterministic per criterion 13. This is the contract the later agent-run glue and
  Generator consume.

### Fixtures (guidance for the Tester — not implementation)
- The reference app's `/openapi.json` is the canonical **real** fixture: capture it once (import
  `reference_app.backend.app:app` and call its OpenAPI generator, or GET `/openapi.json` on the clean
  running app) and assert the normalized surface against it (criteria 6–12). Additional small
  hand-crafted OpenAPI snippets and malformed/non-OpenAPI documents are appropriate for the
  error/`$ref`-resolution cases. URL loading (criterion 3) may use a local stub server or a mocked
  HTTP layer so no external network is required.

## Definition of Done
- All acceptance criteria **1–19** pass.
- The loader module (public import path documented + stable), the normalized-surface model with the
  pinned serialized key names, intra-document `$ref` resolution, deterministic JSON serialization, the
  named error types (including the GraphQL/unsupported-deferred path), the `connectors/tests/` suite,
  and `connectors/README.md` all exist under `connectors/`.
- `uv run pytest connectors/tests -q` is green from a clean checkout under `uv`.
- No protected file changed (`DESIGN.md`, `META_PLAN.md`, `AGILE_PLAN.md`, `CLAUDE.md`, `.harness/**`);
  no change to `reference_app/**` behavior; Phase 0 `make test` / `make eval` / backend pytest still
  pass. Consistent with `DESIGN.md §4/§5.1/§12/§13` and `AGILE_PLAN.md` D1.
- The Tester can, from this spec alone (paths, source kinds, the pinned normalized-surface key names +
  the reference fixture's operations/schemas/security, the determinism + serialization contract, and
  the named error behaviors), author the failing verification tests **without reading the
  implementation**.

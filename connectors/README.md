# connectors — API spec loader

`connectors/` holds the QA agent's **schema-grounding data sources**. The first
of these is the **OpenAPI spec loader**: it loads an OpenAPI (3.x) document and
normalizes it into a deterministic, JSON-serializable **API surface** that a
downstream Generator uses to ground API assertions in the schema
(`DESIGN.md §5.1`).

## Public API (stable)

```python
from connectors.spec_loader import (
    load_spec,               # entry point
    ApiSurface,              # normalized surface object (returned by load_spec)
    SpecLoadError,           # base load/parse error
    UnsupportedSourceError,  # deferred / unsupported source kind
)

surface = load_spec(source, source_type="auto")
data = surface.to_dict()     # plain, JSON-serializable dict
```

- **`load_spec(source, source_type="auto") -> ApiSurface`** — loads a spec and
  returns the normalized surface.
- **`ApiSurface.to_dict() -> dict`** — renders the surface to a plain,
  deterministic, JSON-serializable dict (see shape below).

### Accepted source kinds (auto-detected)

`source_type="auto"` (the default) detects the kind of `source`:

| Source | Detection |
|---|---|
| Parsed mapping / `dict` | `isinstance(source, Mapping)` |
| HTTP(S) URL | string starting with `http://` / `https://` |
| Raw JSON string | string whose first non-space char is `{` or `[` |
| Local file path | any other string that names an existing file (JSON) |

`bytes`/`bytearray` are decoded as UTF-8 and treated as strings. Equivalent
inputs across kinds (the same document as dict / file / string / URL) produce
**equal** normalized surfaces.

`source_type` may be forced to `"openapi"`. `"graphql"` (and other
recognized-but-unsupported kinds) raise `UnsupportedSourceError` — see below.

> YAML source support is **not** implemented. A YAML string is treated as a
> file path (and, if no such file exists, raises `SpecLoadError`); only JSON is
> parsed inline.

### Side-effect containment

- **No network egress** except when the source is explicitly an HTTP(S) URL.
- **No files are written** during a load.
- Nothing is logged or persisted. The loader handles specs, not credentials.

## Normalized surface shape (`to_dict()`)

```jsonc
{
  "title": "Reference Shop API",       // from info.title
  "version": "0.1.0",                  // from info.version
  "security_schemes": {                // verbatim from components.securitySchemes
    "HTTPBasic": { "type": "http", "scheme": "basic" }
  },
  "operations": [                      // sorted by (path, method) — deterministic
    {
      "method": "POST",                // upper-cased
      "path": "/cart/items",           // templated path preserved verbatim
      "operation_id": "add_to_cart_cart_items_post",  // or null
      "summary": "Add To Cart",        // or null
      "parameters": [                  // list; empty when none
        { "name": "order_id", "in": "path", "required": true, "schema": { ... } }
      ],
      "request_body": {                // object or null
        "schema": { "properties": { "product_id": {...}, "quantity": {...} }, ... },
        "content_type": "application/json",
        "required": true
      },
      "responses": {                   // mapping: status-code string -> { schema }
        "200": { "schema": { "properties": { "id": {...}, "items": {...}, "total": {...} } } }
      },
      "security": [ { "HTTPBasic": [] } ]  // operation's declared security, else
                                           // the document-level default, else []
    }
  ]
}
```

### Key guarantees

- **Deterministic:** operations are emitted sorted by `(path, method)`;
  serializing the same input twice yields byte-identical JSON (no timestamps,
  no object addresses).
- **`$ref` resolution:** intra-document `$ref`s (`#/components/...`) in request
  bodies, responses, and parameter schemas are resolved/inlined, so consumers
  read the concrete `properties` directly — a resolved object schema has **no
  top-level `$ref`**. External refs (other files/URLs) and cyclic refs are left
  untouched.
- **Security fidelity:** `security_schemes` reflects the document verbatim; each
  operation's `security` faithfully reflects the document (neither invented nor
  dropped).
- **Source-agnostic operation shape:** operations use only the generic keys
  above (`method`, `path`, `operation_id`, `summary`, `parameters`,
  `request_body`, `responses`, `security`) — no OpenAPI-only fields — so a
  future GraphQL adapter can populate the same surface model.

## Error types

| Error | Raised when |
|---|---|
| `SpecLoadError` | malformed / non-OpenAPI document (no `openapi`/`swagger` version or no `paths`), invalid JSON, missing file, or unreachable/failing URL. |
| `UnsupportedSourceError` | the source kind is recognized but not supported yet — chiefly `source_type="graphql"`. Subclasses `SpecLoadError`. |

## GraphQL — deferred

The normalized model and `load_spec` entry point are shaped to accommodate a
future GraphQL adapter (the operation shape is source-agnostic). The GraphQL
adapter itself is **out of scope** for this unit: `source_type="graphql"`
raises `UnsupportedSourceError` so the deferral is explicit rather than a crash.

---

# connectors — per-run target config

`connectors.target_config` is the **per-run input contract** an authoring run reads: the
target UI URL, the API-spec source (delegated to the spec loader above), the freeform BRD
path, a Basic-Auth credential **reference** (an env-var / vault-key *name*, never the secret
value — `DESIGN.md §11.4`), and the seven structured **Planner fields** (`DESIGN.md §6`). It
validates required fields, is **secret-safe**, and delegates spec parsing to
`connectors.spec_loader` (no duplication).

## Public API (stable)

```python
from connectors.target_config import (
    load_target_config,     # entry point
    TargetConfig,           # validated config object (returned by the loader)
    TargetConfigError,      # missing / malformed / invalid field
    CredentialUnsetError,   # referenced env var unset at resolve time (NOT a
                            # subclass of TargetConfigError)
)

cfg = load_target_config(source, source_type="auto")
data     = cfg.to_dict()            # plain, deterministic, secret-free dict
surface  = cfg.load_api_spec()      # -> connectors.spec_loader.ApiSurface (delegation)
secret   = cfg.resolve_credential() # reads the referenced env var at call time
```

- **`load_target_config(source, source_type="auto") -> TargetConfig`** — loads and
  validates a config from a **mapping** (already-parsed dict) or a **JSON file path**
  string. `source_type="auto"` (default) detects which. Raises `TargetConfigError` on any
  missing/empty/wrong-typed field or on an unreadable / non-JSON file; the message names
  the offending field.
- **`TargetConfig.to_dict() -> dict`** — renders to a plain, deterministic, **secret-free**
  dict using the pinned key names and stable ordering (same input → identical output;
  file == equivalent mapping).
- **`TargetConfig.load_api_spec()`** — delegates the `api_spec_source` to
  `connectors.spec_loader.load_spec(...)` and returns its `ApiSurface`. This unit performs
  **no** independent spec parsing; the loader's `SpecLoadError` / `UnsupportedSourceError`
  propagate **unchanged** (never rewrapped into `TargetConfigError`).
- **`TargetConfig.resolve_credential() -> str`** — reads the env var named by
  `basic_auth_credential_ref` **at call time**, returns its value **to the caller only**
  (never stored back on the object, never logged), and raises `CredentialUnsetError` when
  the variable is unset.
- **`repr(cfg)` / `str(cfg)`** — secret-free; expose the credential **reference name** only.

## Config schema (pinned key names)

| Key | Type | Meaning |
|---|---|---|
| `target_url` | string | running target **UI** URL (must be `http(s)://…`) |
| `api_spec_source` | string \| mapping | a `source` accepted by `connectors.spec_loader.load_spec` (stored as given, not parsed here) |
| `brd_path` | string | filesystem path to the freeform BRD document |
| `basic_auth_credential_ref` | string | the **name** of the env var / vault key holding the Basic-Auth credential — a **reference**, never the secret. No raw username/password field exists. |
| `planner_fields` | mapping | the **seven** Planner fields below (exactly — no more, no fewer) |

### The seven Planner fields (`DESIGN.md §6`)

| Key | `DESIGN.md §6` field | Rule |
|---|---|---|
| `target_scope` | Target scope (feature/flow) | non-empty free text |
| `intent` | Intent / goal | non-empty free text |
| `expected_behavior` | Expected behavior / acceptance criteria | non-empty free text |
| `priority_risk` | Priority / risk areas | non-empty free text |
| `test_data_preconditions` | Test data / preconditions | non-empty free text |
| `out_of_scope_constraints` | Out-of-scope / constraints | non-empty free text |
| `depth` | Depth | enumerated: `smoke` \| `regression` \| `exhaustive` |

Each of the seven is **required** and non-empty; `depth` must be one of the enumerated
values (case-sensitive, no surrounding whitespace) or the loader raises `TargetConfigError`.

## Secret-safety contract (`DESIGN.md §11.4`)

- The object stores the credential **reference name** only — there is **no** field for a
  username/password value; any inlined secret keys in the source are ignored (not retained).
- A resolved secret is **never** stored on the object and **never** appears in `to_dict()`,
  `repr()`, `str()`, or logs. Resolution happens **only** when `resolve_credential()` is
  called, and the value is returned to the caller without being cached.
- `resolve_credential()` raises `CredentialUnsetError` (distinct from `TargetConfigError`)
  when the referenced env var is unset.

## Error types

| Error | Raised when |
|---|---|
| `TargetConfigError` | a required field is missing/empty/wrong-typed/malformed (message names the field), `depth` is out of set, or the config file is unreadable / not valid JSON. |
| `CredentialUnsetError` | the env var named by `basic_auth_credential_ref` is unset at `resolve_credential()` time. **Not** a subclass of `TargetConfigError`. |
| `SpecLoadError` / `UnsupportedSourceError` | propagated **unchanged** from the spec-loader hand-off (`load_api_spec()`). |

## Example config

`connectors/examples/reference_app.target.json` is the canonical, secret-free example wired
to the clean reference app (`target_url` `http://127.0.0.1:5173`, `api_spec_source`
`http://127.0.0.1:8000/openapi.json`, `brd_path` `reference_app/BRD.md`,
`basic_auth_credential_ref` `REF_APP_BASIC_AUTH`, and all seven Planner fields populated with
`depth` in the enum). It loads and validates cleanly and contains no credential value.

---

# connectors — Playwright-MCP config

`connectors/mcp/playwright.mcp.json` is the **Playwright MCP server configuration** the
authoring agent uses to drive a browser and obtain **grounded DOM snapshots** — the
role/label/test-id locators that the reliability layer requires be read from the live DOM,
never invented (`DESIGN.md §4/§5.1`). It is a **static config artifact only**: this unit does
**not** launch the server, spawn a browser, run `npx`, or reach the network.

## File path & shape

- **Path (binding):** `connectors/mcp/playwright.mcp.json`
- **Format:** the Claude Code MCP-server config form — a JSON object with a top-level
  **`mcpServers`** map. The server key is exactly **`playwright`**, and its value is the
  standard stdio launch definition (`command` + `args`).

```jsonc
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": [
        "-y",
        "@playwright/mcp@0.0.41",   // pinned package + EXACT version (§11.10)
        "--headless",               // deterministic, snapshot-oriented runs
        "--browser", "chromium"     // concrete engine — unambiguous DOM-snapshot channel
      ]
    }
  }
}
```

## Pinned server + exact version (`DESIGN.md §11.10`)

- **Package:** the official Playwright MCP server, npm **`@playwright/mcp`**.
- **Version:** pinned to an **exact** `@playwright/mcp@0.0.41` (`major.minor.patch`). This is
  a supply-chain integrity requirement: the reference **never** uses a floating specifier
  (`latest`, `@next`, `^`, `~`, `*`, `>=`, ranges, an `x` wildcard, or a bare unversioned
  name). The specific number may be updated to the release the team has verified/mirrored,
  but it must remain an exact pin.

## Browser / DOM-snapshot options

- **`--headless`** — the browser runs headless so runs are deterministic and oriented to DOM
  snapshots rather than interactive display.
- **`--browser chromium`** — a concrete browser engine, so the grounded-DOM-snapshot channel
  is unambiguous.

## How later units consume it

- **Unit 5** (`p1-subagents-planner-generator`) and **unit 6** (`p1-agent-run-glue`) point
  Claude Code at this file / the stable `playwright` server key to obtain the MCP browser
  channel. The stable fields they rely on — the server key `playwright`, the `command`/`args`
  launch, and this file path — are fixed here so a consumer can reference them without editing
  the file.

## Target-agnostic & secret-safe (`DESIGN.md §11.4`)

- This file wires the Playwright MCP **server**, not any specific target. It bakes in **no**
  target UI/API URL, port, or credential value — the per-run target URL and credential
  *reference* live in the unit-2 per-run target config (`connectors.target_config`).

## Runtime prerequisite (documentation only — not tested live)

- Launching this server (unit 6/7, not here) requires **Node/`npx`** available in the run
  environment so `npx @playwright/mcp@0.0.41` can start. This unit performs no launch/install;
  Node availability is a documented runtime prerequisite for later units, validated live in
  unit 7, not by this unit's static tests.

---

## Tests

```
uv run pytest connectors/tests -q
```

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

## Tests

```
uv run pytest connectors/tests -q
```

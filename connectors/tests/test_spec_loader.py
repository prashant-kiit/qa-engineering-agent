# Acceptance suite for p1-connectors-spec-loader (TDD red).
#
# Encodes acceptance criteria 1-19 from .harness/tasks/p1-connectors-spec-loader.md against
# the reference app's real OpenAPI document plus small hand-crafted malformed documents.
#
# The loader implementation does not exist yet. Every test consumes the `spec_loader`
# fixture (conftest.py), which imports `connectors.spec_loader`; that import raises
# ModuleNotFoundError until the developer implements the module -> the whole suite is
# legitimately red for the RIGHT reason (missing implementation), not broken scaffolding.
#
# NAMING ASSUMPTIONS the developer must honor (documented in the coverage note):
#   - public module:        connectors.spec_loader
#   - loader entry point:   load_spec(source, source_type="auto") -> surface object
#   - serialization method: surface.to_dict() -> plain JSON-serializable dict
#   - base load error:      spec_loader.SpecLoadError
#   - unsupported error:    spec_loader.UnsupportedSourceError  (may subclass SpecLoadError)
#   - request_body nests its resolved schema under key "schema" (mirrors responses' {schema})
#   - source_type="graphql" selects the deferred/unsupported GraphQL path (criterion 17)
#   - operations serialize sorted by (path, method) (the spec's stated canonical ordering)

import json

import pytest

# ---- reference fixture expectations (from the clean app's OpenAPI document) -------------

EXPECTED_OPERATION_KEYS = {
    ("GET", "/products"),
    ("GET", "/cart"),
    ("POST", "/cart/items"),
    ("POST", "/checkout"),
    ("GET", "/orders/{order_id}"),
}

# Pinned per-operation serialized keys (criterion 8 / Model). request_body/operation_id/
# summary MAY be null but the key is present.
OPERATION_KEYS = {
    "method",
    "path",
    "operation_id",
    "summary",
    "parameters",
    "request_body",
    "responses",
    "security",
}


# ---- helpers ----------------------------------------------------------------------------


def ops_by_key(surface_dict):
    """Map (method, path) -> operation dict from a serialized surface."""
    return {(op["method"], op["path"]): op for op in surface_dict["operations"]}


def property_names(schema):
    """Concrete field names declared directly on a resolved (de-$ref'd) object schema."""
    assert isinstance(schema, dict), f"schema should be a mapping, got {type(schema)!r}"
    return set(schema.get("properties", {}).keys())


def as_surface_dict(surface):
    """Serialize a surface object via its documented to_dict() method (criterion 13)."""
    assert hasattr(surface, "to_dict"), (
        "the surface object must expose a to_dict() serialization method (Interfaces "
        "§Serialization)"
    )
    return surface.to_dict()


# ========================================================================================
# Loading from multiple source kinds (criteria 1-5)
# ========================================================================================


def test_load_from_in_memory_dict(spec_loader, openapi_doc):
    """Criterion 1: an already-parsed OpenAPI mapping loads without error."""
    surface = spec_loader.load_spec(openapi_doc)
    assert surface is not None
    data = as_surface_dict(surface)
    assert isinstance(data, dict)
    assert data["operations"], "surface should enumerate operations for a valid document"


def test_load_from_local_file_matches_dict(spec_loader, openapi_doc, openapi_file):
    """Criterion 2: a JSON file path parses to the same surface as the equivalent dict."""
    from_file = as_surface_dict(spec_loader.load_spec(openapi_file))
    from_dict = as_surface_dict(spec_loader.load_spec(openapi_doc))
    assert from_file == from_dict


def test_load_from_http_url_matches_dict(spec_loader, openapi_doc, openapi_url):
    """Criterion 3: an HTTP URL serving the doc parses to the equivalent surface."""
    from_url = as_surface_dict(spec_loader.load_spec(openapi_url))
    from_dict = as_surface_dict(spec_loader.load_spec(openapi_doc))
    assert from_url == from_dict


def test_load_from_raw_json_string_matches_dict(spec_loader, openapi_doc, openapi_json_str):
    """Criterion 4: a raw JSON string yields the equivalent surface."""
    from_str = as_surface_dict(spec_loader.load_spec(openapi_json_str))
    from_dict = as_surface_dict(spec_loader.load_spec(openapi_doc))
    assert from_str == from_dict


def test_source_kind_autodetection_equivalent(
    spec_loader, openapi_doc, openapi_file, openapi_json_str, openapi_url
):
    """Criterion 5: one auto-detecting entry point accepts every kind and equivalent
    inputs across dict/file/string/URL produce EQUAL normalized surfaces."""
    surfaces = [
        as_surface_dict(spec_loader.load_spec(openapi_doc)),
        as_surface_dict(spec_loader.load_spec(openapi_file)),
        as_surface_dict(spec_loader.load_spec(openapi_json_str)),
        as_surface_dict(spec_loader.load_spec(openapi_url)),
    ]
    first = surfaces[0]
    for other in surfaces[1:]:
        assert other == first


# ========================================================================================
# Normalized API surface — shape and content (criteria 6-12)
# ========================================================================================


def test_document_metadata(spec_loader, openapi_doc):
    """Criterion 6: title and version come from the OpenAPI info object."""
    data = as_surface_dict(spec_loader.load_spec(openapi_doc))
    assert data["title"] == openapi_doc["info"]["title"]
    assert data["version"] == openapi_doc["info"]["version"]


def test_operations_enumerated_exactly(spec_loader, openapi_doc):
    """Criterion 7: exactly the fixture's (method, path) pairs, no phantom ops; method
    upper-cased; templated path preserved."""
    data = as_surface_dict(spec_loader.load_spec(openapi_doc))
    keys = set(ops_by_key(data).keys())
    assert keys == EXPECTED_OPERATION_KEYS
    for op in data["operations"]:
        assert op["method"] == op["method"].upper()
    assert ("GET", "/orders/{order_id}") in keys  # templated path preserved verbatim


def test_per_operation_fields_present(spec_loader, openapi_doc):
    """Criterion 8: each operation exposes the pinned field names (nullable ones present
    as keys); parameters is a list, responses a mapping, security a list."""
    data = as_surface_dict(spec_loader.load_spec(openapi_doc))
    for op in data["operations"]:
        assert OPERATION_KEYS.issubset(set(op.keys())), (
            f"operation {op.get('method')} {op.get('path')} missing pinned keys: "
            f"{OPERATION_KEYS - set(op.keys())}"
        )
        assert isinstance(op["parameters"], list)
        assert isinstance(op["responses"], dict)
        assert isinstance(op["security"], list)


def test_path_parameter_surfaced(spec_loader, openapi_doc):
    """Criterion 9: GET /orders/{order_id} exposes a required path param named order_id."""
    data = as_surface_dict(spec_loader.load_spec(openapi_doc))
    op = ops_by_key(data)[("GET", "/orders/{order_id}")]
    params = {p["name"]: p for p in op["parameters"]}
    assert "order_id" in params, "order_id path parameter must be surfaced"
    order_id = params["order_id"]
    assert order_id["in"] == "path"
    assert order_id["required"] is True


def test_request_body_schema_resolved(spec_loader, openapi_doc):
    """Criterion 10: POST /cart/items request body $ref -> AddItem is resolved so the
    concrete fields product_id + quantity are directly readable (no dangling $ref)."""
    data = as_surface_dict(spec_loader.load_spec(openapi_doc))
    op = ops_by_key(data)[("POST", "/cart/items")]
    assert op["request_body"] is not None, "POST /cart/items declares a request body"
    schema = op["request_body"]["schema"]
    assert "$ref" not in schema, "request body schema must be resolved, not a raw $ref"
    assert {"product_id", "quantity"}.issubset(property_names(schema))


def test_response_schema_resolved_to_order(spec_loader, openapi_doc):
    """Criterion 11: POST /checkout success response resolves to the Order schema with its
    concrete fields (total, items, id) reachable — enabling schema-grounded assertions."""
    data = as_surface_dict(spec_loader.load_spec(openapi_doc))
    op = ops_by_key(data)[("POST", "/checkout")]
    assert "200" in op["responses"], "checkout must expose its 200 response"
    schema = op["responses"]["200"]["schema"]
    assert "$ref" not in schema, "response schema must be resolved, not a raw $ref"
    fields = property_names(schema)
    assert {"id", "items", "total"}.issubset(fields)


def test_security_schemes_and_per_operation_security(spec_loader, openapi_doc):
    """Criterion 12: security_schemes reflects the document (HTTPBasic, http type) and each
    operation faithfully reflects its declared security requirement (round-trip fidelity)."""
    data = as_surface_dict(spec_loader.load_spec(openapi_doc))
    declared_schemes = openapi_doc["components"]["securitySchemes"]

    assert "HTTPBasic" in data["security_schemes"]
    assert data["security_schemes"]["HTTPBasic"]["type"] == "http"
    # Faithful reflection: neither invent nor drop what the document declares.
    assert data["security_schemes"] == declared_schemes

    for op in data["operations"]:
        declared = openapi_doc["paths"][op["path"]][op["method"].lower()].get("security", [])
        assert op["security"] == declared


# ========================================================================================
# Determinism & serialization (criteria 13-14)
# ========================================================================================


def test_serialization_is_json_serializable_and_stable(spec_loader, openapi_doc):
    """Criterion 13: to_dict() is JSON-serializable and serializing the SAME input twice
    yields byte-identical output (no non-deterministic content)."""
    first = as_surface_dict(spec_loader.load_spec(openapi_doc))
    second = as_surface_dict(spec_loader.load_spec(openapi_doc))
    dumped_first = json.dumps(first)  # must not raise -> JSON-serializable
    dumped_second = json.dumps(second)
    assert dumped_first == dumped_second


def test_operations_deterministically_ordered(spec_loader, openapi_doc):
    """Criterion 13: operations are emitted in the spec's canonical order — sorted by
    (path, method) — so ordering is stable and independent of input dict ordering."""
    data = as_surface_dict(spec_loader.load_spec(openapi_doc))
    keys = [(op["path"], op["method"]) for op in data["operations"]]
    assert keys == sorted(keys)


def test_round_trip_equality_across_source_kinds(
    spec_loader, openapi_doc, openapi_file, openapi_json_str, openapi_url
):
    """Criterion 14: the serialized surface is equal across dict/file/string/URL forms of
    the same document."""
    dict_form = as_surface_dict(spec_loader.load_spec(openapi_doc))
    assert as_surface_dict(spec_loader.load_spec(openapi_file)) == dict_form
    assert as_surface_dict(spec_loader.load_spec(openapi_json_str)) == dict_form
    assert as_surface_dict(spec_loader.load_spec(openapi_url)) == dict_form


# ========================================================================================
# Error behavior (criteria 15-17)
# ========================================================================================


def test_non_openapi_object_rejected(spec_loader):
    """Criterion 15: a JSON object lacking OpenAPI markers raises the named load error
    (not a silent empty surface, not a bare KeyError)."""
    not_openapi = {"hello": "world", "foo": [1, 2, 3]}
    with pytest.raises(spec_loader.SpecLoadError):
        spec_loader.load_spec(not_openapi)


def test_malformed_json_string_rejected(spec_loader):
    """Criterion 15: syntactically invalid JSON raises the named load error."""
    with pytest.raises(spec_loader.SpecLoadError):
        spec_loader.load_spec('{"openapi": "3.1.0", "paths": {')  # truncated / invalid JSON


def test_missing_file_rejected(spec_loader, tmp_path):
    """Criterion 16: a missing file path raises the named load error."""
    missing = str(tmp_path / "does-not-exist.json")
    with pytest.raises(spec_loader.SpecLoadError):
        spec_loader.load_spec(missing)


def test_unreachable_url_rejected(spec_loader, unreachable_url):
    """Criterion 16: an unreachable/failing URL raises the named load error."""
    with pytest.raises(spec_loader.SpecLoadError):
        spec_loader.load_spec(unreachable_url)


def test_unsupported_graphql_source_rejected(spec_loader):
    """Criterion 17: a GraphQL / unsupported source raises the named 'not supported yet'
    error, confirming the deferral is explicit rather than a crash."""
    graphql_sdl = "type Query { products: [Product!]! }\ntype Product { id: ID! }"
    with pytest.raises(spec_loader.UnsupportedSourceError):
        spec_loader.load_spec(graphql_sdl, source_type="graphql")


def test_operation_shape_is_source_agnostic(spec_loader, openapi_doc):
    """Criterion 17 (structural): the normalized operation shape uses only generic keys
    (method/path/parameters/request_body/responses/security/...), not OpenAPI-only fields,
    so a future GraphQL adapter can populate the same surface model."""
    data = as_surface_dict(spec_loader.load_spec(openapi_doc))
    for op in data["operations"]:
        extra = set(op.keys()) - OPERATION_KEYS
        assert not extra, f"operation shape leaks non-generic keys: {extra}"


# ========================================================================================
# Placement, no-regression / side-effect containment (criteria 18-19)
# ========================================================================================


def test_public_import_path_exposes_api(spec_loader):
    """Criterion 18: the loader is importable at the stable public path and exposes the
    documented entry point + named errors."""
    assert hasattr(spec_loader, "load_spec")
    assert callable(spec_loader.load_spec)
    assert isinstance(spec_loader.SpecLoadError, type)
    assert issubclass(spec_loader.SpecLoadError, Exception)
    assert isinstance(spec_loader.UnsupportedSourceError, type)
    assert issubclass(spec_loader.UnsupportedSourceError, Exception)


def test_no_network_egress_for_non_url_sources(spec_loader, openapi_doc, openapi_file,
                                               openapi_json_str, monkeypatch):
    """Criterion 19: dict/file/string sources perform NO network egress — they load fine
    even with socket creation disabled (only an explicit URL source may touch the network)."""
    import socket as socket_module

    def _no_sockets(*args, **kwargs):
        raise AssertionError("non-URL source must not open a network socket")

    monkeypatch.setattr(socket_module, "socket", _no_sockets)

    assert spec_loader.load_spec(openapi_doc) is not None
    assert spec_loader.load_spec(openapi_file) is not None
    assert spec_loader.load_spec(openapi_json_str) is not None


def test_no_file_writes_on_load(spec_loader, openapi_doc, tmp_path, monkeypatch):
    """Criterion 19: loading a spec performs no writes to the working directory."""
    monkeypatch.chdir(tmp_path)
    before = set(p.name for p in tmp_path.iterdir())
    spec_loader.load_spec(openapi_doc)
    after = set(p.name for p in tmp_path.iterdir())
    assert after == before, f"loader wrote unexpected files: {after - before}"

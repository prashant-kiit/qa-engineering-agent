"""OpenAPI spec loader → normalized, deterministic API surface.

Loads an OpenAPI (3.x) document from any of several source kinds — an already
parsed mapping, a local file path, an HTTP(S) URL, or a raw JSON string — and
produces a normalized :class:`ApiSurface`. The surface exposes per-operation
method / path / parameters / request body / responses / security with
intra-document ``$ref`` resolution, plus the document's security schemes, and
serializes to a plain, deterministic, JSON-serializable dict via ``to_dict()``.

The public contract (import path, entry point, serialized key names, error
types) is documented in ``connectors/README.md``.

Design notes
------------
* No network egress occurs except when the source is explicitly an HTTP(S) URL.
* No files are written; nothing is logged or persisted. The loader handles API
  specifications, not secrets.
* The operation model uses only source-agnostic keys so a future GraphQL adapter
  can populate the same surface shape (GraphQL itself is deferred and raises
  :class:`UnsupportedSourceError`).
"""

from __future__ import annotations

import copy
import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional


# --------------------------------------------------------------------------- #
# Errors
# --------------------------------------------------------------------------- #


class SpecLoadError(Exception):
    """Raised when a spec cannot be loaded, parsed, or recognized.

    Covers malformed / non-OpenAPI documents and unreachable file/URL sources.
    """


class UnsupportedSourceError(SpecLoadError):
    """Raised when the source kind is recognized but not supported yet.

    The canonical deferred case is GraphQL (``source_type="graphql"``). It
    subclasses :class:`SpecLoadError` so broad ``except SpecLoadError`` handlers
    still catch it, while callers can distinguish the deferral explicitly.
    """


# --------------------------------------------------------------------------- #
# Normalized surface model
# --------------------------------------------------------------------------- #


@dataclass
class Operation:
    """A single normalized API operation (source-agnostic shape)."""

    method: str
    path: str
    operation_id: Optional[str] = None
    summary: Optional[str] = None
    parameters: list = field(default_factory=list)
    request_body: Optional[dict] = None
    responses: dict = field(default_factory=dict)
    security: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "method": self.method,
            "path": self.path,
            "operation_id": self.operation_id,
            "summary": self.summary,
            "parameters": copy.deepcopy(self.parameters),
            "request_body": copy.deepcopy(self.request_body),
            "responses": copy.deepcopy(self.responses),
            "security": copy.deepcopy(self.security),
        }


@dataclass
class ApiSurface:
    """A normalized, JSON-serializable view over an API document."""

    title: str
    version: str
    operations: list = field(default_factory=list)
    security_schemes: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Render the surface to a plain, deterministic dict.

        Operations are emitted sorted by ``(path, method)`` so the same input
        always yields byte-identical JSON regardless of input dict ordering.
        """
        ordered = sorted(self.operations, key=lambda op: (op.path, op.method))
        return {
            "title": self.title,
            "version": self.version,
            "security_schemes": copy.deepcopy(self.security_schemes),
            "operations": [op.to_dict() for op in ordered],
        }


# --------------------------------------------------------------------------- #
# $ref resolution (intra-document only)
# --------------------------------------------------------------------------- #


def _resolve_pointer(doc: Mapping, ref: str) -> Any:
    """Resolve a local JSON pointer like ``#/components/schemas/Order``."""
    parts = ref.lstrip("#/").split("/")
    node: Any = doc
    for part in parts:
        # JSON-pointer unescaping (~1 -> /, ~0 -> ~)
        part = part.replace("~1", "/").replace("~0", "~")
        if isinstance(node, Mapping) and part in node:
            node = node[part]
        else:
            raise KeyError(ref)
    return node


def _resolve_refs(node: Any, doc: Mapping, seen: frozenset) -> Any:
    """Recursively inline intra-document ``$ref``s.

    External refs (not starting with ``#/``) and refs that would create a cycle
    are left untouched to keep resolution total and terminating.
    """
    if isinstance(node, Mapping):
        ref = node.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/"):
            if ref in seen:
                # Break the cycle: leave the reference as-is.
                return {"$ref": ref}
            try:
                target = _resolve_pointer(doc, ref)
            except KeyError:
                return {"$ref": ref}
            return _resolve_refs(target, doc, seen | {ref})
        return {k: _resolve_refs(v, doc, seen) for k, v in node.items()}
    if isinstance(node, list):
        return [_resolve_refs(item, doc, seen) for item in node]
    return node


def _resolve(node: Any, doc: Mapping) -> Any:
    return _resolve_refs(copy.deepcopy(node), doc, frozenset())


# --------------------------------------------------------------------------- #
# Source loading / detection
# --------------------------------------------------------------------------- #

_HTTP_TABLE = ("http://", "https://")


def _looks_like_json(text: str) -> bool:
    stripped = text.lstrip()
    return stripped[:1] in ("{", "[")


def _load_from_url(url: str) -> Any:
    try:
        with urllib.request.urlopen(url) as resp:  # noqa: S310 (explicit URL source)
            raw = resp.read()
    except (urllib.error.URLError, OSError) as exc:
        raise SpecLoadError(f"could not fetch spec from URL {url!r}: {exc}") from exc
    try:
        return json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise SpecLoadError(
            f"URL {url!r} did not return valid JSON: {exc}"
        ) from exc


def _load_from_file(path: str) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        raise SpecLoadError(f"could not read spec file {path!r}: {exc}") from exc
    try:
        return json.loads(text)
    except ValueError as exc:
        raise SpecLoadError(
            f"spec file {path!r} is not valid JSON: {exc}"
        ) from exc


def _load_from_json_string(text: str) -> Any:
    try:
        return json.loads(text)
    except ValueError as exc:
        raise SpecLoadError(f"source string is not valid JSON: {exc}") from exc


def _load_document(source: Any) -> Any:
    """Auto-detect the source kind and return the parsed document object."""
    if isinstance(source, Mapping):
        return source
    if isinstance(source, (bytes, bytearray)):
        source = source.decode("utf-8")
    if isinstance(source, str):
        candidate = source.strip()
        if candidate[:8].lower().startswith(_HTTP_TABLE):
            return _load_from_url(candidate)
        if _looks_like_json(candidate):
            return _load_from_json_string(candidate)
        # Otherwise treat it as a filesystem path.
        if os.path.exists(candidate):
            return _load_from_file(candidate)
        raise SpecLoadError(
            f"source {source!r} is not a mapping, URL, JSON string, or existing file path"
        )
    raise SpecLoadError(f"unsupported source object of type {type(source).__name__!r}")


# --------------------------------------------------------------------------- #
# Normalization
# --------------------------------------------------------------------------- #

_METHODS = ("get", "put", "post", "delete", "options", "head", "patch", "trace")


def _validate_openapi(doc: Any) -> None:
    if not isinstance(doc, Mapping):
        raise SpecLoadError("document is not a JSON object / mapping")
    if "openapi" not in doc and "swagger" not in doc:
        raise SpecLoadError(
            "document is not an OpenAPI spec: missing 'openapi' (or 'swagger') version field"
        )
    if "paths" not in doc or not isinstance(doc["paths"], Mapping):
        raise SpecLoadError("document is not an OpenAPI spec: missing 'paths' object")


def _select_content_schema(content: Mapping, doc: Mapping) -> Optional[dict]:
    """Pick a content schema deterministically (prefer application/json)."""
    if not isinstance(content, Mapping) or not content:
        return None
    if "application/json" in content:
        chosen = content["application/json"]
    else:
        chosen = content[sorted(content.keys())[0]]
    schema = chosen.get("schema") if isinstance(chosen, Mapping) else None
    if schema is None:
        return None
    return _resolve(schema, doc)


def _normalize_parameters(raw_params: list, doc: Mapping) -> list:
    params = []
    for raw in raw_params:
        resolved = _resolve(raw, doc) if isinstance(raw, Mapping) else raw
        if not isinstance(resolved, Mapping):
            continue
        params.append(
            {
                "name": resolved.get("name"),
                "in": resolved.get("in"),
                "required": bool(resolved.get("required", False)),
                "schema": _resolve(resolved.get("schema", {}), doc),
            }
        )
    return params


def _normalize_request_body(raw_body: Any, doc: Mapping) -> Optional[dict]:
    if not isinstance(raw_body, Mapping):
        return None
    content = raw_body.get("content", {})
    schema = _select_content_schema(content, doc)
    content_type = None
    if isinstance(content, Mapping) and content:
        content_type = (
            "application/json"
            if "application/json" in content
            else sorted(content.keys())[0]
        )
    return {
        "schema": schema,
        "content_type": content_type,
        "required": bool(raw_body.get("required", False)),
    }


def _normalize_responses(raw_responses: Any, doc: Mapping) -> dict:
    responses: dict = {}
    if not isinstance(raw_responses, Mapping):
        return responses
    for code in sorted(raw_responses.keys(), key=str):
        resp = raw_responses[code]
        if not isinstance(resp, Mapping):
            responses[str(code)] = {"schema": None}
            continue
        schema = _select_content_schema(resp.get("content", {}), doc)
        responses[str(code)] = {"schema": schema}
    return responses


def _normalize(doc: Mapping) -> ApiSurface:
    info = doc.get("info", {}) if isinstance(doc.get("info"), Mapping) else {}
    doc_security = doc.get("security")
    components = doc.get("components", {})
    security_schemes = {}
    if isinstance(components, Mapping):
        security_schemes = copy.deepcopy(components.get("securitySchemes", {}) or {})

    operations: list = []
    paths = doc.get("paths", {})
    for path, path_item in paths.items():
        if not isinstance(path_item, Mapping):
            continue
        shared_params = path_item.get("parameters", []) or []
        for method in _METHODS:
            op = path_item.get(method)
            if not isinstance(op, Mapping):
                continue
            raw_params = list(shared_params) + list(op.get("parameters", []) or [])
            if "security" in op:
                security = copy.deepcopy(op.get("security") or [])
            elif isinstance(doc_security, list):
                security = copy.deepcopy(doc_security)
            else:
                security = []
            operations.append(
                Operation(
                    method=method.upper(),
                    path=path,
                    operation_id=op.get("operationId"),
                    summary=op.get("summary"),
                    parameters=_normalize_parameters(raw_params, doc),
                    request_body=_normalize_request_body(op.get("requestBody"), doc),
                    responses=_normalize_responses(op.get("responses"), doc),
                    security=security,
                )
            )

    return ApiSurface(
        title=info.get("title", ""),
        version=info.get("version", ""),
        operations=operations,
        security_schemes=security_schemes,
    )


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #


def load_spec(source: Any, source_type: str = "auto") -> ApiSurface:
    """Load an API spec from ``source`` and return a normalized :class:`ApiSurface`.

    Parameters
    ----------
    source:
        A parsed mapping/dict, a local file path, an HTTP(S) URL, or a raw JSON
        string. When ``source_type="auto"`` (the default) the kind is detected
        automatically.
    source_type:
        ``"auto"`` (default) or ``"openapi"`` to force OpenAPI handling.
        ``"graphql"`` (and any other recognized-but-unsupported kind) raises
        :class:`UnsupportedSourceError` — GraphQL support is deferred.

    Raises
    ------
    UnsupportedSourceError:
        The source kind is recognized but not supported yet (e.g. GraphQL).
    SpecLoadError:
        The source is unreachable, unreadable, malformed, or not an OpenAPI
        document.
    """
    normalized_type = (source_type or "auto").lower()
    if normalized_type in ("graphql", "graphql-sdl", "graphql-introspection"):
        raise UnsupportedSourceError(
            "GraphQL sources are not supported yet (deferred); the loader currently "
            "handles OpenAPI documents only."
        )
    if normalized_type not in ("auto", "openapi"):
        raise UnsupportedSourceError(
            f"unsupported source_type {source_type!r}; expected 'auto' or 'openapi'"
        )

    doc = _load_document(source)
    _validate_openapi(doc)
    return _normalize(doc)

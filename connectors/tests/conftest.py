# Shared fixtures for the p1-connectors-spec-loader acceptance suite (TDD red).
#
# The Tester encodes the spec (.harness/tasks/p1-connectors-spec-loader.md) WITHOUT
# reading the loader implementation. The loader does not exist yet, so every test that
# depends on the `spec_loader` fixture errors at import time — the legitimate TDD-red reason.
#
# Canonical REAL fixture: the clean reference backend's own OpenAPI document, captured by
# importing `reference_app.backend.app:app` and calling its OpenAPI generator. The clean app
# is never modified. URL loading uses a local in-thread stub HTTP server so no external
# network is required.

import importlib
import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest


@pytest.fixture(scope="session")
def openapi_doc():
    """The reference app's real OpenAPI 3.1 document as a plain JSON-round-tripped dict.

    Captured from the clean app's OpenAPI generator; not mutated. Round-tripping through
    json guarantees a plain, order-stable dict independent of pydantic/model objects.
    """
    from reference_app.backend.app import app  # binding ASGI import path (Phase 0)

    return json.loads(json.dumps(app.openapi()))


@pytest.fixture
def spec_loader():
    """Import the loader at its stable public path.

    NAMING ASSUMPTION (see p1-connectors-spec-loader.tests.md): the public module is
    `connectors.spec_loader`. Until the developer creates it this import raises
    ModuleNotFoundError, which is the expected red failure for the whole suite.
    """
    return importlib.import_module("connectors.spec_loader")


@pytest.fixture
def openapi_json_str(openapi_doc):
    """The same document serialized as a raw JSON string (criterion 4)."""
    return json.dumps(openapi_doc)


@pytest.fixture
def openapi_file(openapi_doc, tmp_path):
    """A local filesystem path to a JSON file holding the document (criterion 2)."""
    path = tmp_path / "openapi.json"
    path.write_text(json.dumps(openapi_doc), encoding="utf-8")
    return str(path)


@pytest.fixture
def openapi_url(openapi_doc):
    """A local stub HTTP server serving the document at /openapi.json (criterion 3).

    Binds to an ephemeral loopback port; no external network is used. Torn down after the
    test.
    """
    body = json.dumps(openapi_doc).encode("utf-8")

    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802 (stdlib naming)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):  # silence the stub server
            pass

    server = HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        yield f"http://{host}:{port}/openapi.json"
    finally:
        server.shutdown()
        server.server_close()


@pytest.fixture
def unreachable_url():
    """A loopback URL whose port is closed, so any fetch is refused (criterion 16)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()  # port now free -> connection should be refused
    return f"http://127.0.0.1:{port}/openapi.json"

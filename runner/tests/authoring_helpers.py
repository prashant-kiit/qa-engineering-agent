"""Shared test helpers for the p1-agent-run-glue acceptance suite.

Lives in a **uniquely-named** module (not `conftest`) so that importing these symbols
(`from authoring_helpers import ...`) is unambiguous even when the whole repo test suite is
collected together — two bare `conftest` modules (runner/tests + connectors/tests) collide
under pytest's prepend importmode, so shared constants + the mock runners must NOT be imported
via `from conftest import ...`.

Everything here is offline: the API surface loads from an in-memory OpenAPI dict (no network),
and the agent runner is a MOCK that never launches Claude Code / Playwright MCP / a browser.
"""

from __future__ import annotations

import json
from pathlib import Path

# Repo root: runner/tests/authoring_helpers.py -> parents[2] == repo root.
REPO_ROOT = Path(__file__).resolve().parents[2]

# Pinned read-only artifacts the glue composes (DESIGN / spec Interfaces §Paths).
QA_PROMPT_PATH = REPO_ROOT / "agent_config" / "qa_system_prompt.md"
MCP_CONFIG_REL = "connectors/mcp/playwright.mcp.json"
EXAMPLE_CONFIG_PATH = REPO_ROOT / "connectors" / "examples" / "reference_app.target.json"

# The BRD-injection placeholder token pinned by unit 4 / the spec.
BRD_TOKEN = "{{BRD}}"

# A distinctive secret value that must never leak into any surface (criterion 17).
SECRET_SENTINEL = "S3CR3T-SENTINEL-DO-NOT-LEAK-9c1f2a"

# A unique BRD body marker used to assert injection happened.
BRD_SENTINEL = "BRD-BODY-MARKER-Zzz-particular-42"

CREDENTIAL_REF = "REF_APP_BASIC_AUTH"


# --------------------------------------------------------------------------- #
# In-memory OpenAPI doc used as `api_spec_source` (no network required)
# --------------------------------------------------------------------------- #

SAMPLE_OPENAPI = {
    "openapi": "3.1.0",
    "info": {"title": "Reference Shop API", "version": "9.9.9"},
    "paths": {
        "/cart": {
            "get": {"operationId": "getCart", "responses": {"200": {"description": "ok"}}}
        },
        "/checkout": {
            "post": {
                "operationId": "checkout",
                "responses": {"200": {"description": "ok"}},
            }
        },
    },
}


def fresh_openapi() -> dict:
    """A defensive deep copy of the sample OpenAPI doc."""
    return json.loads(json.dumps(SAMPLE_OPENAPI))


# --------------------------------------------------------------------------- #
# Config-mapping factory (offline; api_spec_source is an in-memory dict)
# --------------------------------------------------------------------------- #

PLANNER_FIELDS = {
    "target_scope": "Shop storefront: browse, cart, checkout",
    "intent": "Verify a shopper can complete a purchase",
    "expected_behavior": "Cart totals correct; checkout returns an order id",
    "priority_risk": "Payment + cart arithmetic",
    "test_data_preconditions": "Seeded catalog, registered user",
    "out_of_scope_constraints": "No real payment gateway",
    "depth": "regression",
}


def make_config(
    brd_path,
    *,
    api_spec_source=None,
    target_url="http://127.0.0.1:5173",
    credential_ref=CREDENTIAL_REF,
    planner_fields=None,
) -> dict:
    """Build a valid target-config mapping (api_spec_source defaults to the sample dict)."""
    return {
        "target_url": target_url,
        "api_spec_source": fresh_openapi() if api_spec_source is None else api_spec_source,
        "brd_path": str(brd_path),
        "basic_auth_credential_ref": credential_ref,
        "planner_fields": dict(PLANNER_FIELDS if planner_fields is None else planner_fields),
    }


# --------------------------------------------------------------------------- #
# MOCK agent runners (the injectable seam substitute — no model/network/browser)
# --------------------------------------------------------------------------- #
#
# NAMING ASSUMPTION (recorded in p1-agent-run-glue.tests.md):
#   * The runner seam is a CALLABLE invoked once as `agent_runner(invocation)`.
#   * The invocation bundle exposes its fields as ATTRIBUTES (invocation.system_prompt, ...).
#   * The runner returns a `runner.authoring.AgentRunOutput(status=..., generated_tests=...)`.
# These are the pinned seam names from the task spec; the developer must honor them.


class RecordingRunner:
    """A successful mock runner: records the invocation, returns canned tests + status."""

    def __init__(self, generated_tests=None, status="ok"):
        self.generated_tests = dict(generated_tests or {})
        self.status = status
        self.calls = []

    def __call__(self, invocation):
        from runner.authoring import AgentRunOutput

        self.calls.append(invocation)
        return AgentRunOutput(status=self.status, generated_tests=dict(self.generated_tests))

    @property
    def invocation(self):
        assert self.calls, "runner was never invoked"
        return self.calls[-1]


class RaisingRunner:
    """A mock runner that raises, to prove failures are surfaced (criterion 16)."""

    def __init__(self, exc=None):
        self.exc = exc or RuntimeError("mock runner boom")
        self.calls = []

    def __call__(self, invocation):
        self.calls.append(invocation)
        raise self.exc

"""Shared test helpers for the ``p1-agent-authoring-gate-credential-exception`` suite
(TDD red).

Lives in a **uniquely-named** module (NOT ``conftest``) so importing these symbols
(``from credential_exception_helpers import ...``) is unambiguous even when the whole
repo test suite is collected together — per the import-hygiene lesson already recorded
in ``runner/tests/opencode_helpers.py`` (two bare ``conftest`` modules collide under
pytest's prepend importmode).

This module deliberately does **not** duplicate the existing ``opencode_helpers.
make_invocation`` factory (that factory's signature is pinned by the already-reviewed
unit-7 suite and must not be touched). Instead it builds an
:class:`~runner.authoring.AuthoringInvocation` **directly**, so it can pass the new,
not-yet-existing ``basic_auth_credential_value`` keyword — which is expected to raise
``TypeError: __init__() got an unexpected keyword argument 'basic_auth_credential_value'``
until unit 6 adds the field (the legitimate TDD-red reason for every test that uses it).
"""

from __future__ import annotations

from runner.authoring import AuthoringInvocation

from opencode_helpers import (
    AUTH_REF_NAME,
    MCP_CONFIG_REL,
    PLANNER_FIELD_MARKERS,
    TARGET_URL_MARKER,
)

# A distinctive, non-secret TEST value standing in for a resolved credential value.
# Never the real reference-app fixture ('testuser'/'testpass') — this suite only proves
# the *mechanism*, independent of which value unit 8 later passes through it.
TEST_CREDENTIAL_VALUE = "CRED-VALUE-SENTINEL-do-not-confuse-with-ref-4b9d1"


def make_invocation_with_credential_value(
    output_dir,
    *,
    basic_auth_credential_value=None,
    system_prompt=None,
    target_url=None,
) -> AuthoringInvocation:
    """Build an ``AuthoringInvocation`` with the new opt-in field explicitly set.

    Mirrors ``opencode_helpers.make_invocation``'s other field values (reusing its
    constants) so the only *intentional* difference between two invocations built by
    this helper is ``basic_auth_credential_value`` — enabling byte-identical-message
    comparisons (AC5) and opt-in-delivery comparisons (AC6).
    """
    sp = (
        system_prompt
        if system_prompt is not None
        else (
            "<!-- QA_SYSTEM_PROMPT_VERSION: v1 -->\n"
            "credential-exception-suite system prompt (no {{BRD}} token here)\n"
        )
    )
    return AuthoringInvocation(
        system_prompt=sp,
        api_surface={"base_url": "http://127.0.0.1:8000", "endpoints": []},
        target_url=target_url if target_url is not None else TARGET_URL_MARKER,
        planner_fields=dict(PLANNER_FIELD_MARKERS),
        mcp_config_path=MCP_CONFIG_REL,
        planner_agent="qa-planner",
        generator_agent="qa-generator",
        basic_auth_credential_ref=AUTH_REF_NAME,
        output_dir=str(output_dir),
        basic_auth_credential_value=basic_auth_credential_value,
    )

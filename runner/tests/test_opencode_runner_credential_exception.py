"""TDD-red acceptance suite for ``p1-agent-authoring-gate-credential-exception`` — the
opt-in ``basic_auth_credential_value`` delivery path in
``runner.opencode_runner.OpenCodeRunner._compose_message`` / ``__call__``.

Encodes AC5-AC7 of
``.harness/tasks/p1-agent-authoring-gate-credential-exception.md``. This suite is
**additive only**: it does NOT modify ``test_opencode_runner.py``, and in particular
does NOT touch ``test_c13_target_auth_stays_reference_only`` — that test must keep
passing unmodified as the strongest, most direct proof that the default (no opt-in)
path stays byte-identical (AC5).

Offline only: no model key, no network, no browser, no real OpenCode process — every
OpenCode invocation is routed through the injected ``opencode_helpers.
FakeCommandRunner`` mock.

Red-at-authoring-time reason (legitimate TDD red): ``AuthoringInvocation`` does not yet
accept the ``basic_auth_credential_value`` keyword, so every invocation built via
``credential_exception_helpers.make_invocation_with_credential_value`` raises
``TypeError: unexpected keyword argument 'basic_auth_credential_value'`` until unit 6
adds the field.

Criterion -> test map lives in
``.harness/tasks/p1-agent-authoring-gate-credential-exception.tests.md``.
"""

from __future__ import annotations

from opencode_helpers import (
    AUTH_REF_NAME,
    FakeCommandRunner,
    MODEL_KEY_SENTINEL,
    OPENAI_KEY_ENV,
    agent_visible_text,
    import_adapter,
    make_invocation,
    output_text,
)

from credential_exception_helpers import (
    TEST_CREDENTIAL_VALUE,
    make_invocation_with_credential_value,
)


# =========================================================================== #
# AC5 — default path (`basic_auth_credential_value is None`) byte-identical
# =========================================================================== #


def test_explicit_none_message_matches_todays_default_path(tmp_path):
    """AC5: an invocation with ``basic_auth_credential_value=None`` (explicit
    opt-out / default) composes a message byte-identical to one built without the new
    field at all (``opencode_helpers.make_invocation``, the existing, unmodified
    unit-7 helper) -- for BOTH roles."""
    mod = import_adapter()
    baseline_inv = make_invocation(tmp_path / "out")
    new_inv = make_invocation_with_credential_value(
        tmp_path / "out",
        basic_auth_credential_value=None,
        system_prompt=baseline_inv.system_prompt,
        target_url=baseline_inv.target_url,
    )
    for role in ("Planner", "Generator"):
        baseline_msg = mod.OpenCodeRunner._compose_message(baseline_inv, role)
        new_msg = mod.OpenCodeRunner._compose_message(new_inv, role)
        assert new_msg == baseline_msg


# =========================================================================== #
# AC6 — opt-in path delivers the value, for both roles, alongside the reference name
# =========================================================================== #


def test_opt_in_value_present_for_both_roles_alongside_reference_name(tmp_path):
    """AC6: with ``basic_auth_credential_value`` set to a non-None string, the
    composed message for BOTH the Planner and Generator roles includes that exact
    value, and continues to include the existing reference-name sentence (supplemented,
    not replaced)."""
    mod = import_adapter()
    inv = make_invocation_with_credential_value(
        tmp_path / "out", basic_auth_credential_value=TEST_CREDENTIAL_VALUE
    )
    for role in ("Planner", "Generator"):
        msg = mod.OpenCodeRunner._compose_message(inv, role)
        assert TEST_CREDENTIAL_VALUE in msg, (
            f"{role} message missing the opt-in credential value"
        )
        assert repr(AUTH_REF_NAME) in msg, (
            f"{role} message lost the existing reference-name sentence"
        )


def test_opt_in_value_reaches_full_mock_run_surface(monkeypatch, tmp_path):
    """AC6 (end-to-end): driving the full (mocked) adapter with an opt-in invocation
    delivers the credential value to the agent-visible surface, alongside the
    reference name — proving the wiring from invocation through to the actual
    OpenCode-bound argv/prompt, not just the static ``_compose_message`` unit."""
    mod = import_adapter()
    monkeypatch.setenv(OPENAI_KEY_ENV, MODEL_KEY_SENTINEL)
    mock = FakeCommandRunner(mode="ok")
    inv = make_invocation_with_credential_value(
        tmp_path / "out", basic_auth_credential_value=TEST_CREDENTIAL_VALUE
    )
    runner = mod.OpenCodeRunner(command_runner=mock)
    output = runner(inv)

    surfaces = agent_visible_text(mock) + "\n" + output_text(output)
    assert TEST_CREDENTIAL_VALUE in surfaces
    assert AUTH_REF_NAME in surfaces


# =========================================================================== #
# AC7 — no OPENAI_API_KEY regression, on either path
# =========================================================================== #


def test_openai_key_handling_unaffected_with_default_invocation(
    monkeypatch, tmp_path, capsys
):
    """AC7: with ``basic_auth_credential_value`` at its default (None), the
    ``OPENAI_API_KEY`` model-credential path is untouched: present in the child env,
    absent from every agent-visible / output surface."""
    mod = import_adapter()
    monkeypatch.setenv(OPENAI_KEY_ENV, MODEL_KEY_SENTINEL)
    mock = FakeCommandRunner(mode="ok")
    inv = make_invocation_with_credential_value(
        tmp_path / "out", basic_auth_credential_value=None
    )
    runner = mod.OpenCodeRunner(command_runner=mock)
    output = runner(inv)

    env_values = [c["env"].get(OPENAI_KEY_ENV) for c in mock.calls]
    assert MODEL_KEY_SENTINEL in env_values

    captured = capsys.readouterr()
    surfaces = "\n".join(
        [agent_visible_text(mock), output_text(output), captured.out, captured.err]
    )
    assert MODEL_KEY_SENTINEL not in surfaces


def test_openai_key_handling_unaffected_with_opt_in_invocation(
    monkeypatch, tmp_path, capsys
):
    """AC7: even when the SAME invocation also carries the new opt-in credential
    VALUE, ``OPENAI_API_KEY`` handling is unaffected -- no cross-talk between the two
    independent secret paths."""
    mod = import_adapter()
    monkeypatch.setenv(OPENAI_KEY_ENV, MODEL_KEY_SENTINEL)
    mock = FakeCommandRunner(mode="ok")
    inv = make_invocation_with_credential_value(
        tmp_path / "out", basic_auth_credential_value=TEST_CREDENTIAL_VALUE
    )
    runner = mod.OpenCodeRunner(command_runner=mock)
    output = runner(inv)

    env_values = [c["env"].get(OPENAI_KEY_ENV) for c in mock.calls]
    assert MODEL_KEY_SENTINEL in env_values

    captured = capsys.readouterr()
    surfaces = "\n".join(
        [agent_visible_text(mock), output_text(output), captured.out, captured.err]
    )
    assert MODEL_KEY_SENTINEL not in surfaces
    # The opt-in value IS expected on this surface (that's the feature) -- but never
    # the model key.
    assert TEST_CREDENTIAL_VALUE in surfaces

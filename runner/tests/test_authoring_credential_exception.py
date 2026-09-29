"""TDD-red acceptance suite for ``p1-agent-authoring-gate-credential-exception`` — the
scoped, opt-in ``expose_credential_for_exploration`` carve-out on unit-6's
``runner.authoring.run_authoring``.

Encodes AC1-AC4 of
``.harness/tasks/p1-agent-authoring-gate-credential-exception.md``. Adds tests only —
no existing test in ``runner/tests/test_authoring.py`` is modified.

Uses the same offline fixtures/mocks as the unit-6 suite (``authoring_helpers`` +
``conftest.py``: ``valid_config``, ``clean_brd``, ``config_factory``,
``recording_runner``). No model key, no network, no browser.

Red-at-authoring-time reasons (legitimate TDD red):
  * ``run_authoring`` does not yet accept ``expose_credential_for_exploration``
    -> ``TypeError: unexpected keyword argument``;
  * ``AuthoringInvocation`` does not yet have a ``basic_auth_credential_value`` field
    -> ``AttributeError`` when read, or ``TypeError`` when constructed with it.

Criterion -> test map lives in
``.harness/tasks/p1-agent-authoring-gate-credential-exception.tests.md``.
"""

from __future__ import annotations

import dataclasses

import pytest

from connectors.target_config import CredentialUnsetError

from runner.authoring import AuthoringInvocation, run_authoring

from authoring_helpers import CREDENTIAL_REF, RecordingRunner

# A distinctive, non-secret TEST value standing in for a resolved credential value.
CRED_EXPOSURE_TEST_VALUE = "CRED-EXPOSURE-TEST-VALUE-plaintext-7d2f1"


# =========================================================================== #
# AC4 — AuthoringInvocation field is additive, optional, keyword-compatible
# =========================================================================== #


def test_authoring_invocation_gains_optional_credential_value_field():
    """AC4: the dataclass gains ``basic_auth_credential_value: Optional[str] = None``,
    appended after the existing fields, with a default (no reordering required)."""
    fields = {f.name: f for f in dataclasses.fields(AuthoringInvocation)}
    assert "basic_auth_credential_value" in fields, (
        "AuthoringInvocation is missing the new optional "
        "'basic_auth_credential_value' field"
    )
    new_field = fields["basic_auth_credential_value"]
    assert new_field.default is None, (
        "'basic_auth_credential_value' must default to None"
    )
    # Every existing field name/order is preserved (additive only, no reordering).
    existing_order = [
        "system_prompt",
        "api_surface",
        "target_url",
        "planner_fields",
        "mcp_config_path",
        "planner_agent",
        "generator_agent",
        "basic_auth_credential_ref",
        "output_dir",
    ]
    names = [f.name for f in dataclasses.fields(AuthoringInvocation)]
    assert names[: len(existing_order)] == existing_order


def test_existing_keyword_construction_sites_still_work_unmodified(tmp_path):
    """AC4: the existing keyword-argument-only construction pattern (as used by
    ``opencode_helpers.make_invocation``) keeps working, and the new field defaults
    to ``None`` when omitted."""
    inv = AuthoringInvocation(
        system_prompt="p",
        api_surface={},
        target_url="http://x.test",
        planner_fields={},
        mcp_config_path="mcp.json",
        planner_agent="qa-planner",
        generator_agent="qa-generator",
        basic_auth_credential_ref="SOME_REF",
        output_dir=str(tmp_path),
    )
    assert inv.basic_auth_credential_value is None


# =========================================================================== #
# AC1 — default (omitted / False) behavior fully preserved
# =========================================================================== #


def test_omitted_flag_defaults_invocation_value_to_none(tmp_path, valid_config):
    """AC1: with the flag omitted, the invocation handed to agent_runner carries
    ``basic_auth_credential_value is None`` — the default-preserving behavior."""
    runner = RecordingRunner({"a.spec.ts": "x"})
    run_authoring(valid_config, agent_runner=runner, output_dir=str(tmp_path))
    assert runner.invocation.basic_auth_credential_value is None


def test_explicit_false_matches_omitted_default(tmp_path, valid_config):
    """AC1: passing ``expose_credential_for_exploration=False`` explicitly is
    identical, in every observable way, to omitting it."""
    r1 = RecordingRunner({"a.spec.ts": "x"})
    r2 = RecordingRunner({"a.spec.ts": "x"})
    res1 = run_authoring(valid_config, agent_runner=r1, output_dir=str(tmp_path / "o1"))
    res2 = run_authoring(
        valid_config,
        agent_runner=r2,
        output_dir=str(tmp_path / "o2"),
        expose_credential_for_exploration=False,
    )
    assert r1.invocation.basic_auth_credential_value is None
    assert r2.invocation.basic_auth_credential_value is None
    assert res1.system_prompt == res2.system_prompt
    assert res1.api_surface == res2.api_surface


def test_default_path_does_not_call_resolve_credential(monkeypatch, tmp_path, valid_config):
    """AC1: with the flag at its default, ``resolve_credential`` is never invoked (no
    new call site is exercised) — the referenced env var may stay entirely unset."""
    monkeypatch.delenv(CREDENTIAL_REF, raising=False)
    runner = RecordingRunner({"a.spec.ts": "x"})
    # Must NOT raise CredentialUnsetError -- resolve_credential is not called by default.
    res = run_authoring(valid_config, agent_runner=runner, output_dir=str(tmp_path))
    assert res.runner_status == "ok"
    assert runner.invocation.basic_auth_credential_value is None


# =========================================================================== #
# AC2 — opt-in resolves and carries the value, nowhere else
# =========================================================================== #


def test_opt_in_resolves_credential_onto_invocation(monkeypatch, tmp_path, valid_config):
    """AC2: with the flag True and the env var set, the invocation's new field equals
    the resolved value (config.resolve_credential()'s result)."""
    monkeypatch.setenv(CREDENTIAL_REF, CRED_EXPOSURE_TEST_VALUE)
    runner = RecordingRunner({"a.spec.ts": "x"})
    run_authoring(
        valid_config,
        agent_runner=runner,
        output_dir=str(tmp_path),
        expose_credential_for_exploration=True,
    )
    assert runner.invocation.basic_auth_credential_value == CRED_EXPOSURE_TEST_VALUE
    # The reference name still flows through unchanged, alongside the resolved value.
    assert runner.invocation.basic_auth_credential_ref == CREDENTIAL_REF


def test_opt_in_value_never_exposed_by_run_result(monkeypatch, tmp_path, valid_config):
    """AC2: the returned RunResult never exposes the resolved value — not as an
    attribute, not in repr(), not via any dict/JSON produced by inspecting it."""
    monkeypatch.setenv(CREDENTIAL_REF, CRED_EXPOSURE_TEST_VALUE)
    runner = RecordingRunner({"a.spec.ts": "x"})
    res = run_authoring(
        valid_config,
        agent_runner=runner,
        output_dir=str(tmp_path),
        expose_credential_for_exploration=True,
    )
    # Sanity: the opt-in really did resolve the value onto the invocation (else this
    # test would trivially pass for the wrong reason).
    assert runner.invocation.basic_auth_credential_value == CRED_EXPOSURE_TEST_VALUE

    assert not hasattr(res, "basic_auth_credential_value"), (
        "RunResult must never expose the resolved credential value as an attribute"
    )
    assert CRED_EXPOSURE_TEST_VALUE not in repr(res)
    # No __dict__-style serialization surface exposes it either (RunResult uses
    # __slots__; guard against a future non-slotted regression too).
    for attr_name in dir(res):
        if attr_name.startswith("_"):
            continue
        try:
            value = getattr(res, attr_name)
        except AttributeError:
            continue
        if callable(value):
            continue
        assert CRED_EXPOSURE_TEST_VALUE not in str(value), (
            f"resolved credential value leaked via RunResult.{attr_name}"
        )


# =========================================================================== #
# AC3 — unset credential still raises, unchanged
# =========================================================================== #


def test_opt_in_with_unset_env_var_raises_credential_unset_error(
    monkeypatch, tmp_path, valid_config
):
    """AC3: with the flag True and the referenced env var unset,
    ``connectors.target_config.CredentialUnsetError`` propagates unchanged — no new,
    parallel error path is introduced."""
    monkeypatch.delenv(CREDENTIAL_REF, raising=False)
    runner = RecordingRunner({"a.spec.ts": "x"})
    with pytest.raises(CredentialUnsetError) as excinfo:
        run_authoring(
            valid_config,
            agent_runner=runner,
            output_dir=str(tmp_path),
            expose_credential_for_exploration=True,
        )
    assert CREDENTIAL_REF in str(excinfo.value)
    # No run occurred and nothing was written (consistent with other unit-6 error paths).
    assert runner.calls == []

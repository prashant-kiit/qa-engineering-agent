"""TDD-red acceptance suite for ``p1-opencode-runner`` — the OpenCode runner adapter.

Encodes the spec's enumerated, **mock-testable** acceptance criteria (1–19) using an
**injected mock command-runner** (:class:`opencode_helpers.FakeCommandRunner`). There is
**no** model key, **no** network, **no** browser, and **no** real OpenCode process here.

Red-at-authoring-time reasons (legitimate TDD red):
  * ``runner.opencode_runner`` does not exist yet (adapter tests → ``ImportError``);
  * ``connectors/opencode/opencode.json`` + ``.opencode/agent/*.md`` do not exist yet
    (config/agent-def presence tests → ``AssertionError``).

Import hygiene: shared symbols come from the uniquely-named ``opencode_helpers`` module,
never from a bare ``conftest`` (which would collide across test dirs under pytest's
prepend importmode).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from opencode_helpers import (
    AUTH_REF_NAME,
    AUTH_SENTINEL,
    BRD_CONTENT_MARKER,
    BRD_TOKEN,
    CANNED_TESTS,
    EXPECTED_MODEL,
    MODEL_KEY_SENTINEL,
    OPENAI_KEY_ENV,
    OPENCODE_CONFIG_REL,
    OPENCODE_GENERATOR_DEF,
    OPENCODE_PLANNER_DEF,
    PINNED_MCP_SERVER,
    PLANNER_FIELD_MARKERS,
    QA_PROMPT_PATH,
    REPO_ROOT,
    SYS_PROMPT_MARKER,
    TARGET_URL_MARKER,
    FakeCommandRunner,
    agent_flags_in_order,
    agent_visible_text,
    governing_config,
    import_adapter,
    make_invocation,
    model_arg,
    normalize_argv,
    output_text,
)


# --------------------------------------------------------------------------- #
# Small run helper: a successful adapter run with a mock command-runner.
# --------------------------------------------------------------------------- #


def _run(monkeypatch, tmp_path, *, mock=None, runner_kwargs=None, invocation=None,
         set_key=True, set_auth=False):
    """Construct ``OpenCodeRunner`` with the mock seam and invoke it once."""
    mod = import_adapter()
    if set_key:
        monkeypatch.setenv(OPENAI_KEY_ENV, MODEL_KEY_SENTINEL)
    if set_auth:
        monkeypatch.setenv(AUTH_REF_NAME, AUTH_SENTINEL)
    mock = mock or FakeCommandRunner(mode="ok")
    invocation = invocation or make_invocation(tmp_path / "glue_out")
    runner = mod.OpenCodeRunner(command_runner=mock, **(runner_kwargs or {}))
    output = runner(invocation)
    return mod, runner, mock, invocation, output


# =========================================================================== #
# Seam conformance
# =========================================================================== #


def test_c1_satisfies_agentrunner_seam_through_glue(monkeypatch, tmp_path):
    """C1: a callable ``(AuthoringInvocation)->AgentRunOutput`` the unit-6 glue can drive."""
    from authoring_helpers import make_config

    from runner import authoring

    mod = import_adapter()
    monkeypatch.setenv(OPENAI_KEY_ENV, MODEL_KEY_SENTINEL)

    brd = tmp_path / "BRD.md"
    brd.write_text(f"# BRD\n{BRD_CONTENT_MARKER}\n", encoding="utf-8")
    config = make_config(
        str(brd), target_url=TARGET_URL_MARKER, planner_fields=dict(PLANNER_FIELD_MARKERS)
    )

    mock = FakeCommandRunner(mode="ok")
    runner = mod.OpenCodeRunner(command_runner=mock)
    assert callable(runner)

    result = authoring.run_authoring(
        config, agent_runner=runner, output_dir=str(tmp_path / "out")
    )
    assert result.runner_status == "ok"
    assert mock.called


# =========================================================================== #
# Constructed OpenCode invocation (asserted on argv/env/cwd/input given to the mock)
# =========================================================================== #


def test_c2_invokes_opencode_binary_in_run_mode(monkeypatch, tmp_path):
    """C2: argv starts with the pinned binary + the non-interactive ``run`` subcommand."""
    mod, _r, mock, _inv, _out = _run(monkeypatch, tmp_path)
    assert mock.called
    assert mod.OPENCODE_BIN == "opencode"
    for call in mock.calls:
        argv = call["argv"]
        assert Path(argv[0]).name == "opencode"
        assert "run" in argv[:2]


def test_c3_selects_gpt4o_mini_model(monkeypatch, tmp_path):
    """C3a: the argv explicitly selects ``openai/gpt-4o-mini`` (matches DEFAULT_MODEL)."""
    mod, _r, mock, _inv, _out = _run(monkeypatch, tmp_path)
    assert mod.DEFAULT_MODEL == EXPECTED_MODEL
    selected = {model_arg(c["argv"]) for c in mock.calls}
    assert EXPECTED_MODEL in selected


def test_c3_model_is_bumpable_config_value(monkeypatch, tmp_path):
    """C3b: overriding the model knob changes the argv (bumpable-config property)."""
    override = "openai/gpt-4o"
    _mod, _r, mock, _inv, _out = _run(
        monkeypatch, tmp_path, runner_kwargs={"model": override}
    )
    selected = {model_arg(c["argv"]) for c in mock.calls}
    assert override in selected
    assert EXPECTED_MODEL not in selected


def test_c4_wires_mcp_via_governing_config(monkeypatch, tmp_path):
    """C4: the run is governed by an OpenCode config declaring the pinned Playwright MCP."""
    _mod, _r, mock, _inv, _out = _run(monkeypatch, tmp_path)
    cfg = governing_config(mock)
    assert cfg is not None, "no governing OpenCode config resolved from the invocation"
    assert cfg.get("model") == EXPECTED_MODEL
    # OpenCode MCP shape: top-level `mcp` key (not the Claude-native `mcpServers`).
    assert "mcp" in cfg
    assert PINNED_MCP_SERVER in json.dumps(cfg)


def test_c5_delivers_brd_injected_prompt_and_seven_fields(monkeypatch, tmp_path):
    """C5: the BRD-injected system prompt + all seven planner fields reach OpenCode."""
    _mod, _r, mock, _inv, _out = _run(monkeypatch, tmp_path)
    surfaces = agent_visible_text(mock)
    assert SYS_PROMPT_MARKER in surfaces
    assert BRD_CONTENT_MARKER in surfaces
    for value in PLANNER_FIELD_MARKERS.values():
        assert value in surfaces, f"planner field value not delivered: {value!r}"
    # The adapter must NOT re-inject the {{BRD}} token nor re-author the prompt.
    assert BRD_TOKEN not in surfaces


def test_c5_does_not_modify_shared_prompt_file(monkeypatch, tmp_path):
    """C5: the shared ``agent_config/qa_system_prompt.md`` is not edited by the run."""
    before = QA_PROMPT_PATH.read_bytes()
    _run(monkeypatch, tmp_path)
    assert QA_PROMPT_PATH.read_bytes() == before


def test_c6_points_at_target_url(monkeypatch, tmp_path):
    """C6: ``invocation.target_url`` reaches the run."""
    _mod, _r, mock, _inv, _out = _run(monkeypatch, tmp_path)
    assert TARGET_URL_MARKER in agent_visible_text(mock)


def test_c7_planner_precedes_generator(monkeypatch, tmp_path):
    """C7: the Planner role is exercised before the Generator role; both present, distinct."""
    _mod, _r, mock, _inv, _out = _run(monkeypatch, tmp_path)
    flags = agent_flags_in_order(mock)
    if "qa-planner" in flags and "qa-generator" in flags:
        # Two-ordered-runs form: assert call order.
        assert flags.index("qa-planner") < flags.index("qa-generator")
    else:
        # Single-orchestrator form: both identities present in the governing surfaces.
        surfaces = agent_visible_text(mock)
        cfg_text = json.dumps(governing_config(mock) or {})
        haystack = surfaces + "\n" + cfg_text
        assert "qa-planner" in haystack and "qa-generator" in haystack


def test_c8_workspace_distinct_from_output_dir(monkeypatch, tmp_path):
    """C8: the command-runner cwd is a workspace that is NOT ``invocation.output_dir``."""
    _mod, _r, mock, inv, _out = _run(monkeypatch, tmp_path)
    assert mock.called
    for call in mock.calls:
        assert call["cwd"], "no cwd passed to the command-runner"
        assert Path(call["cwd"]).resolve() != Path(inv.output_dir).resolve()


# =========================================================================== #
# Output capture
# =========================================================================== #


def test_c9_captures_generated_tests_into_mapping(monkeypatch, tmp_path):
    """C9: a successful run returns status 'ok' + byte-exact tests keyed by rel filename."""
    _mod, _r, _mock, _inv, output = _run(monkeypatch, tmp_path)
    assert output.status == "ok"
    got = dict(output.generated_tests)
    for name, content in CANNED_TESTS.items():
        assert name in got, f"expected captured test {name!r} in {sorted(got)}"
        assert got[name] == content
    for name in got:
        assert not Path(name).is_absolute(), f"filename must be workspace-relative: {name!r}"


def test_c10_end_to_end_through_glue_writes_files(monkeypatch, tmp_path):
    """C10: driving the glue writes exactly the captured files under output_dir, byte-exact."""
    from authoring_helpers import make_config

    from runner import authoring

    mod = import_adapter()
    monkeypatch.setenv(OPENAI_KEY_ENV, MODEL_KEY_SENTINEL)

    brd = tmp_path / "BRD.md"
    brd.write_text(f"# BRD\n{BRD_CONTENT_MARKER}\n", encoding="utf-8")
    config = make_config(
        str(brd), target_url=TARGET_URL_MARKER, planner_fields=dict(PLANNER_FIELD_MARKERS)
    )
    out_dir = tmp_path / "out"
    mock = FakeCommandRunner(mode="ok")
    runner = mod.OpenCodeRunner(command_runner=mock)

    authoring.run_authoring(config, agent_runner=runner, output_dir=str(out_dir))
    for name, content in CANNED_TESTS.items():
        written = out_dir / name
        assert written.is_file(), f"glue did not write {name!r}"
        assert written.read_text(encoding="utf-8") == content


# =========================================================================== #
# Credential handling & secret-safety (§11.5, §11.4)
# =========================================================================== #


def test_c11_model_key_injected_into_child_env_only(monkeypatch, tmp_path, capsys):
    """C11: OPENAI_API_KEY present in the child env; sentinel absent from every surface."""
    _mod, _r, mock, _inv, output = _run(monkeypatch, tmp_path)
    # Present in at least one child env passed to the command-runner.
    env_values = [c["env"].get(OPENAI_KEY_ENV) for c in mock.calls]
    assert MODEL_KEY_SENTINEL in env_values

    captured = capsys.readouterr()
    surfaces = "\n".join(
        [agent_visible_text(mock), output_text(output), captured.out, captured.err]
    )
    assert MODEL_KEY_SENTINEL not in surfaces
    # Also absent from raw argv specifically.
    for call in mock.calls:
        assert MODEL_KEY_SENTINEL not in " ".join(call["argv"])


def test_c12_missing_model_credential_raises_named_error(monkeypatch, tmp_path):
    """C12: with OPENAI_API_KEY unset, a real spawn is refused with the named adapter error."""
    mod = import_adapter()
    monkeypatch.delenv(OPENAI_KEY_ENV, raising=False)
    mock = FakeCommandRunner(mode="ok")
    runner = mod.OpenCodeRunner(command_runner=mock)
    invocation = make_invocation(tmp_path / "out")

    # Assumed named base error (spec: developer's choice; pinned to `OpenCodeRunnerError`).
    with pytest.raises(mod.OpenCodeRunnerError) as excinfo:
        runner(invocation)

    assert not mock.called, "no OpenCode process should be spawned when the key is missing"
    msg = str(excinfo.value)
    assert OPENAI_KEY_ENV in msg
    assert MODEL_KEY_SENTINEL not in msg


def test_c13_target_auth_stays_reference_only(monkeypatch, tmp_path, capsys):
    """C13: the resolved Basic-Auth secret never appears in argv/prompt/logs/output."""
    _mod, _r, mock, _inv, output = _run(monkeypatch, tmp_path, set_auth=True)
    captured = capsys.readouterr()
    surfaces = "\n".join(
        [agent_visible_text(mock), output_text(output), captured.out, captured.err]
    )
    assert AUTH_SENTINEL not in surfaces


# =========================================================================== #
# Error / non-success behavior (surfaced, never swallowed)
# =========================================================================== #


def test_c14_nonzero_exit_yields_nonok_scrubbed_detail(monkeypatch, tmp_path, capsys):
    """C14: a non-zero OpenCode exit → non-'ok' status, human-readable detail, no secret."""
    mock = FakeCommandRunner(mode="fail", stderr="opencode exited with an error")
    _mod, _r, _mock, _inv, output = _run(monkeypatch, tmp_path, mock=mock, set_auth=True)
    assert output.status != "ok"
    assert output.detail  # present + human-readable
    captured = capsys.readouterr()
    scan = "\n".join([output_text(output), captured.out, captured.err])
    assert MODEL_KEY_SENTINEL not in scan
    assert AUTH_SENTINEL not in scan


def test_c14_normal_run_failure_is_not_an_exception(monkeypatch, tmp_path):
    """C14: a normal (non-zero) run failure returns a status, it does not raise."""
    mock = FakeCommandRunner(mode="fail", stderr="boom")
    # Should not raise — must return a non-ok AgentRunOutput.
    _mod, _r, _mock, _inv, output = _run(monkeypatch, tmp_path, mock=mock)
    assert output.status != "ok"


def test_c15_no_tests_produced_yields_nonok(monkeypatch, tmp_path):
    """C15: exit 0 but no matching test files → non-'ok' status, empty/omitted mapping."""
    mock = FakeCommandRunner(mode="empty")
    _mod, _r, _mock, _inv, output = _run(monkeypatch, tmp_path, mock=mock)
    assert output.status != "ok"
    assert not dict(output.generated_tests)


def test_c16_missing_connector_config_raises_named_error(monkeypatch, tmp_path):
    """C16: an unresolvable connector config → the named adapter error (not silent success)."""
    mod = import_adapter()
    monkeypatch.setenv(OPENAI_KEY_ENV, MODEL_KEY_SENTINEL)
    mock = FakeCommandRunner(mode="ok")
    missing = tmp_path / "does_not_exist" / "opencode.json"
    runner = mod.OpenCodeRunner(command_runner=mock, opencode_config_path=str(missing))
    invocation = make_invocation(tmp_path / "out")
    with pytest.raises(mod.OpenCodeRunnerError):
        runner(invocation)


# =========================================================================== #
# Determinism, placement, no-regression
# =========================================================================== #


def test_c17_deterministic_construction(monkeypatch, tmp_path):
    """C17: two runs from identical inputs yield identical argv (modulo the temp workspace)."""
    mod = import_adapter()
    monkeypatch.setenv(OPENAI_KEY_ENV, MODEL_KEY_SENTINEL)
    invocation = make_invocation(tmp_path / "out")

    mock_a = FakeCommandRunner(mode="ok")
    mod.OpenCodeRunner(command_runner=mock_a)(invocation)
    mock_b = FakeCommandRunner(mode="ok")
    mod.OpenCodeRunner(command_runner=mock_b)(invocation)

    assert mock_a.called and mock_b.called
    assert len(mock_a.calls) == len(mock_b.calls)
    for ca, cb in zip(mock_a.calls, mock_b.calls):
        na = normalize_argv(ca["argv"], ca["cwd"])
        nb = normalize_argv(cb["argv"], cb["cwd"])
        assert na == nb
    # Governing config content is identical too.
    assert governing_config(mock_a) == governing_config(mock_b)


def test_c18_pinned_constants_and_import_path(monkeypatch, tmp_path):
    """C18: the pinned public import path exposes the pinned constants + seam + errors."""
    mod = import_adapter()
    assert mod.DEFAULT_MODEL == EXPECTED_MODEL
    assert mod.OPENAI_API_KEY_ENV == OPENAI_KEY_ENV
    assert mod.OPENCODE_CONFIG_PATH == OPENCODE_CONFIG_REL
    assert mod.OPENCODE_BIN == "opencode"
    assert mod.PLANNER_AGENT == "qa-planner"
    assert mod.GENERATOR_AGENT == "qa-generator"
    assert hasattr(mod, "OpenCodeRunner")
    assert issubclass(mod.OpenCodeRunnerError, Exception)


def test_c18_connector_config_artifact_shape():
    """C18/C4: the shipped connectors/opencode/opencode.json exists with the pinned shape."""
    cfg_path = REPO_ROOT / OPENCODE_CONFIG_REL
    assert cfg_path.is_file(), f"missing OpenCode connector config: {cfg_path}"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    assert "$schema" in cfg
    assert cfg.get("model") == EXPECTED_MODEL
    assert "mcp" in cfg, "OpenCode config must declare MCP under the top-level `mcp` key"
    text = json.dumps(cfg)
    assert PINNED_MCP_SERVER in text
    assert "chromium" in text
    # References the shared portable QA prompt and/or the two named agents.
    assert (
        "agent_config/qa_system_prompt.md" in text
        or "qa-planner" in text
        or "instructions" in cfg
    )


def test_c18_opencode_agent_defs_exist_and_reference_shared_prompt():
    """C18/scope-5: OpenCode Planner/Generator agent defs reference the shared QA prompt.

    Accepts the pinned markdown-file location OR the inline-`agent` alternative in
    connectors/opencode/opencode.json (spec Interfaces §Paths exception).
    """
    files_present = OPENCODE_PLANNER_DEF.is_file() and OPENCODE_GENERATOR_DEF.is_file()
    if files_present:
        planner = OPENCODE_PLANNER_DEF.read_text(encoding="utf-8")
        generator = OPENCODE_GENERATOR_DEF.read_text(encoding="utf-8")
        assert "qa_system_prompt.md" in planner
        assert "qa_system_prompt.md" in generator
    else:
        cfg_path = REPO_ROOT / OPENCODE_CONFIG_REL
        assert cfg_path.is_file(), (
            "neither .opencode/agent/qa-*.md files nor an inline `agent` block present"
        )
        cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        agent_block = cfg.get("agent", {})
        assert "qa-planner" in agent_block and "qa-generator" in agent_block
        assert "qa_system_prompt.md" in json.dumps(cfg)


def test_c19_no_egress_no_writes_outside_workspace(monkeypatch, tmp_path):
    """C19: in tests the adapter writes nothing outside the injected/tmp workspace.

    The mock command-runner never spawns a process (no egress); the adapter's own
    workspace is the mock's recorded cwd. Assert nothing landed in output_dir directly
    (the glue is the single writer of output_dir) and the run stayed hermetic.
    """
    out_dir = tmp_path / "glue_out"
    invocation = make_invocation(out_dir)
    _mod, _r, mock, inv, _out = _run(monkeypatch, tmp_path, invocation=invocation)
    # The adapter itself must not write into output_dir (single-writer rule).
    if out_dir.exists():
        assert not any(out_dir.rglob("*.spec.ts")), (
            "adapter wrote tests into output_dir; the glue is the single writer"
        )
    # Every workspace cwd is under tmp / a per-run temp dir, never the repo tree root.
    for call in mock.calls:
        cwd = Path(call["cwd"]).resolve()
        assert cwd != REPO_ROOT

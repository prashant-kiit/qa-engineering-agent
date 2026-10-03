"""Acceptance suite for `p1-agent-run-glue` — the Phase 1 agent-run glue (TDD red).

Encodes the enumerated acceptance criteria of .harness/tasks/p1-agent-run-glue.md using a
MOCK agent runner (conftest). No model key, no network, no browser, no real Claude Code /
Playwright MCP. The glue module `runner.authoring` does not exist yet, so this module fails
to import — the legitimate red reason.

Criterion → test map lives in .harness/tasks/p1-agent-run-glue.tests.md.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from connectors.spec_loader import SpecLoadError
from connectors.target_config import TargetConfigError

# --- module under test (does not exist yet -> ModuleNotFoundError = red) --------------
from runner.authoring import DEFAULT_OUTPUT_DIR, run_authoring

from authoring_helpers import (  # uniquely-named module; safe across whole-suite collection
    BRD_SENTINEL,
    BRD_TOKEN,
    CREDENTIAL_REF,
    MCP_CONFIG_REL,
    QA_PROMPT_PATH,
    SECRET_SENTINEL,
    PLANNER_FIELDS,
    RaisingRunner,
    RecordingRunner,
)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #


def _config_dict(result):
    """Normalize RunResult.config (TargetConfig or its to_dict) to a plain dict."""
    cfg = result.config
    return cfg.to_dict() if hasattr(cfg, "to_dict") else cfg


def _invocation_blob(inv) -> str:
    """Concatenate every invocation field into one string for leak scans."""
    parts = [
        inv.system_prompt,
        inv.api_surface,
        inv.target_url,
        inv.planner_fields,
        inv.mcp_config_path,
        inv.planner_agent,
        inv.generator_agent,
        inv.basic_auth_credential_ref,
        inv.output_dir,
    ]
    return "\n".join(str(p) for p in parts)


def _assert_glue_error(exc: Exception, *, must_contain: str | None = None):
    """Assert `exc` is a glue-owned named error (defined in the `runner` package),
    not a re-raised connectors error."""
    mod = type(exc).__module__ or ""
    assert mod.startswith("runner"), (
        f"expected a named glue error defined in the runner package, "
        f"got {type(exc).__name__!r} from module {mod!r}"
    )
    assert not isinstance(exc, (TargetConfigError, SpecLoadError))
    if must_contain is not None:
        assert must_contain in str(exc), (
            f"error message {str(exc)!r} should name {must_contain!r}"
        )


def _patch_prompt_path(monkeypatch, new_path: str) -> list[str]:
    """Point the glue at a substitute QA system prompt by monkeypatching whatever
    module-level attribute holds the qa_system_prompt.md path.

    NAMING ASSUMPTION (recorded in the coverage note): the glue exposes the QA
    system-prompt path as a module-level attribute so it is monkeypatchable.
    """
    import runner.authoring as authoring

    patched = []
    for name, val in list(vars(authoring).items()):
        try:
            s = str(val)
        except Exception:
            continue
        if s.endswith("qa_system_prompt.md"):
            monkeypatch.setattr(authoring, name, new_path)
            patched.append(name)
    return patched


def _dir_is_empty(path: Path) -> bool:
    return (not path.exists()) or not any(path.iterdir())


# =========================================================================== #
# Assembly — config, spec, prompt
# =========================================================================== #


def test_loads_target_config_via_unit2(tmp_path, valid_config, recording_runner):
    """Criterion 1: config loaded through unit 2; run result reflects its fields."""
    res = run_authoring(valid_config, agent_runner=recording_runner, output_dir=str(tmp_path))
    cfg = _config_dict(res)
    assert cfg["target_url"] == valid_config["target_url"]
    assert cfg["basic_auth_credential_ref"] == CREDENTIAL_REF
    assert cfg["planner_fields"] == valid_config["planner_fields"]
    # All seven planner fields carried through, incl. depth.
    assert set(cfg["planner_fields"]) == set(PLANNER_FIELDS)
    assert cfg["planner_fields"]["depth"] == "regression"


def test_loads_api_surface_via_units_1_and_2(
    tmp_path, valid_config, recording_runner, expected_api_surface
):
    """Criterion 2: API surface obtained via config.load_api_spec() (unit 1), no network."""
    res = run_authoring(valid_config, agent_runner=recording_runner, output_dir=str(tmp_path))
    assert res.api_surface == expected_api_surface
    # And it is the normalized surface, not the raw doc.
    assert res.api_surface["title"] == "Reference Shop API"
    op_keys = {(o["method"], o["path"]) for o in res.api_surface["operations"]}
    assert op_keys == {("GET", "/cart"), ("POST", "/checkout")}


def test_brd_injected_present_no_residue_and_template_preserved(
    tmp_path, config_factory, clean_brd, recording_runner
):
    """Criterion 3a/3b/3d: BRD text present, no `{{BRD}}` residue, template preserved."""
    brd_path, brd_text = clean_brd
    cfg = config_factory(brd_path)
    res = run_authoring(cfg, agent_runner=recording_runner, output_dir=str(tmp_path))

    prompt = res.system_prompt
    # (a) contains the BRD body text
    assert BRD_SENTINEL in prompt
    assert brd_text.strip() in prompt
    # (b) no residual placeholder token
    assert BRD_TOKEN not in prompt
    # (d) the non-BRD template is preserved (stable version marker from unit-4 prompt)
    assert "<!-- QA_SYSTEM_PROMPT_VERSION: v1 -->" in prompt


def test_brd_replaced_exactly_once_no_double_substitution(
    tmp_path, config_factory, token_bearing_brd, recording_runner
):
    """Criterion 3c: the single original placeholder is replaced once; a `{{BRD}}` in the
    BRD body is NOT recursively re-substituted."""
    brd_path, brd_text = token_bearing_brd
    # The real QA prompt template must have exactly one placeholder to begin with.
    assert QA_PROMPT_PATH.read_text(encoding="utf-8").count(BRD_TOKEN) == 1

    cfg = config_factory(brd_path)
    res = run_authoring(cfg, agent_runner=recording_runner, output_dir=str(tmp_path))
    prompt = res.system_prompt

    assert BRD_SENTINEL in prompt
    # The BRD body carried its own literal token through verbatim (exactly one), proving
    # the original single placeholder was consumed once and no extra substitution occurred.
    assert prompt.count(BRD_TOKEN) == brd_text.count(BRD_TOKEN) == 1


def test_deterministic_assembly(tmp_path, valid_config):
    """Criterion 4: same inputs -> byte-identical assembled artifacts."""
    r1 = RecordingRunner({"a.spec.ts": "x"})
    r2 = RecordingRunner({"a.spec.ts": "x"})
    res1 = run_authoring(valid_config, agent_runner=r1, output_dir=str(tmp_path / "o1"))
    res2 = run_authoring(valid_config, agent_runner=r2, output_dir=str(tmp_path / "o2"))

    assert res1.system_prompt == res2.system_prompt
    assert res1.api_surface == res2.api_surface
    assert res1.planner_agent == res2.planner_agent
    assert res1.generator_agent == res2.generator_agent
    assert Path(res1.mcp_config_path).name == Path(res2.mcp_config_path).name


# =========================================================================== #
# Referencing MCP config + sub-agents
# =========================================================================== #


def test_mcp_config_referenced(tmp_path, valid_config, recording_runner):
    """Criterion 5: pinned MCP config path referenced in result + passed to runner."""
    res = run_authoring(valid_config, agent_runner=recording_runner, output_dir=str(tmp_path))
    norm = str(res.mcp_config_path).replace("\\", "/")
    assert norm.endswith(MCP_CONFIG_REL)
    inv = recording_runner.invocation
    assert str(inv.mcp_config_path).replace("\\", "/").endswith(MCP_CONFIG_REL)


def test_planner_and_generator_referenced(tmp_path, valid_config, recording_runner):
    """Criterion 6: both sub-agents referenced by pinned identities, distinct + present."""
    res = run_authoring(valid_config, agent_runner=recording_runner, output_dir=str(tmp_path))
    assert "qa-planner" in str(res.planner_agent)
    assert "qa-generator" in str(res.generator_agent)
    assert str(res.planner_agent) != str(res.generator_agent)
    inv = recording_runner.invocation
    assert "qa-planner" in str(inv.planner_agent)
    assert "qa-generator" in str(inv.generator_agent)


# =========================================================================== #
# Runner seam (mock-substitutable) + output writing
# =========================================================================== #


def test_runner_invoked_with_assembled_invocation(
    tmp_path, valid_config, recording_runner, expected_api_surface
):
    """Criterion 7: injected runner receives the full invocation bundle (pinned fields)."""
    out = str(tmp_path)
    res = run_authoring(valid_config, agent_runner=recording_runner, output_dir=out)

    assert len(recording_runner.calls) == 1
    inv = recording_runner.invocation
    assert inv.system_prompt == res.system_prompt
    assert BRD_TOKEN not in inv.system_prompt
    # api_surface may be the ApiSurface or its to_dict — normalize before compare.
    inv_surface = inv.api_surface.to_dict() if hasattr(inv.api_surface, "to_dict") else inv.api_surface
    assert inv_surface == expected_api_surface
    assert inv.target_url == valid_config["target_url"]
    assert dict(inv.planner_fields) == valid_config["planner_fields"]
    assert str(inv.mcp_config_path).replace("\\", "/").endswith(MCP_CONFIG_REL)
    assert "qa-planner" in str(inv.planner_agent)
    assert "qa-generator" in str(inv.generator_agent)
    assert inv.basic_auth_credential_ref == CREDENTIAL_REF
    assert Path(inv.output_dir).resolve() == Path(out).resolve()


def test_no_hardcoded_live_call(monkeypatch, tmp_path, valid_config):
    """Criterion 8: with no key/env/network, the glue calls only the injected runner."""
    for var in ("ANTHROPIC_API_KEY", "CLAUDE_API_KEY", "ANTHROPIC_AUTH_TOKEN"):
        monkeypatch.delenv(var, raising=False)
    runner = RecordingRunner({"only.spec.ts": "// ok\n"})
    res = run_authoring(valid_config, agent_runner=runner, output_dir=str(tmp_path))
    # The injected runner was the sole thing invoked.
    assert len(runner.calls) == 1
    assert res.runner_status == "ok"


def test_generated_tests_written_to_output_dir(tmp_path, valid_config):
    """Criterion 9: each returned file is written with byte-exact content."""
    generated = {
        "cart.spec.ts": "// cart spec\nimport {test} from '@playwright/test';\n",
        "api/orders.api.spec.ts": "// nested orders api spec\n",
    }
    runner = RecordingRunner(generated)
    out = tmp_path / "gen"
    res = run_authoring(valid_config, agent_runner=runner, output_dir=str(out))

    for rel, content in generated.items():
        written = out / rel
        assert written.is_file(), f"{rel} was not written"
        assert written.read_text(encoding="utf-8") == content
    # written_test_paths reports exactly the files written.
    names = {Path(p).name for p in res.written_test_paths}
    assert names == {"cart.spec.ts", "orders.api.spec.ts"}
    assert len(res.written_test_paths) == 2


def test_default_output_dir_constant():
    """Criterion 10 (constant): DEFAULT_OUTPUT_DIR is the pinned runner/generated path."""
    assert str(DEFAULT_OUTPUT_DIR).replace("\\", "/").rstrip("/").endswith("runner/generated")


def test_default_output_dir_used_when_none(monkeypatch, tmp_path, valid_config):
    """Criterion 10 (behavior): when output_dir is None, the glue resolves to the default.

    NAMING ASSUMPTION (recorded): DEFAULT_OUTPUT_DIR is a module global consulted at call
    time for the None default; monkeypatched here to a tmp dir to avoid polluting the repo.
    """
    import runner.authoring as authoring

    fake_default = tmp_path / "generated"
    monkeypatch.setattr(authoring, "DEFAULT_OUTPUT_DIR", str(fake_default))
    runner = RecordingRunner({"d.spec.ts": "// default\n"})
    res = authoring.run_authoring(valid_config, agent_runner=runner)  # no output_dir

    assert Path(res.output_dir).resolve() == fake_default.resolve()
    assert (fake_default / "d.spec.ts").read_text(encoding="utf-8") == "// default\n"


def test_run_result_shape_and_values(
    tmp_path, valid_config, expected_api_surface
):
    """Criterion 11: RunResult exposes all pinned attributes with matching values."""
    generated = {"one.spec.ts": "// one\n"}
    runner = RecordingRunner(generated, status="ok")
    out = tmp_path / "rr"
    res = run_authoring(valid_config, agent_runner=runner, output_dir=str(out))

    for attr in (
        "config",
        "system_prompt",
        "api_surface",
        "mcp_config_path",
        "planner_agent",
        "generator_agent",
        "output_dir",
        "written_test_paths",
        "runner_status",
    ):
        assert hasattr(res, attr), f"RunResult missing pinned attribute {attr!r}"

    assert _config_dict(res)["target_url"] == valid_config["target_url"]
    assert isinstance(res.system_prompt, str) and BRD_TOKEN not in res.system_prompt
    assert res.api_surface == expected_api_surface
    assert Path(res.output_dir).resolve() == out.resolve()
    assert res.runner_status == "ok"
    assert [Path(p).name for p in res.written_test_paths] == ["one.spec.ts"]


# =========================================================================== #
# Error behavior (surfaced, never swallowed)
# =========================================================================== #


def test_invalid_config_raises_unit2_error(tmp_path, config_factory, clean_brd):
    """Criterion 12: invalid/missing config -> TargetConfigError; no run, no writes."""
    brd_path, _ = clean_brd
    bad = config_factory(brd_path)
    del bad["target_url"]  # required field missing
    runner = RecordingRunner({"x.spec.ts": "x"})
    out = tmp_path / "out"
    with pytest.raises(TargetConfigError):
        run_authoring(bad, agent_runner=runner, output_dir=str(out))
    assert runner.calls == []
    assert _dir_is_empty(out)


def test_spec_load_failure_propagates_unchanged(tmp_path, config_factory, clean_brd):
    """Criterion 13: unloadable/malformed spec -> SpecLoadError; no run, no writes."""
    brd_path, _ = clean_brd
    # A mapping that is not an OpenAPI document -> spec_loader raises SpecLoadError.
    cfg = config_factory(brd_path, api_spec_source={"not": "an openapi spec"})
    runner = RecordingRunner({"x.spec.ts": "x"})
    out = tmp_path / "out"
    with pytest.raises(SpecLoadError):
        run_authoring(cfg, agent_runner=runner, output_dir=str(out))
    assert runner.calls == []
    assert _dir_is_empty(out)


def test_missing_brd_raises_named_glue_error(tmp_path, config_factory):
    """Criterion 14: unreadable/missing BRD -> named glue error naming the path."""
    missing = tmp_path / "nope" / "BRD.md"
    cfg = config_factory(str(missing))
    runner = RecordingRunner({"x.spec.ts": "x"})
    out = tmp_path / "out"
    with pytest.raises(Exception) as ei:
        run_authoring(cfg, agent_runner=runner, output_dir=str(out))
    _assert_glue_error(ei.value, must_contain=str(missing))
    assert runner.calls == []
    assert _dir_is_empty(out)


@pytest.mark.parametrize(
    "bad_prompt",
    [
        "# Prompt with no placeholder at all\nnothing here\n",
        "# Prompt with two placeholders\n{{BRD}}\n...\n{{BRD}}\n",
    ],
    ids=["zero-tokens", "two-tokens"],
)
def test_bad_placeholder_count_raises_named_glue_error(
    monkeypatch, tmp_path, valid_config, bad_prompt
):
    """Criterion 15: prompt without exactly one `{{BRD}}` token -> named glue error."""
    bad_prompt_path = tmp_path / "bad_qa_system_prompt.md"
    bad_prompt_path.write_text(bad_prompt, encoding="utf-8")
    patched = _patch_prompt_path(monkeypatch, str(bad_prompt_path))
    assert patched, (
        "could not find a module-level QA-prompt-path attribute to monkeypatch; "
        "the glue must expose the qa_system_prompt.md path as a module attribute"
    )

    runner = RecordingRunner({"x.spec.ts": "x"})
    out = tmp_path / "out"
    with pytest.raises(Exception) as ei:
        run_authoring(valid_config, agent_runner=runner, output_dir=str(out))
    _assert_glue_error(ei.value)
    assert runner.calls == []
    assert _dir_is_empty(out)


def test_runner_exception_is_surfaced(tmp_path, valid_config):
    """Criterion 16a: a runner that raises is not swallowed (exception surfaces)."""
    boom = RuntimeError("mock runner exploded")
    runner = RaisingRunner(boom)
    out = tmp_path / "out"
    with pytest.raises(Exception) as ei:
        run_authoring(valid_config, agent_runner=runner, output_dir=str(out))
    # Either the original is propagated or re-raised with context — never suppressed.
    assert ei.value is boom or ei.value.__cause__ is boom or "exploded" in str(ei.value)


def test_runner_error_status_not_reported_as_success(tmp_path, valid_config):
    """Criterion 16b: a runner error status surfaces; no false 'successful write'."""
    runner = RecordingRunner(generated_tests={}, status="error")
    out = tmp_path / "out"
    res = run_authoring(valid_config, agent_runner=runner, output_dir=str(out))
    assert res.runner_status == "error"
    assert list(res.written_test_paths) == []
    assert _dir_is_empty(out)


# =========================================================================== #
# Secret-safety (§11.4)
# =========================================================================== #


def test_only_credential_reference_flows_through(
    monkeypatch, capsys, tmp_path, valid_config
):
    """Criterion 17: a sentinel secret in env leaks into NO surface; only the ref name flows."""
    monkeypatch.setenv(CREDENTIAL_REF, SECRET_SENTINEL)
    generated = {"leak_check.spec.ts": "// generated content\n"}
    runner = RecordingRunner(generated)
    out = tmp_path / "secure"
    res = run_authoring(valid_config, agent_runner=runner, output_dir=str(out))

    # Reference NAME flows through (invocation + result); resolved VALUE never does.
    inv = runner.invocation
    assert inv.basic_auth_credential_ref == CREDENTIAL_REF

    surfaces = {
        "system_prompt": res.system_prompt,
        "result_repr": repr(res),
        "invocation": _invocation_blob(inv),
    }
    for name, blob in surfaces.items():
        assert SECRET_SENTINEL not in str(blob), f"secret leaked into {name}"

    # Written artifacts must not contain the secret.
    for f in out.rglob("*"):
        if f.is_file():
            assert SECRET_SENTINEL not in f.read_text(encoding="utf-8")

    # No log/print output leaks the secret.
    captured = capsys.readouterr()
    assert SECRET_SENTINEL not in captured.out
    assert SECRET_SENTINEL not in captured.err

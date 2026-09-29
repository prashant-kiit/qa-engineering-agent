"""TDD-red acceptance suite for the headless-execution-fix amendment (AF1-AF6) to the
unit-7 OpenCode runner adapter.

Source of truth: ``.harness/tasks/p1-agent-authoring-gate.md`` ->
"Adapter headless-execution fix (Interpretation #4, concrete)". This amendment makes
Interpretation flag #4 concrete: OpenCode's headless ``run`` needs ``--auto``
(auto-approve tool permissions), ``--dir <workspace>``, a continue-session flag on the
Generator's (second) invocation, and a workspace-local *materialized* config (governed
by a ``permission.external_directory: "deny"`` policy) instead of pointing
``OPENCODE_CONFIG`` straight at the shipped ``connectors/opencode/opencode.json``.

**Additive only.** This module does NOT modify ``test_opencode_runner.py``,
``test_opencode_runner_credential_exception.py``, or ``opencode_helpers.py`` — it only
imports (read-only) the existing mock-command-runner pattern
(:class:`opencode_helpers.FakeCommandRunner`) those suites already use. Suite-specific
helpers live in the uniquely-named ``opencode_headless_fix_helpers`` module (not
``conftest``), per the import-hygiene lesson already recorded in ``opencode_helpers.py``.

Offline only (AF5): every OpenCode invocation is routed through the injected
``FakeCommandRunner`` mock — no real subprocess, no network egress, no real
``OPENAI_API_KEY`` (a placeholder sentinel, as unit 7's existing tests already use, is
sufficient to satisfy the adapter's pre-spawn credential check).

Legitimate TDD-red reasons at authoring time (no implementation of this amendment
exists yet):
  * AF1 — the argv the current adapter builds (``_build_argv``) has no ``--auto`` and
    no ``--dir`` at all, so the presence assertions fail.
  * AF2 — the current adapter never emits a continue-session flag on any call, so the
    "Generator call DOES carry one" assertion fails.
  * AF3/AF3a/AF3b/AF4 — ``OPENCODE_CONFIG`` currently points straight at the resolved
    shipped ``connectors/opencode/opencode.json`` path (see ``_build_env``); there is no
    workspace-local materialization step and no injected ``permission`` block, so the
    "not the shipped path" / "materialized permission.external_directory == 'deny'"
    assertions fail. AF3b's premise check (the shipped
    ``agent_config/qa_system_prompt.md`` template still contains the literal
    ``{{BRD}}`` placeholder) passes today; the materialization assertion itself fails
    because no materialized instructions file exists at all yet.

Criterion -> test map + red output lives in
``.harness/tasks/p1-agent-authoring-gate.tests.md`` (appended section).
"""

from __future__ import annotations

import json
from pathlib import Path

from opencode_helpers import (
    EXPECTED_MODEL,
    FakeCommandRunner,
    MODEL_KEY_SENTINEL,
    OPENAI_KEY_ENV,
    import_adapter,
    make_invocation,
)

from opencode_headless_fix_helpers import (
    SHIPPED_CONFIG_ABS,
    find_file_refs,
    flag_value,
    is_inside,
    load_shipped_config,
    resolve_file_ref,
)

REPO_ROOT = SHIPPED_CONFIG_ABS.resolve().parents[2]


def _run_ok(monkeypatch, tmp_path, **runner_kwargs):
    """Construct ``OpenCodeRunner`` with the mock seam and invoke it once (mode='ok')."""
    mod = import_adapter()
    monkeypatch.setenv(OPENAI_KEY_ENV, MODEL_KEY_SENTINEL)
    mock = FakeCommandRunner(mode="ok")
    invocation = make_invocation(tmp_path / "glue_out")
    runner = mod.OpenCodeRunner(command_runner=mock, **runner_kwargs)
    output = runner(invocation)
    return mod, runner, mock, invocation, output


# =========================================================================== #
# AF1 — `--auto` and `--dir <workspace==cwd>` on every invocation
# =========================================================================== #


def test_af1_every_call_has_auto_and_dir_matching_cwd(monkeypatch, tmp_path):
    """AF1: every recorded call's argv includes ``--auto`` and ``--dir <cwd>``."""
    _mod, _r, mock, _inv, _out = _run_ok(monkeypatch, tmp_path)
    assert mock.called
    assert len(mock.calls) >= 2, "expected (at least) the Planner + Generator calls"
    for call in mock.calls:
        argv = call["argv"]
        assert "--auto" in argv, f"missing auto-approve-permissions flag in argv: {argv}"
        dir_value = flag_value(argv, "--dir")
        assert dir_value is not None, f"missing --dir <workspace> in argv: {argv}"
        assert Path(dir_value).resolve() == Path(call["cwd"]).resolve(), (
            f"--dir value {dir_value!r} does not match this call's cwd {call['cwd']!r}"
        )


# =========================================================================== #
# AF2 — continue-session flag ONLY on the second (Generator) invocation
# =========================================================================== #


def test_af2_continue_absent_on_planner_present_on_generator(monkeypatch, tmp_path):
    """AF2: Planner (first) call has no continue flag; Generator (second) call does."""
    _mod, _r, mock, _inv, _out = _run_ok(monkeypatch, tmp_path)
    assert len(mock.calls) >= 2
    first_argv = mock.calls[0]["argv"]
    second_argv = mock.calls[-1]["argv"]

    def has_continue(argv):
        return "--continue" in argv or "-c" in argv

    assert not has_continue(first_argv), (
        f"Planner (first) invocation must NOT carry a continue-session flag: {first_argv}"
    )
    assert has_continue(second_argv), (
        f"Generator (second) invocation must carry a continue-session flag: {second_argv}"
    )


# =========================================================================== #
# AF3 — materialized, workspace-local config (not the shipped file)
# =========================================================================== #
#
# Split per the TPM's spec correction (orchestrator-traced imprecision in the original
# AF3 wording): the agent-role `{file:...}` references (AF3a) are legitimately
# byte-identical copies of their shipped source (those files never change at runtime),
# but the top-level `instructions` entry (AF3b) must resolve to the run's *injected,
# token-free* `invocation.system_prompt` — NOT a byte-copy of the shipped
# `agent_config/qa_system_prompt.md` **template**, which still contains the literal,
# unresolved `{{BRD}}` placeholder (verified below). Materializing that raw template
# into the workspace would contradict the frozen `test_c5_delivers_brd_injected_prompt_
# and_seven_fields` (in `test_opencode_runner.py`, NOT touched by this amendment),
# which scans every file under the workspace for the literal `{{BRD}}` token via the
# shared `agent_visible_text` helper and asserts it is absent.


def test_af3_config_is_workspace_local_materialized_json(monkeypatch, tmp_path):
    """AF3 (general): OPENCODE_CONFIG resolves to a single workspace-local materialized
    JSON file, shared across both calls of one run, preserving `model`/`mcp` unchanged
    from the shipped config — while the shipped config itself stays byte-unmodified on
    disk. (Instructions/agent-file-reference content is covered by AF3b/AF3a below.)"""
    shipped_bytes_before = SHIPPED_CONFIG_ABS.read_bytes()

    _mod, _r, mock, _inv, _out = _run_ok(monkeypatch, tmp_path)

    shipped_bytes_after = SHIPPED_CONFIG_ABS.read_bytes()
    assert shipped_bytes_after == shipped_bytes_before, (
        "the shipped connectors/opencode/opencode.json must remain byte-unmodified "
        "on disk after the run (it is read, never written)"
    )

    assert len(mock.calls) >= 2
    shipped = load_shipped_config()
    shipped_abs_resolved = SHIPPED_CONFIG_ABS.resolve()

    cfg_env_values = set()
    for call in mock.calls:
        cfg_path_str = call["env"].get("OPENCODE_CONFIG")
        assert cfg_path_str, "OPENCODE_CONFIG not set in this call's child env"
        cfg_path = Path(cfg_path_str).resolve()
        cfg_env_values.add(str(cfg_path))
        ws = Path(call["cwd"])

        assert cfg_path != shipped_abs_resolved, (
            "OPENCODE_CONFIG must point at a materialized workspace-local file, "
            "never the shipped connectors/opencode/opencode.json path"
        )
        assert is_inside(cfg_path, ws), (
            f"materialized config {cfg_path} is not inside the run workspace {ws}"
        )
        assert cfg_path.is_file(), f"materialized config file does not exist: {cfg_path}"
        materialized = json.loads(cfg_path.read_text(encoding="utf-8"))

        assert materialized.get("model") == shipped.get("model") == EXPECTED_MODEL
        assert materialized.get("mcp") == shipped.get("mcp"), (
            "materialized config's `mcp` block must be unchanged from the shipped config"
        )

    assert len(cfg_env_values) == 1, (
        "OPENCODE_CONFIG must be identical across both invocations of the same run "
        f"(one materialization per run, shared by Planner and Generator); got {cfg_env_values}"
    )


def test_af3a_agent_role_file_refs_are_byte_identical_in_workspace(monkeypatch, tmp_path):
    """AF3a: every `{file:...}` reference under `agent.*.prompt` (the qa-planner /
    qa-generator agent-definition stand-ins) resolves, relative to the materialized
    config's own parent directory, to an in-workspace file byte-identical to its
    shipped source (`.opencode/agent/qa-planner.md` / `qa-generator.md`) — these agent
    definitions never change at runtime, so an exact copy is correct here."""
    _mod, _r, mock, _inv, _out = _run_ok(monkeypatch, tmp_path)
    assert len(mock.calls) >= 2
    shipped = load_shipped_config()
    shipped_refs = find_file_refs(shipped)
    assert shipped_refs, (
        "expected >=1 {file:...} reference in the shipped config "
        "(e.g. agent.qa-planner.prompt) to anchor this assertion"
    )

    for call in mock.calls:
        cfg_path = Path(call["env"]["OPENCODE_CONFIG"]).resolve()
        ws = Path(call["cwd"])
        materialized = json.loads(cfg_path.read_text(encoding="utf-8"))

        materialized_refs = find_file_refs(materialized)
        assert len(materialized_refs) == len(shipped_refs), (
            "materialized config must carry the same number of {file:...} references "
            "as the shipped config, in the same structural positions"
        )
        for (shipped_json_path, _s_raw, shipped_ref), (mat_json_path, _m_raw, mat_ref) in zip(
            shipped_refs, materialized_refs
        ):
            assert shipped_json_path == mat_json_path, (
                "materialized {file:...} reference occupies a different json-structure "
                f"position than the shipped config: {shipped_json_path} vs {mat_json_path}"
            )
            orig_content = (REPO_ROOT / resolve_file_ref(shipped_ref)).read_bytes()
            resolved = cfg_path.parent / resolve_file_ref(mat_ref)
            assert resolved.is_file(), (
                f"materialized {{file:...}} reference does not exist on disk: {resolved}"
            )
            assert is_inside(resolved, ws), (
                f"materialized {{file:...}} reference is outside the workspace: {resolved}"
            )
            assert resolved.read_bytes() == orig_content, (
                f"materialized {{file:...}} reference {resolved} diverges from shipped source"
            )


def test_af3b_instructions_resolve_to_injected_system_prompt_not_shipped_template(
    monkeypatch, tmp_path
):
    """AF3b: the shipped `agent_config/qa_system_prompt.md` is the raw, unresolved
    TEMPLATE (still contains the literal `{{BRD}}` placeholder) -- so the materialized
    config's `instructions` entries must NOT be byte-copies of it. Instead each
    `instructions` entry resolves, relative to the materialized config's own parent
    directory, to an in-workspace file whose content equals THIS RUN's
    `invocation.system_prompt` (the already BRD-injected, token-free prompt unit 6's
    glue assembled before the adapter ever saw it) -- and that materialized file must
    never contain the literal `{{BRD}}` token (reinforcing, not duplicating,
    `test_c5_delivers_brd_injected_prompt_and_seven_fields`'s guarantee)."""
    # Sanity-anchor the premise: the shipped template really is unresolved.
    shipped = load_shipped_config()
    shipped_instructions = shipped.get("instructions", [])
    assert shipped_instructions, "expected >=1 entry in the shipped config's `instructions`"
    for shipped_rel in shipped_instructions:
        shipped_source_text = (REPO_ROOT / shipped_rel).read_text(encoding="utf-8")
        assert "{{BRD}}" in shipped_source_text, (
            f"expected the shipped template {shipped_rel!r} to still contain the "
            "unresolved {{BRD}} placeholder (premise of this test)"
        )

    mod, _r, mock, invocation, _out = _run_ok(monkeypatch, tmp_path)
    assert len(mock.calls) >= 2
    assert "{{BRD}}" not in invocation.system_prompt, (
        "test setup error: the crafted invocation's system_prompt must already be "
        "BRD-injected/token-free (mirrors the real unit-6 glue output)"
    )

    for call in mock.calls:
        cfg_path = Path(call["env"]["OPENCODE_CONFIG"]).resolve()
        ws = Path(call["cwd"])
        materialized = json.loads(cfg_path.read_text(encoding="utf-8"))
        materialized_instructions = materialized.get("instructions", [])
        assert len(materialized_instructions) == len(shipped_instructions)

        for materialized_rel in materialized_instructions:
            resolved = cfg_path.parent / materialized_rel
            assert resolved.is_file(), (
                f"materialized instructions entry does not exist on disk: {resolved}"
            )
            assert is_inside(resolved, ws), (
                f"materialized instructions file is outside the workspace: {resolved}"
            )
            content = resolved.read_text(encoding="utf-8")
            assert content == invocation.system_prompt, (
                "materialized instructions file must equal this run's "
                "invocation.system_prompt exactly -- NOT a byte-copy of the shipped "
                f"agent_config/qa_system_prompt.md template ({resolved})"
            )
            assert "{{BRD}}" not in content, (
                f"materialized instructions file {resolved} must never contain the "
                "literal, unresolved {{BRD}} placeholder"
            )


# =========================================================================== #
# AF4 — permission.external_directory is "deny", never "allow"
# =========================================================================== #


def test_af4_permission_external_directory_is_deny(monkeypatch, tmp_path):
    """AF4: the materialized config's `permission.external_directory` == "deny"."""
    _mod, _r, mock, _inv, _out = _run_ok(monkeypatch, tmp_path)
    assert mock.calls
    for call in mock.calls:
        cfg_path = Path(call["env"]["OPENCODE_CONFIG"]).resolve()
        materialized = json.loads(cfg_path.read_text(encoding="utf-8"))
        permission = materialized.get("permission")
        assert permission is not None, "materialized config is missing a `permission` block"
        assert permission.get("external_directory") == "deny", (
            f"expected permission.external_directory == 'deny', got {permission!r}"
        )


def test_af4_external_directory_never_allow_across_constructor_variants(monkeypatch, tmp_path):
    """AF4 (negative invariant): across default construction, a model override, and a
    custom `opencode_config_path` (pointing at an input config that does NOT itself
    declare a `permission` block), the materialized config's
    `permission.external_directory` is never `"allow"` — if the adapter sets the key
    at all, it must be `"deny"`."""
    mod = import_adapter()

    # Variant A: default construction.
    # Variant B: model override.
    # Variant C: custom opencode_config_path — a minimal input config with NO
    # `permission` key of its own, proving the adapter (not the input file) enforces
    # the deny.
    minimal_cfg_path = tmp_path / "custom_input" / "opencode.json"
    minimal_cfg_path.parent.mkdir(parents=True, exist_ok=True)
    minimal_cfg_path.write_text(
        json.dumps({"$schema": "https://opencode.ai/config.json", "model": EXPECTED_MODEL}),
        encoding="utf-8",
    )

    variants = [
        ("default", {}),
        ("model-override", {"model": "openai/gpt-4o"}),
        ("custom-config-path", {"opencode_config_path": str(minimal_cfg_path)}),
    ]

    for label, kwargs in variants:
        monkeypatch.setenv(OPENAI_KEY_ENV, MODEL_KEY_SENTINEL)
        mock = FakeCommandRunner(mode="ok")
        invocation = make_invocation(tmp_path / f"glue_out_{label}")
        runner = mod.OpenCodeRunner(command_runner=mock, **kwargs)
        runner(invocation)

        assert mock.calls, f"variant {label!r} ({kwargs}) never invoked the command-runner"
        for call in mock.calls:
            cfg_path = Path(call["env"]["OPENCODE_CONFIG"]).resolve()
            materialized = json.loads(cfg_path.read_text(encoding="utf-8"))
            perm = materialized.get("permission") or {}
            # The adapter must actually set the key (a silently-absent key would
            # default to allow in OpenCode) — this pins the positive requirement
            # alongside the negative invariant below.
            assert "external_directory" in perm, (
                f"variant {label!r} ({kwargs}): materialized config must explicitly set "
                f"permission.external_directory (got permission={perm!r})"
            )
            assert perm["external_directory"] != "allow", (
                f"variant {label!r} ({kwargs}) materialized permission.external_directory "
                "== 'allow' — this must never happen"
            )
            assert perm["external_directory"] == "deny", (
                f"variant {label!r} ({kwargs}): permission.external_directory must be "
                f"'deny', got {perm['external_directory']!r}"
            )

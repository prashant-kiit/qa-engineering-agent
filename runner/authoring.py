"""Agent-run glue for Phase 1 — assemble & drive a single per-run authoring invocation.

This module **composes** (does not re-implement) the already-built Phase 1 pieces into
one per-run authoring invocation and drives it through an **injectable agent runner**:

* unit 2 — :func:`connectors.target_config.load_target_config` (load + validate config);
* unit 1 — the config's :meth:`TargetConfig.load_api_spec` (normalized API surface);
* unit 4 — the generic QA system prompt at :data:`QA_SYSTEM_PROMPT_PATH`, into which the
  per-run BRD is injected at the single ``{{BRD}}`` token;
* unit 3 — the Playwright-MCP config at :data:`MCP_CONFIG_PATH`;
* unit 5 — the ``qa-planner`` / ``qa-generator`` product sub-agents (referenced by
  identity).

The runner seam (:class:`AgentRunner`) is a **callable** ``agent_runner(invocation) ->``
:class:`AgentRunOutput`. Unit 7 provides the real (live) runner; unit-6 tests substitute a
mock. The glue **never** launches Claude Code / Playwright MCP / a browser itself, and
**never** resolves, logs, or persists the Basic-Auth secret — it carries only the
credential **reference name** (``DESIGN.md §11.4``).

Public contract (documented in ``runner/README.md``)::

    run_authoring(config_source, *, agent_runner, output_dir=None,
                  source_type="auto") -> RunResult

Named glue error: :class:`AuthoringError` (BRD unreadable/missing; bad ``{{BRD}}`` count).
``TargetConfigError`` (unit 2) and ``SpecLoadError`` / ``UnsupportedSourceError`` (unit 1)
propagate **unchanged**. A runner failure is **surfaced**, never swallowed.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional, Protocol

from connectors.target_config import load_target_config

# --------------------------------------------------------------------------- #
# Pinned, read-only artifact paths the glue composes (spec Interfaces §Paths).
# Kept as module-level attributes so tests can monkeypatch them.
# --------------------------------------------------------------------------- #

# runner/authoring.py -> parents[1] == repo root.
REPO_ROOT = Path(__file__).resolve().parents[1]

#: unit-4 generic QA system prompt (monkeypatchable module attribute).
QA_SYSTEM_PROMPT_PATH = str(REPO_ROOT / "agent_config" / "qa_system_prompt.md")

#: unit-3 Playwright-MCP config.
MCP_CONFIG_PATH = str(REPO_ROOT / "connectors" / "mcp" / "playwright.mcp.json")

#: unit-5 product sub-agent identities (referenced, not redefined).
PLANNER_AGENT = "qa-planner"
GENERATOR_AGENT = "qa-generator"

#: The BRD-injection placeholder token pinned by unit 4.
BRD_TOKEN = "{{BRD}}"

#: Pinned default output directory for generated tests (consulted at call time).
DEFAULT_OUTPUT_DIR = str(REPO_ROOT / "runner" / "generated")


# --------------------------------------------------------------------------- #
# Named glue error
# --------------------------------------------------------------------------- #


class AuthoringError(Exception):
    """Glue-owned error for authoring-assembly failures.

    Raised for a **missing/unreadable BRD file** (message names the BRD path) and a QA
    system prompt whose ``{{BRD}}`` token does not appear **exactly once**. Deliberately
    **not** a subclass of the unit-1/unit-2 errors, which propagate unchanged.
    """


# --------------------------------------------------------------------------- #
# Runner seam — invocation bundle, runner output, runner interface
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class AuthoringInvocation:
    """The assembled per-run invocation bundle handed to the injected runner.

    Carries only the credential **reference name** (never a resolved secret value).
    """

    system_prompt: str
    api_surface: Any
    target_url: str
    planner_fields: Mapping[str, str]
    mcp_config_path: str
    planner_agent: str
    generator_agent: str
    basic_auth_credential_ref: str
    output_dir: str


@dataclass
class AgentRunOutput:
    """What an agent runner returns.

    ``status`` is ``"ok"`` on success (any other value is treated as a non-success
    status and no artifacts are written); ``generated_tests`` maps a **relative filename**
    to file **content**; ``detail`` is an optional human-readable message.
    """

    status: str
    generated_tests: Mapping[str, str] = field(default_factory=dict)
    detail: Optional[str] = None


class AgentRunner(Protocol):
    """The injectable runner seam: a callable ``agent_runner(invocation) -> output``."""

    def __call__(self, invocation: AuthoringInvocation) -> AgentRunOutput:  # pragma: no cover
        ...


# --------------------------------------------------------------------------- #
# Run result
# --------------------------------------------------------------------------- #


class RunResult:
    """Structured result of a single authoring run.

    Its :func:`repr` is **secret-free** — no resolved credential value is ever held or
    rendered (only the credential reference name flows through, via ``config``).
    """

    __slots__ = (
        "config",
        "system_prompt",
        "api_surface",
        "mcp_config_path",
        "planner_agent",
        "generator_agent",
        "output_dir",
        "written_test_paths",
        "runner_status",
    )

    def __init__(
        self,
        *,
        config,
        system_prompt,
        api_surface,
        mcp_config_path,
        planner_agent,
        generator_agent,
        output_dir,
        written_test_paths,
        runner_status,
    ):
        self.config = config
        self.system_prompt = system_prompt
        self.api_surface = api_surface
        self.mcp_config_path = mcp_config_path
        self.planner_agent = planner_agent
        self.generator_agent = generator_agent
        self.output_dir = output_dir
        self.written_test_paths = written_test_paths
        self.runner_status = runner_status

    def __repr__(self) -> str:  # secret-free
        return (
            f"{type(self).__name__}(target_url={getattr(self.config, 'target_url', None)!r}, "
            f"mcp_config_path={self.mcp_config_path!r}, "
            f"planner_agent={self.planner_agent!r}, generator_agent={self.generator_agent!r}, "
            f"output_dir={self.output_dir!r}, "
            f"written_test_paths={list(self.written_test_paths)!r}, "
            f"runner_status={self.runner_status!r})"
        )


# --------------------------------------------------------------------------- #
# BRD injection
# --------------------------------------------------------------------------- #


def _inject_brd(prompt: str, brd_path: str) -> str:
    """Return ``prompt`` with its single ``{{BRD}}`` token replaced by the BRD file body.

    Raises :class:`AuthoringError` if the prompt does not contain exactly one token, or
    if the BRD file cannot be read (message names the BRD path).
    """
    token_count = prompt.count(BRD_TOKEN)
    if token_count != 1:
        raise AuthoringError(
            f"QA system prompt must contain the {BRD_TOKEN} placeholder exactly once "
            f"(found {token_count})"
        )

    try:
        with open(brd_path, "r", encoding="utf-8") as fh:
            brd_text = fh.read()
    except OSError as exc:
        raise AuthoringError(
            f"could not read BRD file {brd_path!r}: {exc}"
        ) from exc

    # Replace exactly once; a `{{BRD}}` inside the BRD body is not re-substituted.
    return prompt.replace(BRD_TOKEN, brd_text, 1)


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #


def run_authoring(
    config_source,
    *,
    agent_runner,
    output_dir=None,
    source_type: str = "auto",
) -> RunResult:
    """Assemble a per-run authoring invocation, drive the injected runner, write outputs.

    Parameters
    ----------
    config_source:
        A target-config mapping or a file path — forwarded to unit-2's
        :func:`~connectors.target_config.load_target_config`.
    agent_runner:
        The injected runner (keyword-only, required): a callable
        ``agent_runner(invocation) -> AgentRunOutput``. No live default is used.
    output_dir:
        Output directory for generated tests; defaults to :data:`DEFAULT_OUTPUT_DIR`
        (consulted at call time).
    source_type:
        Forwarded to unit-2's loader.

    Returns
    -------
    RunResult

    Raises
    ------
    connectors.target_config.TargetConfigError
        Invalid/missing config (propagated unchanged).
    connectors.spec_loader.SpecLoadError / UnsupportedSourceError
        Spec load failure (propagated unchanged).
    AuthoringError
        Missing/unreadable BRD file, or a bad ``{{BRD}}`` placeholder count.
    """
    # 1. Config (unit 2) — TargetConfigError propagates unchanged.
    config = load_target_config(config_source, source_type)

    # 2. API surface (units 1+2) — SpecLoadError / UnsupportedSourceError propagate.
    api_surface_obj = config.load_api_spec()
    api_surface = api_surface_obj.to_dict()

    # 3. QA system prompt (unit 4) + BRD injection — glue errors short-circuit here,
    #    before the runner is invoked and before anything is written.
    with open(QA_SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as fh:
        prompt_template = fh.read()
    system_prompt = _inject_brd(prompt_template, config.brd_path)

    # 4. Resolve the output directory (default consulted at call time).
    resolved_output_dir = DEFAULT_OUTPUT_DIR if output_dir is None else output_dir
    resolved_output_dir = str(resolved_output_dir)

    # 5. Assemble the invocation bundle (units 3 + 5, credential REFERENCE only).
    invocation = AuthoringInvocation(
        system_prompt=system_prompt,
        api_surface=api_surface,
        target_url=config.target_url,
        planner_fields=dict(config.planner_fields),
        mcp_config_path=MCP_CONFIG_PATH,
        planner_agent=PLANNER_AGENT,
        generator_agent=GENERATOR_AGENT,
        basic_auth_credential_ref=config.basic_auth_credential_ref,
        output_dir=resolved_output_dir,
    )

    # 6. Drive the injected runner — a runner failure is surfaced, never swallowed.
    output = agent_runner(invocation)

    status = getattr(output, "status", None)
    generated_tests = dict(getattr(output, "generated_tests", {}) or {})

    # 7. Write generated tests only on a successful status (never falsely report a
    #    successful write for an error status).
    written_test_paths: list[str] = []
    if status == "ok":
        base = Path(resolved_output_dir)
        for rel_name, content in generated_tests.items():
            dest = base / rel_name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8")
            written_test_paths.append(str(dest))

    # 8. Structured, secret-free result.
    return RunResult(
        config=config,
        system_prompt=system_prompt,
        api_surface=api_surface,
        mcp_config_path=MCP_CONFIG_PATH,
        planner_agent=PLANNER_AGENT,
        generator_agent=GENERATOR_AGENT,
        output_dir=resolved_output_dir,
        written_test_paths=written_test_paths,
        runner_status=status,
    )

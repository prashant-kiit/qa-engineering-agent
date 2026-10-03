"""OpenCode runner adapter for Phase 1 (unit 7, ``p1-opencode-runner``).

A concrete implementation of the unit-6 ``AgentRunner`` seam
(:mod:`runner.authoring`) that binds the open-source **OpenCode** headless coding
agent — driving the OpenAI model ``openai/gpt-4o-mini`` — to the authoring
pipeline. Given an assembled :class:`~runner.authoring.AuthoringInvocation`, it

* reads the platform-owned model credential from the ``OPENAI_API_KEY``
  **reference** (env var) and injects it **only** into the OpenCode child
  process environment — never into argv, prompt, logs, artifacts, or output;
* governs the run with the shipped OpenCode connector config
  (``connectors/opencode/opencode.json``) that wires the Playwright MCP server;
* drives the **Planner → Generator** flow (two ordered ``opencode run --agent``
  invocations) under the generic QA system prompt (with the BRD already injected
  upstream by unit 6) plus the seven structured Planner fields and the target
  URL;
* runs OpenCode through an **injected command-runner seam** (a real subprocess
  wrapper by default; a fake in unit tests) so it is unit-tested with **no**
  model key, network, browser, or real OpenCode process;
* captures the generated TS Playwright + API test files from a **workspace**
  (distinct from ``invocation.output_dir``) and returns them as
  :class:`~runner.authoring.AgentRunOutput.generated_tests` for the unit-6 glue
  to write.

Public import path (binding): ``runner.opencode_runner``.

Constants (binding names)
-------------------------
``DEFAULT_MODEL``, ``OPENAI_API_KEY_ENV``, ``OPENCODE_CONFIG_PATH``,
``OPENCODE_BIN``, ``PLANNER_AGENT``, ``GENERATOR_AGENT``, ``CAPTURE_GLOBS``.

Command-runner seam
--------------------
``command_runner(argv, *, cwd, env, input=None, timeout=None) -> CompletedCommand``
where :class:`CompletedCommand` exposes ``returncode`` (int), ``stdout`` (str),
``stderr`` (str). Every OpenCode invocation is routed through this seam.

Errors
------
:class:`OpenCodeRunnerError` — misconfiguration that must not proceed to a spawn:
a **missing model credential** at run time (message names the reference, never a
value) and a **missing connector config**. A *normal* run failure (non-zero exit
or no tests produced) is **not** an exception: it returns a non-``"ok"``
:class:`~runner.authoring.AgentRunOutput` with a **secret-scrubbed** ``detail``.
"""

from __future__ import annotations

import copy
import fnmatch
import json
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Protocol

from runner.authoring import AgentRunOutput, AuthoringInvocation

# --------------------------------------------------------------------------- #
# Module constants (binding names / values)
# --------------------------------------------------------------------------- #

#: runner/opencode_runner.py -> parents[1] == repo root.
REPO_ROOT = Path(__file__).resolve().parents[1]

#: The model OpenCode drives — a bumpable config value (override at construction).
DEFAULT_MODEL = "openai/gpt-4o-mini"

#: Platform model-credential **reference name** (DESIGN.md §11.5). Never a value.
OPENAI_API_KEY_ENV = "OPENAI_API_KEY"

#: Repo-root-relative path to the shipped OpenCode connector config.
OPENCODE_CONFIG_PATH = "connectors/opencode/opencode.json"

#: The pinned OpenCode CLI binary name (DESIGN.md §11.10 supply-chain).
OPENCODE_BIN = "opencode"

#: Product sub-agent identities (align with the invocation's fields).
PLANNER_AGENT = "qa-planner"
GENERATOR_AGENT = "qa-generator"

#: Glob patterns used to collect generated tests from the run workspace.
CAPTURE_GLOBS = ("**/*.spec.ts", "**/*.test.ts", "**/*.api.spec.ts")

#: OpenCode's config-discovery env var (child env points it at the connector config).
OPENCODE_CONFIG_ENV = "OPENCODE_CONFIG"

#: OpenCode's headless auto-approve-tool-permissions flag (AF1).
OPENCODE_AUTO_FLAG = "--auto"

#: OpenCode's workspace/root directory flag (AF1) -- must equal the call's ``cwd``.
OPENCODE_DIR_FLAG = "--dir"

#: OpenCode's continue-session flag (AF2) -- carries the Planner's plan/session into
#: the Generator's invocation. Only ever placed on the second (Generator) call.
OPENCODE_CONTINUE_FLAG = "--continue"

#: The materialized, workspace-local config's filename (shared by both invocations
#: of one run; lives at the workspace root, alongside the ``cwd`` OpenCode is given).
MATERIALIZED_CONFIG_FILENAME = "opencode.json"

#: Matches OpenCode's ``{file:<path>}`` config-value convention.
_FILE_REF_RE = re.compile(r"\{file:([^}]+)\}")


# --------------------------------------------------------------------------- #
# Named adapter error
# --------------------------------------------------------------------------- #


class OpenCodeRunnerError(Exception):
    """Adapter misconfiguration that must not proceed to an OpenCode spawn.

    Raised for a **missing model credential** at run time (message names the
    ``OPENAI_API_KEY`` reference, never a secret value) and for a **missing
    connector config**. A normal run failure is **not** an exception — see
    module docstring.
    """


# --------------------------------------------------------------------------- #
# Command-runner seam (the injectable interface)
# --------------------------------------------------------------------------- #


@dataclass
class CompletedCommand:
    """Result of a completed OpenCode invocation (binding attribute names)."""

    returncode: int
    stdout: str = ""
    stderr: str = ""


class CommandRunner(Protocol):
    """Injectable command-runner seam.

    A single callable the adapter routes every OpenCode invocation through, so
    unit-8's real runner and unit-7's mock both satisfy it.
    """

    def __call__(  # pragma: no cover - structural protocol
        self,
        argv: list[str],
        *,
        cwd: str,
        env: Mapping[str, str],
        input: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> CompletedCommand:
        ...


def default_command_runner(
    argv: list[str],
    *,
    cwd: str,
    env: Mapping[str, str],
    input: Optional[str] = None,
    timeout: Optional[float] = None,
) -> CompletedCommand:
    """The real (subprocess-backed) command-runner. NOT exercised by unit tests.

    Spawns the OpenCode CLI. Present so a default construction works end-to-end
    in unit 8; unit-7 tests always inject a fake and never reach this path.
    """
    proc = subprocess.run(  # pragma: no cover - never run in unit tests
        list(argv),
        cwd=cwd,
        env=dict(env),
        input=input,
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    return CompletedCommand(
        returncode=proc.returncode, stdout=proc.stdout or "", stderr=proc.stderr or ""
    )


# --------------------------------------------------------------------------- #
# The adapter
# --------------------------------------------------------------------------- #


class OpenCodeRunner:
    """A concrete ``AgentRunner`` that drives OpenCode to author tests.

    Instances are callable ``(AuthoringInvocation) -> AgentRunOutput`` so the
    unit-6 glue can drive them directly.

    Constructor knobs (all keyword, all with working defaults):

    * ``command_runner`` — the injected command-runner seam
      (default :func:`default_command_runner`; unit tests inject a fake).
    * ``model`` — default :data:`DEFAULT_MODEL` (``openai/gpt-4o-mini``).
    * ``opencode_config_path`` — default :data:`OPENCODE_CONFIG_PATH`.
    * ``workspace_dir`` — default ``None`` (a per-run temp workspace is created,
      distinct from ``invocation.output_dir``).
    * ``credential_env`` — default :data:`OPENAI_API_KEY_ENV`.
    * ``opencode_bin`` — default :data:`OPENCODE_BIN`.
    * ``timeout`` — optional per-run timeout forwarded to the command-runner.
    """

    def __init__(
        self,
        *,
        command_runner: Optional[CommandRunner] = None,
        model: str = DEFAULT_MODEL,
        opencode_config_path: str = OPENCODE_CONFIG_PATH,
        workspace_dir: Optional[str] = None,
        credential_env: str = OPENAI_API_KEY_ENV,
        opencode_bin: str = OPENCODE_BIN,
        timeout: Optional[float] = None,
    ) -> None:
        self._command_runner: CommandRunner = command_runner or default_command_runner
        self.model = model
        self.opencode_config_path = opencode_config_path
        self.workspace_dir = workspace_dir
        self.credential_env = credential_env
        self.opencode_bin = opencode_bin
        self.timeout = timeout

    # -- config resolution --------------------------------------------------- #

    def _resolve_config_path(self) -> Path:
        """Resolve + verify the governing OpenCode connector config path."""
        raw = Path(self.opencode_config_path)
        path = raw if raw.is_absolute() else (REPO_ROOT / raw)
        if not path.is_file():
            raise OpenCodeRunnerError(
                f"OpenCode connector config not found: {path}"
            )
        return path

    # -- workspace ----------------------------------------------------------- #

    def _make_workspace(self, invocation: AuthoringInvocation) -> Path:
        """Create/return a run workspace distinct from ``invocation.output_dir``."""
        if self.workspace_dir is not None:
            ws = Path(self.workspace_dir)
            ws.mkdir(parents=True, exist_ok=True)
        else:
            ws = Path(tempfile.mkdtemp(prefix="opencode-ws-"))
        # Guarantee the single-writer rule: never the glue's output_dir.
        if ws.resolve() == Path(invocation.output_dir).resolve():
            raise OpenCodeRunnerError(
                "run workspace must be distinct from the invocation output_dir"
            )
        return ws

    # -- message assembly ---------------------------------------------------- #

    @staticmethod
    def _compose_message(invocation: AuthoringInvocation, role: str) -> str:
        """Assemble the deterministic run message for a role.

        Delivers ``invocation.system_prompt`` (BRD already injected upstream —
        the token is **not** re-injected here), the ``target_url``, and the seven
        ``planner_fields``. Carries only the Basic-Auth **reference name** — never
        a resolved secret — UNLESS ``invocation.basic_auth_credential_value`` has
        been explicitly, opt-in set (a narrow, documented carve-out; see
        ``runner/README.md``), in which case the resolved value is additionally
        included so the agent can submit it through a real login form. The default
        (``None``) path is byte-identical to the pre-carve-out behavior.
        """
        fields = "\n".join(
            f"- {key}: {value}" for key, value in invocation.planner_fields.items()
        )
        message = (
            f"{invocation.system_prompt}\n\n"
            f"## Active role\n{role}\n\n"
            f"## Target application\n{invocation.target_url}\n\n"
            f"## Structured planner fields\n{fields}\n\n"
            "## Target-app authentication\n"
            "Basic-Auth is provided at runtime via the credential reference "
            f"{invocation.basic_auth_credential_ref!r} (reference name only).\n"
        )
        credential_value = getattr(invocation, "basic_auth_credential_value", None)
        if credential_value is not None:
            message += (
                "The resolved credential value for this run is "
                f"{credential_value!r} — use it to submit the target app's login "
                "form (username/password Basic-Auth) so you can explore the "
                "authenticated parts of the app.\n"
            )
        return message

    # -- credential ------------------------------------------------------------ #

    def _require_credential(self) -> str:
        """Verify the model credential reference is set BEFORE any spawn (named error)."""
        key = os.environ.get(self.credential_env)
        if not key:
            raise OpenCodeRunnerError(
                f"model credential reference {self.credential_env!r} is unset; "
                "refusing to spawn OpenCode"
            )
        return key

    # -- env ----------------------------------------------------------------- #

    def _build_env(self, materialized_config_path: Path) -> dict[str, str]:
        """Build the child env: inherit, inject the model key + config discovery.

        The model key is injected here (child env) **only**. It is never placed in
        argv, the message/prompt, logs, or the returned output. ``OPENCODE_CONFIG``
        points at the run's **materialized, workspace-local** config (AF3) -- never
        at the shipped ``connectors/opencode/opencode.json`` path.
        """
        key = self._require_credential()
        env = dict(os.environ)
        env[self.credential_env] = key
        env[OPENCODE_CONFIG_ENV] = str(materialized_config_path)
        return env

    # -- config materialization (AF3, AF4) ------------------------------------ #

    def _materialize_ref(self, raw_ref: str, config_dir: Path, workspace: Path) -> None:
        """Copy the file a config-relative ref points at into the workspace.

        The ref (an ``instructions`` entry or the inner path of a ``{file:...}``
        value) is resolved -- preferring :data:`REPO_ROOT` (the shipped config's
        real convention; the shipped config's own directory does not contain
        these files), falling back to the governing config's own directory -- and
        copied byte-for-byte to the *same relative path* under the workspace, so
        that resolving the (unchanged) ref string relative to the materialized
        config's own parent directory (the workspace root) lands on an
        byte-identical, in-workspace copy.
        """
        rel = raw_ref[2:] if raw_ref.startswith("./") else raw_ref
        rel_path = Path(rel)
        if rel_path.is_absolute():
            return
        for base in (REPO_ROOT, config_dir):
            candidate = base / rel_path
            if candidate.is_file():
                dest = workspace / rel_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(candidate.read_bytes())
                return

    def _materialize_file_refs(self, obj: Any, config_dir: Path, workspace: Path) -> None:
        """Recursively copy every ``{file:...}``-referenced file into the workspace.

        These are the agent-role definitions (``agent.*.prompt``, e.g.
        ``.opencode/agent/qa-planner.md`` / ``qa-generator.md``) -- static
        instructions that never change at runtime, so a byte-identical copy is
        correct (AF3a).
        """
        if isinstance(obj, dict):
            for value in obj.values():
                self._materialize_file_refs(value, config_dir, workspace)
        elif isinstance(obj, list):
            for value in obj:
                self._materialize_file_refs(value, config_dir, workspace)
        elif isinstance(obj, str):
            match = _FILE_REF_RE.search(obj)
            if match:
                self._materialize_ref(match.group(1), config_dir, workspace)

    @staticmethod
    def _materialize_instruction(raw_ref: str, workspace: Path, system_prompt: str) -> None:
        """Write this run's injected system prompt at an ``instructions`` entry's path.

        The shipped ``agent_config/qa_system_prompt.md`` referenced by
        ``instructions`` is the raw, unresolved **template** (it still carries the
        literal ``{{BRD}}`` placeholder -- substituted upstream by unit 6's glue).
        Byte-copying that template into the workspace would reintroduce the
        unresolved token into agent-visible surfaces. Instead, each
        ``instructions`` entry resolves (relative to the materialized config's own
        parent directory) to a workspace-local file containing THIS run's already
        BRD-injected, token-free ``invocation.system_prompt`` (AF3b).
        """
        rel = raw_ref[2:] if raw_ref.startswith("./") else raw_ref
        rel_path = Path(rel)
        if rel_path.is_absolute():
            return
        dest = workspace / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(system_prompt, encoding="utf-8")

    def _materialize_config(
        self, workspace: Path, config_path: Path, invocation: AuthoringInvocation
    ) -> Path:
        """Materialize a workspace-local copy of the governing config (AF3, AF4).

        Reads (never writes) the shipped/custom ``config_path``, preserves its
        ``model``/``mcp`` content unchanged, forces
        ``permission.external_directory == "deny"`` (AF4, always -- regardless of
        what the input config declares), writes each ``instructions`` entry as
        this run's injected ``invocation.system_prompt`` (AF3b), copies every
        ``{file:...}``-referenced agent-role file byte-identically into the
        workspace (AF3a; mirroring its relative path so the unchanged ref string
        still resolves), and writes the result to a single, workspace-local JSON
        file shared by every invocation of this run.
        """
        shipped = json.loads(config_path.read_text(encoding="utf-8"))
        materialized = copy.deepcopy(shipped)

        permission = dict(materialized.get("permission") or {})
        permission["external_directory"] = "deny"
        materialized["permission"] = permission

        config_dir = config_path.parent
        for entry in materialized.get("instructions") or []:
            if isinstance(entry, str):
                self._materialize_instruction(entry, workspace, invocation.system_prompt)
        self._materialize_file_refs(materialized, config_dir, workspace)

        materialized_path = workspace / MATERIALIZED_CONFIG_FILENAME
        materialized_path.write_text(
            json.dumps(materialized, indent=2), encoding="utf-8"
        )
        return materialized_path

    # -- argv ---------------------------------------------------------------- #

    def _build_argv(
        self, message: str, agent: str, workspace: Path, *, continue_session: bool
    ) -> list[str]:
        argv = [
            self.opencode_bin,
            "run",
            message,
            "--model",
            self.model,
            "--agent",
            agent,
            OPENCODE_AUTO_FLAG,
            OPENCODE_DIR_FLAG,
            str(workspace),
        ]
        if continue_session:
            argv.append(OPENCODE_CONTINUE_FLAG)
        return argv

    # -- capture ------------------------------------------------------------- #

    def _collect_tests(self, workspace: Path) -> dict[str, str]:
        """Collect workspace files matching the pinned globs (rel filename -> content)."""
        collected: dict[str, str] = {}
        for path in sorted(workspace.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(workspace).as_posix()
            if any(_glob_match(rel, glob) for glob in CAPTURE_GLOBS):
                collected[rel] = path.read_text(encoding="utf-8")
        return collected

    # -- scrubbing ----------------------------------------------------------- #

    def _scrub(self, text: str) -> str:
        """Remove the resolved model-credential value from any human-facing text."""
        if not text:
            return text
        key = os.environ.get(self.credential_env)
        if key:
            text = text.replace(key, "***")
        return text

    # -- the seam ------------------------------------------------------------ #

    def __call__(self, invocation: AuthoringInvocation) -> AgentRunOutput:
        # 1. Governing config must exist (misconfiguration -> named error).
        config_path = self._resolve_config_path()

        # 2. Model credential must be present BEFORE any spawn (named error).
        self._require_credential()

        # 3. Per-run workspace, distinct from output_dir (single-writer rule).
        workspace = self._make_workspace(invocation)

        # 4. Materialize a workspace-local config (AF3, AF4) -- one per run, shared
        #    by both invocations -- and the child env pointing at it.
        materialized_config_path = self._materialize_config(
            workspace, config_path, invocation
        )
        env = self._build_env(materialized_config_path)

        # 5. Drive Planner -> Generator (two ordered runs), sharing the workspace.
        #    `--auto` + `--dir <workspace>` on every call (AF1); the continue-session
        #    flag only on the second (Generator) call (AF2).
        runs = (
            (PLANNER_AGENT, invocation.planner_agent or PLANNER_AGENT),
            (GENERATOR_AGENT, invocation.generator_agent or GENERATOR_AGENT),
        )
        for index, (role_label, agent) in enumerate(runs):
            message = self._compose_message(invocation, role_label)
            argv = self._build_argv(
                message, agent, workspace, continue_session=(index > 0)
            )
            result = self._command_runner(
                argv,
                cwd=str(workspace),
                env=env,
                input=None,
                timeout=self.timeout,
            )
            if result.returncode != 0:
                detail = self._scrub(
                    f"OpenCode {agent} run failed (exit {result.returncode})"
                    + (f": {result.stderr.strip()}" if result.stderr else "")
                )
                return AgentRunOutput(status="error", generated_tests={}, detail=detail)

        # 5. Capture generated tests from the workspace.
        generated_tests = self._collect_tests(workspace)
        if not generated_tests:
            return AgentRunOutput(
                status="error",
                generated_tests={},
                detail="OpenCode run produced no capturable test files",
            )

        return AgentRunOutput(status="ok", generated_tests=generated_tests, detail=None)


def _glob_match(rel: str, glob: str) -> bool:
    """Match a workspace-relative posix path against a ``**``-aware glob."""
    if glob.startswith("**/"):
        tail = glob[3:]
        return fnmatch.fnmatch(rel, tail) or fnmatch.fnmatch(rel, glob) or fnmatch.fnmatch(
            rel, "*/" + tail
        ) or fnmatch.fnmatch(Path(rel).name, tail)
    return fnmatch.fnmatch(rel, glob)


def make_opencode_runner(**knobs) -> OpenCodeRunner:
    """Thin factory returning a configured :class:`OpenCodeRunner`."""
    return OpenCodeRunner(**knobs)

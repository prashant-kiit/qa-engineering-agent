"""Shared test helpers for the ``p1-opencode-runner`` acceptance suite (TDD red).

Lives in a **uniquely-named** module (NOT ``conftest``) so importing these symbols
(``from opencode_helpers import ...``) is unambiguous even when the whole repo test
suite is collected together — two bare ``conftest`` modules collide under pytest's
prepend importmode, so shared constants + the mock command-runner must NOT be imported
via ``from conftest import ...`` (import-hygiene lesson from the unit-6 suite).

Everything here is **offline**: no model key, no network, no browser, and **no real
OpenCode process**. The OpenCode CLI is exercised only through an **injected mock
command-runner** (:class:`FakeCommandRunner`) that records the argv/cwd/env/input it
receives and can simulate success (writing canned test files into the run workspace),
a non-zero exit, or a zero-exit-with-no-tests run — it never spawns a process.

The module under test is imported **lazily** (see :func:`import_adapter`) so that, before
the implementation exists, each adapter test fails individually with a clear
``ImportError`` (legitimate TDD red for the missing ``runner.opencode_runner`` module).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from runner.authoring import AuthoringInvocation  # unit-6 seam type (exists)

# Repo root: runner/tests/opencode_helpers.py -> parents[2] == repo root.
REPO_ROOT = Path(__file__).resolve().parents[2]

# Pinned (read-only) referenced artifacts.
QA_PROMPT_PATH = REPO_ROOT / "agent_config" / "qa_system_prompt.md"
MCP_CONFIG_REL = "connectors/mcp/playwright.mcp.json"
OPENCODE_CONFIG_REL = "connectors/opencode/opencode.json"
OPENCODE_PLANNER_DEF = REPO_ROOT / ".opencode" / "agent" / "qa-planner.md"
OPENCODE_GENERATOR_DEF = REPO_ROOT / ".opencode" / "agent" / "qa-generator.md"

# Pinned facts from the spec / unit-3 config.
PINNED_MCP_SERVER = "@playwright/mcp@0.0.41"
EXPECTED_MODEL = "openai/gpt-4o-mini"
OPENAI_KEY_ENV = "OPENAI_API_KEY"

# Distinctive sentinels that must never leak into any agent-visible surface.
MODEL_KEY_SENTINEL = "OPENAI-KEY-SENTINEL-DO-NOT-LEAK-7f3a1c"
AUTH_SENTINEL = "BASIC-AUTH-SENTINEL-DO-NOT-LEAK-9c1f2a"

# Reference (name only) for the target-app Basic-Auth credential.
AUTH_REF_NAME = "REF_APP_BASIC_AUTH"

# Unique markers embedded in the crafted invocation so we can assert delivery.
SYS_PROMPT_MARKER = "SYS-PROMPT-MARKER-8a71f-do-not-remove"
BRD_CONTENT_MARKER = "BRD-CONTENT-MARKER-4d2e9-injected-body"
TARGET_URL_MARKER = "http://target.example.test:5173/shop-xyz"
BRD_TOKEN = "{{BRD}}"

# The seven structured Planner fields, each with a uniquely-identifiable value.
PLANNER_FIELD_MARKERS = {
    "target_scope": "SCOPE-MARKER-storefront-browse-cart-checkout",
    "intent": "INTENT-MARKER-shopper-completes-purchase",
    "expected_behavior": "BEHAVIOR-MARKER-cart-totals-and-order-id",
    "priority_risk": "RISK-MARKER-payment-and-arithmetic",
    "test_data_preconditions": "PRECOND-MARKER-seeded-catalog-user",
    "out_of_scope_constraints": "OOS-MARKER-no-real-payment-gateway",
    # `depth` is a constrained enum in unit-2 (`{smoke, regression, exhaustive}`); it must
    # be a valid value (not a sentinel marker) because C1/C10 push these fields through the
    # real glue. `"regression"` is still assertable in the delivered surface (C5).
    "depth": "regression",
}

# Canned "generated" test files the mock writes into the workspace on success.
CANNED_TESTS = {
    "cart.spec.ts": "// cart e2e test\nimport { test } from '@playwright/test';\n",
    "orders.api.spec.ts": "// orders api test\nimport { test } from '@playwright/test';\n",
}


def make_invocation(output_dir, *, system_prompt=None, target_url=None) -> AuthoringInvocation:
    """Build an :class:`AuthoringInvocation` directly, with unique, assertable markers.

    ``system_prompt`` mimics the glue's output: the generic QA prompt (a stable version
    marker) with the per-run BRD **already injected** (a BRD body marker) and **no**
    residual ``{{BRD}}`` token — the adapter must not re-inject or re-author it.
    """
    sp = system_prompt if system_prompt is not None else (
        "<!-- QA_SYSTEM_PROMPT_VERSION: v1 -->\n"
        f"{SYS_PROMPT_MARKER}\n"
        "You are a senior QA engineer. Reliability rules: DOM_GROUNDING, "
        "MEANINGFUL_ASSERTIONS, API_CROSS_CHECK.\n\n"
        "## Per-run BRD\n"
        f"injected business context: {BRD_CONTENT_MARKER}\n"
    )
    return AuthoringInvocation(
        system_prompt=sp,
        api_surface={
            "base_url": "http://127.0.0.1:8000",
            "endpoints": [{"method": "GET", "path": "/cart", "operation_id": "getCart"}],
        },
        target_url=target_url if target_url is not None else TARGET_URL_MARKER,
        planner_fields=dict(PLANNER_FIELD_MARKERS),
        mcp_config_path=MCP_CONFIG_REL,
        planner_agent="qa-planner",
        generator_agent="qa-generator",
        basic_auth_credential_ref=AUTH_REF_NAME,
        output_dir=str(output_dir),
    )


# --------------------------------------------------------------------------- #
# Mock command-runner (the injected seam substitute — never spawns a process)
# --------------------------------------------------------------------------- #
#
# NAMING / SHAPE ASSUMPTIONS (recorded in p1-opencode-runner.tests.md):
#   * OpenCodeRunner routes EVERY OpenCode invocation through an injected callable
#     `command_runner(argv, *, cwd, env, input=None, timeout=None) -> CompletedCommand`.
#   * CompletedCommand exposes `.returncode` (int), `.stdout` (str), `.stderr` (str).
#   * The constructor accepts keyword `command_runner=`.
# These are the spec's pinned command-runner seam facts; the developer must honor them.


@dataclass
class FakeCompleted:
    """Stand-in for the adapter's ``CompletedCommand`` result (binding attr names)."""

    returncode: int = 0
    stdout: str = ""
    stderr: str = ""


class FakeCommandRunner:
    """A mock command-runner: records every call; optionally writes canned tests.

    * ``mode="ok"``   — exit 0 and write ``files`` into the run ``cwd`` (drives 9/10/17).
    * ``mode="fail"`` — non-zero exit with ``stderr`` and no files (drives 14).
    * ``mode="empty"``— exit 0 but write no files (drives 15).

    Never spawns a real process.
    """

    def __init__(self, *, mode="ok", files=None, returncode=None, stderr=""):
        self.mode = mode
        self.files = dict(files if files is not None else CANNED_TESTS)
        self.stderr = stderr
        if returncode is not None:
            self._rc = returncode
        else:
            self._rc = 3 if mode == "fail" else 0
        self.calls = []  # list of {argv, cwd, env, input, timeout}

    def __call__(self, argv, *, cwd, env, input=None, timeout=None):
        self.calls.append(
            {
                "argv": list(argv),
                "cwd": str(cwd),
                "env": dict(env),
                "input": input,
                "timeout": timeout,
            }
        )
        if self.mode == "ok" and self._rc == 0:
            base = Path(cwd)
            for rel, content in self.files.items():
                dest = base / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(content, encoding="utf-8")
        return FakeCompleted(returncode=self._rc, stdout="", stderr=self.stderr)

    @property
    def called(self) -> bool:
        return bool(self.calls)


# --------------------------------------------------------------------------- #
# Lazy import of the module under test (missing at TDD-red time)
# --------------------------------------------------------------------------- #


def import_adapter():
    """Import ``runner.opencode_runner`` lazily so each test reds on the missing module."""
    import importlib

    return importlib.import_module("runner.opencode_runner")


# --------------------------------------------------------------------------- #
# Surface-collection helpers (what the agent/OpenCode can actually see)
# --------------------------------------------------------------------------- #


def agent_visible_text(mock: FakeCommandRunner) -> str:
    """Concatenate every agent-visible surface across all recorded calls.

    Includes: argv, piped stdin, and every file present under each call's ``cwd``
    workspace (adapter-materialized instructions / config / canned outputs). **Excludes
    the child env** — the child env is where the model key legitimately lives, so it must
    be excluded from any "secret must be absent" scan.
    """
    parts: list[str] = []
    for call in mock.calls:
        parts.append(" ".join(call["argv"]))
        if call["input"]:
            parts.append(str(call["input"]))
        ws = Path(call["cwd"])
        if ws.is_dir():
            for p in sorted(ws.rglob("*")):
                if p.is_file():
                    try:
                        parts.append(p.read_text(encoding="utf-8"))
                    except (OSError, UnicodeDecodeError):
                        pass
    return "\n".join(parts)


def output_text(output) -> str:
    """Every human/artifact-facing surface of an ``AgentRunOutput`` as one string."""
    parts = [str(getattr(output, "status", "")), str(getattr(output, "detail", "") or "")]
    for k, v in dict(getattr(output, "generated_tests", {}) or {}).items():
        parts.append(str(k))
        parts.append(str(v))
    return "\n".join(parts)


def model_arg(argv) -> str | None:
    """Return the value selected via ``--model`` (space or ``=`` form), if present."""
    for i, a in enumerate(argv):
        if a == "--model" and i + 1 < len(argv):
            return argv[i + 1]
        if a.startswith("--model="):
            return a.split("=", 1)[1]
        if a in ("-m",) and i + 1 < len(argv):
            return argv[i + 1]
    return None


def agent_flags_in_order(mock: FakeCommandRunner) -> list[str]:
    """All ``--agent <name>`` values across calls, in invocation order."""
    out: list[str] = []
    for call in mock.calls:
        argv = call["argv"]
        for i, a in enumerate(argv):
            if a == "--agent" and i + 1 < len(argv):
                out.append(argv[i + 1])
            elif a.startswith("--agent="):
                out.append(a.split("=", 1)[1])
    return out


def governing_config(mock: FakeCommandRunner):
    """Resolve + parse the OpenCode config governing the run (any pinned discovery form).

    Preference order: ``OPENCODE_CONFIG`` env var → ``--config <path>`` flag → an
    ``opencode.json`` copied into the run workspace cwd. Returns the parsed JSON dict, or
    ``None`` if no governing config could be resolved.
    """
    for call in mock.calls:
        env = call["env"]
        argv = call["argv"]
        cfg = env.get("OPENCODE_CONFIG")
        if cfg and Path(cfg).is_file():
            return json.loads(Path(cfg).read_text(encoding="utf-8"))
        if "--config" in argv:
            i = argv.index("--config")
            if i + 1 < len(argv) and Path(argv[i + 1]).is_file():
                return json.loads(Path(argv[i + 1]).read_text(encoding="utf-8"))
        ws_cfg = Path(call["cwd"]) / "opencode.json"
        if ws_cfg.is_file():
            return json.loads(ws_cfg.read_text(encoding="utf-8"))
    return None


def normalize_argv(argv, cwd) -> list[str]:
    """Replace the per-run workspace path in argv with a stable placeholder (for 17)."""
    return [a.replace(str(cwd), "<WS>") for a in argv]

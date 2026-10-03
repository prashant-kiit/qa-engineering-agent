# Acceptance suite for p1-mcp-config (TDD red).
#
# Encodes acceptance criteria 1-15 from .harness/tasks/p1-mcp-config.md against the
# committed Playwright-MCP config artifact. Written WITHOUT reading any implementation
# (unbiased TDD red).
#
# The config artifact does NOT exist yet (connectors/mcp/playwright.mcp.json is absent),
# so every test that consumes it fails for the RIGHT reason (missing file / missing keys),
# not broken scaffolding. Unit-1's test_spec_loader.py and unit-2's test_target_config.py
# are untouched and still pass.
#
# ALL tests are purely STATIC: they read + parse the committed file (and connectors/README.md)
# and assert on contents. No MCP server is launched, no browser is spawned, no npx/Node is
# invoked, and no network I/O is performed.
#
# ASSUMPTIONS the developer MUST honor (recorded in p1-mcp-config.tests.md). The spec pins
# these as BINDING contract:
#   - config path (binding):    connectors/mcp/playwright.mcp.json
#   - top-level key (binding):  "mcpServers" -> object map
#   - server key (binding):     "playwright"
#   - launch shape (binding):   "command" (non-empty str) + "args" (list[str])
#   - package (binding):        @playwright/mcp
#   - version (binding form):   exact @playwright/mcp@X.Y.Z (no latest / range / tag / bare)
# Developer-choice details asserted only at the spec's documented requirement level:
#   - concrete `command` launcher token (e.g. npx) is NOT pinned by the spec -> not asserted
#   - browser-engine token is developer's choice from the supported set -> asserted as
#     "some concrete engine present", not a specific literal
#   - arg ordering is developer's choice -> not asserted

import json
import re
from pathlib import Path

import pytest

# ---- repo layout -------------------------------------------------------------------------
# connectors/tests/<thisfile> -> parents[2] == repo root
REPO_ROOT = Path(__file__).resolve().parents[2]

# BINDING path from Interfaces §Paths.
CONFIG_PATH = REPO_ROOT / "connectors" / "mcp" / "playwright.mcp.json"
README_PATH = REPO_ROOT / "connectors" / "README.md"

# BINDING identity from Interfaces §Server entry.
PACKAGE = "@playwright/mcp"
SERVER_KEY = "playwright"

# Known Playwright browser-engine tokens (criterion 10): a concrete engine must be one of
# the server's supported set. The exact choice is the developer's.
BROWSER_ENGINES = ("chromium", "firefox", "webkit", "chrome", "msedge")

# Floating / unpinned specifier fragments forbidden by §11.10 (criterion 8).
FLOATING_TOKENS = ("^", "~", "*", ">=", "<=", ">", "<", "||", "@latest", "@next")

# Target-agnostic forbidden substrings (criterion 13): the reference-app URLs / ports and
# any baked credential value must NOT appear. These belong in the unit-2 per-run config.
FORBIDDEN_SUBSTRINGS = (
    "127.0.0.1:5173",
    "127.0.0.1:8000",
    "localhost:5173",
    "localhost:8000",
    ":5173",
    ":8000",
)


# ---- helpers -----------------------------------------------------------------------------
def _load_config():
    """Read + parse the committed config file. Absent file / bad JSON is the red reason."""
    assert CONFIG_PATH.exists(), (
        f"Config file missing at pinned path {CONFIG_PATH.relative_to(REPO_ROOT)} "
        "(criterion 1)."
    )
    raw = CONFIG_PATH.read_text(encoding="utf-8")
    return json.loads(raw)


def _server_def(config):
    servers = config["mcpServers"]
    return servers[SERVER_KEY]


def _launch_tokens(server):
    """All strings that make up the launch surface (command + args), for token scanning."""
    tokens = []
    cmd = server.get("command")
    if isinstance(cmd, str):
        tokens.append(cmd)
    args = server.get("args")
    if isinstance(args, list):
        tokens.extend(a for a in args if isinstance(a, str))
    return tokens


def _package_ref(server):
    """The single launch token that references @playwright/mcp, or None."""
    for tok in _launch_tokens(server):
        if PACKAGE in tok:
            return tok
    return None


def _all_string_values(obj):
    """Recursively collect every string value in the server definition (for option scans)."""
    out = []
    if isinstance(obj, str):
        out.append(obj)
    elif isinstance(obj, list):
        for x in obj:
            out.extend(_all_string_values(x))
    elif isinstance(obj, dict):
        for k, v in obj.items():
            out.append(k)
            out.extend(_all_string_values(v))
    return out


# ---- Presence & parseability -------------------------------------------------------------
def test_config_file_present_at_pinned_path():
    """Criterion 1: file exists at connectors/mcp/playwright.mcp.json."""
    assert CONFIG_PATH.exists(), (
        f"Expected config at {CONFIG_PATH.relative_to(REPO_ROOT)} (Interfaces §Paths)."
    )
    assert CONFIG_PATH.is_file()


def test_config_is_valid_json_single_top_level_object():
    """Criterion 2: parses as valid JSON with a single top-level object."""
    config = _load_config()
    assert isinstance(config, dict), "Top-level JSON value must be an object."


# ---- Shape / schema ----------------------------------------------------------------------
def test_mcpservers_map_present():
    """Criterion 3: top-level `mcpServers` key whose value is an object (map)."""
    config = _load_config()
    assert "mcpServers" in config, "Missing top-level `mcpServers` key."
    assert isinstance(config["mcpServers"], dict), "`mcpServers` must be an object map."


def test_playwright_server_declared():
    """Criterion 4: `mcpServers` contains a `playwright` server whose value is an object."""
    config = _load_config()
    servers = config["mcpServers"]
    assert SERVER_KEY in servers, "Missing `playwright` server under `mcpServers`."
    assert isinstance(servers[SERVER_KEY], dict), "`playwright` server must be an object."


def test_launch_shape_command_and_args():
    """Criterion 5: stdio launch shape -> non-empty `command` string + `args` list[str]."""
    server = _server_def(_load_config())

    assert "command" in server, "`playwright` server missing `command`."
    assert isinstance(server["command"], str), "`command` must be a string."
    assert server["command"].strip(), "`command` must be non-empty."

    assert "args" in server, "`playwright` server missing `args`."
    assert isinstance(server["args"], list), "`args` must be an array."
    assert server["args"], "`args` must be non-empty."
    assert all(isinstance(a, str) for a in server["args"]), "all `args` must be strings."


def test_optional_env_is_object_without_secret_values():
    """Criterion 5 (env clause): if present, `env` is an object with no baked secret values.

    env is by reference/name only (§11.4). We assert no obvious secret VALUE leaks: each
    value should be an env-var reference form, not a raw credential literal.
    """
    server = _server_def(_load_config())
    if "env" not in server:
        pytest.skip("optional `env` not present")
    env = server["env"]
    assert isinstance(env, dict), "`env`, if present, must be an object."
    for k, v in env.items():
        assert isinstance(v, str), f"env value for {k!r} must be a string reference."
        # A reference (name or ${VAR}) is fine; a raw credential literal is not. We forbid
        # the reference-app basic-auth credential value markers appearing here.
        assert "password" not in v.lower(), f"env {k!r} must not embed a secret value."


def test_package_reference_present():
    """Criterion 6: the official @playwright/mcp package token appears in the launch."""
    server = _server_def(_load_config())
    ref = _package_ref(server)
    assert ref is not None, (
        f"Launch (command+args) must reference the {PACKAGE!r} package."
    )


# ---- Version pinning (supply-chain, §11.10) ----------------------------------------------
def test_exact_version_pinned():
    """Criterion 7: package pinned to exact @playwright/mcp@X.Y.Z (concrete major.minor.patch)."""
    server = _server_def(_load_config())
    ref = _package_ref(server)
    assert ref is not None, "no @playwright/mcp reference to check version on."

    m = re.search(r"@playwright/mcp@(\d+\.\d+\.\d+)\b", ref)
    assert m, (
        f"Package reference {ref!r} must pin an exact @playwright/mcp@X.Y.Z version."
    )
    version = m.group(1)
    assert re.fullmatch(r"\d+\.\d+\.\d+", version), (
        f"Version {version!r} must be a concrete major.minor.patch."
    )


def test_no_floating_specifier():
    """Criterion 8: no floating/unpinned form (bare / latest / range operator / tag)."""
    server = _server_def(_load_config())
    ref = _package_ref(server)
    assert ref is not None, "no @playwright/mcp reference to check."

    # Not the bare, unversioned package name.
    assert ref != PACKAGE, f"Package must not be bare/unversioned ({PACKAGE!r})."

    # The character immediately after the package name must be `@version`, not end/other.
    after = ref.split(PACKAGE, 1)[1]
    assert after.startswith("@"), (
        f"Package reference {ref!r} must be followed by @<version> (no bare name)."
    )
    version_part = after[1:]
    # No floating tokens anywhere in the reference.
    for tok in FLOATING_TOKENS:
        assert tok not in ref, f"Package reference {ref!r} must not contain {tok!r}."
    # The version segment itself must not be a tag like `latest`/`next` and must be numeric.
    first_seg = re.split(r"[\s\"']", version_part)[0] if version_part else ""
    assert first_seg not in ("latest", "next"), (
        f"Version {version_part!r} must be a concrete pin, not a dist-tag."
    )
    assert re.match(r"^\d+\.\d+\.\d+", version_part), (
        f"Version segment {version_part!r} must start with a concrete X.Y.Z pin."
    )
    # Guard against a trailing 'x' wildcard like 0.0.x
    assert "x" not in re.split(r"[\s\"']", version_part)[0].lower(), (
        f"Version {version_part!r} must not use an `x` wildcard."
    )


# ---- Grounded-DOM-snapshot / browser options ---------------------------------------------
def test_headless_mode_declared():
    """Criterion 9: config declares headless browser mode (deterministic snapshots)."""
    server = _server_def(_load_config())
    values = " ".join(_all_string_values(server)).lower()
    assert "headless" in values, (
        "config must declare a headless browser mode (e.g. `--headless`)."
    )


def test_browser_engine_declared():
    """Criterion 10: a concrete browser engine (e.g. chromium) is declared."""
    server = _server_def(_load_config())
    tokens = [t.lower() for t in _all_string_values(server)]
    joined = " ".join(tokens)
    found = [e for e in BROWSER_ENGINES if re.search(rf"\b{e}\b", joined)]
    assert found, (
        f"config must declare a concrete browser engine, one of {BROWSER_ENGINES}."
    )


# ---- Consumable by later units -----------------------------------------------------------
def test_server_key_and_path_stable_for_consumers():
    """Criterion 11: stable `playwright` server key + launch fields at the pinned path."""
    config = _load_config()
    assert SERVER_KEY in config["mcpServers"], "server key must be exactly `playwright`."
    server = config["mcpServers"][SERVER_KEY]
    assert "command" in server and "args" in server, (
        "launch fields (command/args) must be present for consumers (units 5/6)."
    )
    assert CONFIG_PATH == REPO_ROOT / "connectors" / "mcp" / "playwright.mcp.json"


# ---- Docs --------------------------------------------------------------------------------
def test_readme_documents_config():
    """Criterion 12: connectors/README.md gains a section naming the file path + package."""
    assert README_PATH.exists(), "connectors/README.md must exist."
    text = README_PATH.read_text(encoding="utf-8")
    assert "playwright.mcp.json" in text, (
        "README must document the config file path (playwright.mcp.json)."
    )
    assert PACKAGE in text, f"README must name the pinned package {PACKAGE!r}."


# ---- Target-agnostic / no baked secrets --------------------------------------------------
def test_config_is_target_agnostic_no_urls_or_secrets():
    """Criterion 13: no target UI/API URL, port, or credential value baked into the file."""
    assert CONFIG_PATH.exists(), "config file must exist to assert target-agnosticism."
    raw = CONFIG_PATH.read_text(encoding="utf-8")
    for bad in FORBIDDEN_SUBSTRINGS:
        assert bad not in raw, (
            f"config must be target-agnostic; found forbidden substring {bad!r} "
            "(target URL/port belongs in the unit-2 per-run config)."
        )
    # No obvious baked credential value.
    assert "password" not in raw.lower(), "config must not embed a credential value."

"""Static acceptance suite for p1-subagents-planner-generator (TDD red).

Encodes the spec at .harness/tasks/p1-subagents-planner-generator.md WITHOUT
reading any implementation. This unit ships two Claude Code *product* sub-agent
definition files plus a product-agents doc — all static text artifacts — so
acceptance is entirely static: presence / YAML-frontmatter shape / pinned
`name` values / greppable markers / required textual references / role
distinctness / harness-role non-collision.

The two agent files and the doc do NOT exist yet, so criteria that read them
fail at read time (missing file) or on the missing-marker / missing-substring
assertions — the legitimate TDD-red reasons. These tests perform NO model call,
agent run, MCP start, browser launch, or network I/O; they only read/parse the
committed text files.

Frontmatter parsing: the repo has no PyYAML dependency (verified), and the spec
forbids adding one in a test. The `.claude/agents/*.md` frontmatter is a simple
flat `key: value` block delimited by `---` fences; we parse that block manually
(splitting on the leading fences and reading `key: value` lines). This matches
the schema of the five existing harness role files. Recorded as an assumption in
the coverage note.

Pinned binding paths / literals come straight from the spec's Interfaces section.
"""

from pathlib import Path

import pytest

# Repo root: this file is agent_config/tests/test_product_agents.py -> parents[2].
REPO_ROOT = Path(__file__).resolve().parents[2]

# Interfaces §Paths (binding).
PLANNER_PATH = REPO_ROOT / ".claude" / "agents" / "qa-planner.md"
GENERATOR_PATH = REPO_ROOT / ".claude" / "agents" / "qa-generator.md"
DOC_PATH = REPO_ROOT / "agent_config" / "product_agents.md"

# Pinned product `name` values (binding).
PLANNER_NAME = "qa-planner"
GENERATOR_NAME = "qa-generator"

# The five build-harness role names — product `name`s must collide with NONE.
HARNESS_ROLE_NAMES = {"tpm", "tester", "developer", "reviewer", "git-deployer"}
HARNESS_ROLE_FILES = {
    "tpm": REPO_ROOT / ".claude" / "agents" / "tpm.md",
    "tester": REPO_ROOT / ".claude" / "agents" / "tester.md",
    "developer": REPO_ROOT / ".claude" / "agents" / "developer.md",
    "reviewer": REPO_ROOT / ".claude" / "agents" / "reviewer.md",
    "git-deployer": REPO_ROOT / ".claude" / "agents" / "git-deployer.md",
}

# Interfaces §Markers (binding literal tokens).
MARKER_PLANNER = "<!-- PRODUCT_AGENT: PLANNER -->"
MARKER_GENERATOR = "<!-- PRODUCT_AGENT: GENERATOR -->"

# Required literal reference substrings (binding).
QA_PROMPT_PATH_REF = "agent_config/qa_system_prompt.md"
MCP_CONFIG_PATH_REF = "connectors/mcp/playwright.mcp.json"


# --------------------------------------------------------------------------- #
# Helpers — read committed text once per call; missing file => red for the
# right reason (the artifact does not exist yet). Frontmatter parsed manually.
# --------------------------------------------------------------------------- #
def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _parse_frontmatter(text: str) -> dict:
    """Parse the leading `---`-delimited YAML frontmatter block into a flat dict.

    The `.claude/agents/*.md` schema is a simple flat `key: value` block (as in
    the existing harness role files). We split on the leading `---` fences and
    read `key: value` lines. Raises AssertionError if the file does not open with
    a valid, closed frontmatter block — a legitimate red reason for a malformed
    or missing artifact.
    """
    assert text.startswith("---"), "file must open with a `---` frontmatter fence"
    # Everything after the opening fence, up to the next fence on its own line.
    body = text[len("---"):]
    end = body.find("\n---")
    assert end != -1, "frontmatter block is not closed with a `---` fence"
    block = body[:end]
    fields: dict[str, str] = {}
    for line in block.splitlines():
        if not line.strip() or ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


# --------------------------------------------------------------------------- #
# Presence & format (criteria 1-3)
# --------------------------------------------------------------------------- #
def test_c1_planner_file_present_nonempty_utf8():
    """C1: Planner file exists at the pinned path, non-empty, valid UTF-8."""
    assert PLANNER_PATH.is_file(), f"missing Planner agent file: {PLANNER_PATH}"
    text = _read(PLANNER_PATH)  # decoding as utf-8 asserts valid UTF-8
    assert text.strip(), "Planner file is empty"


def test_c2_generator_file_present_nonempty_utf8():
    """C2: Generator file exists at the pinned path, non-empty, valid UTF-8."""
    assert GENERATOR_PATH.is_file(), f"missing Generator agent file: {GENERATOR_PATH}"
    text = _read(GENERATOR_PATH)  # decoding as utf-8 asserts valid UTF-8
    assert text.strip(), "Generator file is empty"


def test_c3_doc_present_nonempty():
    """C3: agent_config/product_agents.md exists and is non-empty."""
    assert DOC_PATH.is_file(), f"missing product-agents doc: {DOC_PATH}"
    assert _read(DOC_PATH).strip(), "product-agents doc is empty"


# --------------------------------------------------------------------------- #
# Frontmatter shape (criteria 4-7)
# --------------------------------------------------------------------------- #
def test_c4_planner_valid_frontmatter_required_fields():
    """C4: Planner opens with a YAML frontmatter block with non-empty name/description/tools."""
    fields = _parse_frontmatter(_read(PLANNER_PATH))
    for key in ("name", "description", "tools"):
        assert key in fields, f"Planner frontmatter missing required field: {key}"
        assert fields[key], f"Planner frontmatter field {key} is empty"


def test_c5_generator_valid_frontmatter_required_fields():
    """C5: Generator opens with a YAML frontmatter block with non-empty name/description/tools."""
    fields = _parse_frontmatter(_read(GENERATOR_PATH))
    for key in ("name", "description", "tools"):
        assert key in fields, f"Generator frontmatter missing required field: {key}"
        assert fields[key], f"Generator frontmatter field {key} is empty"


def test_c6_planner_name_is_pinned_value():
    """C6: Planner frontmatter `name` equals exactly `qa-planner`."""
    fields = _parse_frontmatter(_read(PLANNER_PATH))
    assert fields.get("name") == PLANNER_NAME, (
        f"Planner name must be {PLANNER_NAME!r}, got {fields.get('name')!r}"
    )


def test_c7_generator_name_is_pinned_value():
    """C7: Generator frontmatter `name` equals exactly `qa-generator`."""
    fields = _parse_frontmatter(_read(GENERATOR_PATH))
    assert fields.get("name") == GENERATOR_NAME, (
        f"Generator name must be {GENERATOR_NAME!r}, got {fields.get('name')!r}"
    )


# --------------------------------------------------------------------------- #
# Collision avoidance / distinct from harness roles (criteria 8-11)
# --------------------------------------------------------------------------- #
def test_c8_names_do_not_collide_with_harness_roles():
    """C8: neither product `name` is any of the five harness role names."""
    planner_name = _parse_frontmatter(_read(PLANNER_PATH)).get("name")
    generator_name = _parse_frontmatter(_read(GENERATOR_PATH)).get("name")
    assert planner_name not in HARNESS_ROLE_NAMES, (
        f"Planner name {planner_name!r} collides with a harness role"
    )
    assert generator_name not in HARNESS_ROLE_NAMES, (
        f"Generator name {generator_name!r} collides with a harness role"
    )


def test_c9_product_agent_markers_present():
    """C9: each file carries its exact literal PRODUCT_AGENT marker."""
    assert MARKER_PLANNER in _read(PLANNER_PATH), (
        f"Planner file missing marker: {MARKER_PLANNER}"
    )
    assert MARKER_GENERATOR in _read(GENERATOR_PATH), (
        f"Generator file missing marker: {MARKER_GENERATOR}"
    )


def test_c10_each_file_self_identifies_as_product_agent():
    """C10: each file declares itself a product agent (case-insensitive `product` + its marker)."""
    planner = _read(PLANNER_PATH)
    generator = _read(GENERATOR_PATH)
    assert "product" in planner.lower(), "Planner must self-identify as a product agent"
    assert MARKER_PLANNER in planner
    assert "product" in generator.lower(), "Generator must self-identify as a product agent"
    assert MARKER_GENERATOR in generator


def test_c11_harness_role_files_unchanged_and_present():
    """C11: the five harness role files still exist with their original `name` values."""
    for role_name, path in HARNESS_ROLE_FILES.items():
        assert path.is_file(), f"harness role file missing: {path}"
        fields = _parse_frontmatter(_read(path))
        assert fields.get("name") == role_name, (
            f"harness role file {path.name} name changed: expected {role_name!r}, "
            f"got {fields.get('name')!r}"
        )
    # The product names must not appear as any harness role file's `name`.
    harness_names = {
        _parse_frontmatter(_read(p)).get("name") for p in HARNESS_ROLE_FILES.values()
    }
    assert PLANNER_NAME not in harness_names
    assert GENERATOR_NAME not in harness_names


# --------------------------------------------------------------------------- #
# Required references — bind to prompt & grounding sources (criteria 12-14)
# --------------------------------------------------------------------------- #
def test_c12_both_reference_qa_system_prompt_path():
    """C12: each file contains the exact QA system prompt path substring."""
    assert QA_PROMPT_PATH_REF in _read(PLANNER_PATH), (
        f"Planner must reference {QA_PROMPT_PATH_REF}"
    )
    assert QA_PROMPT_PATH_REF in _read(GENERATOR_PATH), (
        f"Generator must reference {QA_PROMPT_PATH_REF}"
    )


def test_c13_both_reference_reliability_rules():
    """C13: each file references the reliability rules (case-insensitive `reliability`)."""
    assert "reliability" in _read(PLANNER_PATH).lower(), (
        "Planner must reference the reliability rules"
    )
    assert "reliability" in _read(GENERATOR_PATH).lower(), (
        "Generator must reference the reliability rules"
    )


def test_c14_both_reference_mcp_dom_snapshot_grounding():
    """C14: each file references Playwright MCP + the pinned MCP config path + `snapshot`."""
    for label, path in (("Planner", PLANNER_PATH), ("Generator", GENERATOR_PATH)):
        text = _read(path)
        lower = text.lower()
        assert "playwright mcp" in lower, f"{label} must reference Playwright MCP"
        assert MCP_CONFIG_PATH_REF in text, (
            f"{label} must reference the MCP config path {MCP_CONFIG_PATH_REF}"
        )
        assert "snapshot" in lower, f"{label} must reference DOM-snapshot grounding"


# --------------------------------------------------------------------------- #
# Planner role correctness (criteria 15-16)
# --------------------------------------------------------------------------- #
def test_c15_planner_produces_structured_test_plan():
    """C15: Planner body references producing a structured test plan."""
    assert "test plan" in _read(PLANNER_PATH).lower(), (
        "Planner must reference producing a structured test plan"
    )


def test_c16_planner_references_brd_and_seven_structured_fields():
    """C16: Planner references the freeform BRD and the seven structured Planner fields."""
    text = _read(PLANNER_PATH)
    lower = text.lower()
    assert "brd" in lower, "Planner must reference the freeform BRD"
    assert "structured" in lower, "Planner must reference the structured Planner fields"
    assert "field" in lower, "Planner must reference the structured fields"


# --------------------------------------------------------------------------- #
# Generator role correctness (criteria 17-18)
# --------------------------------------------------------------------------- #
def test_c17_generator_consumes_plan_outputs_ts_playwright_api():
    """C17: Generator references consuming the plan and authoring TS Playwright + API tests."""
    text = _read(GENERATOR_PATH)
    lower = text.lower()
    assert "plan" in lower, "Generator must reference consuming the Planner's plan"
    assert "typescript" in lower, "Generator must reference TypeScript"
    assert "playwright" in lower, "Generator must reference Playwright"
    assert "api" in lower, "Generator must reference API tests"


def test_c18_generator_and_planner_roles_are_distinct():
    """C18: the two files carry only their own PRODUCT_AGENT marker, not the other's."""
    planner = _read(PLANNER_PATH)
    generator = _read(GENERATOR_PATH)
    assert MARKER_GENERATOR not in planner, "Planner file must NOT carry the GENERATOR marker"
    assert MARKER_PLANNER not in generator, "Generator file must NOT carry the PLANNER marker"


# --------------------------------------------------------------------------- #
# Docs, determinism, placement (criteria 19-21)
# --------------------------------------------------------------------------- #
def test_c19_doc_names_both_agents_and_distinction():
    """C19: doc names both file paths, both `name` values, the product distinction, and the prompt."""
    doc = _read(DOC_PATH)
    assert ".claude/agents/qa-planner.md" in doc, "doc must name the Planner file path"
    assert ".claude/agents/qa-generator.md" in doc, "doc must name the Generator file path"
    assert PLANNER_NAME in doc, "doc must name the qa-planner value"
    assert GENERATOR_NAME in doc, "doc must name the qa-generator value"
    assert "product" in doc.lower(), "doc must state these are the QA product's agents"
    assert QA_PROMPT_PATH_REF in doc, "doc must reference the bound QA system prompt"


def test_c20_committed_files_are_deterministic():
    """C20: reading each committed file twice yields identical bytes."""
    for path in (PLANNER_PATH, GENERATOR_PATH, DOC_PATH):
        assert path.read_bytes() == path.read_bytes()


def test_c21_artifacts_live_at_pinned_homes():
    """C21: agent files live under .claude/agents/ and the doc under agent_config/."""
    agents_dir = REPO_ROOT / ".claude" / "agents"
    agent_config_dir = REPO_ROOT / "agent_config"
    assert PLANNER_PATH.parent == agents_dir
    assert GENERATOR_PATH.parent == agents_dir
    assert DOC_PATH.parent == agent_config_dir
    assert PLANNER_PATH.is_file() and GENERATOR_PATH.is_file() and DOC_PATH.is_file()

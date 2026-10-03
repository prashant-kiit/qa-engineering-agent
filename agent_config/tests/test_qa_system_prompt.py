"""Static acceptance suite for p1-qa-system-prompt (TDD red).

Encodes the spec at .harness/tasks/p1-qa-system-prompt.md WITHOUT reading any
implementation. This unit is a pure content artifact (the generic QA system
prompt + its README), so acceptance is entirely static: presence / shape /
marker / generic-safety checks against the committed text files.

The prompt file does NOT exist yet, so criteria that read it fail at read time
(FileNotFoundError) or on the missing-marker assertions — the legitimate TDD-red
reasons. These tests perform NO model call, agent run, browser launch, or
network I/O; they only read/parse committed text.

Pinned binding paths / literals come straight from the spec's Interfaces section.
"""

from pathlib import Path

import pytest

# Repo root: this file is agent_config/tests/test_qa_system_prompt.py -> parents[2].
REPO_ROOT = Path(__file__).resolve().parents[2]

# Interfaces §Paths (binding).
PROMPT_PATH = REPO_ROOT / "agent_config" / "qa_system_prompt.md"
README_PATH = REPO_ROOT / "agent_config" / "README.md"

# Interfaces §Markers (binding literal tokens).
VERSION_MARKER = "<!-- QA_SYSTEM_PROMPT_VERSION: v1 -->"
SECTION_PERSONA = "<!-- SECTION: PERSONA -->"
SECTION_METHODOLOGY = "<!-- SECTION: METHODOLOGY -->"
SECTION_RELIABILITY = "<!-- SECTION: RELIABILITY_RULES -->"
SECTION_STRUCTURED_FIELDS = "<!-- SECTION: STRUCTURED_FIELDS_REF -->"
SECTION_BRD_INJECTION = "<!-- SECTION: BRD_INJECTION -->"

RULE_DOM_GROUNDING = "<!-- RULE: DOM_GROUNDING -->"
RULE_MEANINGFUL_ASSERTIONS = "<!-- RULE: MEANINGFUL_ASSERTIONS -->"
RULE_API_CROSS_CHECK = "<!-- RULE: API_CROSS_CHECK -->"
RULE_HEAL_VS_REGRESSION = "<!-- RULE: HEAL_VS_REGRESSION -->"
RULE_UNTRUSTED_APP_CONTENT = "<!-- RULE: UNTRUSTED_APP_CONTENT -->"

ALL_RULE_ANCHORS = [
    RULE_DOM_GROUNDING,
    RULE_MEANINGFUL_ASSERTIONS,
    RULE_API_CROSS_CHECK,
    RULE_HEAL_VS_REGRESSION,
    RULE_UNTRUSTED_APP_CONTENT,
]

BRD_PLACEHOLDER = "{{BRD}}"

# Generic-safety forbidden substrings (criteria 17-18): reference-app specifics
# that must NEVER be baked into a tenant-agnostic committed artifact.
FORBIDDEN_TARGET_TOKENS = [
    "127.0.0.1:5173",
    "127.0.0.1:8000",
    ":5173",
    ":8000",
    "testuser",
    "testpass",
]


# --------------------------------------------------------------------------- #
# Helpers — read committed text once per call; missing file => red for the
# right reason (the artifact does not exist yet).
# --------------------------------------------------------------------------- #
def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _section_slice(text: str, anchor: str) -> str:
    """Return the text from `anchor` up to the next `<!-- SECTION:` anchor.

    Used to scope in-section assertions (e.g. the BRD placeholder must live
    inside the BRD-injection section).
    """
    start = text.index(anchor)
    rest = text[start + len(anchor):]
    nxt = rest.find("<!-- SECTION:")
    return rest if nxt == -1 else rest[:nxt]


# --------------------------------------------------------------------------- #
# Presence & format (criteria 1-2)
# --------------------------------------------------------------------------- #
def test_c1_prompt_file_present_and_nonempty_utf8():
    """C1: prompt exists at the pinned path, non-empty, valid UTF-8."""
    assert PROMPT_PATH.is_file(), f"missing prompt file: {PROMPT_PATH}"
    text = _read(PROMPT_PATH)  # decoding as utf-8 asserts valid UTF-8
    assert text.strip(), "prompt file is empty"


def test_c2_readme_present_and_nonempty():
    """C2: agent_config/README.md exists and is non-empty."""
    assert README_PATH.is_file(), f"missing README: {README_PATH}"
    assert _read(README_PATH).strip(), "README is empty"


# --------------------------------------------------------------------------- #
# Version marker (criterion 3)
# --------------------------------------------------------------------------- #
def test_c3_version_marker_v1_exact_literal():
    """C3: exact literal v1 version marker is present."""
    assert VERSION_MARKER in _read(PROMPT_PATH)


# --------------------------------------------------------------------------- #
# Required sections / named reliability rules (criteria 4-13)
# --------------------------------------------------------------------------- #
def test_c4_persona_section_anchor_present():
    """C4: persona section anchor present with non-trivial following content."""
    text = _read(PROMPT_PATH)
    assert SECTION_PERSONA in text
    assert _section_slice(text, SECTION_PERSONA).strip(), "persona section has no content"


def test_c5_methodology_section_anchor_present():
    """C5: methodology section anchor present with non-trivial following content."""
    text = _read(PROMPT_PATH)
    assert SECTION_METHODOLOGY in text
    assert _section_slice(text, SECTION_METHODOLOGY).strip(), "methodology section has no content"


def test_c6_reliability_rules_section_anchor_present():
    """C6: reliability-rules section anchor present."""
    assert SECTION_RELIABILITY in _read(PROMPT_PATH)


def test_c7_dom_grounding_rule_present():
    """C7: DOM-grounding rule anchor present."""
    assert RULE_DOM_GROUNDING in _read(PROMPT_PATH)


def test_c8_meaningful_assertions_rule_present():
    """C8: meaningful/non-vacuous assertions rule anchor present."""
    assert RULE_MEANINGFUL_ASSERTIONS in _read(PROMPT_PATH)


def test_c9_api_cross_check_rule_present():
    """C9: API cross-check anchoring rule anchor present."""
    assert RULE_API_CROSS_CHECK in _read(PROMPT_PATH)


def test_c10_heal_vs_regression_rule_present():
    """C10: self-heal-vs-regression rule anchor present."""
    assert RULE_HEAL_VS_REGRESSION in _read(PROMPT_PATH)


def test_c11_untrusted_app_content_rule_present():
    """C11: untrusted-app-content / prompt-injection-defense rule anchor present."""
    assert RULE_UNTRUSTED_APP_CONTENT in _read(PROMPT_PATH)


def test_c12_all_five_reliability_rule_anchors_present():
    """C12: the full set of five named rule anchors is present (none omitted)."""
    text = _read(PROMPT_PATH)
    missing = [anchor for anchor in ALL_RULE_ANCHORS if anchor not in text]
    assert not missing, f"missing reliability-rule anchors: {missing}"


def test_c13_structured_fields_reference_present():
    """C13: structured-fields reference section present.

    Asserts the anchor plus references to the "seven"/"structured fields" and the
    freeform "BRD" driving the Planner. Assumption (recorded in coverage note):
    the spec requires the "seven"/"structured fields" and "BRD" references be
    present; wording is the developer's, so the check is case-insensitive on those
    documented tokens and does NOT require a field-schema table.
    """
    text = _read(PROMPT_PATH)
    assert SECTION_STRUCTURED_FIELDS in text
    section = _section_slice(text, SECTION_STRUCTURED_FIELDS).lower()
    assert "seven" in section or "structured field" in section, (
        "structured-fields section must reference the seven structured Planner fields"
    )
    assert "brd" in section, "structured-fields section must reference the freeform BRD"


# --------------------------------------------------------------------------- #
# BRD-injection mechanism (criteria 14-16)
# --------------------------------------------------------------------------- #
def test_c14_brd_injection_section_anchor_present():
    """C14: BRD-injection section anchor present."""
    assert SECTION_BRD_INJECTION in _read(PROMPT_PATH)


def test_c15_brd_placeholder_present_exactly_once_in_section():
    """C15: the literal {{BRD}} placeholder appears exactly once, inside the section."""
    text = _read(PROMPT_PATH)
    assert text.count(BRD_PLACEHOLDER) == 1, (
        f"expected exactly one {BRD_PLACEHOLDER}, found {text.count(BRD_PLACEHOLDER)}"
    )
    assert SECTION_BRD_INJECTION in text
    section = _section_slice(text, SECTION_BRD_INJECTION)
    assert BRD_PLACEHOLDER in section, "{{BRD}} must live inside the BRD-injection section"


def test_c16_brd_injection_section_has_no_baked_tenant_content():
    """C16: the injection slot carries no reference-app/tenant content baked in."""
    text = _read(PROMPT_PATH)
    section = _section_slice(text, SECTION_BRD_INJECTION)
    for token in FORBIDDEN_TARGET_TOKENS:
        assert token not in section, f"baked tenant/target token in BRD section: {token!r}"


# --------------------------------------------------------------------------- #
# Generic / secret-safety (criteria 17-18)
# --------------------------------------------------------------------------- #
def test_c17_prompt_has_no_target_specific_content():
    """C17: prompt contains no reference-app URLs or Basic-Auth credential values."""
    text = _read(PROMPT_PATH)
    for token in FORBIDDEN_TARGET_TOKENS:
        assert token not in text, f"forbidden target/credential token in prompt: {token!r}"


def test_c18_no_secrets_in_prompt_or_readme():
    """C18: neither prompt nor README embeds credential/secret values."""
    for path in (PROMPT_PATH, README_PATH):
        text = _read(path)
        for token in ("testuser", "testpass"):
            assert token not in text, f"secret-like value {token!r} in {path.name}"


# --------------------------------------------------------------------------- #
# Docs (criterion 19)
# --------------------------------------------------------------------------- #
def test_c19_readme_documents_contract():
    """C19: README names the prompt path, v1, and the {{BRD}} placeholder token."""
    readme = _read(README_PATH)
    assert "agent_config/qa_system_prompt.md" in readme, "README must name the prompt path"
    assert "v1" in readme, "README must reference version v1"
    assert BRD_PLACEHOLDER in readme, "README must document the {{BRD}} placeholder"


# --------------------------------------------------------------------------- #
# Determinism (criterion 20)
# --------------------------------------------------------------------------- #
def test_c20_committed_files_are_deterministic():
    """C20: reading each committed file twice yields identical bytes."""
    for path in (PROMPT_PATH, README_PATH):
        assert path.read_bytes() == path.read_bytes()


# --------------------------------------------------------------------------- #
# Placement / static-only (criterion 21)
# --------------------------------------------------------------------------- #
def test_c21_artifacts_live_under_agent_config():
    """C21: prompt + README live under agent_config/ at the pinned paths."""
    agent_config = REPO_ROOT / "agent_config"
    assert PROMPT_PATH.parent == agent_config
    assert README_PATH.parent == agent_config
    assert PROMPT_PATH.is_file() and README_PATH.is_file()

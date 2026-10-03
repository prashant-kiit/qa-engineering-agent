"""Shared test helpers for the AF1-AF6 headless-execution-fix suite (TDD red).

Amends unit 7's ``OpenCodeRunner`` adapter per
``.harness/tasks/p1-agent-authoring-gate.md`` -> "Adapter headless-execution fix
(Interpretation #4, concrete)". Lives in a **uniquely-named** module (NOT ``conftest``)
so importing these symbols is unambiguous under pytest's prepend importmode (the same
import-hygiene lesson already recorded in ``opencode_helpers.py``).

This module is purely additive: it does not modify ``opencode_helpers.py`` or any
existing test file. It re-uses (imports, never edits) ``opencode_helpers.REPO_ROOT`` /
``OPENCODE_CONFIG_REL`` as the single source of truth for the shipped connector-config
location.

Everything here is offline: no model key, no network, no browser, no real OpenCode
process.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from opencode_helpers import OPENCODE_CONFIG_REL, REPO_ROOT

#: Absolute path to the shipped (read-only, must-stay-byte-unmodified) connector config.
SHIPPED_CONFIG_ABS = REPO_ROOT / OPENCODE_CONFIG_REL

#: Matches OpenCode's ``{file:<path>}`` config-value convention.
FILE_REF_RE = re.compile(r"\{file:([^}]+)\}")


def load_shipped_config() -> dict:
    """Parse the shipped ``connectors/opencode/opencode.json`` fresh from disk."""
    return json.loads(SHIPPED_CONFIG_ABS.read_text(encoding="utf-8"))


def resolve_file_ref(raw_ref: str) -> str:
    """Normalize a ``{file:...}`` inner path (strip a leading ``./`` if present)."""
    ref = raw_ref
    if ref.startswith("./"):
        ref = ref[2:]
    return ref


def find_file_refs(obj: Any, path: tuple = ()) -> list[tuple[tuple, str, str]]:
    """Recursively find every ``{file:...}`` reference anywhere in a JSON-like value.

    Returns a list of ``(json_path_tuple, raw_string_value, file_ref_relpath)`` in a
    stable (dict-insertion / list-index) traversal order, so two structurally-parallel
    documents (e.g. the shipped config and a materialized stand-in that only rewrites
    path *values*, not structure) yield refs in the same relative order.
    """
    out: list[tuple[tuple, str, str]] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.extend(find_file_refs(v, path + (k,)))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.extend(find_file_refs(v, path + (i,)))
    elif isinstance(obj, str):
        m = FILE_REF_RE.search(obj)
        if m:
            out.append((path, obj, m.group(1)))
    return out


def flag_value(argv: list[str], flag: str) -> str | None:
    """Return the value passed to ``flag`` (space or ``=`` form), if present."""
    for i, a in enumerate(argv):
        if a == flag and i + 1 < len(argv):
            return argv[i + 1]
        if a.startswith(flag + "="):
            return a.split("=", 1)[1]
    return None


def is_inside(path: Path, base: Path) -> bool:
    """True iff ``path`` is ``base`` itself or located somewhere under it."""
    try:
        path.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False

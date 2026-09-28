# Pytest fixtures for the p1-agent-run-glue acceptance suite (offline; mock runner).
#
# Shared constants + the mock agent-runner classes live in the uniquely-named module
# `authoring_helpers` (NOT here) so they can be imported without colliding with the
# connectors/tests `conftest` under pytest's prepend importmode. This file exposes only
# pytest fixtures, which pytest injects by name regardless of module-name collisions.

from __future__ import annotations

import pytest

from authoring_helpers import (
    BRD_SENTINEL,
    BRD_TOKEN,
    RecordingRunner,
    fresh_openapi,
    make_config,
)


@pytest.fixture
def sample_openapi():
    """A small, valid in-memory OpenAPI document (used as `api_spec_source`)."""
    return fresh_openapi()


@pytest.fixture
def expected_api_surface(sample_openapi):
    """The unit-1 normalized surface `.to_dict()` for `sample_openapi`.

    Computed via the *composed* unit-1 loader (not the module under test) so the
    glue's `api_surface` output can be asserted byte-for-byte.
    """
    from connectors import spec_loader

    return spec_loader.load_spec(sample_openapi).to_dict()


@pytest.fixture
def clean_brd(tmp_path):
    """A BRD file with a unique body marker and NO `{{BRD}}` token.

    Drives criteria 3a/3b/3d (injection present, no residue, template preserved).
    Returns (path_str, text).
    """
    text = (
        "# Per-run BRD\n\n"
        f"This is the injected business context. {BRD_SENTINEL}\n"
        "The shopper must be able to check out end to end.\n"
    )
    p = tmp_path / "BRD.md"
    p.write_text(text, encoding="utf-8")
    return str(p), text


@pytest.fixture
def token_bearing_brd(tmp_path):
    """A BRD whose body itself contains a literal `{{BRD}}` token.

    Drives criterion 3c: the single original placeholder is replaced exactly once
    and the injected body is not recursively re-substituted.
    Returns (path_str, text).
    """
    text = (
        "# Tricky BRD\n\n"
        f"{BRD_SENTINEL} — this body intentionally contains a literal {BRD_TOKEN} token.\n"
    )
    p = tmp_path / "BRD_with_token.md"
    p.write_text(text, encoding="utf-8")
    return str(p), text


@pytest.fixture
def config_factory():
    """Return the config-mapping builder (`authoring_helpers.make_config`)."""
    return make_config


@pytest.fixture
def valid_config(clean_brd):
    """A ready-to-use valid config mapping pointing at the clean BRD."""
    brd_path, _text = clean_brd
    return make_config(brd_path)


@pytest.fixture
def recording_runner():
    return RecordingRunner(
        {"cart.spec.ts": "// cart test\n", "orders.api.spec.ts": "// orders api test\n"}
    )

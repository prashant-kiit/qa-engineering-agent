"""Per-run target configuration → validated, secret-safe :class:`TargetConfig`.

Loads the configuration a single authoring run needs — the target **UI URL**, the
**API-spec source** (consumed by the unit-1 :mod:`connectors.spec_loader`), the
freeform **BRD path**, a Basic-Auth credential **reference** (an env-var / vault-key
*name*, never the secret value — ``DESIGN.md §11.4``), and the seven structured
**Planner fields** (``DESIGN.md §6``).

The loader validates required fields (raising :class:`TargetConfigError`), delegates
API-spec parsing to :func:`connectors.spec_loader.load_spec` (no duplication), and is
**secret-safe**: the resolved credential value is never stored on the object nor emitted
by ``to_dict()`` / ``repr()`` / ``str()`` / logging. The credential is resolved from the
environment only at call time via :meth:`TargetConfig.resolve_credential`, which raises
:class:`CredentialUnsetError` when the referenced variable is unset.

The public contract (import path, entry point, serialized key names, error types) is
documented in ``connectors/README.md``.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Mapping

# Imported as a module (not a bound name) so the delegation target is looked up
# dynamically at call time — tests monkeypatch ``connectors.spec_loader.load_spec``.
from connectors import spec_loader


# --------------------------------------------------------------------------- #
# Errors
# --------------------------------------------------------------------------- #


class TargetConfigError(Exception):
    """Raised when a target config is missing a required field, malformed, or invalid.

    Messages name the offending field. Distinct from :class:`CredentialUnsetError`.
    """


class CredentialUnsetError(Exception):
    """Raised by :meth:`TargetConfig.resolve_credential` when the referenced env var
    / vault key is unset at resolve time.

    Deliberately **not** a subclass of :class:`TargetConfigError`: a missing secret at
    runtime is a distinct condition from an invalid config at load time.
    """


# --------------------------------------------------------------------------- #
# Pinned contract
# --------------------------------------------------------------------------- #

REQUIRED_TOP_LEVEL = (
    "target_url",
    "api_spec_source",
    "brd_path",
    "basic_auth_credential_ref",
    "planner_fields",
)

SEVEN_PLANNER_FIELDS = (
    "target_scope",
    "intent",
    "expected_behavior",
    "priority_risk",
    "test_data_preconditions",
    "out_of_scope_constraints",
    "depth",
)

DEPTH_ENUM = ("smoke", "regression", "exhaustive")

_URL_SCHEMES = ("http://", "https://")


# --------------------------------------------------------------------------- #
# Model
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class TargetConfig:
    """A validated, secret-safe per-run target configuration.

    Carries the credential **reference name** only — never a resolved secret value.
    """

    target_url: str
    api_spec_source: Any
    brd_path: str
    basic_auth_credential_ref: str
    planner_fields: Mapping[str, str]

    def to_dict(self) -> dict:
        """Render to a plain, deterministic, secret-free dict with the pinned keys.

        Key order is fixed (top-level, then the seven planner fields in pinned order)
        so the same input always serializes byte-identically.
        """
        return {
            "target_url": self.target_url,
            "api_spec_source": self.api_spec_source,
            "brd_path": str(self.brd_path),
            "basic_auth_credential_ref": self.basic_auth_credential_ref,
            "planner_fields": {
                name: self.planner_fields[name] for name in SEVEN_PLANNER_FIELDS
            },
        }

    def __repr__(self) -> str:  # secret-free: only the reference NAME appears
        return (
            f"{type(self).__name__}(target_url={self.target_url!r}, "
            f"api_spec_source={self.api_spec_source!r}, "
            f"brd_path={str(self.brd_path)!r}, "
            f"basic_auth_credential_ref={self.basic_auth_credential_ref!r}, "
            f"planner_fields={{...seven fields, depth={self.planner_fields['depth']!r}}})"
        )

    def load_api_spec(self):
        """Delegate to :func:`connectors.spec_loader.load_spec` (unit 1) and return its
        :class:`~connectors.spec_loader.ApiSurface`.

        This unit performs no independent spec parsing; the loader's named errors
        (``SpecLoadError`` / ``UnsupportedSourceError``) propagate unchanged.
        """
        return spec_loader.load_spec(self.api_spec_source)

    def resolve_credential(self) -> str:
        """Resolve the referenced Basic-Auth credential from the environment at call time.

        Reads the env var named by ``basic_auth_credential_ref`` and returns its value to
        the caller. The value is **not** stored back on the object and is **not** logged.
        Raises :class:`CredentialUnsetError` when the env var is unset.
        """
        value = os.environ.get(self.basic_auth_credential_ref)
        if value is None:
            raise CredentialUnsetError(
                f"credential env var {self.basic_auth_credential_ref!r} is not set"
            )
        return value


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #


def _read_source(source: Any, source_type: str) -> Mapping:
    """Return a config mapping from a mapping or a JSON file path."""
    if isinstance(source, Mapping):
        return source
    if isinstance(source, (str, os.PathLike)):
        path = os.fspath(source)
        try:
            with open(path, "r", encoding="utf-8") as fh:
                text = fh.read()
        except OSError as exc:
            raise TargetConfigError(
                f"could not read target config file {path!r}: {exc}"
            ) from exc
        try:
            parsed = json.loads(text)
        except ValueError as exc:
            raise TargetConfigError(
                f"target config file {path!r} is not valid JSON: {exc}"
            ) from exc
        if not isinstance(parsed, Mapping):
            raise TargetConfigError(
                f"target config file {path!r} must contain a JSON object"
            )
        return parsed
    raise TargetConfigError(
        f"unsupported target config source of type {type(source).__name__!r}; "
        "expected a mapping or a file path"
    )


def _require_nonempty_str(mapping: Mapping, key: str) -> str:
    value = mapping[key]
    if not isinstance(value, str) or value.strip() == "":
        raise TargetConfigError(
            f"field {key!r} must be a non-empty string (got {value!r})"
        )
    return value


def _validate_planner(planner: Any) -> dict:
    if not isinstance(planner, Mapping):
        raise TargetConfigError(
            f"field 'planner_fields' must be a mapping of the seven planner fields "
            f"(got {type(planner).__name__})"
        )
    validated: dict = {}
    for name in SEVEN_PLANNER_FIELDS:
        if name not in planner:
            raise TargetConfigError(
                f"planner field {name!r} is required but missing"
            )
        value = planner[name]
        if name == "depth":
            if value not in DEPTH_ENUM:
                raise TargetConfigError(
                    f"planner field 'depth' must be one of "
                    f"{sorted(DEPTH_ENUM)} (got {value!r})"
                )
        else:
            if not isinstance(value, str) or value.strip() == "":
                raise TargetConfigError(
                    f"planner field {name!r} must be a non-empty string (got {value!r})"
                )
        validated[name] = value
    return validated


def load_target_config(source: Any, source_type: str = "auto") -> TargetConfig:
    """Load and validate a per-run target config, returning a :class:`TargetConfig`.

    Parameters
    ----------
    source:
        An already-parsed config mapping, or a filesystem path to a JSON config file.
    source_type:
        Reserved source-kind hint; ``"auto"`` (default) detects mapping vs file path.

    Raises
    ------
    TargetConfigError
        A required field is missing, empty, wrong-typed, or malformed (message names
        the offending field), or the file is unreadable / not valid JSON.
    """
    mapping = _read_source(source, source_type)

    # Required top-level fields present (named error, never a bare KeyError).
    for key in REQUIRED_TOP_LEVEL:
        if key not in mapping:
            raise TargetConfigError(f"required field {key!r} is missing")

    target_url = _require_nonempty_str(mapping, "target_url")
    if not target_url.lower().startswith(_URL_SCHEMES):
        raise TargetConfigError(
            f"field 'target_url' must be an http(s) URL (got {target_url!r})"
        )

    api_spec_source = mapping["api_spec_source"]
    if api_spec_source is None or (
        isinstance(api_spec_source, str) and api_spec_source.strip() == ""
    ):
        raise TargetConfigError("field 'api_spec_source' must be a non-empty source")

    brd_path = _require_nonempty_str(mapping, "brd_path")

    credential_ref = _require_nonempty_str(mapping, "basic_auth_credential_ref")

    planner = _validate_planner(mapping["planner_fields"])

    return TargetConfig(
        target_url=target_url,
        api_spec_source=api_spec_source,
        brd_path=brd_path,
        basic_auth_credential_ref=credential_ref,
        planner_fields=planner,
    )

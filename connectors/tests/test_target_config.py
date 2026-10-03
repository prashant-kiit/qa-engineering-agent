# Acceptance suite for p1-target-config (TDD red).
#
# Encodes acceptance criteria 1-18 from .harness/tasks/p1-target-config.md against small
# hand-crafted config mappings/files, an env-var sentinel, and the shipped reference-app
# example config. Written WITHOUT reading the implementation (unbiased TDD red).
#
# The target-config module does not exist yet. Every test consumes the `target_config`
# fixture, which imports `connectors.target_config`; that import raises ModuleNotFoundError
# until the developer implements the module -> the whole NEW suite is legitimately red for
# the RIGHT reason (missing implementation), not broken scaffolding. Unit-1's
# test_spec_loader.py is untouched and still passes.
#
# NAMING ASSUMPTIONS the developer MUST honor (recorded in p1-target-config.tests.md).
# The spec (Interfaces) leaves several public names to the developer's choice but requires
# them documented + stable; the Tester pins the most natural per the spec:
#   - public module:            connectors.target_config
#   - loader entry point:       load_target_config(source, source_type="auto") -> TargetConfig
#   - config object type:       TargetConfig
#   - named config error:       connectors.target_config.TargetConfigError
#   - credential-unset error:   connectors.target_config.CredentialUnsetError
#                               (distinct named error; NOT a subclass of TargetConfigError)
#   - spec hand-off:            TargetConfig.load_api_spec() -> connectors.spec_loader.ApiSurface
#   - credential resolution:    TargetConfig.resolve_credential() -> str (secret; never stored)
#   - serialization:            TargetConfig.to_dict() -> plain deterministic dict; safe __repr__
#   - example config file:      connectors/examples/reference_app.target.json
#
# The PINNED serialized field names (from the spec's Model + Seven-Planner-fields tables) are
# NOT assumptions — they are binding contract keys:
#   top-level: target_url, api_spec_source, brd_path, basic_auth_credential_ref, planner_fields
#   planner:   target_scope, intent, expected_behavior, priority_risk,
#              test_data_preconditions, out_of_scope_constraints, depth

import copy
import importlib
import json
import logging
from pathlib import Path

import pytest

# ---- repo layout -------------------------------------------------------------------------
# connectors/tests/<thisfile> -> parents[2] == repo root
REPO_ROOT = Path(__file__).resolve().parents[2]
REAL_BRD = REPO_ROOT / "reference_app" / "BRD.md"
EXAMPLE_CONFIG = REPO_ROOT / "connectors" / "examples" / "reference_app.target.json"

# ---- pinned contract names ---------------------------------------------------------------
REQUIRED_TOP_LEVEL = [
    "target_url",
    "api_spec_source",
    "brd_path",
    "basic_auth_credential_ref",
    "planner_fields",
]
SEVEN_PLANNER_FIELDS = [
    "target_scope",
    "intent",
    "expected_behavior",
    "priority_risk",
    "test_data_preconditions",
    "out_of_scope_constraints",
    "depth",
]
DEPTH_ENUM = {"smoke", "regression", "exhaustive"}

SENTINEL_ENV_NAME = "TEST_TARGET_CONFIG_SENTINEL_CRED"
SENTINEL_SECRET = "s3cr3t-sentinel-VALUE-DO-NOT-LEAK-8b21f"


# ---- fixtures / helpers ------------------------------------------------------------------


@pytest.fixture
def target_config():
    """Import the target-config module at its stable public path.

    NAMING ASSUMPTION: the public module is `connectors.target_config`. Until the developer
    creates it this import raises ModuleNotFoundError, the expected red failure for the whole
    NEW suite.
    """
    return importlib.import_module("connectors.target_config")


def _planner_fields():
    return {
        "target_scope": "Shop checkout flow: browse -> add to cart -> checkout",
        "intent": "Verify a logged-in user can complete a purchase end to end",
        "expected_behavior": "Cart totals are correct and checkout returns an order id",
        "priority_risk": "Payment + inventory decrement are the highest-risk areas",
        "test_data_preconditions": "Seeded catalog with at least one in-stock product",
        "out_of_scope_constraints": "No real payment gateway; do not mutate other users",
        "depth": "regression",
    }


def _valid_mapping():
    """A fresh, fully-valid config mapping (uses the REAL BRD path so it exists on disk)."""
    return {
        "target_url": "http://127.0.0.1:5173",
        "api_spec_source": "http://127.0.0.1:8000/openapi.json",
        "brd_path": str(REAL_BRD),
        "basic_auth_credential_ref": "REF_APP_BASIC_AUTH",
        "planner_fields": _planner_fields(),
    }


def _load(target_config, mapping):
    return target_config.load_target_config(mapping)


# =========================================================================================
# Loading & schema (criteria 1-4)
# =========================================================================================


def test_load_from_mapping_returns_object(target_config):
    """Criterion 1: a complete mapping loads without error and yields a config object."""
    cfg = _load(target_config, _valid_mapping())
    assert cfg is not None


def test_load_from_json_file_equals_mapping(target_config, tmp_path):
    """Criterion 2: a JSON file with the same fields loads equal to the mapping form."""
    mapping = _valid_mapping()
    path = tmp_path / "run.target.json"
    path.write_text(json.dumps(mapping), encoding="utf-8")

    from_file = target_config.load_target_config(str(path))
    from_map = target_config.load_target_config(copy.deepcopy(mapping))

    assert from_file.to_dict() == from_map.to_dict()


def test_invalid_json_file_raises_named_error(target_config, tmp_path):
    """Criterion 2 (load error): a malformed/non-JSON config file raises the named error,
    not an arbitrary uncaught exception."""
    bad = tmp_path / "broken.target.json"
    bad.write_text("{ this is : not json", encoding="utf-8")
    with pytest.raises(target_config.TargetConfigError):
        target_config.load_target_config(str(bad))


def test_object_exposes_pinned_top_level_fields(target_config):
    """Criterion 3: the object exposes the pinned top-level field names with the given values."""
    mapping = _valid_mapping()
    cfg = _load(target_config, mapping)
    assert cfg.target_url == mapping["target_url"]
    assert cfg.api_spec_source == mapping["api_spec_source"]
    assert str(cfg.brd_path) == mapping["brd_path"]
    assert cfg.basic_auth_credential_ref == mapping["basic_auth_credential_ref"]
    assert cfg.planner_fields is not None


def test_seven_planner_fields_exactly(target_config):
    """Criterion 4: serialized planner_fields carries EXACTLY the seven pinned names."""
    cfg = _load(target_config, _valid_mapping())
    planner = cfg.to_dict()["planner_fields"]
    assert set(planner.keys()) == set(SEVEN_PLANNER_FIELDS)


def test_planner_field_values_roundtrip(target_config):
    """Criterion 3/4: each of the seven planner values is carried through to serialization."""
    mapping = _valid_mapping()
    cfg = _load(target_config, mapping)
    planner = cfg.to_dict()["planner_fields"]
    for name in SEVEN_PLANNER_FIELDS:
        assert planner[name] == mapping["planner_fields"][name]


# =========================================================================================
# Validation & named error (criteria 5-8)
# =========================================================================================


@pytest.mark.parametrize("field", REQUIRED_TOP_LEVEL)
def test_missing_required_top_level_field_rejected(target_config, field):
    """Criterion 5: omitting any required top-level field raises the named config error
    (not a bare KeyError, not a silent default), naming the offending field."""
    mapping = _valid_mapping()
    del mapping[field]
    with pytest.raises(target_config.TargetConfigError) as exc:
        target_config.load_target_config(mapping)
    # named error, not a bare KeyError
    assert not isinstance(exc.value, KeyError)
    assert field in str(exc.value)


@pytest.mark.parametrize(
    "field,bad_value",
    [
        ("target_url", ""),            # empty
        ("target_url", "not-a-url"),   # not URL-shaped
        ("target_url", 123),           # wrong type
        ("basic_auth_credential_ref", ""),      # blank
        ("basic_auth_credential_ref", "   "),   # whitespace-only
        ("basic_auth_credential_ref", 42),      # non-string
        ("planner_fields", "not-a-mapping"),    # not a mapping
        ("planner_fields", []),                 # not a mapping
    ],
)
def test_malformed_field_rejected_named(target_config, field, bad_value):
    """Criterion 6: a wrong-typed/empty/malformed field raises the named config error whose
    message identifies the offending field."""
    mapping = _valid_mapping()
    mapping[field] = bad_value
    with pytest.raises(target_config.TargetConfigError) as exc:
        target_config.load_target_config(mapping)
    assert field in str(exc.value)


@pytest.mark.parametrize("depth", sorted(DEPTH_ENUM))
def test_depth_enum_accepts_valid(target_config, depth):
    """Criterion 7: each documented depth value loads cleanly."""
    mapping = _valid_mapping()
    mapping["planner_fields"]["depth"] = depth
    cfg = target_config.load_target_config(mapping)
    assert cfg.to_dict()["planner_fields"]["depth"] == depth


@pytest.mark.parametrize("depth", ["deep", "SMOKE", "full", "", "regression ", None])
def test_depth_out_of_set_rejected(target_config, depth):
    """Criterion 7: a depth outside the enumerated set raises the named config error."""
    mapping = _valid_mapping()
    mapping["planner_fields"]["depth"] = depth
    with pytest.raises(target_config.TargetConfigError) as exc:
        target_config.load_target_config(mapping)
    assert "depth" in str(exc.value)


@pytest.mark.parametrize("missing", SEVEN_PLANNER_FIELDS)
def test_each_planner_field_required(target_config, missing):
    """Criterion 8: absent OR empty for any of the seven planner fields raises the named
    config error naming that field."""
    # absent
    mapping = _valid_mapping()
    del mapping["planner_fields"][missing]
    with pytest.raises(target_config.TargetConfigError) as exc:
        target_config.load_target_config(mapping)
    assert missing in str(exc.value)


@pytest.mark.parametrize("empty_field", [f for f in SEVEN_PLANNER_FIELDS if f != "depth"])
def test_empty_planner_text_field_rejected(target_config, empty_field):
    """Criterion 8: an empty required (free-text) planner field raises the named error."""
    mapping = _valid_mapping()
    mapping["planner_fields"][empty_field] = ""
    with pytest.raises(target_config.TargetConfigError) as exc:
        target_config.load_target_config(mapping)
    assert empty_field in str(exc.value)


# =========================================================================================
# Secret-safety (criteria 9-11)
# =========================================================================================


def _serialized_surfaces(cfg):
    """Every text surface the spec says must be secret-free: to_dict JSON, repr, str."""
    return [json.dumps(cfg.to_dict()), repr(cfg), str(cfg)]


def test_only_reference_is_stored_no_inlined_secret(target_config):
    """Criterion 9: an attempt to inline a raw secret is rejected OR the value is not retained;
    no secret value is reachable on the object."""
    mapping = _valid_mapping()
    mapping["password"] = SENTINEL_SECRET  # attacker/mistake: inline a secret
    mapping["basic_auth"] = {"username": "u", "password": SENTINEL_SECRET}
    try:
        cfg = target_config.load_target_config(mapping)
    except target_config.TargetConfigError:
        return  # rejecting the inlined secret satisfies the criterion
    # If accepted, the sentinel must not be reachable anywhere on the object.
    for surface in _serialized_surfaces(cfg):
        assert SENTINEL_SECRET not in surface
    assert SENTINEL_SECRET not in json.dumps(vars(cfg), default=str)


def test_serialization_leaks_no_secret_but_shows_reference(target_config, monkeypatch, caplog):
    """Criterion 10: with the secret present in the environment under the referenced name,
    to_dict/repr/str/logs contain the reference NAME but never the secret VALUE."""
    monkeypatch.setenv(SENTINEL_ENV_NAME, SENTINEL_SECRET)
    mapping = _valid_mapping()
    mapping["basic_auth_credential_ref"] = SENTINEL_ENV_NAME

    with caplog.at_level(logging.DEBUG):
        cfg = target_config.load_target_config(mapping)
        as_dict = cfg.to_dict()

    # reference name IS present
    assert as_dict["basic_auth_credential_ref"] == SENTINEL_ENV_NAME
    # secret VALUE is NOWHERE
    for surface in _serialized_surfaces(cfg):
        assert SENTINEL_ENV_NAME in surface  # the name is fine to show
        assert SENTINEL_SECRET not in surface
    assert SENTINEL_SECRET not in caplog.text


def test_resolution_is_at_call_time_and_non_retaining(target_config, monkeypatch, caplog):
    """Criterion 11: resolve_credential() returns the secret to the caller at call time and
    does NOT store it back; re-serialization still leaks nothing."""
    monkeypatch.setenv(SENTINEL_ENV_NAME, SENTINEL_SECRET)
    mapping = _valid_mapping()
    mapping["basic_auth_credential_ref"] = SENTINEL_ENV_NAME
    cfg = target_config.load_target_config(mapping)

    with caplog.at_level(logging.DEBUG):
        resolved = cfg.resolve_credential()

    assert SENTINEL_SECRET in str(resolved)  # caller does get the secret
    assert SENTINEL_SECRET not in caplog.text  # but it is never logged
    # After resolving, the object must STILL be secret-free.
    for surface in _serialized_surfaces(cfg):
        assert SENTINEL_SECRET not in surface


def test_resolve_unset_credential_raises_distinct_named_error(target_config, monkeypatch):
    """Criterion 11: resolving when the referenced env var is unset raises the named
    credential-unset error, distinct from the config/validation error."""
    monkeypatch.delenv(SENTINEL_ENV_NAME, raising=False)
    mapping = _valid_mapping()
    mapping["basic_auth_credential_ref"] = SENTINEL_ENV_NAME
    cfg = target_config.load_target_config(mapping)  # loads fine: ref is present
    with pytest.raises(target_config.CredentialUnsetError):
        cfg.resolve_credential()
    # distinct from the config error
    assert not issubclass(target_config.CredentialUnsetError, target_config.TargetConfigError)


# =========================================================================================
# Spec-loader hand-off (criteria 12-13)
# =========================================================================================


def test_spec_handoff_delegates_and_matches_unit1(target_config, spec_loader, openapi_doc):
    """Criterion 12: load_api_spec() delegates to connectors.spec_loader.load_spec and yields
    the SAME ApiSurface unit-1 produces for that source (in-memory dict; no network)."""
    mapping = _valid_mapping()
    mapping["api_spec_source"] = openapi_doc  # dict source -> no network needed
    cfg = target_config.load_target_config(mapping)

    surface = cfg.load_api_spec()
    expected = spec_loader.load_spec(copy.deepcopy(openapi_doc))
    assert surface.to_dict() == expected.to_dict()


def test_spec_handoff_calls_load_spec_with_source(target_config, monkeypatch, openapi_doc):
    """Criterion 12: the hand-off passes api_spec_source through to load_spec unchanged and
    performs no independent parsing."""
    import connectors.spec_loader as sl

    captured = {}
    sentinel_surface = object()

    def _fake_load_spec(source, *args, **kwargs):
        captured["source"] = source
        return sentinel_surface

    monkeypatch.setattr(sl, "load_spec", _fake_load_spec)

    mapping = _valid_mapping()
    mapping["api_spec_source"] = openapi_doc
    cfg = target_config.load_target_config(mapping)
    result = cfg.load_api_spec()

    assert result is sentinel_surface
    assert captured["source"] == openapi_doc


def test_spec_handoff_propagates_loader_error_unchanged(target_config):
    """Criterion 13: when load_spec raises its named error, the hand-off propagates it
    unchanged (SpecLoadError), NOT rewrapped into the config error."""
    import connectors.spec_loader as sl

    mapping = _valid_mapping()
    mapping["api_spec_source"] = {"not": "an-openapi-doc"}  # loads as config, fails as spec
    cfg = target_config.load_target_config(mapping)
    with pytest.raises(sl.SpecLoadError):
        cfg.load_api_spec()


def test_spec_handoff_propagates_unsupported_error_unchanged(target_config, monkeypatch, openapi_doc):
    """Criterion 13: UnsupportedSourceError from load_spec propagates unchanged, not swallowed
    and not rewrapped into TargetConfigError."""
    import connectors.spec_loader as sl

    def _raise_unsupported(source, *args, **kwargs):
        raise sl.UnsupportedSourceError("graphql not supported")

    monkeypatch.setattr(sl, "load_spec", _raise_unsupported)

    mapping = _valid_mapping()
    mapping["api_spec_source"] = openapi_doc
    cfg = target_config.load_target_config(mapping)
    with pytest.raises(sl.UnsupportedSourceError):
        cfg.load_api_spec()


# =========================================================================================
# Reference-app example config (criteria 14-15)
# =========================================================================================


def test_example_config_present_and_valid(target_config):
    """Criterion 14: the committed example config loads + validates cleanly with the wired
    reference-app values and all seven planner fields (depth in the enum)."""
    cfg = target_config.load_target_config(str(EXAMPLE_CONFIG))
    d = cfg.to_dict()
    assert d["target_url"] == "http://127.0.0.1:5173"
    assert d["api_spec_source"] == "http://127.0.0.1:8000/openapi.json"
    assert str(d["brd_path"]).replace("\\", "/").endswith("reference_app/BRD.md")
    assert isinstance(d["basic_auth_credential_ref"], str)
    assert d["basic_auth_credential_ref"].strip() != ""
    planner = d["planner_fields"]
    assert set(planner.keys()) == set(SEVEN_PLANNER_FIELDS)
    for name in SEVEN_PLANNER_FIELDS:
        assert str(planner[name]).strip() != ""
    assert planner["depth"] in DEPTH_ENUM


def test_example_config_is_secret_free(target_config):
    """Criterion 15: the example config file carries only the credential reference NAME —
    no reference-app username/password value in the file or loaded object."""
    # import the loader first so a missing module is the uniform red reason
    _ = target_config
    raw = EXAMPLE_CONFIG.read_text(encoding="utf-8")
    assert "testuser" not in raw
    assert "testpass" not in raw
    cfg = target_config.load_target_config(str(EXAMPLE_CONFIG))
    for surface in _serialized_surfaces(cfg):
        assert "testpass" not in surface
        assert "testuser" not in surface


# =========================================================================================
# Determinism, placement, no-regression (criterion 16)
# =========================================================================================


def test_to_dict_deterministic_same_input(target_config):
    """Criterion 16: the same input serialized twice yields identical output."""
    m1 = _valid_mapping()
    m2 = _valid_mapping()
    a = target_config.load_target_config(m1).to_dict()
    b = target_config.load_target_config(m2).to_dict()
    assert a == b
    assert json.dumps(a) == json.dumps(b)  # stable key ordering too


def test_to_dict_file_equals_mapping_and_stable_keys(target_config, tmp_path):
    """Criterion 16: a file and its equivalent mapping serialize equal, with the pinned keys."""
    mapping = _valid_mapping()
    path = tmp_path / "run.target.json"
    path.write_text(json.dumps(mapping), encoding="utf-8")

    d_file = target_config.load_target_config(str(path)).to_dict()
    d_map = target_config.load_target_config(copy.deepcopy(mapping)).to_dict()
    assert d_file == d_map
    # pinned top-level keys present
    for key in REQUIRED_TOP_LEVEL:
        assert key in d_map

# Test coverage — `p1-mcp-config` (TDD red)

**Test file (new):** `connectors/tests/test_mcp_config.py`
**Runner:** `uv run pytest connectors/tests -q`
**Constraint honored:** all tests are purely STATIC — they read/parse the committed config
file and `connectors/README.md` and assert on contents. No MCP launch, no browser, no
`npx`/Node, no network I/O. Existing unit-1 (`test_spec_loader.py`) and unit-2
(`test_target_config.py`) suites were not modified.

## Acceptance criterion → test(s)

| # | Acceptance criterion | Test(s) |
|---|----------------------|---------|
| 1 | File present at pinned path `connectors/mcp/playwright.mcp.json` | `test_config_file_present_at_pinned_path` |
| 2 | Valid JSON, single top-level object | `test_config_is_valid_json_single_top_level_object` |
| 3 | Top-level `mcpServers` key is an object map | `test_mcpservers_map_present` |
| 4 | `playwright` server declared (object value) | `test_playwright_server_declared` |
| 5 | Launch shape: non-empty `command` str + `args` list[str]; optional `env` object w/o secret values | `test_launch_shape_command_and_args`, `test_optional_env_is_object_without_secret_values` |
| 6 | `@playwright/mcp` package token present in launch | `test_package_reference_present` |
| 7 | Exact version pinned `@playwright/mcp@X.Y.Z` | `test_exact_version_pinned` |
| 8 | No floating specifier (bare / `@latest` / `@next` / `^ ~ * >= <= > < \|\|` / `x` wildcard) | `test_no_floating_specifier` |
| 9 | Headless browser mode declared | `test_headless_mode_declared` |
| 10 | Concrete browser engine declared (chromium/firefox/webkit/chrome/msedge) | `test_browser_engine_declared` |
| 11 | Consumable by units 5/6: stable `playwright` key + `command`/`args` at pinned path | `test_server_key_and_path_stable_for_consumers` |
| 12 | README documents the file path + pinned package | `test_readme_documents_config` |
| 13 | Target-agnostic: no ref-app URL/port, no credential value | `test_config_is_target_agnostic_no_urls_or_secrets` |
| 14 | Correct home + purely-static runnable tests | Whole module (path `connectors/tests/`, static-only by construction; runs via `uv run pytest connectors/tests -q`) |
| 15 | No regressions to units 1–2 / protected files | Verified by run: unit-1/unit-2 suites still pass (77 passed); this module adds tests only, performs no writes/network |

## Assumptions the developer MUST honor
Binding contract from the spec (Interfaces): config path `connectors/mcp/playwright.mcp.json`;
top-level `mcpServers` object; server key **exactly** `playwright`; launch shape
`command` (non-empty string) + `args` (array of strings); package `@playwright/mcp` pinned to
an **exact** `X.Y.Z` version. Reference exact pin per spec is `@playwright/mcp@0.0.41`; the
tests enforce *exact pinning* (any concrete `X.Y.Z`), not the specific number.

Developer-choice details NOT over-constrained by the tests:
- The concrete `command` launcher token (e.g. `npx`) is not pinned by the spec → not asserted.
- The browser-engine token is the developer's choice from the supported set → asserted as
  "some concrete engine present", not a specific literal.
- Arg **ordering** is free → not asserted; the package/headless/engine tokens are located by
  scanning the launch surface regardless of position.
- The package reference (`@playwright/mcp@X.Y.Z`) is expected to be a **single `args`
  element** (or embedded in `command`); the token is located by substring across all launch
  tokens. Headless/engine options are located by scanning all string values in the
  `playwright` server definition, so `--headless`/`--browser chromium` args or an equivalent
  documented option surface both satisfy criteria 9–10.
- Target-agnostic check (13) forbids the ref-app URLs/ports (`127.0.0.1:5173`,
  `127.0.0.1:8000`, `localhost:*`, `:5173`, `:8000`) and the substring `password` in the file.

## Red run output (before implementation)

```
14 failed, 77 passed in 1.77s
```

All 14 new `test_mcp_config.py` tests fail for the RIGHT reason — the config artifact
`connectors/mcp/playwright.mcp.json` does not exist and `connectors/README.md` has no MCP
section — not because of scaffolding/import errors. The 77 pre-existing unit-1 + unit-2 tests
still pass unchanged.

Representative failures:
- `test_config_file_present_at_pinned_path` — `False = exists()` on
  `connectors/mcp/playwright.mcp.json` (criterion 1: file missing).
- `test_readme_documents_config` — `'playwright.mcp.json' not in` current README (criterion 12).
- `test_config_is_target_agnostic_no_urls_or_secrets` — file must exist to assert (criterion 13).

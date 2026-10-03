# Review — `p1-mcp-config`

**Verdict: APPROVE**

Independent review of the Playwright-MCP config artifact against the spec, the Tester's
tests, and quality axes. Read-only on code; suite run independently.

## 1. Acceptance (criteria 1–15) — all met
- **1–2 Presence/parse:** `connectors/mcp/playwright.mcp.json` exists at the pinned path and
  is valid JSON (single top-level object).
- **3–4 Shape:** top-level `mcpServers` object; server keyed exactly `playwright` (object).
- **5 Launch shape:** `command` = `"npx"` (non-empty string), `args` = list of strings. No
  `env` block present (optional) — nothing to leak.
- **6 Package ref:** `@playwright/mcp` token present in `args`.
- **7–8 Version pinning (§11.10):** exact pin `@playwright/mcp@0.0.41`; no floating
  specifier (bare / `@latest` / `@next` / `^ ~ * >= <= > < ||` / `x` wildcard).
- **9–10 DOM-snapshot options:** `--headless` and `--browser chromium` (concrete engine)
  declared.
- **11 Consumable:** stable `playwright` key + `command`/`args` at the pinned path.
- **12 Docs:** `connectors/README.md` gains a section naming the file path, the pinned
  package + exact version + §11.10 rationale, the headless/engine options, the unit-5/6
  consumer fields, and the explicit "not launched here; Node/`npx` is a runtime prereq for
  later units, not tested live" note.
- **13 Target-agnostic/secret-free:** no ref-app URL/port and no credential value in the file.
- **14 Home + static tests:** tests live under `connectors/tests/`, run via
  `uv run pytest connectors/tests -q`, and are purely static (parse + assert, no
  launch/browser/npx/network).
- **15 No regressions:** unit-1/unit-2 code, tests, and public APIs unchanged; suite green.

## 2. Test integrity
Tests are unchanged from the Tester's versions (no dev modification). They genuinely enforce
the spec: positive exact-pin regex plus robust negative floating-specifier checks; headless +
concrete-engine scanned across all string values; server-key/path stability; README
path+package; and a file-wide target-agnostic/no-secret substring assertion. No gaming.

**Skip is legitimate:** `test_optional_env_is_object_without_secret_values` skips because the
config declares no optional `env` block, so the env-clause of criterion 5 has nothing to
assert. It masks no gap — secret-safety is enforced independently and file-wide by
`test_config_is_target_agnostic_no_urls_or_secrets` (forbids `password` and any ref-app
URL/port across the entire file text).

## 3. Scope
No creep. Only the config artifact, its test module, and the README section were added; no
prompt, sub-agent, glue, or live-run work. Expected harness updates only (backlog status flip
to `spec-ready (active)`, task/tests artifacts).

## 4. Quality
Config is minimal, well-formed, exactly pinned, headless, concrete-engine, and free of any
target URL / credential. README documentation is complete and accurate. No dead code.

## 5. Protected/reference files
No change to `reference_app/**`, `DESIGN.md`, `META_PLAN.md`, `AGILE_PLAN.md`, `CLAUDE.md`.
Changed files: `connectors/mcp/playwright.mcp.json` (new), `connectors/tests/test_mcp_config.py`
(new), `connectors/README.md` (added section), and the expected `.harness/**` artifacts.

## Test run

```
$ uv run pytest connectors/tests -q
.....s.................................................................. [ 79%]
...................                                                      [100%]
90 passed, 1 skipped in 1.76s
```

Matches the expected 90 passed / 1 skipped.

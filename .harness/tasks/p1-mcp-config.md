# Task: `p1-mcp-config` — `connectors/` Playwright-MCP config (pinned server wiring)

## Title
The **Playwright-MCP server configuration** for `connectors/`: a static config artifact (a Claude
Code-compatible `.mcp.json`-shaped file) that declares the **Playwright MCP server** the authoring
agent uses to drive a browser and obtain **grounded DOM snapshots** (`DESIGN.md §4/§5.1`), with a
**pinned MCP server package identity + exact version** for supply-chain integrity (`DESIGN.md
§11.10`), plus the browser/launch options a grounded-snapshot run needs. Placed physically under
`connectors/` per `DESIGN.md §13`. This is a **config artifact only** — not agent code, not the
prompt, not the sub-agents, not the run glue, and it is **not launched** in this unit. No model key
required; acceptance is **static validation** (presence / shape / schema / version-pinning) exactly
like the Phase 0 infra units.

## Context (plan item)
- **AGILE_PLAN.md → Phase 1 → D3** ("`connectors/` — Playwright-MCP config") and the **Phase 1 unit
  table** unit 3. Deps = Phase 0 (done) → met. (Unit 3 has **no** dependency on units 1/2; it is
  independent config. It is itself a dependency of unit 5 `p1-subagents-planner-generator` and unit 6
  `p1-agent-run-glue`.)
- **Backlog unit 3** (`p1-mcp-config`, status `spec-ready (active)`).
- **DESIGN.md §4** — the sub-agent pipeline (Planner → Generator → …) runs "via a coding CLI **over
  Playwright MCP**"; the Planner "explores the running app" and the Generator emits TS Playwright
  (+ API) tests. Playwright MCP is the browser-driving channel this config wires up.
- **DESIGN.md §5.1** — **Grounding**: "selectors from the live **DOM snapshot observed via Playwright
  MCP** (role/label/test-id locators), never invented." This config is what makes that DOM-snapshot
  channel available to the agent — the reliability layer's #1 flake defense depends on it.
- **DESIGN.md §11.10** — **Supply chain**: "Pinned/verified sandbox image, CLI version, and **MCP
  servers**; signed builds." → the declared MCP server must be pinned to an **exact version**, never
  a floating tag/range (`latest`, `^`, `~`, `*`, `>=`, or an unversioned bare package).
- **DESIGN.md §13** — `connectors/  # **playwright-mcp config**, api-spec loader, per-run target
  config` is the home directory (architecture source of truth for placement; resolves the
  META_PLAN grouping note recorded in `AGILE_PLAN.md → Conflicts`).
- **DESIGN.md §2** — the orchestrator is **Claude Code (headless)**, which "brings native **MCP**,
  sub-agents (`.claude/agents/`) …"; the config format is therefore Claude Code's MCP-server config
  form (`mcpServers` map). **§12** — control-plane glue/tooling is Python (`uv`); this config file is
  a declarative artifact the Python glue (unit 6) and the sub-agents (unit 5) consume — not itself
  test code (test artifacts stay TS Playwright).
- This unit is **only** the MCP server wiring. It is **not** the API spec loader (unit 1, done), the
  per-run target config (unit 2, done), the QA system prompt (unit 4), the Planner/Generator
  sub-agents (unit 5), the agent-run glue (unit 6), or any live run (unit 7).

**Given app state (contracts to build on — do NOT re-derive or modify):**
- `connectors/` already contains real code from units 1–2: `spec_loader.py`, `target_config.py`,
  `__init__.py`, `tests/`, `README.md`, `examples/`. This unit **adds** the MCP config artifact + its
  presence/shape tests + a README section; it must **not** break units 1–2's public APIs or tests.
- **No `.mcp.json` exists anywhere in the repo yet** (verified). `.claude/agents/` currently holds
  only the build-harness roles; no product MCP config is present. This unit creates the first one.
- **Clean reference app (pristine, do not modify):** React+Vite UI at `http://127.0.0.1:5173`,
  FastAPI backend at `http://127.0.0.1:8000`. This config is **target-agnostic** — it wires the
  Playwright MCP *server*, not a specific target URL (the target URL lives in the unit-2 per-run
  target config). Do not bake a tenant/target URL into this file.
- Root project uses `uv` (`pyproject.toml`); Phase 0/1 suites run via `uv run pytest <dir> -q`. The
  Playwright TS project lives at `reference_app/e2e/`. Node/`npx` may or may not be installed in this
  environment — **this unit does not require it** (no launch, no install; static validation only).

## Scope

### In scope
1. **A Playwright-MCP config file** committed under `connectors/` at the pinned path (Interfaces
   §Paths), in **Claude Code MCP-server config form** — a JSON document with a top-level
   **`mcpServers`** object that maps a server key to that server's launch definition. It must be
   valid, parseable JSON.
2. **A declared Playwright MCP server entry** under `mcpServers` (server key **`playwright`**) that
   pins the **official Playwright MCP server package** at an **exact version** via the standard
   stdio-launch shape (a `command` + `args` invoking the pinned package). See Interfaces §Server
   entry for the pinned package/version.
3. **Version pinning for supply-chain integrity** (`DESIGN.md §11.10`): the package reference embeds
   an **exact** version (e.g. `@playwright/mcp@<X.Y.Z>`) — **never** a floating specifier
   (`latest`, `^`, `~`, `*`, `>=`, or a bare unversioned package name).
4. **Grounded-DOM-snapshot / browser launch options** the run needs, expressed via the server's
   documented argument/config surface so a downstream agent can obtain DOM snapshots deterministically:
   at minimum a **headless** browser mode and a named **browser** engine (e.g. `chromium`), declared
   in a way the file itself documents. (These are declarative options in the config; this unit does
   not execute them.)
5. **A machine-readable + human-readable documentation** of the config: a short section added to
   `connectors/README.md` explaining the file's path, its `mcpServers`/`playwright` shape, the pinned
   package + exact version and **why** it is pinned (§11.10), the browser/DOM-snapshot options and
   what they mean, the fields unit 5 / unit 6 will consume, and the explicit note that this artifact
   is **not launched** here (Node/`npx` availability is a documented **runtime** prerequisite for
   later units, not tested live).
6. **A test suite** under `connectors/tests/` (pytest) that performs **static** presence / shape /
   schema / version-pinning validation of the committed config file, runnable via
   `uv run pytest connectors/tests -q`. Tests read and parse the file; they **do not** launch the MCP
   server, spawn a browser, run `npx`, or reach the network.

### Out of scope (defer)
- **Launching the MCP server / spawning a browser / installing the package / any live run** — no
  execution in this unit (that is exercised live in unit 7, and wired by unit 6).
- **The QA system prompt** — unit 4 (`p1-qa-system-prompt`).
- **The Planner/Generator sub-agent definitions** — unit 5 (`p1-subagents-planner-generator`); they
  *reference/consume* this config but are authored separately.
- **The agent-run glue** — unit 6 (`p1-agent-run-glue`); it *points the agent at* this config.
- **Per-run target URL / credentials / API-spec source / BRD path / Planner fields** — those live in
  the unit-2 per-run target config, not here. This file is target-agnostic.
- **Egress allowlist, sandbox image, E2B, git proxy** (`DESIGN.md §11.2/§11.3/§11.6`, §13 `sandbox/`)
  — Phase 3+; not this unit.
- **The API/MCP tool for OpenAPI/GraphQL** as a second MCP server — the API surface is already
  handled by the unit-1 spec loader; this unit wires **only** the Playwright (browser) MCP server.
  (If the developer chooses to leave room for additional servers, the schema must still validate with
  exactly the `playwright` server present and pinned.)
- **Any change** to the clean `reference_app/**` sources, to units 1–2 public behavior, or to
  protected files (`DESIGN.md`, `META_PLAN.md`, `AGILE_PLAN.md`, `CLAUDE.md`, `.harness/**`).

## Acceptance criteria (enumerated, testable — all static)

### Presence & parseability
1. **File present at the pinned path.** The Playwright-MCP config file exists at the exact path in
   Interfaces §Paths (`connectors/mcp/playwright.mcp.json`).
2. **Valid JSON.** The file parses as valid JSON (a single top-level object) with no syntax errors.

### Shape / schema
3. **`mcpServers` map present.** The top-level object contains an `mcpServers` key whose value is an
   object (map) of server-key → server-definition.
4. **`playwright` server declared.** `mcpServers` contains a server keyed **`playwright`** whose value
   is an object.
5. **Launch shape present.** The `playwright` server definition declares a stdio launch via a
   **`command`** (a non-empty string) and an **`args`** array (a list of strings) — the standard
   Claude Code MCP stdio-server shape. (If the developer additionally includes an optional `env`
   object it must be an object; no secret **values** may appear in it — env is by *reference/name*
   only, consistent with `DESIGN.md §11.4`.)
6. **Package reference present.** The launch (`command` + `args`, taken together) references the
   **official Playwright MCP server package** by name — the token `@playwright/mcp` appears in the
   `args` (or command) as the package being run (see Interfaces §Server entry). The Tester asserts the
   package name token is present.

### Version pinning (supply-chain, §11.10)
7. **Exact version pinned.** The Playwright MCP package reference embeds an **exact** semantic version
   pinned to `@playwright/mcp@<X.Y.Z>` form (a concrete `major.minor.patch`).
8. **No floating specifier.** The package reference does **not** use any floating/unpinned form: the
   Tester asserts the package token is **not** `@playwright/mcp` bare (unversioned), **not**
   `@playwright/mcp@latest`, and does **not** contain a range operator (`^`, `~`, `*`, `>=`, `<=`,
   `>`, `<`, `||`, `x`, or an `@next`/tag). (Criterion 7 asserts the positive exact form; this
   asserts the negative — no floating range/tag/bare name.)

### Grounded-DOM-snapshot / browser options
9. **Headless mode declared.** The config declares the browser runs **headless** (e.g. a `--headless`
   flag in `args`, or the server's documented headless option) so runs are deterministic and
   snapshot-oriented — asserted by the Tester against the file's declared options.
10. **Browser engine declared.** The config declares a concrete browser engine (e.g. `chromium`) via
    the server's documented option (e.g. a `--browser chromium` arg), so the DOM-snapshot channel is
    unambiguous. (The exact engine token is the developer's choice from the server's supported set,
    but a concrete engine must be present and documented.)
11. **Consumable by later units.** The fields unit 5 (sub-agents) and unit 6 (glue) rely on — the
    stable server key `playwright`, the `command`/`args` launch, and the file path — are all present
    and stable, so a later consumer can point Claude Code at this file / this server key without
    editing it. (Verified structurally: server key is exactly `playwright`; path matches §Paths.)

### Docs, determinism, placement, no-regression
12. **Documented.** `connectors/README.md` gains a section documenting: the file path; the
    `mcpServers`/`playwright` shape; the pinned package + **exact** version and the §11.10 rationale;
    the headless + browser-engine options and their meaning; which fields unit 5 / unit 6 consume; and
    the explicit "**not launched here; Node/`npx` is a runtime prerequisite for later units, not
    tested live**" note. (The Tester may assert the README section exists and names the file path and
    the pinned package; deep prose is not asserted.)
13. **Config is target-agnostic (no baked secrets / no target URL).** The file contains **no** target
    UI/API URL and **no** credential value — asserted against the file contents (the reference-app
    URLs `127.0.0.1:5173` / `127.0.0.1:8000` and any Basic-Auth username/password must **not** appear
    in this file; those belong to the unit-2 per-run target config, per `DESIGN.md §11.4`).
14. **Correct home + runnable static tests.** The config lives under `connectors/` at the pinned
    path; tests live under `connectors/tests/` and pass via `uv run pytest connectors/tests -q`. The
    tests are **purely static** — they parse the committed file and assert on its contents; they do
    **not** launch the server, spawn a browser, invoke `npx`/Node, or perform network I/O.
15. **No regressions.** No change to `reference_app/**` behavior, to units 1–2's `spec_loader` /
    `target_config` public APIs or their tests, or to any protected file; Phase 0 `make test` /
    `make eval` / backend pytest still pass. This unit adds only the config file, its tests, and the
    README section, and performs **no writes** and **no network egress** at test time.

## Interfaces / contracts (pin these precisely)

### Paths
- **Config file (binding path + name):** `connectors/mcp/playwright.mcp.json`. (New `connectors/mcp/`
  subdirectory; a JSON file in Claude Code MCP-server config form.)
- **Tests:** `connectors/tests/` (pytest), runnable as `uv run pytest connectors/tests -q` (add a new
  test module alongside the existing unit-1/unit-2 tests; do not modify theirs).
- **Docs:** a new section in `connectors/README.md`.

### File format / schema (Claude Code MCP-server config form)
The committed file is a JSON object with, at minimum:
```
{
  "mcpServers": {
    "playwright": {
      "command": "<string, non-empty>",
      "args": [ "<string>", ... ]          // includes the pinned @playwright/mcp@X.Y.Z reference
                                            // and the headless + browser-engine options
      // optional: "env": { ... }          // names/references only — never secret values
    }
  }
}
```
- The **server key must be exactly `playwright`** (criterion 4/11).
- The launch shape (`command` + `args`) is the standard Claude Code stdio MCP server declaration
  (criterion 5). The developer chooses the concrete `command` (e.g. an `npx`-style launcher) and the
  `args` ordering, but the pinned package reference, headless flag, and browser engine must be present
  and discoverable in the file (criteria 6–10).

### Server entry (pinned identity — supply-chain, §11.10)
- **Package (binding):** the **official Playwright MCP server**, npm package **`@playwright/mcp`**.
- **Pinned version (binding form):** an **exact** `@playwright/mcp@<X.Y.Z>` reference — a concrete
  `major.minor.patch`, no range/tag. The reference example version to ship is **`@playwright/mcp@0.0.41`**
  (see §Interpretations — the binding requirement the tests enforce is *exact pinning*, criteria 7–8;
  the specific number may be updated to the version the team has verified/mirrored, but it must remain
  an exact pin, never floating).
- The browser/DOM-snapshot options (criteria 9–10) are expressed through this server's documented
  argument surface (e.g. `--headless`, `--browser chromium`).

### Errors / behavior
- This unit ships **no code** with runtime error behavior — it is a static config artifact plus static
  validation tests. There is no loader/exception surface to define here. (The glue/agent that
  *launches* this server, and its failure handling, is unit 6/7.)

### Fixtures (guidance for the Tester — not implementation)
- The **committed `connectors/mcp/playwright.mcp.json`** is itself the artifact under test — the
  Tester reads and parses it and asserts criteria 1–13 against its contents. No external fixtures,
  servers, network, or Node/`npx` are needed. The version-pinning checks (7–8) are string/parse
  assertions on the package token in `args`/`command`. The target-agnostic check (13) is a
  substring assertion against the file text.

## Definition of Done
- All acceptance criteria **1–15** pass.
- The Playwright-MCP config file exists at `connectors/mcp/playwright.mcp.json` in Claude Code
  MCP-server config form, declaring the `playwright` server that pins **`@playwright/mcp`** to an
  **exact** version (no floating specifier), with **headless** + a concrete **browser engine**
  declared for grounded DOM snapshots, and no baked target URL / credential value.
- The `connectors/tests/` static-validation suite and the `connectors/README.md` section exist; unit-1
  and unit-2 code, tests, and public APIs are unchanged.
- `uv run pytest connectors/tests -q` is green from a clean checkout under `uv` (units 1–2 tests still
  pass unchanged); the tests perform **no** launch / browser / `npx` / network activity.
- No protected file changed (`DESIGN.md`, `META_PLAN.md`, `AGILE_PLAN.md`, `CLAUDE.md`, `.harness/**`);
  no change to `reference_app/**` behavior. Consistent with `DESIGN.md §2/§4/§5.1/§11.4/§11.10/§12/§13`
  and `AGILE_PLAN.md` D3.
- **Tester-can-author-from-this-alone:** from this spec alone (the pinned file path + JSON
  `mcpServers`/`playwright` shape, the required `command`/`args` launch keys, the pinned
  `@playwright/mcp@X.Y.Z` package + the exact-vs-floating version rules, the headless + browser-engine
  option requirements, the target-agnostic/no-secret rule, and the static-only test constraint), the
  Tester can author the failing presence/shape/schema/version-pinning tests **without reading any
  implementation**.

## Interpretations flagged (for human/reviewer awareness)
- **MCP config format.** `DESIGN.md` states Claude Code brings "native MCP" (§2) and lists
  "playwright-mcp config" under `connectors/` (§13) but does **not** pin an exact file format. This
  spec pins the **Claude Code `.mcp.json` `mcpServers`-map form** as the format and
  `connectors/mcp/playwright.mcp.json` as the path — the standard Claude Code MCP-server declaration,
  consistent with the Claude Code orchestrator chosen in §2. Flagged as an interpretation.
- **Exact package + version.** `DESIGN.md` names "Playwright MCP" (§4/§5.1/§12) and requires pinned
  MCP servers (§11.10) but does **not** name the npm package or a version. This spec pins the
  **official `@playwright/mcp`** package and ships **`@playwright/mcp@0.0.41`** as the reference exact
  pin. The **binding, test-enforced** requirement is *exact pinning* (no `latest`/range/bare name);
  the specific version number may be adjusted to the release the team has verified/mirrored per
  §11.10, provided it stays an exact `X.Y.Z` pin. Flagged as an interpretation.

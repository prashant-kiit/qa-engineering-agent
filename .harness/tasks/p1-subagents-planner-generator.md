# Task: `p1-subagents-planner-generator` — the Planner & Generator **product** sub-agents

## Title
The **two product QA sub-agent definitions** for `.claude/agents/`: the **Planner** and the
**Generator** — the two agents the **QA product** runs at authoring time (DESIGN §4). They are
authored in the repo's existing Claude Code sub-agent format (`.claude/agents/<name>.md` with a YAML
frontmatter block followed by a Markdown system-prompt body), matching the frontmatter schema of the
already-present harness role files. The **Planner** explores the running target application over the
Playwright MCP and turns the freeform BRD plus the seven structured Planner fields into a
**structured test plan**; the **Generator** turns that plan into **grounded, executable TypeScript
Playwright UI tests plus API tests**. Both are bound to the generic QA system prompt (unit 4) and its
reliability rules, and both ground themselves in observed evidence (DOM snapshots via the
Playwright-MCP config, unit 3; API schema via the spec loader, unit 1). This is a **definition/config
artifact** — no runtime code, no live model call, no test generation happens in this unit. **No model
key required**; acceptance is **static** (file presence / frontmatter shape / required textual
references), exactly like the unit-3 MCP config and the unit-4 QA system prompt.

**CRITICAL collision-avoidance framing (encoded in acceptance below):** `.claude/agents/` today holds
**only the five build-harness roles** (`tpm`, `tester`, `developer`, `reviewer`, `git-deployer`).
These two new files are **product** agents — the agents the shipped QA product runs — and must never
be confused with the harness build roles that develop this repo. This spec therefore **pins
product-specific, non-colliding `name` values (`qa-planner`, `qa-generator`) and file paths**, and
requires each file to declare itself a product agent, so the orchestrator/harness can never mistake a
product agent for a build role (or vice-versa).

## Context (plan item)
- **AGILE_PLAN.md → Phase 1 → D5** (`.claude/agents/` Planner & Generator product sub-agents) and the
  **Phase 1 unit table** unit 5. Deps: `p1-qa-system-prompt` (done, `22c9954`), `p1-mcp-config`
  (done, `8f0ac6a`), `p1-connectors-spec-loader` (done, `97f9b53`) — **all met**. Unit 5 is itself a
  dependency of unit 6 (`p1-agent-run-glue`, which wires these two agents into a per-run invocation)
  and unit 7 (the live gate).
- **Backlog unit 5** (`p1-subagents-planner-generator`, status `spec-ready (active)`).
- **DESIGN.md §4 (Sub-agents — the Playwright Agents)** — the binding source. Canonical pipeline:
  **BRD/prompt → Planner → Generator → Execution → Healer → Reports → PR to Git.** Role table:
  - **Planner** — "Explores the running app; turns the BRD/prompt into a **structured test plan**."
  - **Generator** — "Turns the plan into executable **TS Playwright** test code (+ API tests)."
  - **Healer** and **Verifier** also appear in §4 — these are **explicitly OUT of scope** for this
    unit (Phase 2 reliability layer). Only Planner and Generator are built here.
- **DESIGN.md §5 (Reliability layer) — item 1 "Grounding"** (the plan/hint calls this "§5.1"):
  "selectors from the live **DOM snapshot observed via Playwright MCP** (role/label/test-id
  locators), **never invented**; API assertions grounded in the OpenAPI/GraphQL schema." → both
  agents must state they ground in observed DOM snapshots (via the Playwright-MCP config) and in the
  API schema; the Generator especially must anchor with schema-grounded API assertions.
- **DESIGN.md §6 (Prompt layer)** — the one generic system prompt (unit 4) is applied to every run,
  and the **seven structured fields drive the Planner**. The agents **reference** the prompt and the
  fields; they do **not** re-define them.
- **DESIGN.md §2** — "configure the brain, don't build it": the CLI is **Claude Code (headless)** and
  its sub-agents live under `.claude/agents/`. These files are portable brain-configuration, not code.
- **DESIGN.md §13** — repo layout groups the generic QA system prompt and `.claude/agents/`
  sub-agents together as the portable agent-config package; `connectors/` holds the Playwright-MCP
  config and the API-spec loader. This unit's files live under `.claude/agents/`.

**Given app state (contracts to reference — do NOT re-derive, duplicate, or modify):**
- **`.claude/agents/` currently holds only the five build-harness role files** (verified):
  `tpm.md`, `tester.md`, `developer.md`, `reviewer.md`, `git-deployer.md`. Their **frontmatter
  schema** is the exact shape to match: a YAML block delimited by `---` … `---` with fields
  **`name`**, **`description`**, and **`tools`** (a comma-separated capability list), followed by a
  Markdown body. These five files are the harness roles that build this repo — they are **not**
  product agents and must remain **unchanged** by this unit.
- **Unit 4 QA system prompt** — `agent_config/qa_system_prompt.md` (done). It carries: the version
  marker `<!-- QA_SYSTEM_PROMPT_VERSION: v1 -->`; a senior-QA persona; a testing-methodology section;
  five **named reliability rules** with anchors `<!-- RULE: DOM_GROUNDING -->`,
  `<!-- RULE: MEANINGFUL_ASSERTIONS -->`, `<!-- RULE: API_CROSS_CHECK -->`,
  `<!-- RULE: HEAL_VS_REGRESSION -->`, `<!-- RULE: UNTRUSTED_APP_CONTENT -->`; a structured-fields
  reference; and the `{{BRD}}` injection point. Both product agents **reference this prompt by path
  and defer to its reliability rules**; they do not restate or override it.
- **Unit 3 Playwright-MCP config** — `connectors/mcp/playwright.mcp.json` (done). This is the pinned
  MCP server wiring (server identity/version live **there**). Agents **reference this config path**
  as the source of DOM-snapshot grounding; they must **not** duplicate or re-pin the server version.
- **Unit 1 API-spec loader** — `connectors/spec_loader.py` (done): loads an OpenAPI spec into a
  normalized API surface. Agents **reference** the API schema as the grounding source for API
  assertions; they do not re-implement it.
- **Unit 2 target config + seven structured Planner fields** — owned by `connectors/target_config.py`
  (done). The **seven fields** are `target_scope`, `intent`, `expected_behavior`, `priority_risk`,
  `test_data_preconditions`, `out_of_scope_constraints`, `depth`. The Planner **references** them (may
  name them) as the intent that drives planning; it does **not** re-define their schema.
- Root project uses `uv` (`pyproject.toml`); Phase 0/1 static/shape suites run via
  `uv run pytest <dir> -q`. The unit-4 static suite lives at `agent_config/tests/`.

## Scope

### In scope
1. **A Planner product sub-agent file** at the pinned path (Interfaces §Paths) —
   `.claude/agents/qa-planner.md` — with a valid YAML frontmatter block (`name`, `description`,
   `tools`) and a Markdown system-prompt body describing the Planner's role at a WHAT level:
   explore the running target app over the Playwright MCP (DOM snapshots), read the API schema,
   combine what it observes with the freeform BRD and the seven structured Planner fields, and
   produce a **structured test plan** of user journeys + API checks (highest-risk/highest-value
   first; respect out-of-scope). Bound to the unit-4 QA system prompt and its reliability rules.
2. **A Generator product sub-agent file** at the pinned path — `.claude/agents/qa-generator.md` —
   with a valid YAML frontmatter block (`name`, `description`, `tools`) and a Markdown body describing
   the Generator's role: consume the Planner's structured test plan and author **executable
   TypeScript Playwright UI tests + API tests** that honor the reliability rules — DOM-grounded
   locators from observed snapshots (never invented), meaningful/non-vacuous assertions, and
   deterministic **API cross-check anchoring** grounded in the API schema. Bound to the unit-4 QA
   system prompt and its reliability rules.
3. **Explicit product-vs-harness distinction** in each file: a pinned product-agent marker
   (Interfaces §Markers) and frontmatter/body content making clear these are **product** QA agents,
   **distinct from** the build-harness roles (`tpm`/`tester`/`developer`/`reviewer`/`git-deployer`).
4. **A short product-agents doc** at the pinned path (`agent_config/product_agents.md`) that names the
   two product agent files + their `name` values, states they are the QA **product's** Planner and
   Generator (not harness roles), and points to the QA system prompt they bind to.
5. **A static test suite** (pytest) under `agent_config/tests/` that performs **presence / frontmatter
   shape / required-reference / distinctness** validation of the two committed agent files + the doc,
   runnable via `uv run pytest agent_config/tests -q`. Tests **read and parse the committed text files
   only** — no model call, no agent run, no MCP, no browser, no network.

### Out of scope (defer)
- **The Healer and Verifier sub-agents** (DESIGN §4) — Phase 2 reliability layer. Do **not** create
  them.
- **The agent-run glue** — unit 6 (`p1-agent-run-glue`): assembling the per-run invocation, injecting
  the BRD into the prompt, pointing at the MCP config, and writing generated tests to an output path.
  This unit only **defines** the two agents; it does not wire or invoke them.
- **Any live agent run / feeding these agents to a model / actually producing a plan or tests** —
  unit 7 (`p1-agent-authoring-gate`), needs a model key.
- **Re-defining or duplicating**: the seven structured Planner fields' schema (unit 2), the QA system
  prompt's persona/methodology/rule prose (unit 4), the MCP server version (unit 3), or the API
  surface (unit 1). These are **referenced**, never re-implemented.
- **Editing** the five existing harness role files, any `connectors/**` or `agent_config/**` source
  other than the new doc + new tests, `reference_app/**`, or protected files (`DESIGN.md`,
  `META_PLAN.md`, `AGILE_PLAN.md`, `CLAUDE.md`, `.harness/**`).
- **Tenant/target-specific content** — no reference-app URLs, credentials, or per-app BRD text baked
  into the agent files; they are generic product definitions.

## Acceptance criteria (enumerated, testable — all static)

### Presence & format
1. **Planner file present at the pinned path.** `.claude/agents/qa-planner.md` exists, is non-empty,
   and is valid UTF-8 text.
2. **Generator file present at the pinned path.** `.claude/agents/qa-generator.md` exists, is
   non-empty, and is valid UTF-8 text.
3. **Doc present.** `agent_config/product_agents.md` exists and is non-empty.

### Frontmatter shape (matches the existing sub-agent schema)
4. **Planner has a valid YAML frontmatter block.** The Planner file begins with a `---`-delimited
   block that parses as YAML and contains the required fields **`name`**, **`description`**, and
   **`tools`**, each non-empty. (Frontmatter shape mirrors the existing `.claude/agents/*.md` files.)
5. **Generator has a valid YAML frontmatter block.** Same as criterion 4 for the Generator file —
   `---`-delimited YAML with non-empty `name`, `description`, `tools`.
6. **Planner `name` is the pinned product value.** The Planner frontmatter `name` equals exactly
   **`qa-planner`**.
7. **Generator `name` is the pinned product value.** The Generator frontmatter `name` equals exactly
   **`qa-generator`**.

### Collision avoidance / distinct from harness roles
8. **`name` values do not collide with harness roles.** Neither `name` value is any of
   `tpm`, `tester`, `developer`, `reviewer`, `git-deployer` (asserted against the exact set).
9. **Product-agent marker present in each file.** The Planner file contains the exact literal marker
   `<!-- PRODUCT_AGENT: PLANNER -->` and the Generator file contains `<!-- PRODUCT_AGENT: GENERATOR -->`
   (Interfaces §Markers) — the deterministic, greppable signal that each is a **product** agent.
10. **Each file declares itself a product agent (not a harness role).** Each file's body contains a
    statement identifying it as a QA **product** agent that is distinct from the build-harness roles
    (the Tester asserts the case-insensitive substring `product` appears, plus the pinned marker of
    criterion 9). The harness roles are not re-described here.
11. **Harness role files unchanged.** The five existing files (`tpm.md`, `tester.md`, `developer.md`,
    `reviewer.md`, `git-deployer.md`) still exist with their original `name` values
    (`tpm`/`tester`/`developer`/`reviewer`/`git-deployer`) — this unit adds product agents, it does
    not touch harness roles.

### Required references — bind to the prompt & grounding sources (WHAT, by pinned reference)
12. **Both agents reference the unit-4 QA system prompt by path.** Each of the two files contains the
    exact literal substring `agent_config/qa_system_prompt.md`.
13. **Both agents reference the reliability rules.** Each file contains a reference to the reliability
    rules that govern generated tests (the Tester asserts the case-insensitive substring
    `reliability` appears in each file, tying the agent to the unit-4 rule set).
14. **Both agents reference MCP / DOM-snapshot grounding.** Each file contains the case-insensitive
    substring `Playwright MCP` **and** references DOM-snapshot grounding via the unit-3 config — the
    Tester asserts each file contains the exact config path substring
    `connectors/mcp/playwright.mcp.json` and the case-insensitive substring `snapshot`.

### Planner role correctness (distinct, correct role)
15. **Planner produces a structured test plan.** The Planner file body references producing a
    **structured test plan** (case-insensitive substring `test plan`) from exploring the running app.
16. **Planner references BRD + the seven structured fields as its inputs.** The Planner file
    references both the freeform **BRD** (substring `BRD`) and the **seven structured Planner fields**
    (case-insensitive substrings `structured` and `field`), consistent with unit-2 ownership — it
    references, it does not re-define their schema.

### Generator role correctness (distinct, correct role)
17. **Generator consumes the plan and outputs TS Playwright + API tests.** The Generator file body
    references consuming the Planner's **test plan** (substring `plan`) and authoring
    **TypeScript Playwright** UI tests plus **API** tests (case-insensitive substrings `TypeScript`,
    `Playwright`, and `API`).
18. **Generator role is distinct from the Planner role.** The two files describe different jobs
    (Planner = explore→plan; Generator = plan→executable tests), enforced by the distinct
    `PRODUCT_AGENT` markers (criterion 9) and by criterion 15 (Planner → plan) vs criterion 17
    (Generator → tests); the Tester asserts the Generator file does **not** carry the PLANNER marker
    and vice-versa.

### Docs, determinism, placement, no-regression
19. **Doc names both product agents and the distinction.** `agent_config/product_agents.md` contains
    the two file paths (`.claude/agents/qa-planner.md`, `.claude/agents/qa-generator.md`), the two
    `name` values (`qa-planner`, `qa-generator`), states they are the QA **product's** Planner and
    Generator (not harness build roles), and references `agent_config/qa_system_prompt.md`.
20. **Deterministic / static artifacts.** The two agent files and the doc are static committed text;
    reading the same file twice yields identical bytes. No generated/templated/nondeterministic
    content.
21. **Correct home + runnable static tests.** The agent files live under `.claude/agents/` and the doc
    under `agent_config/` at the pinned paths; the new tests live under `agent_config/tests/` and pass
    via `uv run pytest agent_config/tests -q`. The tests are **purely static** — they read/parse the
    committed text files and assert on their contents; they do **not** call a model, run an agent,
    start the MCP, launch a browser, or perform network I/O.
22. **No regressions.** No change to the five harness role files, to `reference_app/**` behavior, or
    to units 1–4's files/public APIs/tests; the pre-existing `agent_config/tests` suite and the
    `connectors/` suites still pass, and Phase 0 `make test` / `make eval` / backend pytest still
    pass. This unit adds only the two agent files, the doc, and the new tests, and performs **no
    writes** and **no network egress** at test time.

## Interfaces / contracts (pin these precisely)

### Paths (binding)
- **Planner agent (binding path + name):** `.claude/agents/qa-planner.md`.
- **Generator agent (binding path + name):** `.claude/agents/qa-generator.md`.
- **Product-agents doc (binding):** `agent_config/product_agents.md`.
- **Tests:** under `agent_config/tests/` (pytest), runnable as `uv run pytest agent_config/tests -q`
  (the Tester adds a new test module here alongside the existing unit-4 static tests).

### Frontmatter contract (binding fields; matches existing `.claude/agents/*.md`)
Each agent file **must** open with a YAML frontmatter block delimited by `---` … `---`, parseable as
YAML, containing at least:

| Field | Requirement |
|---|---|
| `name` | Non-empty. Planner = exactly `qa-planner`; Generator = exactly `qa-generator`. Must NOT be any harness role name. |
| `description` | Non-empty; summarizes the **product** agent's role. |
| `tools` | Non-empty; the capability list the role needs (Planner: exploration/observation + read; Generator: authoring/write). The **exact tool names are the developer's choice** — the Tester asserts only that the field is present and non-empty. |

### Markers (binding literal tokens — deterministic targets for tests and for unit 6)
| Purpose | Binding literal marker | Where |
|---|---|---|
| Planner is a product agent | `<!-- PRODUCT_AGENT: PLANNER -->` | in `.claude/agents/qa-planner.md` body (criteria 9, 18) |
| Generator is a product agent | `<!-- PRODUCT_AGENT: GENERATOR -->` | in `.claude/agents/qa-generator.md` body (criteria 9, 18) |

### Required literal reference substrings (binding — so tests & unit 6 can bind deterministically)
- **Both files:** `agent_config/qa_system_prompt.md` (criterion 12); `connectors/mcp/playwright.mcp.json`
  and `Playwright MCP` and `snapshot` (criterion 14); `reliability` (criterion 13).
- **Planner file:** `test plan` (criterion 15); `BRD`, `structured`, `field` (criterion 16).
- **Generator file:** `plan`, `TypeScript`, `Playwright`, `API` (criterion 17).

The **prose content** of each agent body (how the role reasons, the exact wording of its
instructions) is the developer's to author at a genuine senior-QA quality level (the reviewer judges
this). Only the frontmatter fields, the pinned `name` values, the two `PRODUCT_AGENT` markers, and the
required reference substrings above are **test-binding**.

### Collision-avoidance contract (binding, per this unit's CRITICAL framing)
- The two product agents are named `qa-planner` / `qa-generator` and carry the `PRODUCT_AGENT`
  markers; they occupy `.claude/agents/` **alongside** but **distinct from** the five harness roles.
  The names share **no** value with `{tpm, tester, developer, reviewer, git-deployer}` (criterion 8),
  and each file self-identifies as a product agent (criteria 9–10), so neither the orchestrator nor a
  human can mistake a product agent for a build role or vice-versa.

### Errors / behavior
- This unit ships **no** runtime code — it is static definition/config artifacts (two agent files + a
  doc) plus static validation tests. There is no loader/exception surface to define here. (Reading
  these agents, injecting the BRD into the prompt, and invoking them is unit 6.)

### Fixtures (guidance for the Tester — not implementation)
- The committed `.claude/agents/qa-planner.md`, `.claude/agents/qa-generator.md`, and
  `agent_config/product_agents.md` are themselves the artifacts under test — the Tester reads/parses
  them and asserts criteria 1–22 against their contents. Frontmatter is parsed as YAML (split on the
  leading `---` fences). All other checks are substring/regex assertions on the pinned literal tokens
  above. No external fixtures, model, agent, MCP, browser, or network are needed.

## Definition of Done
- All acceptance criteria **1–22** pass.
- `.claude/agents/qa-planner.md` and `.claude/agents/qa-generator.md` exist with valid YAML
  frontmatter (`name` = `qa-planner` / `qa-generator`, plus `description` and `tools`), each carrying
  its `PRODUCT_AGENT` marker, each referencing the unit-4 QA system prompt + reliability rules and MCP
  DOM-snapshot grounding, with the Planner producing a structured test plan from BRD + the seven
  structured fields and the Generator producing grounded TS-Playwright + API tests from that plan.
- The two product agents are unambiguously **distinct** from the five harness roles (non-colliding
  names + explicit product-agent self-identification); the harness role files are unchanged.
- `agent_config/product_agents.md` documents the two agents, their paths/names, the product-vs-harness
  distinction, and the bound QA system prompt; `agent_config/tests/` static tests pass via
  `uv run pytest agent_config/tests -q` (no model/agent/MCP/browser/network activity).
- No protected file changed (`DESIGN.md`, `META_PLAN.md`, `AGILE_PLAN.md`, `CLAUDE.md`, `.harness/**`);
  no change to `reference_app/**` behavior or to units 1–4's files/public APIs/tests; the existing
  `agent_config/tests` and `connectors/` suites and Phase 0 `make test` / `make eval` / backend pytest
  still pass. Consistent with `DESIGN.md §2/§4/§5/§6/§13` and `AGILE_PLAN.md` D5.
- **Tester-can-author-from-this-alone:** from this spec alone (the two pinned agent paths + the doc
  path + the test location; the required frontmatter fields and exact `name` values; the two literal
  `PRODUCT_AGENT` markers; the harness-role name set to exclude; and the full list of required literal
  reference substrings per file), the Tester can author the failing presence/shape/reference/
  distinctness tests **without reading any implementation**.

## Interpretations flagged (for human/reviewer awareness)
- **Agent `name` values + file paths (collision avoidance).** DESIGN §4 names the roles "Planner" and
  "Generator" but does not pin sub-agent `name`s or filenames. This spec pins **`qa-planner`** and
  **`qa-generator`** at `.claude/agents/qa-planner.md` and `.claude/agents/qa-generator.md`,
  specifically so the **product** agents never collide with the build-harness roles
  (`tpm`/`tester`/`developer`/`reviewer`/`git-deployer`) that share the `.claude/agents/` directory.
  These paths + names are now **binding** for unit 6 to reference. Flagged as an interpretation and as
  the explicit collision-avoidance decision.
- **`PRODUCT_AGENT` markers.** DESIGN pins no marker syntax for distinguishing product vs harness
  agents. This spec pins HTML-comment markers (`<!-- PRODUCT_AGENT: PLANNER -->` /
  `... GENERATOR -->`) as inert-but-greppable signals, giving the Tester deterministic targets and the
  orchestrator/humans an unambiguous product-vs-harness signal. Flagged as an interpretation.
- **Doc location.** The product-agents doc is pinned to `agent_config/product_agents.md` (a plain
  Markdown doc, deliberately **not** placed in `.claude/agents/` so it is never itself parsed as a
  sub-agent definition). Flagged as an interpretation.
- **`tools` field values.** Frontmatter must carry a non-empty `tools` list matching the existing
  schema, but the **exact tool names** are the developer's implementation choice (Planner needs
  observation/read capability; Generator needs authoring/write) — the Tester asserts presence/
  non-emptiness only, not specific tools, to stay HOW-agnostic. Flagged so the reviewer does not treat
  a particular tool set as spec-mandated.
- **§ numbering ("§5.1").** The plan/hint refers to grounding as "§5.1"; in ratified `DESIGN.md` this
  is **§5 item 1 (Grounding)**. This spec cites the DESIGN item number and maps it to the plan's
  label. No content conflict.
- **Healer/Verifier excluded.** DESIGN §4 lists four agents; this unit builds only Planner + Generator
  (Phase 1). Healer + Verifier are Phase 2 and are explicitly out of scope. Flagged so the reviewer
  does not treat their absence as a gap.

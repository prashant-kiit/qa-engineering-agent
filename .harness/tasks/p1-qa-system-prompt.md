# Task: `p1-qa-system-prompt` — `agent_config/` generic QA system prompt v1

## Title
The **one generic QA system prompt (v1)** for `agent_config/`: a single, tenant-agnostic
**prompt/content artifact** (Markdown) that encodes a **senior-QA persona**, a **testing
methodology**, the **named reliability rules** (DOM grounding, meaningful/non-vacuous assertions,
API cross-check anchoring, self-heal-vs-regression discipline, and treating target-app content as
**untrusted data**), a **reference to how the seven structured Planner fields + the freeform BRD
drive the Planner** (the fields themselves are **not** re-defined here — they live in the unit-2
target config), and a **defined, machine-targetable BRD-injection mechanism** (an explicit,
documented placeholder the unit-6 glue replaces per run). It is **generic** — no tenant/customer/
target-specific content, no URLs, no credentials, no secrets. This is a **content artifact only** —
not agent code, not the sub-agent definitions, not the run glue, and it is **not fed to a live
model** in this unit. No model key required; acceptance is **static** (presence / shape / marker /
generic-safety), exactly like the Phase 0 infra units and the unit-3 MCP config.

## Context (plan item)
- **AGILE_PLAN.md → Phase 1 → D4** ("`agent_config/` — generic QA system prompt v1") and the
  **Phase 1 unit table** unit 4. Deps = Phase 0 (done) → met. (Unit 4 has **no** dependency on units
  1/2/3; it is an independent content artifact. It is itself a dependency of unit 5
  `p1-subagents-planner-generator` — which references it — and unit 6 `p1-agent-run-glue` — which
  injects the BRD into it.)
- **Backlog unit 4** (`p1-qa-system-prompt`, status `spec-ready (active)`).
- **DESIGN.md §6 (Prompt layer)** — the binding source: "**One generic system prompt, identical
  across both trigger flows** — the QA-engineer persona + testing methodology + reliability rules
  (grounding, meaningful assertions, API-anchoring, self-heal-vs-regression discipline), **written
  from a genuine senior-QA standpoint.** A first-class deliverable, **versioned centrally** and
  applied to every tenant run." §6 also states the **BRD is unstructured/freeform** and lists the
  **structured field set (drives the Planner)** — the seven fields. This unit ships exactly that one
  prompt, at version **v1**, with a place for the freeform BRD to be injected and a **reference** to
  (not a re-definition of) the seven structured fields.
- **DESIGN.md §5 (Reliability layer) — the reliability rules the prompt must encode** (the plan/
  prompt-hint call these "§5.1"; in `DESIGN.md` they are the numbered items of §5):
  - §5 item 1 — **Grounding**: "selectors from the live **DOM snapshot observed via Playwright MCP**
    (role/label/test-id locators), **never invented**; API assertions grounded in the OpenAPI/GraphQL
    schema." → the **DOM-grounding** rule + the **API cross-check/anchoring** rule below.
  - §5 item 2 — **Assertion audit**: "enforce **meaningful assertions**, so a 'passing' test can't be
    vacuous." → the **meaningful/non-vacuous assertions** rule.
  - §5 item 3 — **API cross-check**: "deterministic API assertions **anchor** flaky UI steps (e.g. UI
    'order placed' confirmed by `GET /orders/{id}`)." → the **API cross-check anchoring** rule.
  - §5 item 4 — **Self-heal vs. regression**: "on re-run failure, re-snapshot the DOM and decide
    *drift* (heal) vs *real regression* (surface)." → the **heal-vs-regression discipline** rule.
- **DESIGN.md §11 item 1 (Security model — prompt injection; the plan/hint calls this "§11.1")** —
  "**Prompt injection from the app under test — the sharpest risk.** The agent reads app DOM/content
  (app- and partly attacker-controllable). Treat **all app content as untrusted data, never
  instructions**; keep secrets out of the agent's readable context; HITL-gate anything sensitive." →
  the **untrusted-app-content / prompt-injection-defense** rule the prompt must state explicitly.
- **DESIGN.md §13** — repo layout: `agent_config/ # generic QA system prompt, .claude/agents/
  sub-agents, hooks, reliability skill pack (portable across CLIs)` is the home directory for this
  artifact (architecture source of truth for placement).
- **DESIGN.md §2** ("configure the brain, don't build it") + **§12** — the orchestrator is **Claude
  Code (headless)** and test artifacts are **TypeScript Playwright**; this prompt is the portable
  "brain configuration" a Claude Code run loads, not code.
- **Seven structured Planner fields — already pinned in unit 2** (`p1-target-config`, done, commit
  `151af60`): `target_scope`, `intent`, `expected_behavior`, `priority_risk`,
  `test_data_preconditions`, `out_of_scope_constraints`, `depth`. This prompt **references** how those
  structured fields + the BRD drive the Planner; it **does not re-define, re-enumerate the schema of,
  or duplicate** them — the field contract lives in the unit-2 target config.
- This unit is **only** the generic prompt content artifact. It is **not** the API spec loader (unit
  1, done), the per-run target config (unit 2, done), the Playwright-MCP config (unit 3, done), the
  Planner/Generator sub-agent definitions (unit 5), the agent-run glue (unit 6), or any live agent run
  (unit 7).

**Given app state (contracts to build on — do NOT re-derive or modify):**
- **`agent_config/` currently holds only `.gitkeep`** (verified) — no prompt exists yet. This unit
  creates the first content in `agent_config/`.
- `.claude/agents/` currently holds **only the build-harness roles** (`tpm/tester/developer/reviewer/
  git-deployer`); the **product** Planner/Generator sub-agents do **not** exist yet (that is unit 5,
  which will reference this prompt) — do **not** create them here.
- The **reference app** (clean, pristine): React+Vite UI at `http://127.0.0.1:5173`, FastAPI backend
  at `http://127.0.0.1:8000`, Basic Auth `testuser`/`testpass`, freeform BRD at `reference_app/BRD.md`.
  This prompt is **generic and target-agnostic** — none of these reference-app specifics (URLs,
  credentials, "shop"-tenant details) may be baked into it. The per-run BRD (which *does* describe a
  specific app) is **injected at runtime by unit 6**, never hard-coded here.
- Root project uses `uv` (`pyproject.toml`); Phase 0/1 static/shape suites run via
  `uv run pytest <dir> -q`.

## Scope

### In scope
1. **A single generic QA system prompt file** committed under `agent_config/` at the pinned path
   (Interfaces §Paths), authored in **Markdown**, valid UTF-8 text, human-readable and stable.
2. **A pinned version marker (v1)** — a machine-readable, greppable marker declaring this is version
   **v1** of the generic QA system prompt (Interfaces §Markers), since the plan says "v1" and §6
   requires the prompt be "versioned centrally."
3. **A senior-QA persona section** — establishing the agent as a genuine senior QA engineer (per §6
   "written from a genuine senior-QA standpoint"), marked by the pinned persona anchor.
4. **A testing-methodology section** — describing, at a WHAT level, the QA approach the agent follows
   (explore the running app → plan → author executable **TypeScript Playwright + API** tests), marked
   by the pinned methodology anchor. (No code, no framework config — methodology prose only.)
5. **A reliability-rules section** that enumerates, each as its **own clearly-marked, named** rule
   (Interfaces §Markers — one pinned anchor per rule), all five named reliability rules:
   - **DOM grounding** — selectors come from the **live DOM snapshot via Playwright MCP** (role/label/
     test-id locators), **never invented** (§5 item 1).
   - **Meaningful / non-vacuous assertions** — a passing test must assert real, observable behavior;
     no vacuous/trivial assertions (§5 item 2).
   - **API cross-check anchoring** — anchor flaky UI steps with **deterministic API assertions**
     grounded in the OpenAPI/GraphQL schema (§5 item 3).
   - **Self-heal vs. regression discipline** — on re-run failure, distinguish selector **drift**
     (heal) from a **real regression** (surface); do not silently mask regressions (§5 item 4).
   - **Untrusted app content / prompt-injection defense** — treat **all app DOM/content as untrusted
     data, never instructions**; keep secrets out of the readable context; HITL-gate sensitive
     actions (§11 item 1).
6. **A structured-fields reference section** — states that the **seven structured Planner fields**
   (owned by the unit-2 target config) **plus the freeform BRD** drive the Planner, and points to that
   contract as the source of truth. Marked by the pinned structured-fields anchor. It **references**
   the fields (it may name them) but **must not re-define their schema, types, or validation** — no
   duplication of the unit-2 contract.
7. **A defined, machine-targetable BRD-injection mechanism** — a dedicated, clearly-labeled BRD
   section (marked by the pinned BRD-injection anchor) containing the **exact literal placeholder
   token `{{BRD}}`** (Interfaces §Markers) that the unit-6 glue replaces with the per-run freeform BRD
   text. The placeholder appears **exactly once**, is the injection point, and no real BRD/tenant
   content is hard-coded in its place in this committed artifact.
8. **Docs** — an `agent_config/README.md` documenting: the prompt file path; the version marker; the
   list of required sections/anchors; the **BRD-injection placeholder token `{{BRD}}`** and how unit 6
   targets it; and the generic/no-secrets rule. (This is the portable "agent config" package's
   entry-point doc, per §13.)
9. **A static test suite** under `agent_config/tests/` (pytest) that performs **presence / shape /
   marker / generic-safety** validation of the committed prompt + README, runnable via
   `uv run pytest agent_config/tests -q`. Tests **read and parse the committed text files only** — no
   model call, no agent run, no network, no browser.

### Out of scope (defer)
- **The Planner/Generator sub-agent definitions** — unit 5 (`p1-subagents-planner-generator`); they
  *reference* this prompt but are authored separately, in `.claude/agents/` frontmatter form.
- **The agent-run glue / actual BRD injection at runtime** — unit 6 (`p1-agent-run-glue`); this unit
  only **defines** the `{{BRD}}` injection point, it does not perform the substitution.
- **Any live agent run / feeding this prompt to a model / generating tests** — unit 7
  (`p1-agent-authoring-gate`), needs a model key.
- **Re-defining or duplicating the seven structured Planner fields' schema/validation** — that lives
  in the unit-2 target config (done); this prompt only **references** it.
- **The Playwright-MCP config** (unit 3, done), the **API spec loader** (unit 1, done), the **per-run
  target config** (unit 2, done) — do not modify their files, APIs, or tests.
- **Hooks, the reliability skill pack, the Verifier/Healer sub-agents** (`DESIGN.md §4/§13`) — later
  units/phases; this unit is only the generic system prompt.
- **Any tenant/target-specific content** — no reference-app URLs (`127.0.0.1:5173`/`127.0.0.1:8000`),
  no credentials (`testuser`/`testpass`), no per-app BRD text; the prompt stays generic.
- **Any change** to the clean `reference_app/**` sources, to units 1–3's files/APIs/tests, or to
  protected files (`DESIGN.md`, `META_PLAN.md`, `AGILE_PLAN.md`, `CLAUDE.md`, `.harness/**`).

## Acceptance criteria (enumerated, testable — all static)

### Presence & format
1. **Prompt file present at the pinned path.** The generic QA system prompt exists at the exact path
   in Interfaces §Paths (`agent_config/qa_system_prompt.md`) and is non-empty, valid UTF-8 Markdown
   text.
2. **README present.** `agent_config/README.md` exists and is non-empty.

### Version marker (v1, §6 "versioned centrally")
3. **Version marker present and pinned to v1.** The prompt file contains the exact literal version
   marker in Interfaces §Markers (`<!-- QA_SYSTEM_PROMPT_VERSION: v1 -->`), declaring version **v1**.
   The Tester asserts the exact literal token is present.

### Required sections / named reliability rules (shape via pinned anchors)
4. **Persona section present.** The prompt contains the pinned persona anchor
   (`<!-- SECTION: PERSONA -->`) followed by non-trivial content establishing a senior-QA persona.
5. **Methodology section present.** The prompt contains the pinned methodology anchor
   (`<!-- SECTION: METHODOLOGY -->`) followed by non-trivial content describing the QA testing
   methodology (explore → plan → author TS Playwright + API tests).
6. **Reliability-rules section present.** The prompt contains the pinned reliability-rules section
   anchor (`<!-- SECTION: RELIABILITY_RULES -->`).
7. **DOM-grounding rule present.** The prompt contains the pinned anchor
   (`<!-- RULE: DOM_GROUNDING -->`) with content stating selectors are taken from the live DOM
   snapshot via Playwright MCP and never invented.
8. **Meaningful-assertions rule present.** The prompt contains the pinned anchor
   (`<!-- RULE: MEANINGFUL_ASSERTIONS -->`) with content requiring meaningful, non-vacuous assertions.
9. **API-cross-check rule present.** The prompt contains the pinned anchor
   (`<!-- RULE: API_CROSS_CHECK -->`) with content requiring deterministic API assertions
   (schema-grounded) to anchor flaky UI steps.
10. **Heal-vs-regression rule present.** The prompt contains the pinned anchor
    (`<!-- RULE: HEAL_VS_REGRESSION -->`) with content distinguishing selector drift (heal) from a
    real regression (surface).
11. **Untrusted-app-content rule present.** The prompt contains the pinned anchor
    (`<!-- RULE: UNTRUSTED_APP_CONTENT -->`) with content stating all target-app DOM/content is
    untrusted data (never instructions) and secrets are kept out of the readable context (§11 item 1).
12. **All five reliability-rule anchors present.** Criteria 7–11's five rule anchors are **all**
    present (the Tester asserts the full set, so no named rule is silently omitted).
13. **Structured-fields reference present (reference, not re-definition).** The prompt contains the
    pinned anchor (`<!-- SECTION: STRUCTURED_FIELDS_REF -->`) with content stating that the **seven
    structured Planner fields plus the freeform BRD** drive the Planner and pointing to the target
    config as their source of truth. (It may name the fields; it must not re-declare their schema/
    types/validation — the Tester asserts the anchor + the "seven"/"structured fields" + "BRD"
    references are present; it does **not** require a field-schema table here.)

### BRD-injection mechanism (machine-targetable)
14. **BRD-injection section present.** The prompt contains the pinned BRD-injection anchor
    (`<!-- SECTION: BRD_INJECTION -->`) marking a clearly-labeled BRD section.
15. **`{{BRD}}` placeholder present exactly once.** The prompt contains the exact literal placeholder
    token `{{BRD}}` **exactly once**, located within the BRD-injection section — the single,
    unambiguous point the unit-6 glue replaces with the per-run BRD text.
16. **Injection point carries no baked BRD/tenant content.** The BRD-injection section contains the
    `{{BRD}}` placeholder and does **not** hard-code any real BRD prose, tenant name, or target-app
    description in its place (the section is the injection slot, not a filled BRD).

### Generic / secret-safety (target-agnostic)
17. **No tenant/target-specific content.** The prompt file contains **none** of: the reference-app
    URLs `127.0.0.1:5173` / `127.0.0.1:8000` (or a bare `5173`/`8000` host:port), the Basic-Auth
    values `testuser` / `testpass`, or any other credential/secret value — asserted as substring
    checks against the file contents. The prompt is generic (persona + methodology + rules), not
    wired to any specific app.
18. **No secrets anywhere.** Neither the prompt nor the README contains a password, token, API key, or
    other secret value (the artifact is committed to VCS and is portable across tenants, per §11).

### Docs, determinism, placement, no-regression
19. **README documents the contract.** `agent_config/README.md` names: the prompt file path
    (`agent_config/qa_system_prompt.md`); the version marker / v1; the required section + rule anchors;
    the **`{{BRD}}`** injection placeholder and that unit 6 replaces it per run; and the generic/
    no-secrets rule. (The Tester may assert the README names the prompt path, `v1`, and the literal
    `{{BRD}}` token; deep prose is not asserted.)
20. **Deterministic / static artifact.** The prompt and README are static committed text; reading the
    same file twice yields identical bytes. No generated/templated/nondeterministic content in the
    committed files (the only intended runtime substitution is the `{{BRD}}` token by unit 6).
21. **Correct home + runnable static tests.** The prompt + README live under `agent_config/` at the
    pinned paths; tests live under `agent_config/tests/` and pass via
    `uv run pytest agent_config/tests -q`. The tests are **purely static** — they read/parse the
    committed text files and assert on their contents; they do **not** call a model, run an agent,
    launch a browser, or perform network I/O.
22. **No regressions.** No change to `reference_app/**` behavior, to units 1–3's files/public APIs/
    tests, or to any protected file; Phase 0 `make test` / `make eval` / backend pytest and the
    `connectors/` suites still pass. This unit adds only the prompt, the README, and the tests under
    `agent_config/`, and performs **no writes** and **no network egress** at test time.

## Interfaces / contracts (pin these precisely)

### Paths
- **Prompt file (binding path + name):** `agent_config/qa_system_prompt.md` (Markdown).
- **Docs (binding):** `agent_config/README.md`.
- **Tests:** `agent_config/tests/` (pytest), runnable as `uv run pytest agent_config/tests -q`.

### Markers (binding literal tokens — so tests and later units 5/6 can target the prompt deterministically)
The committed prompt **must contain** the following exact literal tokens (embedded as Markdown/HTML
comments so they are inert when the prompt is read by a model, yet greppable by tests and glue). Each
anchor introduces a human-readable section/rule covering the corresponding topic; the Tester asserts
**anchor presence** (and, for the BRD/version, exact form + count), not specific prose.

| Purpose | Binding literal marker | Notes |
|---|---|---|
| Version (v1) | `<!-- QA_SYSTEM_PROMPT_VERSION: v1 -->` | criterion 3 — exact literal, declares v1 |
| Persona section | `<!-- SECTION: PERSONA -->` | criterion 4 |
| Methodology section | `<!-- SECTION: METHODOLOGY -->` | criterion 5 |
| Reliability-rules section | `<!-- SECTION: RELIABILITY_RULES -->` | criterion 6 |
| Rule: DOM grounding | `<!-- RULE: DOM_GROUNDING -->` | criterion 7 (§5 item 1) |
| Rule: meaningful assertions | `<!-- RULE: MEANINGFUL_ASSERTIONS -->` | criterion 8 (§5 item 2) |
| Rule: API cross-check anchoring | `<!-- RULE: API_CROSS_CHECK -->` | criterion 9 (§5 item 3) |
| Rule: heal vs. regression | `<!-- RULE: HEAL_VS_REGRESSION -->` | criterion 10 (§5 item 4) |
| Rule: untrusted app content | `<!-- RULE: UNTRUSTED_APP_CONTENT -->` | criterion 11 (§11 item 1) |
| Structured-fields reference | `<!-- SECTION: STRUCTURED_FIELDS_REF -->` | criterion 13 (references unit-2 fields; no re-definition) |
| BRD-injection section | `<!-- SECTION: BRD_INJECTION -->` | criterion 14 |
| **BRD placeholder token** | `{{BRD}}` | criteria 15–16 — appears **exactly once**, inside the BRD-injection section; the unit-6 glue replaces it |

- The **version marker** and **`{{BRD}}` placeholder** are the two machine-critical tokens (exact form
  is binding; `{{BRD}}` count is exactly one). The section/rule anchors are binding **presence**
  contracts that give the Tester deterministic targets and give units 5/6 stable references; the
  developer authors the surrounding prose (WHAT the rules say, per Scope §5), which the reviewer
  judges for senior-QA quality.

### Generic-safety (binding rule, per `DESIGN.md §11`)
- The prompt is **portable across tenants** and committed to VCS: it must contain **no** target URL,
  **no** credential value, and **no** secret. The only per-run/tenant-specific content ever present is
  the freeform BRD, and that is introduced **only at runtime** by unit 6 substituting `{{BRD}}` — the
  committed artifact carries the placeholder, never real BRD/tenant text (criteria 16–18).

### Errors / behavior
- This unit ships **no code** with runtime behavior — it is a static content artifact (prompt +
  README) plus static validation tests. There is no loader/exception surface to define here. (The glue
  that reads this prompt and substitutes `{{BRD}}`, and its error handling, is unit 6.)

### Fixtures (guidance for the Tester — not implementation)
- The **committed `agent_config/qa_system_prompt.md`** and **`agent_config/README.md`** are themselves
  the artifacts under test — the Tester reads/parses them and asserts criteria 1–20 against their
  contents. No external fixtures, model, agent, browser, or network are needed. The marker checks are
  substring/regex assertions on the literal tokens above; the `{{BRD}}` count check asserts exactly one
  occurrence; the generic-safety checks (17–18) are substring assertions for the forbidden
  URL/credential tokens.

## Definition of Done
- All acceptance criteria **1–22** pass.
- The generic QA system prompt exists at `agent_config/qa_system_prompt.md`, is version-**v1**-marked,
  and contains the senior-QA persona, testing methodology, all five named reliability rules (DOM
  grounding, meaningful assertions, API cross-check anchoring, heal-vs-regression, untrusted-app-
  content), a structured-fields **reference** (not a re-definition), and a BRD-injection section with
  the single literal `{{BRD}}` placeholder — all discoverable via the pinned marker tokens.
- The prompt is **generic**: no target URL, credential, secret, or baked tenant/BRD content.
- `agent_config/README.md` documents the prompt path, v1, the required anchors, the `{{BRD}}`
  injection point (targeted by unit 6), and the generic/no-secrets rule; `agent_config/tests/` static
  tests exist and pass via `uv run pytest agent_config/tests -q` (performing no model/agent/browser/
  network activity).
- No protected file changed (`DESIGN.md`, `META_PLAN.md`, `AGILE_PLAN.md`, `CLAUDE.md`, `.harness/**`);
  no change to `reference_app/**` behavior or to units 1–3's files/public APIs/tests; Phase 0
  `make test` / `make eval` / backend pytest and the `connectors/` suites still pass. Consistent with
  `DESIGN.md §2/§5/§6/§11/§12/§13` and `AGILE_PLAN.md` D4.
- **Tester-can-author-from-this-alone:** from this spec alone (the pinned prompt + README + test paths,
  the exact version marker `<!-- QA_SYSTEM_PROMPT_VERSION: v1 -->`, the full list of required section/
  rule anchor tokens, the exact `{{BRD}}` placeholder with its exactly-once + in-section rules, the
  forbidden target-URL/credential/secret substrings for generic-safety, and the static-only test
  constraint), the Tester can author the failing presence/shape/marker/generic-safety tests **without
  reading any implementation**.

## Interpretations flagged (for human/reviewer awareness)
- **Prompt file path/name.** `DESIGN.md §13` names "generic QA system prompt" under `agent_config/`
  but does not pin a filename. This spec pins **`agent_config/qa_system_prompt.md`**. Flagged as an
  interpretation (path is now binding for units 5/6 to reference).
- **Marker convention (`<!-- ... -->` anchors + `{{BRD}}`).** `DESIGN.md §6` requires the prompt be
  "versioned centrally," carry the reliability rules, and have a place for the freeform BRD, but does
  not pin a marker syntax. This spec pins HTML-comment section/rule anchors + the literal `{{BRD}}`
  placeholder so the artifact is deterministically testable **and** gives unit 6 a single unambiguous
  substitution target (and unit 5 stable section references). The prose *content* of each section is
  the developer's to author (reviewer judges senior-QA quality); only the marker presence + the two
  machine-critical tokens (version, `{{BRD}}`) are test-binding. Flagged as an interpretation.
- **§ numbering ("§5.1"/"§11.1").** The plan/prompt-hint refer to grounding as "§5.1" and prompt
  injection as "§11.1"; in the ratified `DESIGN.md` these are the **numbered items of §5 (Reliability
  layer)** and **§11 item 1 (Security model)** respectively. This spec cites the `DESIGN.md` item
  numbers precisely and maps them to the plan's labels. No content conflict.
- **Structured fields — reference only.** Per the prompt-hint and unit-2 ownership, this prompt
  **references** the seven Planner fields (may name them) but does **not** re-define their schema; the
  contract stays in `connectors` (unit 2). The Tester therefore does not require a field-schema table
  in this artifact. Flagged so the reviewer does not treat the absence of a field table as a gap.

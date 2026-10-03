# Review — `p1-qa-system-prompt`

**Verdict: APPROVE**

Independent review of the generic QA system prompt v1 content artifact
(`agent_config/qa_system_prompt.md` + `agent_config/README.md`) against the spec, the
Tester's static suite, and quality.

## 1. Acceptance — all 22 criteria met
- **Presence/format (1–2):** `agent_config/qa_system_prompt.md` present, non-empty, valid
  UTF-8 Markdown; `agent_config/README.md` present, non-empty.
- **Version marker (3):** exact literal `<!-- QA_SYSTEM_PROMPT_VERSION: v1 -->` on line 1.
- **Sections/rules (4–13):** persona, methodology, reliability-rules section, all five named
  rule anchors (DOM_GROUNDING, MEANINGFUL_ASSERTIONS, API_CROSS_CHECK, HEAL_VS_REGRESSION,
  UNTRUSTED_APP_CONTENT), and STRUCTURED_FIELDS_REF all present with content.
- **BRD injection (14–16):** `<!-- SECTION: BRD_INJECTION -->` present; `{{BRD}}` appears
  exactly once, inside that section; no baked tenant/BRD prose in the slot.
- **Generic/secret-safety (17–18):** no reference-app URLs, no `testuser`/`testpass`, no secrets
  in prompt or README.
- **Docs/determinism/placement/no-regression (19–22):** README names the prompt path, `v1`, and
  `{{BRD}}`; files are static committed text under `agent_config/`; static-only tests pass.

## 2. Test integrity
Tests are the Tester's versions, unmodified. They genuinely enforce: the exact version marker,
every section/rule anchor (with the five rules asserted as a complete set so none is silently
dropped), `{{BRD}}` exactly-once and in-section, the structured-fields "seven"/"structured field"
+ "BRD" references, and the generic/secret negative denylist. The denylist (17/18) is best-effort
against the spec-named tokens, which the Tester documented and which matches the spec's own
substring-check guidance — acceptable, not a gap.

## 3. Scope
No over-reach. No Planner/Generator sub-agent definitions, no run glue, no live-run/model content.
Change is additive: prompt + README + `agent_config/tests/` only. `reference_app/` and
`connectors/` are untouched (verified via `git status`). The single `.harness/backlog.md` edit is a
status flip (todo → spec-ready active) — orchestration bookkeeping, not a deliverable change.

## 4. Quality (prose, not just anchors)
- **Persona** reads as a genuine senior QA engineer: skeptical of vacuous green, journeys+risk over
  line coverage, no fabrication of locators/endpoints/assertions.
- **Methodology** is a coherent explore → plan → author → refine loop producing TS Playwright UI +
  API tests, grounded in observed app + BRD/fields.
- **Reliability rules are substantive and correct:** DOM grounding binds locators to observed MCP
  snapshots and forbids invention (prefers role/label/test-id); meaningful-assertions requires
  assertions capable of failing and bans trivially-true ones; API cross-check anchors flaky UI to
  schema-grounded deterministic assertions; heal-vs-regression distinguishes drift (heal) from real
  regression (surface) and forbids masking; untrusted-app-content faithfully encodes §11 item 1
  (app content is data never instructions, secrets out of readable context, HITL-gate sensitive
  actions).
- **Genuinely generic:** no tenant/customer specifics, no URLs, no credentials; the BRD slot is the
  single empty `{{BRD}}` placeholder.
- **Structured-fields section** correctly references the seven fields and defers schema/validation
  ownership to the unit-2 target config — a reference, not a re-definition (spec permits naming).

## Test run

```
$ uv run pytest agent_config/tests -q
.....................                                                    [100%]
21 passed in 0.01s

$ uv run pytest connectors/tests -q
.....s..................................................................  [ 79%]
...................                                                       [100%]
90 passed, 1 skipped in 1.77s
```

No protected source, `reference_app/**`, or `connectors/` files changed.

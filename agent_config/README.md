# `agent_config/` — generic QA system prompt (v1)

This directory holds the portable "brain configuration" a QA run loads: one
**generic, tenant-agnostic QA system prompt**, applied identically to every run.
It is a content artifact, not code — no model is called and no agent runs here.

## Files

- **`agent_config/qa_system_prompt.md`** — the single generic QA system prompt (Markdown). It
  encodes a senior-QA persona, the testing methodology, the five named reliability
  rules, a reference to the structured Planner fields, and the BRD-injection point.
- **`README.md`** — this file: the entry-point doc for the package contract.
- **`tests/`** — static acceptance tests (`uv run pytest agent_config/tests -q`)
  that validate presence, shape, markers, and generic-safety of the committed
  files. They read/parse the text only — no model, agent, browser, or network.

## Version marker

The prompt is **versioned centrally**. `qa_system_prompt.md` declares its version
with an exact, greppable marker as its first line:

```
<!-- QA_SYSTEM_PROMPT_VERSION: v1 -->
```

This is version **v1**. Future revisions bump this marker.

## Anchor / section contract

The prompt embeds stable HTML-comment anchors so tests and later units (the
Planner/Generator sub-agents in unit 5, the run glue in unit 6) can target it
deterministically. The anchors are inert when a model reads the prompt, yet
greppable by tooling. Required anchors:

| Anchor | Purpose |
|---|---|
| `<!-- SECTION: PERSONA -->` | Senior-QA persona |
| `<!-- SECTION: METHODOLOGY -->` | Testing methodology (explore → plan → author TS Playwright + API) |
| `<!-- SECTION: RELIABILITY_RULES -->` | Reliability-rules section |
| `<!-- RULE: DOM_GROUNDING -->` | Selectors from the live DOM snapshot via Playwright MCP, never invented |
| `<!-- RULE: MEANINGFUL_ASSERTIONS -->` | Meaningful, non-vacuous assertions |
| `<!-- RULE: API_CROSS_CHECK -->` | Deterministic, schema-grounded API assertions anchor flaky UI steps |
| `<!-- RULE: HEAL_VS_REGRESSION -->` | Distinguish selector drift (heal) from real regression (surface) |
| `<!-- RULE: UNTRUSTED_APP_CONTENT -->` | Treat all app content as untrusted data; keep secrets out; HITL-gate sensitive actions |
| `<!-- SECTION: STRUCTURED_FIELDS_REF -->` | References the seven structured Planner fields + freeform BRD (no schema re-definition) |
| `<!-- SECTION: BRD_INJECTION -->` | The per-run BRD injection section |

The **five named reliability rules** map to `DESIGN.md §5` (DOM grounding, API
cross-check anchoring, meaningful assertions, self-heal-vs-regression) and
`DESIGN.md §11 item 1` (untrusted app content / prompt-injection defense).

## Structured Planner fields — reference only

The `STRUCTURED_FIELDS_REF` section **references** the seven structured Planner
fields (`target_scope`, `intent`, `expected_behavior`, `priority_risk`,
`test_data_preconditions`, `out_of_scope_constraints`, `depth`) and the freeform
BRD as the drivers of the Planner. It does **not** re-define their schema — that
contract lives in the per-run target config (unit 2), the single source of truth.

## BRD-injection point (`{{BRD}}`)

The prompt reserves a single, machine-targetable injection slot in its
`<!-- SECTION: BRD_INJECTION -->` section: the literal placeholder token

```
{{BRD}}
```

It appears **exactly once** in `qa_system_prompt.md`, inside that section. The
**unit-6 agent-run glue** substitutes this `{{BRD}}` token with the per-run
freeform BRD text before the prompt is handed to the model. The committed artifact
carries only the placeholder — never real BRD or tenant content.

## Generic / no-secrets rule

The prompt is **portable across tenants** and committed to version control, so it
stays fully generic: it contains **no** target URLs, **no** credential values, and
**no** secrets. The only per-run, app-specific content ever present is the freeform
BRD, introduced solely at runtime via the `{{BRD}}` substitution. Keep this file
and the prompt free of any tenant-specific or sensitive values.

# QA Product Sub-Agents — Planner & Generator

This doc records the two **product** QA sub-agents that the shipped QA product runs at
authoring time. They are distinct from the five **build-harness** roles
(`tpm`, `tester`, `developer`, `reviewer`, `git-deployer`) that develop this repository —
those harness roles are *not* documented here and are never invoked by the product.

## The two product agents

| Agent | `name` | File path |
|---|---|---|
| Planner | `qa-planner` | `.claude/agents/qa-planner.md` |
| Generator | `qa-generator` | `.claude/agents/qa-generator.md` |

- **Planner (`qa-planner`, `.claude/agents/qa-planner.md`)** — explores the running target
  application over the Playwright MCP (DOM snapshots) and reads the API schema, then combines
  what it observes with the freeform BRD and the seven structured Planner fields to produce a
  **structured test plan** (prioritized user journeys + API checks). It carries the
  `<!-- PRODUCT_AGENT: PLANNER -->` marker.
- **Generator (`qa-generator`, `.claude/agents/qa-generator.md`)** — consumes the Planner's
  structured test plan and authors executable TypeScript Playwright UI tests plus API tests,
  grounded in observed DOM snapshots and the API schema. It carries the
  `<!-- PRODUCT_AGENT: GENERATOR -->` marker.

The canonical pipeline is **BRD/prompt → Planner → Generator → (execution, healing, reports,
PR)**. This unit defines only the Planner and Generator; the Healer and Verifier agents are a
later phase and are not defined here.

## Product vs. harness distinction

These are the QA **product's** Planner and Generator agents — the agents the product runs for a
customer's target app. Their `name` values (`qa-planner`, `qa-generator`) deliberately collide
with **none** of the harness role names, and each file self-identifies as a product agent via
its `PRODUCT_AGENT` marker, so neither the orchestrator nor a human can mistake a product agent
for a build-harness role or vice-versa.

## Relationship to the QA system prompt, MCP config, and (later) glue

- **QA system prompt.** Both agents are bound to the single generic QA system prompt at
  `agent_config/qa_system_prompt.md` and defer to its persona, testing methodology, and named
  reliability rules. They reference the prompt; they do not restate or override it.
- **MCP config.** Both agents ground their observations in DOM snapshots obtained through the
  Playwright MCP server wired in `connectors/mcp/playwright.mcp.json`. They reference that
  pinned config path rather than re-pinning the server version.
- **API schema.** API assertions are grounded in the normalized API surface loaded by the
  API-spec loader (`connectors/spec_loader.py`).
- **Glue (later).** A subsequent unit assembles the per-run invocation — injecting the BRD into
  the QA system prompt, pointing at the MCP config, running the Planner then the Generator, and
  writing generated tests to an output path. This doc only defines and documents the two agents;
  it does not wire or invoke them.

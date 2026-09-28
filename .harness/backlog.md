# Backlog — Phase 1 (In-sandbox authoring loop, local first)

Ordered units of work for the TDD harness. The **TPM** picks the top unit whose deps are `done`,
writes its spec to `.harness/tasks/<id>.md`, and the `/tdd` cycle proceeds.

**Status lifecycle:** `todo` → `spec-ready` (TPM wrote spec) → `in-progress` → `done`.
Source of truth for scope: `AGILE_PLAN.md` (Phase 1, D1–D7) and `DESIGN.md`.

> **Phase 0 is DONE** (all units merged to master; exit gate passed). See `AGILE_PLAN.md` for the
> condensed Phase 0 record. Phase 0 units (`p0-design-note`, `p0-scaffold`, `p0-shop-backend`,
> `p0-shop-frontend`, `p0-brd-release`, `p0-playwright-smoke`, `p0-eval-harness`) are all `done`.

## Phase 1 units

| # | id | Unit | Depends on | Needs model key? | Status |
|---|----|------|-----------|:---:|--------|
| 1 | `p1-connectors-spec-loader` | `connectors/` OpenAPI **spec loader**: load a spec from URL/file/object → a normalized, deterministic, JSON-serializable **API surface** (per-operation method/path/params/request+response schemas with intra-doc `$ref` resolved + declared security) for grounding API assertions (`DESIGN.md §5.1/§13`). GraphQL accommodated at the interface level; adapter deferred. Tested purely with fixtures. | — (Phase 0 done) | no | **done** (merged, commit `97f9b53`) |
| 2 | `p1-target-config` | `connectors/` **per-run target config**: schema + loader for target UI URL, API spec source (feeds unit 1), BRD source path, Basic-Auth credential **reference** (no inline secrets, §11.4), and the **seven structured Planner fields** (§6). Ships a concrete reference-app example config. Acceptance = schema validation + example loads + secret-safety. | `p1-connectors-spec-loader` | no | **done** |
| 3 | `p1-mcp-config` | `connectors/` **Playwright-MCP config**: the MCP server wiring the agent uses for grounded DOM snapshots (§4/§5.1), pinned server identity/version (§11.10). Placed under `connectors/` per §13. Acceptance = presence/shape/schema. | — (Phase 0 done) | no | **done** |
| 4 | `p1-qa-system-prompt` | `agent_config/` **generic QA system prompt v1** (§6): senior-QA persona + methodology + reliability rules (DOM grounding, meaningful assertions, API-anchoring, heal-vs-regression, untrusted-app-content §11.1) + a defined **BRD-injection mechanism**. No tenant-specific content. Acceptance = presence/shape (required sections + rules + injection point). | — (Phase 0 done) | no | done |
| 5 | `p1-subagents-planner-generator` | `.claude/agents/` **Planner** & **Generator** product sub-agents (§4), in the repo's existing sub-agent frontmatter format: Planner explores the running app over MCP → structured test plan from BRD + fields; Generator → grounded TS-Playwright + API tests. Acceptance = presence/shape (valid frontmatter; reference the QA prompt + reliability rules + MCP grounding; distinct from harness roles). | `p1-qa-system-prompt`, `p1-mcp-config`, `p1-connectors-spec-loader` | no | **done** |
| 6 | `p1-agent-run-glue` | **Agent-run glue**: assemble a per-run authoring invocation (read target config + load spec + inject BRD into prompt + point at MCP config + Planner/Generator; write generated tests to a pinned output path). **Unit-tested with a MOCK agent** in place of the real Claude Code call — full wiring/output contract verified without a key. | `p1-target-config`, `p1-subagents-planner-generator`, `p1-mcp-config`, `p1-qa-system-prompt` | no (mock) | todo |
| 7 | `p1-agent-authoring-gate` | **Live gate + first agent-generated tests committed**: run the glue for real (headless Claude Code + Playwright MCP, Planner→Generator) against the running clean reference app + BRD → runnable DOM/schema-grounded TS + API tests that **pass on clean**; commit them; via `eval/score.py` show injected-bug **catch rate better than a naive baseline** (naive floor pinned in this unit's spec). **BLOCKED: requires a model API key.** | `p1-agent-run-glue` (+ all above) | **YES** | todo (blocked on key) |

### Phase 1 exit gate (from `AGILE_PLAN.md` / `META_PLAN.md`)
- From `BRD.md` + the running reference app, the agent (Claude Code + Playwright MCP,
  Planner→Generator) produces **runnable, DOM/schema-grounded** TS Playwright + API tests that
  **pass on the clean app**. *(Unit 7 — needs model key.)*
- The `eval/` harness shows the agent-generated suite's injected-bug **catch rate is better than a
  naive baseline**. *(Unit 7 — needs model key.)*
- Units 1–6 (all key-free) merged and green.

> **Hard external prerequisite (recorded in `AGILE_PLAN.md` → Conflicts):** the live gate (unit 7)
> needs a model API key — none is set in this environment (`claude` CLI present, credentials absent).
> Units 1–6 are buildable/mergeable now; unit 7 is spec-ready but parked until a key is supplied.
>
> Notes: units 3–5 are **config/prompt/sub-agent** artifacts — the Tester encodes their acceptance as
> **presence/shape/schema** checks (like the Phase 0 infra units), not behavioral unit tests. Units 1,
> 2, 6 are code/glue and follow full red→green TDD (unit 6 with a mock agent).

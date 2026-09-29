# Backlog — Phase 1 (In-sandbox authoring loop, local first)

Ordered units of work for the TDD harness. The **TPM** picks the top unit whose deps are `done`,
writes its spec to `.harness/tasks/<id>.md`, and the `/tdd` cycle proceeds.

**Status lifecycle:** `todo` → `spec-ready` (TPM wrote spec) → `in-progress` → `done`.
Source of truth for scope: `AGILE_PLAN.md` (Phase 1, D1–D8) and `DESIGN.md`.

> **Phase 0 is DONE** (all units merged to master; exit gate passed). See `AGILE_PLAN.md` for the
> condensed Phase 0 record. Phase 0 units (`p0-design-note`, `p0-scaffold`, `p0-shop-backend`,
> `p0-shop-frontend`, `p0-brd-release`, `p0-playwright-smoke`, `p0-eval-harness`) are all `done`.

> **BUILD-CLI DEVIATION (human-authorized 2026-09-28; recorded in `AGILE_PLAN.md` → Conflicts):** the
> concrete in-sandbox coding agent for this build is **OpenCode** (open-source terminal coding agent)
> driving **OpenAI `gpt-4o-mini`** via a platform-owned `OPENAI_API_KEY` — **not** Claude Code + Claude.
> This is design-sanctioned (`DESIGN.md §2` configurable-CLI + `META_PLAN.md` Phase-7 open-CLI-swap) and
> cleanly enabled by the unit-6 `AgentRunner` seam. The model is a bumpable config value; `gpt-4o-mini`
> is a weak agentic model flagged as a Phase-2 reliability risk (not a Phase-1 blocker). Unit-5's
> `.claude/agents/*` are **kept** (Claude-CLI path, for the Phase-7 multi-CLI story); the OpenCode unit
> **adds** OpenCode-format agent definitions referencing the same portable QA prompt.

> **CREDENTIAL-EXPOSURE CARVE-OUT DEVIATION (human-authorized 2026-09-29, via explicit in-session
> `AskUserQuestion` — recorded in `AGILE_PLAN.md` → Conflicts):** the reference app's login is a real
> in-app form (`reference_app/frontend/src/views/LoginView.tsx`, credentials held only in local React
> state, never persisted) — the exploring agent cannot log in knowing only the Basic-Auth **reference
> name** unit 6/7 deliberately pass by default. The human chose a **scoped, opt-in, default-off** fixture
> carve-out (new unit `p1-agent-authoring-gate-credential-exception`, inserted before unit 8) over
> building the full `--secrets`-file passthrough mechanism now (deferred, flagged as a Phase 2+ backlog
> candidate) or deferring the live gate entirely. The carve-out applies **only** to the reference app's
> published, non-secret `testuser`/`testpass` fixture account (already plaintext in Phase-0 test files);
> it does **not** loosen the reference-only default for real target-app/tenant credentials.

## Phase 1 units

| # | id | Unit | Depends on | Needs model key? | Status |
|---|----|------|-----------|:---:|--------|
| 1 | `p1-connectors-spec-loader` | `connectors/` OpenAPI **spec loader**: load a spec from URL/file/object → a normalized, deterministic, JSON-serializable **API surface** (per-operation method/path/params/request+response schemas with intra-doc `$ref` resolved + declared security) for grounding API assertions (`DESIGN.md §5.1/§13`). GraphQL accommodated at the interface level; adapter deferred. Tested purely with fixtures. | — (Phase 0 done) | no | **done** (merged, commit `97f9b53`) |
| 2 | `p1-target-config` | `connectors/` **per-run target config**: schema + loader for target UI URL, API spec source (feeds unit 1), BRD source path, Basic-Auth credential **reference** (no inline secrets, §11.4), and the **seven structured Planner fields** (§6). Ships a concrete reference-app example config. Acceptance = schema validation + example loads + secret-safety. | `p1-connectors-spec-loader` | no | **done** (merged, commit `151af60`) |
| 3 | `p1-mcp-config` | `connectors/` **Playwright-MCP config**: the MCP server wiring the agent uses for grounded DOM snapshots (§4/§5.1), pinned server identity/version (§11.10). Placed under `connectors/` per §13. Acceptance = presence/shape/schema. | — (Phase 0 done) | no | **done** (merged, commit `8f0ac6a`) |
| 4 | `p1-qa-system-prompt` | `agent_config/` **generic QA system prompt v1** (§6): senior-QA persona + methodology + reliability rules (DOM grounding, meaningful assertions, API-anchoring, heal-vs-regression, untrusted-app-content §11.1) + a defined **BRD-injection mechanism**. No tenant-specific content. Acceptance = presence/shape (required sections + rules + injection point). | — (Phase 0 done) | no | **done** (merged, commit `22c9954`) |
| 5 | `p1-subagents-planner-generator` | `.claude/agents/` **Planner** & **Generator** product sub-agents (§4), in the repo's existing sub-agent frontmatter format: Planner explores the running app over MCP → structured test plan from BRD + fields; Generator → grounded TS-Playwright + API tests. Acceptance = presence/shape (valid frontmatter; reference the QA prompt + reliability rules + MCP grounding; distinct from harness roles). **Kept as the Claude-CLI path** (Phase-7 multi-CLI). | `p1-qa-system-prompt`, `p1-mcp-config`, `p1-connectors-spec-loader` | no | **done** (merged, commit `f7bee09`) |
| 6 | `p1-agent-run-glue` | **Agent-run glue** at `runner/authoring.py`: assemble a per-run authoring invocation (read target config + load spec + inject BRD into prompt + point at MCP config + Planner/Generator; write generated tests to a pinned output path) and drive an **injectable `AgentRunner` seam** — `agent_runner(AuthoringInvocation) -> AgentRunOutput`. **Unit-tested with a MOCK runner** — full wiring/output contract verified without a key. | `p1-target-config`, `p1-subagents-planner-generator`, `p1-mcp-config`, `p1-qa-system-prompt` | no (mock) | **done** (merged, commit `c3694e0`) |
| 7 | `p1-opencode-runner` | **OpenCode runner adapter** — the concrete `AgentRunner` binding **OpenCode headless + OpenAI `gpt-4o-mini`** to the unit-6 seam: reads the model credential from the `OPENAI_API_KEY` **reference** (platform-owned §11.5, never inlined/logged), wires the Playwright-MCP config into OpenCode's config format, translates the Planner→Generator flow (generic QA prompt with BRD injected + seven fields) into OpenCode's headless-run mechanism at `model=openai/gpt-4o-mini`, and captures the generated TS+API test files as `AgentRunOutput.generated_tests`. Ships the **OpenCode connector config** (`opencode.json`-format: model + MCP) + **OpenCode-format Planner/Generator agent definitions** referencing the shared `agent_config/qa_system_prompt.md`. **Unit-tested WITHOUT the key** by injecting the subprocess/command runner and asserting the **constructed OpenCode invocation** (command/args/`--model`/MCP wiring/prompt-with-BRD/output capture) — no live network/model/browser/OpenCode-process call. Secret is a reference only, never logged. | `p1-agent-run-glue` (+ all above) | **no (mock/dry-run)** | **done** |
| 7.5 | `p1-agent-authoring-gate-credential-exception` | **Scoped, opt-in credential-exposure carve-out** (human-authorized, see the deviation note above): `run_authoring` gains keyword-only `expose_credential_for_exploration: bool = False`; when `True` it resolves the target-app credential (via the config's existing `resolve_credential()`) and sets it on a new optional `AuthoringInvocation.basic_auth_credential_value` field (default `None`) — `RunResult` never exposes it. `OpenCodeRunner._compose_message` stays byte-identical when the field is `None` (default; `test_c13_target_auth_stays_reference_only` unmodified) and includes the resolved value in the composed message only when explicitly set. Narrowly amends units 6 and 7; all existing unit-6/unit-7 tests must keep passing unmodified. Ordinary red→green TDD, key-free. | `p1-opencode-runner` (+ all above) | no (unit tests only) | **spec-ready (active)** |
| 8 | `p1-agent-authoring-gate` | **Live gate + first agent-generated tests committed**: drive the unit-6 glue for real via the **unit-7 OpenCode runner** (headless OpenCode + Playwright MCP, Planner→Generator, `gpt-4o-mini`) against the running clean reference app + BRD → runnable DOM/schema-grounded TS + API tests that **pass on clean**; commit them; via `eval/score.py` show injected-bug **catch rate better than a naive baseline** (naive floor pinned in this unit's spec). Uses unit 7.5's opt-in exposure so the exploring agent can pass the real login form with the reference app's published fixture credential. **BLOCKED: requires unit 7.5 done + `OPENAI_API_KEY`.** | `p1-opencode-runner`, `p1-agent-authoring-gate-credential-exception` (+ all above) | **YES — `OPENAI_API_KEY`** | **blocked** (spec-ready; waiting on 7.5 + key) |

### Phase 1 exit gate (from `AGILE_PLAN.md` / `META_PLAN.md`)
- From `BRD.md` + the running reference app, the agent (**OpenCode + Playwright MCP, Planner→Generator,
  `gpt-4o-mini`** for this build; Claude Code remains the documented default) produces **runnable,
  DOM/schema-grounded** TS Playwright + API tests that **pass on the clean app**. *(Unit 8 — needs
  unit 7.5 done + `OPENAI_API_KEY`.)*
- The `eval/` harness shows the agent-generated suite's injected-bug **catch rate is better than a
  naive baseline**. *(Unit 8 — needs unit 7.5 done + `OPENAI_API_KEY`.)*
- Units 1–7 (all key-free) merged and green; unit 7.5 (key-free) merged and green, with zero regression
  to units 6/7's existing tests.

> **Hard external prerequisite (recorded in `AGILE_PLAN.md` → Conflicts):** the live gate (unit 8) needs
> `OPENAI_API_KEY` — to be supplied by the human. Units 1–7 and 7.5 are buildable/mergeable now (key-free,
> unit-tested with injected fakes — no key, no network, no browser, no real OpenCode process); unit 8 is
> parked until 7.5 is done **and** the key is supplied.
>
> Notes: units 3–5 are **config/prompt/sub-agent** artifacts — the Tester encodes their acceptance as
> **presence/shape/schema** checks (like the Phase 0 infra units), not behavioral unit tests. Units 1,
> 2, 6, 7, 7.5 are code/glue and follow full red→green TDD (units 6, 7, and 7.5 with mock/fake injection
> — unit 6 a mock `AgentRunner`, unit 7 and 7.5 a mock subprocess/command-runner).

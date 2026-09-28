# Agile Plan — Agentic QA Engineer (SaaS)

> The **active phase** is detailed and executable now. Completed phases are condensed and marked
> DONE. Future phases are re-planned to this level of detail each iteration, against the current app
> state + `META_PLAN.md`. `META_PLAN.md` is the fixed north star; this is the living working-detail.
> `DESIGN.md` remains the architecture source of truth.

## Conflicts / deviations for human review

- **DEVIATION (human-authorized 2026-09-28) — coding-agent CLI + model swap: OpenCode + OpenAI
  `gpt-4o-mini`, not Claude Code + Claude.** The human has decided the in-sandbox coding agent for the
  current build is **OpenCode** (the open-source terminal coding agent) driving the OpenAI model
  **`gpt-4o-mini`** via a platform-owned **`OPENAI_API_KEY`**, in place of `DESIGN.md`'s documented
  default (Claude Code, headless, `claude-sonnet-5`). **This is design-sanctioned, not a contradiction:**
  `DESIGN.md §2` explicitly makes the CLI *and* model **per-app configurable** behind a **generic
  sandbox contract**, and `META_PLAN.md` Phase 7 names the **"open-agent CLI swap (Copilot/open CLI via
  the generic sandbox contract)"** as an intended capability — we are exercising that seam early. It is
  **cleanly enabled by the unit-6 `AgentRunner` seam** (`runner/authoring.py`): the glue never hard-codes
  a CLI; it drives an injected runner, so binding OpenCode is a runner implementation, not a rewrite.
  - **Model is a config value, bumpable later** (e.g. `openai/gpt-4o`, `openai/gpt-4.1`) as reliability
    requires — pinned as a module constant in the runner unit.
  - **KNOWN RISK (flag, not a blocker):** `gpt-4o-mini` is a **weak agentic model** and may **strain
    Phase 2's stricter reliability gates** (bug-catch / false-positive / flake / assertion-audit
    thresholds). Tracked as a risk to revisit at Phase 2 start (bump the model or gate the tier), not a
    reason to stop the Phase 1 build.
  - **Claude Code + `claude-sonnet-5` remain the documented default;** OpenCode is the concrete binding
    for this build and a proof of the multi-CLI seam. Unit-5's `.claude/agents/*` are **kept** (the
    Claude-CLI path, retained for the Phase-7 multi-CLI story); the OpenCode unit **adds** OpenCode-format
    agent definitions that reference the **same** portable generic QA prompt + reliability rules (the
    `DESIGN.md §2` portable "QA agent-configuration package"). The portable core is shared; only the
    CLI-specific wrapper differs.
  - **Proposed `DESIGN.md` note — for human sign-off (I did NOT edit `DESIGN.md`).** Add to `§2` (and/or
    `§12` tech-stack row for the in-sandbox orchestrator) a note reading:

    > **CLI/model binding note (build, human-signed 2026-09-28).** The current build drives the
    > in-sandbox authoring loop with **OpenCode** (open-source terminal coding agent) on **OpenAI
    > `gpt-4o-mini`** via a platform-owned `OPENAI_API_KEY`, in place of the default Claude Code +
    > `claude-sonnet-5`. This is an early exercise of the §2 generic sandbox contract / the Phase-7
    > open-agent CLI-swap goal: the CLI and model stay per-app-configurable and the concrete CLI is bound
    > only at the generic **`AgentRunner`** runner seam (`runner/authoring.py`). Claude Code +
    > `claude-sonnet-5` remain the documented default. The model is a config value, bumpable (e.g.
    > `gpt-4o` / `gpt-4.1`) as reliability requires; `gpt-4o-mini` is a weak agentic model and may not
    > clear Phase 2's stricter reliability thresholds (tracked risk).

- **SUPERSEDED — earlier "hard external prerequisite: Claude/Anthropic model key" blocker.** The Phase 1
  exit gate previously stalled because no `ANTHROPIC_API_KEY`/Claude credential was present. The decision
  above **retargets** the live gate to OpenCode + `OPENAI_API_KEY`. The Phase 1 tail is reshaped so a new
  **key-free** unit (`p1-opencode-runner`) is fully buildable now (mock/dry-run of the OpenCode process,
  no network/model call), and only the final live gate (`p1-agent-authoring-gate`) needs the supplied
  `OPENAI_API_KEY`. Under `/auto all` this remains a sanctioned stop-for-external-prerequisite at the
  live gate only — not a design conflict.

- **Placement of the Playwright-MCP config (path note, not a behavior conflict).** `META_PLAN.md`
  Phase 1 lists "Playwright-MCP config" grouped under the `agent_config/` deliverable bullet, while
  `DESIGN.md §13` lists `playwright-mcp config` physically under **`connectors/`**. Resolution: the
  physical config file is placed under **`connectors/` per `DESIGN.md §13`** (architecture source of
  truth for paths); logically it remains part of the portable agent-configuration package. This is a
  grouping-vs-directory distinction, not a contradiction.

- **Language of `connectors/` tooling (clarification, not a deviation).** The `connectors/` spec
  loader + per-run target config are **glue/tooling → Python (`uv`)**, consistent with `DESIGN.md
  §12` ("Python backend/orchestration (glue, queue, sandbox manager)") and the Phase 0 `eval/`
  tooling. The **agent-authored test artifacts remain TypeScript Playwright** (`DESIGN.md §12`),
  unchanged. No conflict.

- Otherwise **none**: the current repo (Phase 0 fully done + merged to master; Phase 1 units 1–6 done +
  pushed on `harness/build`) is consistent with `META_PLAN.md` and `DESIGN.md`.

---

## Phase 0 — Testbed & scaffolding — **DONE (all units merged to master)**

Delivered and gated: repo scaffold + `uv`/`Makefile` tooling (`p0-scaffold`); FastAPI+SQLite shop
backend with Basic Auth / cart / checkout / orders / auto `/openapi.json` (`p0-shop-backend`);
React+Vite shop frontend with a stable `data-testid` DOM contract (`p0-shop-frontend`); freeform
`BRD.md` + release convention + `VERSION` (`p0-brd-release`); TypeScript-Playwright project + smoke
(green-on-clean / red-under-`SMOKE_FAULT`) wired into `make test` (`p0-playwright-smoke`); and the
`eval/` injected-bug harness — ≥3-bug non-invasive launcher overlay, `eval/score.py`
(bug-catch / false-positive / flake / assertion-meaningfulness), a hand-written TS-Playwright
baseline suite, and `make eval` + clean-app `make dev` wiring (`p0-eval-harness`). **Phase 0 exit
gate PASSED:** `make dev` runs API+UI with `/openapi.json` + seed + `BRD.md`; `make test` green on
clean; `make eval` injects ≥3 bugs and prints the four metrics. The clean reference app stayed
pristine (all faults live in non-invasive `eval/` / `e2e/` launcher overlays).

Historical unit table (all `done`, merged): `p0-design-note`, `p0-scaffold`, `p0-shop-backend`,
`p0-shop-frontend`, `p0-brd-release`, `p0-playwright-smoke`, `p0-eval-harness`.

---

## Phase 1 — In-sandbox authoring loop (local first) — **LOCKED for this iteration (2026-09-28, re-locked for the OpenCode tail)**

**Goal (from `META_PLAN.md`):** a headless coding agent + Playwright MCP running **Planner →
Generator** to emit **grounded** TypeScript Playwright + API tests against the reference app, with the
BRD injected as the generic QA system prompt. Local-first (no E2B yet; E2B is Phase 3).

> **Build-CLI note (this iteration):** the concrete coding agent for the live gate is **OpenCode +
> OpenAI `gpt-4o-mini`** (human-authorized; see Conflicts / deviations). This changes only the concrete
> CLI bound at the unit-6 `AgentRunner` seam — the Phase 1 goal, deliverables, and grounding/reliability
> intent are unchanged. `META_PLAN.md`'s "Claude Code" wording is the *default*; the swap is the §2 /
> Phase-7 configurable-CLI seam exercised early.

**Current app state (what the Phase 1 tail builds on — do NOT re-derive or modify):**
- **Units 1–6 are DONE + pushed on `harness/build`:** `p1-connectors-spec-loader` (`97f9b53`),
  `p1-target-config` (`151af60`), `p1-mcp-config` (`8f0ac6a`), `p1-qa-system-prompt` (`22c9954`),
  `p1-subagents-planner-generator` (`f7bee09`), `p1-agent-run-glue` (`c3694e0`).
- **Unit-6 glue** lives at `runner/authoring.py` with public import path `runner.authoring`:
  `run_authoring(config_source, *, agent_runner, output_dir=None, source_type="auto") -> RunResult`.
  It **injects** an `AgentRunner` seam — a callable `agent_runner(AuthoringInvocation) -> AgentRunOutput`.
  `AuthoringInvocation` carries `system_prompt` (final, BRD-injected), `api_surface`, `target_url`,
  `planner_fields` (the seven), `mcp_config_path` (`connectors/mcp/playwright.mcp.json`),
  `planner_agent` (`qa-planner`), `generator_agent` (`qa-generator`), `basic_auth_credential_ref`
  (target-app auth **reference** only), `output_dir`. `AgentRunOutput` = `status` (`"ok"` on success),
  `generated_tests` (relative-filename → content), optional `detail`. The glue writes
  `generated_tests` to `output_dir` **only** on `status == "ok"`, surfaces (never swallows) runner
  failures, and never resolves/logs the target-app secret. **This is the seam the OpenCode runner
  implements.**
- **Reference app (clean, pristine):** FastAPI+SQLite backend at `http://127.0.0.1:8000`; Basic Auth
  `testuser`/`testpass`; **OpenAPI 3.1.0** at `GET /openapi.json`; React+Vite frontend at
  `http://127.0.0.1:5173` with a stable `data-testid` contract; freeform `reference_app/BRD.md`.
  `make dev` / `make test` / `make eval` are real and green.
- **Playwright-MCP config** at `connectors/mcp/playwright.mcp.json` (`mcpServers.playwright` pinned to
  `@playwright/mcp@0.0.41`, headless chromium). **Generic QA system prompt** at
  `agent_config/qa_system_prompt.md` with a single `{{BRD}}` injection token. **Product sub-agents**
  `.claude/agents/qa-planner.md` + `.claude/agents/qa-generator.md` (Claude-CLI format; kept).
- **`eval/` harness** (Phase 0) is the objective measuring stick the Phase 1 gate reuses.

**Locked ordered units** (source of truth for scope: `.harness/backlog.md`; deps below):

| # | id | Depends on | Needs model key? | Status |
|---|----|-----------|:---:|--------|
| 1 | `p1-connectors-spec-loader` | — (Phase 0 done) | no | **done** (`97f9b53`) |
| 2 | `p1-target-config` | `p1-connectors-spec-loader` | no | **done** (`151af60`) |
| 3 | `p1-mcp-config` | — (Phase 0 done) | no | **done** (`8f0ac6a`) |
| 4 | `p1-qa-system-prompt` | — (Phase 0 done) | no | **done** (`22c9954`) |
| 5 | `p1-subagents-planner-generator` | `p1-qa-system-prompt`, `p1-mcp-config`, `p1-connectors-spec-loader` | no | **done** (`f7bee09`) |
| 6 | `p1-agent-run-glue` | `p1-target-config`, `p1-subagents-planner-generator`, `p1-mcp-config`, `p1-qa-system-prompt` | no (mock) | **done** (`c3694e0`) |
| 7 | `p1-opencode-runner` | `p1-agent-run-glue` (+ all above) | **no (mock/dry-run)** | **active (spec-ready)** |
| 8 | `p1-agent-authoring-gate` | `p1-opencode-runner` | **YES — `OPENAI_API_KEY`** | todo (blocked on key) |

Active unit: **7 (`p1-opencode-runner`)** — deps met (unit 6 done). Full contract in
`.harness/tasks/p1-opencode-runner.md`.

### D1–D6 — **DONE** (units 1–6; see the "Current app state" block above and each unit's task spec)
`connectors/` API spec loader (D1), per-run target config (D2), Playwright-MCP config (D3);
`agent_config/` generic QA system prompt (D4) + `.claude/agents/` Planner & Generator (D5); the
agent-run glue with the injectable `AgentRunner` seam (D6). All merged/pushed on `harness/build`.

### D7. OpenCode runner adapter (key-free, mock/dry-run tested) — **ACTIVE (unit 7, `p1-opencode-runner`)**
The concrete **`AgentRunner` adapter** that binds **OpenCode** (headless) + OpenAI **`gpt-4o-mini`** to
the unit-6 seam. It **implements** the injectable runner contract — a callable
`(AuthoringInvocation) -> AgentRunOutput` — by: (a) reading the model credential from a **reference**
(`OPENAI_API_KEY` env-var name, platform-owned per `DESIGN.md §11.5`, never inlined/logged); (b) wiring
the Playwright-MCP config into OpenCode's own config format; (c) translating the Planner→Generator flow
(under the generic QA prompt with the BRD already injected by the glue + the seven planner fields) into
OpenCode's headless-run mechanism at `model=openai/gpt-4o-mini`; (d) capturing the generated TS
Playwright + API test files and returning them as the `AgentRunOutput.generated_tests` mapping the glue
writes. It ships the **OpenCode connector config** (an `opencode.json`-format config wiring model + MCP)
plus **OpenCode-format agent/role definitions** for the Planner/Generator that reference the *same*
portable `agent_config/qa_system_prompt.md`. It is **unit-tested WITHOUT the key** by injecting the
subprocess/command runner and asserting the **constructed OpenCode invocation** (command, args,
`--model openai/gpt-4o-mini`, MCP config wiring, prompt carrying the injected BRD + fields, output
capture) — **no live network/model call, no browser, no real OpenCode process** in tests. Secret handled
as a reference only; never logged. Full contract in `.harness/tasks/p1-opencode-runner.md`.

### D8. Live gate + first agent-generated tests committed — unit 8 (`p1-agent-authoring-gate`) — **NEEDS `OPENAI_API_KEY`**
The **Phase 1 exit-gate demonstration**: with `OPENAI_API_KEY` supplied, drive the unit-6 glue for real
using the **unit-7 OpenCode runner** (headless OpenCode + Playwright MCP, Planner→Generator, model
`gpt-4o-mini`) against the running **clean** reference app + `reference_app/BRD.md`, produce
**runnable, DOM/schema-grounded** TS Playwright + API tests, **commit** them, verify they **pass on the
clean app**, and run them through the Phase 0 `eval/` scorer to show an injected-bug **catch rate better
than a naive baseline** (naive floor pinned in this unit's spec — e.g. a page-load-only / no-meaningful-
assertion suite catching ~0 bugs; the agent suite must beat it, target ≥1 and ideally all 3).
**Blocked on `OPENAI_API_KEY`** (see Conflicts). No source outside a `/tdd` cycle.

### Phase 1 acceptance (exit gate — from `META_PLAN.md`)
- From `BRD.md` + the running reference app, the agent (**OpenCode + Playwright MCP, Planner→Generator,
  `gpt-4o-mini`** — the configured CLI/model for this build; Claude Code remains the documented default)
  produces **runnable** TS Playwright + API tests that are **DOM/schema-grounded** and **pass on the
  clean app**. *(Unit 8 — needs `OPENAI_API_KEY`.)*
- The `eval/` harness shows the agent-generated suite's injected-bug **catch rate is better than a naive
  baseline**. *(Unit 8 — needs `OPENAI_API_KEY`; measured via `eval/score.py`.)*
- Units 1–7 (all key-free) merged and green: `connectors/` spec loader + target config + MCP config,
  generic QA system prompt, Planner/Generator sub-agent definitions, mock-verified run glue, and the
  **mock/dry-run-verified OpenCode runner adapter** all present, tested, and consistent with `DESIGN.md
  §2/§4/§5.1/§6/§11/§13`.

## Verification
- **Units 1–7 (no key):** `uv run pytest connectors/tests -q`, `uv run pytest agent_config/tests -q`,
  `uv run pytest runner/tests -q` all green; config/prompt/sub-agent units pass presence/shape/schema
  checks; the glue unit passes with the mock runner; the **OpenCode runner passes with an injected mock
  command-runner** (asserts the constructed invocation + output capture) — no network, no model, no
  browser, no real OpenCode process.
- **Unit 8 (with key):** supply `OPENAI_API_KEY`; run the glue live via the OpenCode runner; inspect the
  committed agent-generated tests, confirm they run green on clean via the e2e toolchain, and run
  `eval/score.py` to confirm the catch rate beats the naive floor.
- **Later phases:** gated by the `eval/` metrics (see `META_PLAN.md` gates); Phase 3+ additionally by
  a real E2B run. **Phase 2 note:** re-evaluate `gpt-4o-mini` against the stricter reliability gates and
  bump the model constant if needed (see Conflicts risk flag).

## Agile revise loop
After each phase, re-plan the next phase to this level of detail against the **current app state +
`META_PLAN.md`**. Update `DESIGN.md` if a phase forces an architecture change (the OpenCode/model note
above is proposed for human sign-off into `DESIGN.md §2/§12`).
</content>
</invoke>

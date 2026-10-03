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

- **DEVIATION (human-authorized 2026-09-29, via explicit in-session `AskUserQuestion` — NOT an agent's
  self-authorization) — scoped, opt-in credential-exposure carve-out for the Phase-1 live authoring gate
  only.** While attempting the live unit-8 OpenCode + `gpt-4o-mini` authoring run, the Developer found
  that the reference app's login is a **real in-app form**:
  `reference_app/frontend/src/views/LoginView.tsx` holds `username`/`password` only in local React
  `useState` and sends them as a Basic-Auth header on submit — **never** persisted to a cookie,
  `localStorage`, or session. There is therefore no way to pre-authenticate the exploring agent's browser
  session, and the agent cannot get past login without being told the actual credential **value**. But
  unit-6's `run_authoring` (`runner/authoring.py`) and unit-7's `OpenCodeRunner._compose_message`
  (`runner/opencode_runner.py`) deliberately pass only the Basic-Auth **credential reference name**
  (`AuthoringInvocation.basic_auth_credential_ref`) — never the resolved value — into the model-visible
  message, by design, pinned by unit-7's reviewed test `test_c13_target_auth_stays_reference_only`
  (`runner/tests/test_opencode_runner.py`). **That default is correct per `DESIGN.md §11` items 4–5**
  (target-app secrets injected at runtime, never in prompts/logs/traces/artifacts; model/CLI credentials
  platform-owned, never tenant-supplied) **and MUST stay correct** for real target-app credentials from
  Phase 5+ (multi-tenant customer apps) onward.
  - **Why THIS value is exempt.** `testuser`/`testpass` are the reference app's own **published,
    non-secret fixture dev/test account** — already committed in plaintext across Phase-0 artifacts:
    `reference_app/e2e/tests/smoke.spec.ts`, `reference_app/e2e/tests/eval/helpers.ts`,
    `eval/tests/test_eval_harness_verification.py` — and documented as the auth mechanism in
    `reference_app/BRD.md`'s Authentication section (values pinned in `.harness/tasks/p0-shop-backend.md`).
    Exposing an already-public, non-rotatable fixture value to the model for this one local gate run
    carries none of the exfiltration/confidentiality risk `DESIGN.md §11` guards against.
  - **Why the exemption does NOT generalize.** Every future login-gated **customer** app (Phase 5+) has a
    real, private, rotatable Basic-Auth credential; the reference-only default must hold unconditionally
    for those. This carve-out is scoped to the reference app's known-public fixture account only, is
    **opt-in and default-off**, and is used only by the unit-8 live-gate script.
  - **The human's explicit choice (recorded, not an agent's self-authorization).** The human was asked,
    via this session's `AskUserQuestion` tool — a real, explicit user decision — to choose between
    (a) a scoped, opt-in, default-off fixture carve-out for the local gate run only; (b) building the full
    `@playwright/mcp --secrets`-file passthrough mechanism now (the model references secrets by name and
    never sees the raw value, for this AND future customer apps); or (c) deferring the live gate entirely.
    **The human chose (a).**
  - **(b) is deferred, not abandoned — flagged as a real Phase 2+ backlog candidate.** A durable
    `--secrets`-file (or equivalent named-reference-passthrough) mechanism belongs in `connectors/` /
    `runner/` ahead of Phase 5's real multi-tenant customer-app credentials, since every future
    login-gated customer app hits this same problem. Not built now; tracked for re-planning at Phase 2+
    (do not let this be forgotten — re-surface it when Phase 2 is locked).
  - **Scoped task spec:** `.harness/tasks/p1-agent-authoring-gate-credential-exception.md` — a small,
    **separate** unit, `p1-agent-authoring-gate-credential-exception`, inserted between unit 7 and unit 8
    in the Phase 1 unit table (unit 8 now additionally depends on it). Kept **separate** from
    `p1-agent-authoring-gate.md` rather than folded in, because it narrowly amends two already-`done`
    units' contracts (`runner/authoring.py` unit 6, `runner/opencode_runner.py` unit 7) with
    independently testable, ordinary red→green TDD criteria — distinct in kind from unit 8's own
    (already-adapted, live-demo/measurement) Roles/Interpretations. Separating it gives it its own clean
    TDD cycle, review, and commit boundary without further overloading unit 8's already-long spec, and
    keeps unit 8's spec unmodified (a completed plan-gated artifact).

- Otherwise **none**: the current repo (Phase 0 fully done + merged to master; Phase 1 units 1–7 done +
  pushed on `harness/build`, latest `d0fcd70`) is consistent with `META_PLAN.md` and `DESIGN.md`.

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

## Phase 1 — In-sandbox authoring loop (local first) — **LOCKED for this iteration (2026-09-29, re-locked for the credential-exception unit)**

**Goal (from `META_PLAN.md`):** a headless coding agent + Playwright MCP running **Planner →
Generator** to emit **grounded** TypeScript Playwright + API tests against the reference app, with the
BRD injected as the generic QA system prompt. Local-first (no E2B yet; E2B is Phase 3).

> **Build-CLI note (this iteration):** the concrete coding agent for the live gate is **OpenCode +
> OpenAI `gpt-4o-mini`** (human-authorized; see Conflicts / deviations). This changes only the concrete
> CLI bound at the unit-6 `AgentRunner` seam — the Phase 1 goal, deliverables, and grounding/reliability
> intent are unchanged. `META_PLAN.md`'s "Claude Code" wording is the *default*; the swap is the §2 /
> Phase-7 configurable-CLI seam exercised early.

**Current app state (what the Phase 1 tail builds on — do NOT re-derive or modify):**
- **Units 1–7 are DONE + pushed on `harness/build`:** `p1-connectors-spec-loader` (`97f9b53`),
  `p1-target-config` (`151af60`), `p1-mcp-config` (`8f0ac6a`), `p1-qa-system-prompt` (`22c9954`),
  `p1-subagents-planner-generator` (`f7bee09`), `p1-agent-run-glue` (`c3694e0`), `p1-opencode-runner`
  (`d0fcd70`).
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
  `testuser`/`testpass` (a **published, non-secret fixture account** — see the new Conflicts entry);
  **OpenAPI 3.1.0** at `GET /openapi.json`; React+Vite frontend at `http://127.0.0.1:5173` with a stable
  `data-testid` contract and a **real in-app login form** (`LoginView.tsx`, credentials held only in
  local React state, never persisted); freeform `reference_app/BRD.md`. `make dev` / `make test` /
  `make eval` are real and green.
- **Playwright-MCP config** at `connectors/mcp/playwright.mcp.json` (`mcpServers.playwright` pinned to
  `@playwright/mcp@0.0.41`, headless chromium). **Generic QA system prompt** at
  `agent_config/qa_system_prompt.md` with a single `{{BRD}}` injection token. **Product sub-agents**
  `.claude/agents/qa-planner.md` + `.claude/agents/qa-generator.md` (Claude-CLI format; kept).
- **`eval/` harness** (Phase 0) is the objective measuring stick the Phase 1 gate reuses.
- **NEW (this re-lock): the login form cannot be pre-authenticated.** The live gate cannot proceed
  without a narrow, opt-in mechanism for the exploring agent to receive the reference app's published
  fixture credential *value* (not just its reference name). See Conflicts / deviations above and the new
  unit below.

**Locked ordered units** (source of truth for scope: `.harness/backlog.md`; deps below):

| # | id | Depends on | Needs model key? | Status |
|---|----|-----------|:---:|--------|
| 1 | `p1-connectors-spec-loader` | — (Phase 0 done) | no | **done** (`97f9b53`) |
| 2 | `p1-target-config` | `p1-connectors-spec-loader` | no | **done** (`151af60`) |
| 3 | `p1-mcp-config` | — (Phase 0 done) | no | **done** (`8f0ac6a`) |
| 4 | `p1-qa-system-prompt` | — (Phase 0 done) | no | **done** (`22c9954`) |
| 5 | `p1-subagents-planner-generator` | `p1-qa-system-prompt`, `p1-mcp-config`, `p1-connectors-spec-loader` | no | **done** (`f7bee09`) |
| 6 | `p1-agent-run-glue` | `p1-target-config`, `p1-subagents-planner-generator`, `p1-mcp-config`, `p1-qa-system-prompt` | no (mock) | **done** (`c3694e0`) |
| 7 | `p1-opencode-runner` | `p1-agent-run-glue` (+ all above) | **no (mock/dry-run)** | **done** (`d0fcd70`) |
| 7.5 | `p1-agent-authoring-gate-credential-exception` | `p1-opencode-runner` | no (unit tests only) | **active (spec-ready)** |
| 8 | `p1-agent-authoring-gate` | `p1-opencode-runner`, `p1-agent-authoring-gate-credential-exception` | **YES — `OPENAI_API_KEY`** | **blocked** (spec-ready; waiting on unit 7.5 + the key) |

Active unit: **7.5 (`p1-agent-authoring-gate-credential-exception`)** — a small, key-free, ordinary
red→green TDD unit that amends units 6 and 7's contracts with a narrow, opt-in, default-off credential-
exposure mechanism (see Conflicts / deviations above for the human-authorized rationale). Full contract
in `.harness/tasks/p1-agent-authoring-gate-credential-exception.md`. Unit 8 (`p1-agent-authoring-gate`,
the Phase 1 EXIT GATE, contract unchanged in `.harness/tasks/p1-agent-authoring-gate.md`) now additionally
depends on 7.5 and remains **blocked** until 7.5 is done **and** `OPENAI_API_KEY` is supplied.

### D1–D6 — **DONE** (units 1–6; see the "Current app state" block above and each unit's task spec)
`connectors/` API spec loader (D1), per-run target config (D2), Playwright-MCP config (D3);
`agent_config/` generic QA system prompt (D4) + `.claude/agents/` Planner & Generator (D5); the
agent-run glue with the injectable `AgentRunner` seam (D6). All merged/pushed on `harness/build`.

### D7. OpenCode runner adapter (key-free, mock/dry-run tested) — **DONE (unit 7, `p1-opencode-runner`, `d0fcd70`)**
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

### D7.5. Scoped credential-exposure carve-out for the live gate — unit 7.5 (`p1-agent-authoring-gate-credential-exception`) — **ACTIVE (spec-ready)**
A **narrow, opt-in, default-off** amendment to units 6 and 7 so the unit-8 live gate can actually
authenticate the exploring agent against the reference app's real in-app login form, without weakening
the reference-only default for real target-app/tenant credentials. `run_authoring` gains a keyword-only
`expose_credential_for_exploration: bool = False`; when `True` (and only then) it resolves the
target-app credential itself and sets it onto a new, optional `AuthoringInvocation.
basic_auth_credential_value` field (default `None`) — `RunResult` still never exposes it.
`OpenCodeRunner._compose_message` stays **byte-identical** to today when that field is `None` (the
default; `test_c13_target_auth_stays_reference_only` must pass **unmodified**), and includes the value
in the composed message **only** when explicitly set. Full contract, including why the reference app's
`testuser`/`testpass` is exempt and why the exemption does not generalize, in
`.harness/tasks/p1-agent-authoring-gate-credential-exception.md` (see also Conflicts / deviations above
for the human-authorized decision this unit implements).

### D8. Live gate + first agent-generated tests committed — unit 8 (`p1-agent-authoring-gate`) — **BLOCKED (spec-ready) · NEEDS unit 7.5 done + `OPENAI_API_KEY`**
The **Phase 1 exit-gate demonstration**: with `OPENAI_API_KEY` supplied, drive the unit-6 glue for real
using the **unit-7 OpenCode runner** (headless OpenCode + Playwright MCP, Planner→Generator, model
`gpt-4o-mini`) against the running **clean** reference app + `reference_app/BRD.md`, produce
**runnable, DOM/schema-grounded** TS Playwright + API tests, **commit** them, verify they **pass on the
clean app**, and run them through the Phase 0 `eval/` scorer to show an injected-bug **catch rate better
than a naive baseline** (naive floor pinned in this unit's spec — e.g. a page-load-only / no-meaningful-
assertion suite catching ~0 bugs; the agent suite must beat it, target ≥1 and ideally all 3).
Pinned in `.harness/tasks/p1-agent-authoring-gate.md`: generated suite →
`reference_app/e2e/tests/generated/`; eval report → `eval/reports/p1-agent-authoring-gate.eval.json`
(+`.txt`) + manifest `…run.json`; **naive floor `bug_catch_rate` = 0.0**, PASS = `bug_catch > 0.0`
(≥1 of 3) ∧ `false_positive == 0.0` ∧ `flake == 0.0` ∧ `assertion_meaningfulness > 0.0`; live runner
`make authoring` (needs key), model-free verify `make authoring-gate` + `uv run pytest eval/tests -q`.
This is a **live demonstration/measurement** unit: the Developer/orchestrator performs the one-time
live run (key from `.env`) and commits its outputs; the Tester's harness + Reviewer bind to the
committed artifacts model-free (see spec §Roles + §Interpretations). **Requires `OPENAI_API_KEY`**
(see Conflicts). **Now also requires unit 7.5** so the live run's exploring agent can actually log in
(the live-gate script, unit 8's `runner/authoring_gate.py`, is the only permitted caller of
`expose_credential_for_exploration=True`, and only for the reference app's published fixture account —
see unit 7.5's spec). No source outside a `/tdd` cycle. Unit 8's own spec file
(`.harness/tasks/p1-agent-authoring-gate.md`) is **unchanged** by this re-lock.

### Phase 1 acceptance (exit gate — from `META_PLAN.md`)
- From `BRD.md` + the running reference app, the agent (**OpenCode + Playwright MCP, Planner→Generator,
  `gpt-4o-mini`** — the configured CLI/model for this build; Claude Code remains the documented default)
  produces **runnable** TS Playwright + API tests that are **DOM/schema-grounded** and **pass on the
  clean app**. *(Unit 8 — needs unit 7.5 done + `OPENAI_API_KEY`.)*
- The `eval/` harness shows the agent-generated suite's injected-bug **catch rate is better than a naive
  baseline**. *(Unit 8 — needs unit 7.5 done + `OPENAI_API_KEY`; measured via `eval/score.py`.)*
- Units 1–7 (all key-free) merged and green: `connectors/` spec loader + target config + MCP config,
  generic QA system prompt, Planner/Generator sub-agent definitions, mock-verified run glue, and the
  **mock/dry-run-verified OpenCode runner adapter** all present, tested, and consistent with `DESIGN.md
  §2/§4/§5.1/§6/§11/§13`.
- Unit 7.5's narrow credential-exposure amendment is done, key-free, tested, and does not regress any
  unit-6/unit-7 existing test.

## Verification
- **Units 1–7 (no key):** `uv run pytest connectors/tests -q`, `uv run pytest agent_config/tests -q`,
  `uv run pytest runner/tests -q` all green; config/prompt/sub-agent units pass presence/shape/schema
  checks; the glue unit passes with the mock runner; the **OpenCode runner passes with an injected mock
  command-runner** (asserts the constructed invocation + output capture) — no network, no model, no
  browser, no real OpenCode process.
- **Unit 7.5 (no key):** `uv run pytest runner/tests -q` — the full existing unit-6/unit-7 suite passes
  **unmodified**, plus new tests for the opt-in exposure path (default off; explicit on carries the
  resolved value into the composed message only; `RunResult`/logs stay secret-free).
- **Unit 8 (with key, after 7.5):** supply `OPENAI_API_KEY`; run the glue live via the OpenCode runner
  with `expose_credential_for_exploration=True`; inspect the committed agent-generated tests, confirm
  they run green on clean via the e2e toolchain, and run `eval/score.py` to confirm the catch rate beats
  the naive floor.
- **Later phases:** gated by the `eval/` metrics (see `META_PLAN.md` gates); Phase 3+ additionally by
  a real E2B run. **Phase 2 note:** re-evaluate `gpt-4o-mini` against the stricter reliability gates and
  bump the model constant if needed (see Conflicts risk flag); **also re-plan the deferred durable
  `--secrets`-file passthrough mechanism** (Conflicts, 2026-09-29 entry) ahead of Phase 5's real
  multi-tenant customer credentials.

## Agile revise loop
After each phase, re-plan the next phase to this level of detail against the **current app state +
`META_PLAN.md`**. Update `DESIGN.md` if a phase forces an architecture change (the OpenCode/model note
above is proposed for human sign-off into `DESIGN.md §2/§12`).

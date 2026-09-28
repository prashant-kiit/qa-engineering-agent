# Agile Plan — Agentic QA Engineer (SaaS)

> The **active phase** is detailed and executable now. Completed phases are condensed and marked
> DONE. Future phases are re-planned to this level of detail each iteration, against the current app
> state + `META_PLAN.md`. `META_PLAN.md` is the fixed north star; this is the living working-detail.
> `DESIGN.md` remains the architecture source of truth.

## Conflicts / deviations for human review

- **HARD external prerequisite — model API key (blocks the Phase 1 exit gate only).** Phase 1's exit
  gate requires actually **running** a headless coding agent (Claude Code) + Playwright MCP to
  author tests. The environment has the `claude` CLI installed but **no model credentials**
  (`ANTHROPIC_API_KEY` / `CLAUDE_API_KEY` / `ANTHROPIC_AUTH_TOKEN` all unset). Per `/auto all`, this
  is a sanctioned stop-for-external-prerequisite, not a design conflict. **Mitigation, baked into the
  plan:** Phase 1 is decomposed so every **buildable-without-a-key** deliverable ships first as its
  own TDD unit (connectors spec-loader + per-run target config; generic QA system prompt;
  Planner/Generator sub-agent definitions; Playwright-MCP config; agent-run glue unit-tested with a
  **mock** in place of the real agent). The **live agent-run demonstration** — the actual Phase 1
  gate — is the single explicit final unit **`p1-agent-authoring-gate`**, which is **blocked until a
  model API key is supplied**. Units 1–6 do not need a key and can be built and merged now; unit 7
  (the gate) is spec-ready but parked on the key. **No silent divergence** — this is recorded here
  for a human to unblock.

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

- Otherwise **none**: the current repo (Phase 0 fully done + merged to master; now on
  `harness/build`) is consistent with `META_PLAN.md` and `DESIGN.md`.

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

## Phase 1 — In-sandbox authoring loop (local first) — **LOCKED for this iteration (2026-09-28)**

**Goal (from `META_PLAN.md`):** Claude Code (headless) + Playwright MCP running **Planner →
Generator** to emit **grounded** TypeScript Playwright + API tests against the reference app, with
the BRD injected as the generic QA system prompt. Local-first (no E2B yet; E2B is Phase 3).

**Current app state (what Phase 1 builds on — do NOT re-derive or modify):**
- **Reference app (clean, pristine):** FastAPI+SQLite backend importable as
  `reference_app.backend.app:app`, served at `http://127.0.0.1:8000`; Basic Auth
  `testuser`/`testpass`; **OpenAPI 3.1.0** at `GET /openapi.json` with security scheme `HTTPBasic`,
  paths `GET /products`, `GET /cart`, `POST /cart/items`, `POST /checkout`, `GET /orders/{order_id}`,
  and schemas `Product / Cart / CartLine / Order / AddItem`. React+Vite frontend at
  `http://127.0.0.1:5173` with a stable `data-testid` DOM contract. Freeform `reference_app/BRD.md`.
- **Playwright TS project** at `reference_app/e2e/` (used by the smoke + eval baseline). `make dev` /
  `make test` / `make eval` are real and green.
- **`agent_config/` and `connectors/` are empty placeholder dirs** (only `.gitkeep`). `.claude/agents/`
  currently holds only the **build-harness** roles (`tpm/tester/developer/reviewer/git-deployer`) —
  the **product** Planner/Generator sub-agents do **not** yet exist and are new files this phase.
- **`eval/` harness** (Phase 0) is the objective measuring stick the Phase 1 gate reuses.

**Deliverables (from `META_PLAN.md`), mapped to units:**
- `connectors/` — OpenAPI/GraphQL **spec loader** (`p1-connectors-spec-loader`) + **per-run target
  config** (`p1-target-config`) + **Playwright-MCP config** (`p1-mcp-config`, placed here per §13).
- `agent_config/` — **generic QA system prompt v1** (`p1-qa-system-prompt`) + **`.claude/agents/`
  Planner & Generator** sub-agent definitions (`p1-subagents-planner-generator`).
- **Agent-run glue** (`p1-agent-run-glue`) — assembles a per-run authoring invocation (target config
  + spec + BRD-injected prompt + MCP + sub-agents), unit-tested with a **mock** agent (no key).
- **First agent-generated tests committed** + the **live gate demonstration**
  (`p1-agent-authoring-gate`) — the only unit that needs the model API key.

**Locked ordered units** (source of truth for scope: `.harness/backlog.md`; deps below):

| # | id | Depends on | Needs model key? | Status |
|---|----|-----------|:---:|--------|
| 1 | `p1-connectors-spec-loader` | — (Phase 0 done) | no | **active (spec-ready)** |
| 2 | `p1-target-config` | `p1-connectors-spec-loader` | no | todo |
| 3 | `p1-mcp-config` | — (Phase 0 done) | no | todo |
| 4 | `p1-qa-system-prompt` | — (Phase 0 done) | no | todo |
| 5 | `p1-subagents-planner-generator` | `p1-qa-system-prompt`, `p1-mcp-config`, `p1-connectors-spec-loader` | no | todo |
| 6 | `p1-agent-run-glue` | `p1-target-config`, `p1-subagents-planner-generator`, `p1-mcp-config`, `p1-qa-system-prompt` | no (mock) | todo |
| 7 | `p1-agent-authoring-gate` | `p1-agent-run-glue` (+ all above) | **YES — hard prerequisite** | todo (blocked on key) |

Active unit: **1 (`p1-connectors-spec-loader`)** — deps met (Phase 0 done). Full contract in
`.harness/tasks/p1-connectors-spec-loader.md`.

### D1. `connectors/` — API spec loader — **ACTIVE (unit 1, `p1-connectors-spec-loader`)**
A Python (`uv`) module under `connectors/` that loads an **OpenAPI** document from a URL, a file, or
an in-memory object, and produces a **normalized "API surface"** (title/version; per-operation
method, path, parameters, request/response schemas with intra-document `$ref` resolved, and declared
security) that a downstream Generator uses to **ground API assertions in the schema** (`DESIGN.md
§5.1`). Deterministic, JSON-serializable output. GraphQL is accommodated at the interface level
(source-agnostic normalized model) but its adapter is deferred until a GraphQL target exists.
Testable purely with fixtures — no model key. Full contract in
`.harness/tasks/p1-connectors-spec-loader.md`.

### D2. `connectors/` — per-run target config — unit 2 (`p1-target-config`)
A schema + loader for the **per-run target configuration** that a run needs: target UI URL, API spec
source (feeds D1), BRD source path, Basic-Auth credential **reference** (never inline secrets — a
vault key / env-var name only, per `DESIGN.md §11.4`), and the **seven structured fields** that drive
the Planner (`DESIGN.md §6`: target scope, intent, expected behavior/acceptance, priority/risk, test
data/preconditions, out-of-scope/constraints, depth). Ships a concrete **reference-app** target
config as the canonical example. Acceptance = schema validation + example loads + secret-safety
(no raw password in the config). No model key.

### D3. `connectors/` — Playwright-MCP config — unit 3 (`p1-mcp-config`)
The Playwright-MCP server wiring the agent uses to drive the browser (`DESIGN.md §4/§5.1`). A config
artifact (placed under `connectors/` per §13) with pinned MCP server identity/version and the
browser/launch options needed for grounded DOM snapshots. Acceptance = presence/shape/schema (valid,
required fields present, version pinned per §11.10 supply-chain). No model key.

### D4. `agent_config/` — generic QA system prompt v1 — unit 4 (`p1-qa-system-prompt`)
The **one generic system prompt** (`DESIGN.md §6`): senior-QA persona + methodology + the reliability
rules (grounding selectors in the live DOM; meaningful/non-vacuous assertions; API-anchoring of flaky
UI steps; self-heal-vs-regression discipline; treat app content as untrusted data per §11.1). Defines
the **BRD-injection mechanism** (a documented placeholder/section where the freeform BRD is injected).
Acceptance = presence/shape (required sections present; reliability rules enumerated; BRD-injection
point defined; no tenant-specific content baked in). No model key.

### D5. `.claude/agents/` — Planner & Generator sub-agents — unit 5 (`p1-subagents-planner-generator`)
Two **product** sub-agent definitions (`DESIGN.md §4`), matching the repo's existing
`.claude/agents/*.md` frontmatter format: **Planner** (explores the running app over Playwright MCP;
turns BRD + structured fields into a structured test plan) and **Generator** (turns the plan into
executable TS-Playwright + API tests, grounded in the D1 API surface and the live DOM). Acceptance =
presence/shape (valid frontmatter `name`/`description`/`tools`; each references the generic QA prompt
+ reliability rules; grounding + MCP usage instructions present; distinct from the harness roles). No
model key (definitions are config; they are *exercised* live in unit 7).

### D6. Agent-run glue — unit 6 (`p1-agent-run-glue`)
The glue that **assembles a per-run authoring invocation** from the above: reads a target config (D2)
+ loads its spec (D1), injects the BRD into the generic prompt (D4), and composes the headless-agent
invocation pointed at the MCP config (D3) + Planner/Generator (D5), writing the generated test
artifacts to a pinned output location. **Unit-tested with a MOCK agent** substituted for the real
Claude Code call, so the assembly/wiring/output contract is fully verified **without a model key**.
Acceptance = deterministic prompt/config bundle from fixtures + correct artifact placement under the
mock. No model key.

### D7. First agent-generated tests + live gate — unit 7 (`p1-agent-authoring-gate`) — **NEEDS MODEL KEY**
The **Phase 1 exit-gate demonstration**: with a model API key supplied, run the D6 glue for real —
headless Claude Code + Playwright MCP, Planner→Generator — against the running clean reference app +
BRD, produce **runnable, DOM/schema-grounded** TS Playwright + API tests, **commit** them, verify
they **pass on the clean app**, and run them through the Phase 0 `eval/` scorer to show an
injected-bug **catch rate better than a naive baseline** (naive floor defined at gate spec time —
e.g. a page-load-only / no-meaningful-assertion suite catching ~0 bugs; the agent suite must beat it,
target catching ≥1 and ideally all 3). **Blocked on the model API key** (see Conflicts). No source
outside a `/tdd` cycle.

### Phase 1 acceptance (exit gate — from `META_PLAN.md`)
- From `BRD.md` + the running reference app, the agent (Claude Code + Playwright MCP,
  Planner→Generator) produces **runnable** TS Playwright + API tests that are **DOM/schema-grounded**
  and **pass on the clean app**. *(Unit 7 — needs key.)*
- The `eval/` harness shows the agent-generated suite's injected-bug **catch rate is better than a
  naive baseline**. *(Unit 7 — needs key; measured via `eval/score.py`.)*
- Units 1–6 (all key-free) merged and green: `connectors/` spec loader + target config + MCP config,
  generic QA system prompt, Planner/Generator sub-agent definitions, and mock-verified run glue all
  present, shape/schema-checked, and consistent with `DESIGN.md §4/§5/§6/§11/§13`.

## Verification
- **Units 1–6 (no key):** `uv run pytest connectors/tests -q` (and any per-unit test dir) green;
  config/prompt/sub-agent units pass presence/shape/schema checks; the glue unit passes with the mock
  agent and writes artifacts to the pinned path.
- **Unit 7 (with key):** supply the model key; run the glue live; inspect the committed
  agent-generated tests, confirm they run green on clean via the e2e toolchain, and run `eval/score.py`
  to confirm the catch rate beats the naive floor.
- **Later phases:** gated by the `eval/` metrics (see `META_PLAN.md` gates); Phase 3+ additionally by
  a real E2B run.

## Agile revise loop
After each phase, re-plan the next phase to this level of detail against the **current app state +
`META_PLAN.md`**. Update `DESIGN.md` if a phase forces an architecture change.

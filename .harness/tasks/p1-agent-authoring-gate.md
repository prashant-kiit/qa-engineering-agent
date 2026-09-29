# Task: `p1-agent-authoring-gate` — Live authoring gate + first agent-generated tests committed (Phase 1 EXIT GATE)

## Title
The **Phase 1 exit-gate demonstration + measurement** unit. With `OPENAI_API_KEY` supplied, drive the
unit-6 authoring glue (`runner.authoring.run_authoring`) **for real** through the unit-7
`OpenCodeRunner` adapter — headless **OpenCode** + **Playwright MCP**, running **Planner → Generator**
on model **`openai/gpt-4o-mini`** — against the **running CLEAN reference app** (UI `:5173`, API
`:8000/openapi.json`) with `reference_app/BRD.md` injected as the generic QA system prompt. The agent
must **PRODUCE grounded TypeScript Playwright + API tests** that are (a) **DOM/schema-grounded**
(locators/assertions tied to the real app's `data-testid` DOM contract and the served OpenAPI surface —
not invented), (b) **pass on the clean app** (zero false positives), and (c) via `eval/score.py` show an
**injected-bug catch rate strictly better than a pinned naive-baseline floor**. The generated suite is
then **committed**, alongside a **committed eval-report artifact** capturing the four reliability
metrics. Because this is a **live, credit-spending, non-deterministic** run, the live invocation is
performed **once** (by the Developer role / orchestrator, using the key) and its **outputs** (the
generated suite + the eval report + a provenance manifest) are the **committed artifacts**; the Tester's
and Reviewer's checks bind to those committed artifacts + re-run the committed suite **without** calling
the live model, so the gate is **reproducible and verifiable deterministically after the fact**.

> **BLOCKED-UNTIL-KEY:** this unit requires `OPENAI_API_KEY` (present in the repo-root **gitignored**
> `.env`). The live run WILL spend a small amount of OpenAI credit. Units 1–7 are already done + pushed
> on `harness/build`; this is the final Phase 1 unit and its exit gate.

## Context (plan item)
- **AGILE_PLAN.md → Phase 1 → D8** ("Live gate + first agent-generated tests committed — unit 8
  (`p1-agent-authoring-gate`) — NEEDS `OPENAI_API_KEY`") and the **Phase 1 acceptance (exit gate)** in
  both `AGILE_PLAN.md` and `META_PLAN.md` Phase 1:
  - *"from BRD + running app, the agent produces runnable, DOM/schema-grounded tests that pass on the
    clean app"*; and
  - *"eval shows a baseline injected-bug catch rate better than naive."*
- **Backlog unit 8** (`p1-agent-authoring-gate`, status `spec-ready (active)`).
- **AGILE_PLAN.md → Conflicts / deviations** — the human-authorized CLI/model swap to **OpenCode +
  `gpt-4o-mini`** (platform-owned `OPENAI_API_KEY`). This unit is the live proof of that whole chain
  (units 1–7) working end-to-end. **`gpt-4o-mini` is a weak agentic model** — the naive-floor + Phase-1
  thresholds below are set so a *genuine-but-modest* agent result clears them while still being a
  meaningful bar; the **stricter** reliability thresholds are Phase 2 (see the risk flag).
- **DESIGN.md §4** — the product pipeline `BRD/prompt → Planner → Generator → …`; this unit exercises
  the **Planner → Generator** authoring portion live. (Verifier / Healer / API cross-check / self-heal
  are Phase 2; Execution-in-E2B / PR delivery are Phase 3.)
- **DESIGN.md §5.1 (Grounding)** — selectors from the live DOM snapshot via Playwright MCP; API
  assertions grounded in the served schema. This unit's central *quality* claim is that the generated
  tests are **genuinely grounded**, not invented/gamed.
- **DESIGN.md §6** — one generic QA system prompt + per-run BRD + the seven structured Planner fields;
  the glue has already assembled these into the invocation (unit 6) and the OpenCode adapter delivers
  them (unit 7). This unit does **not** re-author the prompt.
- **DESIGN.md §11.4 / §11.5** — target-app Basic-Auth and model/CLI credentials are handled as
  references, never committed/logged. The `OPENAI_API_KEY` (platform model credential) must never appear
  in any committed artifact, generated test, report, manifest, log, or trace.
- **META_PLAN.md — "the `eval/` injected-bug harness is the objective gate every phase is measured
  against."** This unit measures the *agent-generated* suite with that same harness.

**Given app state (contracts this unit builds on — do NOT re-derive, duplicate, or modify):**
- **Units 1–7 DONE + pushed on `harness/build`** (latest `d0fcd70`): `connectors/` spec loader +
  per-run target config + Playwright-MCP config; `agent_config/qa_system_prompt.md`; `.claude/agents/*`
  and `.opencode/agent/*` Planner/Generator defs; the unit-6 glue `runner.authoring.run_authoring`; the
  unit-7 `runner.opencode_runner.OpenCodeRunner` adapter + `connectors/opencode/opencode.json`.
- **Unit-6 glue** `run_authoring(config_source, *, agent_runner, output_dir=None, source_type="auto")
  -> RunResult` — writes `AgentRunOutput.generated_tests` (relative-filename → content) to `output_dir`
  **only** on `status == "ok"`; surfaces (never swallows) runner failures; never resolves/logs the
  target-app secret. Default `output_dir` = `runner/generated` (this unit **overrides** it to the pinned
  path below).
- **Unit-7 adapter** `OpenCodeRunner` — the concrete `AgentRunner` binding OpenCode headless +
  `openai/gpt-4o-mini` + Playwright MCP; reads `OPENAI_API_KEY` from the env **reference**, injects it
  only into the child process env, never into argv/prompt/logs/output. Its command-runner seam has a
  **real subprocess default** (never exercised by unit-7 tests) — this unit exercises it **live**.
  Capture globs collect `**/*.spec.ts` / `**/*.test.ts` / `**/*.api.spec.ts`.
- **Reference app (clean, pristine):** FastAPI+SQLite backend `http://127.0.0.1:8000` (Basic Auth
  `testuser`/`testpass`, OpenAPI 3.1.0 at `GET /openapi.json`), React+Vite frontend
  `http://127.0.0.1:5173` with a stable `data-testid` contract, `reference_app/BRD.md`. `make dev`
  launches the CLEAN app.
- **`eval/` harness (Phase 0):**
  - `eval/buggy_backend.py` — clean + **three** injected-bug variants selected by `EVAL_BUG`:
    `checkout_total`, `cart_quantity`, `order_auth_bypass`.
  - `eval/score.py` — runs a TS-Playwright suite against clean + the 3 buggy variants (with re-runs,
    default 2) and computes the **four pinned metrics** (`bug_catch_rate`, `false_positive_rate`,
    `flake_rate`, `assertion_meaningfulness_rate`); `--json` emits a machine-readable object with a
    `metrics` field + per-variant/per-test breakdown. **Its scored suite is currently hard-wired to the
    baseline** (`reference_app/e2e/tests/eval/` via `playwright.eval.config.ts`) — see Interpretation
    flag #3 for how this unit scores the *generated* suite instead.
  - `playwright.eval.config.ts` — the eval `webServer` pattern (launches `eval/buggy_backend.py` honoring
    `EVAL_BUG` + the Vite frontend, fresh process per run, reseeded DB) — the model to reuse for the
    generated suite.
- Root uses `uv` (`pyproject.toml`); the e2e Node/Playwright project lives at `reference_app/e2e/`.
- **`.env`** (repo root, **gitignored** at `.gitignore:154`) holds `OPENAI_API_KEY` (+ `E2B_API_KEY`,
  out of scope — Phase 3).

## Scope

### In scope
1. **Perform the LIVE authoring run (once).** With `OPENAI_API_KEY` in env from `.env`, and the **CLEAN**
   reference app running, drive `runner.authoring.run_authoring` with the unit-7 `OpenCodeRunner` as
   `agent_runner` and `output_dir` = the pinned generated-tests path, using the shipped reference-app
   target config (`connectors/examples/reference_app.target.json`) — so OpenCode + Playwright MCP runs
   **Planner → Generator** on `gpt-4o-mini` and emits grounded TS Playwright + API tests. This live run
   is the **Developer role's** job for this unit (see §Roles).
2. **A live gate runner** (make target + backing script under `runner/`) that performs step 1 headlessly
   and end-to-end: brings up / assumes the clean app, invokes the glue+adapter live, then **scores** the
   produced suite via `eval/score.py` and **writes** the eval-report artifact + provenance manifest to
   the pinned paths. (Interfaces §Gate runner.)
3. **Commit the first agent-generated tests** at the pinned path (Interfaces §Paths): the runnable TS
   Playwright + API specs the agent authored. These become a durable, versioned artifact.
4. **Score the GENERATED suite with `eval/score.py`** over the clean + 3 buggy variants (reusing the
   harness's four pinned metric definitions — NOT re-defining them) and **commit** the machine-readable
   eval report + a human-readable rendering (Interfaces §Paths).
5. **Commit a provenance manifest** stamping the run (Interfaces §Manifest): CLI = OpenCode + pinned
   version, model = `openai/gpt-4o-mini`, MCP server version (`@playwright/mcp@0.0.41`), reference-app
   `VERSION`, timestamp, `reruns`, the pinned naive floor + thresholds, and the computed PASS/FAIL —
   **secret-free**.
6. **Minimal glue to let the scorer target the generated suite** (Interpretation flag #3): a scoring
   path that runs `eval/score.py`'s metric logic against the **generated** suite (e.g. a
   `playwright.agent.config.ts` with `testDir ./tests/generated` reusing the eval `webServer` pattern +
   a scorer option/env to select it) — **without breaking** the existing baseline `make eval` path.
   This is the smallest change that flows through TDD.
7. **A deterministic verification harness** (the Tester's artifact; Interfaces §Verification) that does
   **NOT** call the live model and asserts the acceptance against the **committed** artifacts: the
   generated suite exists + is valid/non-trivial TS specs, **passes on the clean app**, and the committed
   eval report shows the pinned thresholds met. Runnable via `uv run pytest <gate tests> -q` and/or a
   `make authoring-gate` target.
8. **If (and only if) the live run reveals the unit-7 adapter cannot actually emit files headlessly**
   (e.g. it needs OpenCode's `--auto` tool-permission auto-approve, `--dir <workspace>`, or
   `-c/--continue` + `-s/--session` to carry the Planner's plan into the Generator run), make the
   **smallest** adapter adjustment to enable a real headless file-emitting run — which then **re-flows
   through unit-7's tests** (they must stay green). (Interpretation flag #4.)

### Out of scope (defer)
- **Verifier / Healer / assertion-audit-as-a-gate / API cross-check / self-heal / deterministic replay**
  — Phase 2. (Phase 2 also sets the *stricter* bug-catch / false-positive / flake / assertion-audit
  thresholds and re-evaluates `gpt-4o-mini`.)
- **E2B sandboxing, egress allowlist, git proxy, PR delivery** — Phase 3.
- **Multi-tenancy, control-plane, CI / GitHub Actions triggers, memory/versioning, metrics/billing** —
  Phases 4–7. This unit is **local-first**.
- **Re-authoring the QA system prompt, the seven fields, or the sub-agent defs; changing the unit-6 glue
  contract or the unit-7 adapter contract** (beyond the narrowly-scoped item 8, which re-flows through
  unit-7's tests).
- **Real secret vaulting / rotation / metering** — only env-var **reference** resolution from `.env`.
- **Making the app catch all 3 bugs a hard requirement** — the Phase-1 bar is *better than naive*
  (≥1 bug caught) with a clean pass; catching all 3 is the aspirational target, not the gate.

## Acceptance criteria (enumerated, testable)

> **Split by role.** Criteria **G1–G6** are the *demonstration* the live run must achieve (produced by
> the Developer/orchestrator using the key). Criteria **V1–V8** are the *deterministic verification* the
> Tester's harness + the Reviewer bind to **committed artifacts** and **re-running the committed suite**,
> **without** the live model. The unit is DONE only when the committed artifacts satisfy V1–V8 (which
> can only be true if G1–G6 were achieved).

### Live demonstration (G) — achieved by the one-time live run
- **G1. Agent authored tests.** The live `run_authoring` + `OpenCodeRunner` run against the CLEAN app
  returns `AgentRunOutput.status == "ok"` with a **non-empty** `generated_tests` mapping, and the glue
  writes ≥1 runnable TS Playwright/API spec to the pinned generated-tests path.
- **G2. Both authoring roles ran.** The run exercised **Planner → Generator** (planner before
  generator) on `openai/gpt-4o-mini` via OpenCode + Playwright MCP against `http://127.0.0.1:5173` /
  `http://127.0.0.1:8000/openapi.json` (evidenced by the provenance manifest + the run completing).
- **G3. Grounded, not invented.** The generated tests are **DOM/schema-grounded**: UI locators
  correspond to the reference app's real `data-testid` contract and/or real visible affordances, and API
  assertions correspond to real endpoints/fields of the served OpenAPI surface. (Judged by the Reviewer;
  see V6.)
- **G4. Passes on clean.** The committed generated suite runs **green on the clean app**
  (`false_positive_rate == 0.0`).
- **G5. Beats the naive floor.** `eval/score.py` over the generated suite reports
  `bug_catch_rate` **strictly greater** than the pinned naive floor (Interfaces §Thresholds) — i.e. the
  suite catches **≥1** of the 3 injected-bug variants — while `false_positive_rate == 0.0` and
  `flake_rate == 0.0`, and `assertion_meaningfulness_rate > 0.0` (≥1 generated test passes clean AND
  fails ≥1 buggy variant).
- **G6. Artifacts committed.** The generated suite, the eval report (machine + human-readable), and the
  provenance manifest are committed at their pinned paths; **no secret** (`OPENAI_API_KEY` value, nor any
  resolved target-app credential) appears in any of them, nor in any log/trace.

### Deterministic verification (V) — Tester harness + Reviewer, no live model
- **V1. Generated suite present + non-trivial.** The committed generated-tests path exists and contains
  ≥1 `*.spec.ts` / `*.api.spec.ts` (per the capture globs) that (a) is syntactically valid TS Playwright
  (collectable by `npx playwright test --list`) and (b) contains **real assertions** (≥1 `expect(...)`
  per spec; not an empty/`test.skip`-only/page-load-only shell).
- **V2. Passes on clean (reproduced).** Running the committed generated suite against the **clean**
  reference app is **green** — reproducing `false_positive_rate == 0.0`. (The harness launches the clean
  app via the pinned Playwright config's `webServer`, reusing the eval pattern — no live model.)
- **V3. Committed eval report exists + is well-formed.** The pinned eval-report JSON exists, is valid
  JSON, carries a `metrics` object with the four pinned keys (`bug_catch_rate`, `false_positive_rate`,
  `flake_rate`, `assertion_meaningfulness_rate`) as numbers in `0..1`, records which suite/config was
  scored (the **generated** suite, not the baseline), the `reruns` used, and a per-variant caught/
  not-caught breakdown.
- **V4. Thresholds met (bound to the committed report).** The committed report's metrics satisfy the
  pinned Phase-1 thresholds (Interfaces §Thresholds): `bug_catch_rate > NAIVE_BUG_CATCH_FLOOR` (i.e.
  ≥ 1/3), `false_positive_rate == 0.0`, `flake_rate == 0.0`, `assertion_meaningfulness_rate > 0.0`. The
  verification reads these from the committed report — it does **not** rely on `eval/score.py`'s own
  exit code (that Phase-0 gate demands `bug_catch == 1.0`; this Phase-1 gate is *better-than-naive*).
- **V5. Provenance manifest present + secret-free.** The pinned manifest exists and records the stamped
  fields (Interfaces §Manifest); a scan of the generated suite + eval report + manifest + any emitted log
  finds **no** `OPENAI_API_KEY` value and **no** resolved target-app secret.
- **V6. Grounding/meaningfulness audit (Reviewer).** The Reviewer independently (a) **re-runs** the
  committed generated suite against the clean app (green) and (b) **re-scores** it via the generated-suite
  scoring path and reproduces `bug_catch_rate > naive floor`, and (c) audits ≥1 generated test to confirm
  its locators/API assertions are **grounded in the real app** (real `data-testid`/endpoint/field) and
  the passing is **not gamed** (no trivially-true/always-pass assertions; no asserting on invented DOM).
- **V7. No regressions.** The existing baseline `make eval` path still runs and still reports the Phase-0
  baseline metrics (`bug_catch == 1.0`, `fp == 0`, `flake == 0`); `make test` (smoke) stays green; units
  1–7 test suites (`uv run pytest connectors/tests agent_config/tests runner/tests -q`) still pass; the
  unit-7 adapter tests still pass (including after any item-8 adjustment). The **clean** reference app
  (`reference_app/backend/**`, `reference_app/frontend/**`) is unchanged.
- **V8. Reproducible without the key.** All of V1–V7 run with **no** `OPENAI_API_KEY`, **no** live model
  call, **no** OpenAI network egress — only launching the local app + Playwright + reading committed
  artifacts. Re-verifying the gate never re-spends credit.

## Interfaces / contracts (pin these precisely)

### Paths (binding)
- **Generated tests (committed; the live run's `output_dir`):**
  `reference_app/e2e/tests/generated/` — the agent-authored TS Playwright + API specs (relative
  filenames as returned by the adapter's capture). Placed inside the e2e Node/Playwright project so the
  existing toolchain runs them.
- **Generated-suite Playwright config:** `reference_app/e2e/playwright.agent.config.ts` — `testDir:
  './tests/generated'`, **reusing** the `playwright.eval.config.ts` `webServer` pattern (launches
  `eval/buggy_backend.py` honoring `EVAL_BUG` + the Vite frontend, fresh process per run) so the same
  suite can be run on clean + each buggy variant. Must not alter the existing eval/smoke configs.
- **Eval report (committed):**
  - `eval/reports/p1-agent-authoring-gate.eval.json` — the machine-readable `eval/score.py --json` object
    produced by scoring the **generated** suite (four metrics + per-variant/per-test breakdown + `reruns`
    + which suite was scored).
  - `eval/reports/p1-agent-authoring-gate.eval.txt` — the human-readable metrics table (the scorer's
    printed table) for the same run.
- **Provenance manifest (committed):** `eval/reports/p1-agent-authoring-gate.run.json` (§Manifest).
- **Live gate runner script:** under `runner/` (e.g. `runner/authoring_gate.py`; exact filename the
  developer's choice, documented) — backs the `make authoring` target.
- **Verification tests (Tester):** `eval/tests/test_agent_authoring_gate_verification.py` (new module;
  do not disturb `eval/tests/test_eval_harness_verification.py`) — runnable via `uv run pytest eval/tests
  -q`.
- **Docs:** extend `eval/README.md` (or `runner/README.md`) documenting the gate: the live-run command,
  the generated-suite scoring path, the artifact paths, the naive floor + thresholds, and the
  secret-safety rules.
- **Read-only referenced artifacts:** `connectors/examples/reference_app.target.json`,
  `reference_app/BRD.md`, `runner.authoring`, `runner.opencode_runner`, `connectors/opencode/opencode.json`,
  `agent_config/qa_system_prompt.md`, `.opencode/agent/*`, `eval/buggy_backend.py`, `eval/score.py`,
  `reference_app/VERSION`.

### Gate runner (binding commands)
- **Live (Developer / orchestrator; requires `OPENAI_API_KEY`):** `make authoring` — reads
  `OPENAI_API_KEY` from env (loaded from `.env`), ensures/assumes the CLEAN reference app is up
  (reuse `make dev`'s launcher for backend `reference_app.backend.app:app` :8000 + Vite :5173), drives
  `run_authoring(..., agent_runner=OpenCodeRunner(), output_dir="reference_app/e2e/tests/generated")`,
  then scores the generated suite via `eval/score.py` over clean + 3 buggy variants and writes the eval
  report + manifest to the pinned paths. Idempotent-friendly (a re-run overwrites the artifacts).
- **Verify (Tester / Reviewer; NO key):** `make authoring-gate` — (re-)scores the **committed** generated
  suite via the generated-suite scoring path over clean + 3 buggy variants and exits **0 iff** the pinned
  Phase-1 thresholds hold (§Thresholds); and/or `uv run pytest eval/tests -q` for the deterministic
  report/suite-shape assertions. Neither touches the live model.

### Thresholds (binding — reuse `eval/score.py`'s metric definitions verbatim)
- **`NAIVE_BUG_CATCH_FLOOR = 0.0`** — the naive baseline is a **trivial/empty/page-load-only** suite that
  performs no meaningful (bug-discriminating) assertions and therefore catches **0** of the 3 injected
  variants (`bug_catch_rate == 0.0`). This is the floor the agent suite must beat. (The floor is a pinned
  constant; committing an actual trivial suite to empirically show 0.0 is *optional* — the gate binds to
  the constant.)
- **Phase-1 PASS requires ALL of:**
  - `bug_catch_rate > NAIVE_BUG_CATCH_FLOOR` — i.e. **≥ 1/3 ≈ 0.334**: the generated suite catches **≥1**
    of the 3 injected-bug variants (`checkout_total` / `cart_quantity` / `order_auth_bypass`).
  - `false_positive_rate == 0.0` — the generated suite **passes on the clean app** (hard requirement,
    from META_PLAN "pass on the clean app").
  - `flake_rate == 0.0` — deterministic across the scorer's re-runs (**`reruns = 2`**, the scorer
    default).
  - `assertion_meaningfulness_rate > 0.0` — **≥1** generated test is *meaningful* (passes clean AND fails
    ≥1 buggy variant), proving the passing is grounded/discriminating, not trivial.
- **Aspirational target (NOT a gate):** `bug_catch_rate == 1.0` (all 3 caught). `gpt-4o-mini` is weak;
  the *stricter* thresholds (higher catch, assertion-audit pass-rate, low flake as a hard bar) are
  **Phase 2**.
- **Metric definitions are exactly `eval/score.py`'s** (do not redefine): `bug_catch_rate` = caught
  variants / 3; `false_positive_rate` = baseline-clean failures / tests; `flake_rate` = flaky
  (variant,test) pairs / pairs; `assertion_meaningfulness_rate` = meaningful tests / tests.

### Manifest (binding fields — `eval/reports/p1-agent-authoring-gate.run.json`)
Valid JSON, **secret-free**, recording at least: `cli` (`"opencode"`) + its pinned version, `model`
(`"openai/gpt-4o-mini"`), `mcp_server` (`"@playwright/mcp@0.0.41"`), `reference_app_version` (from
`reference_app/VERSION`), `timestamp` (ISO-8601), `reruns`, `naive_bug_catch_floor` (`0.0`), the four
computed `metrics`, the `thresholds` applied, `generated_suite_path`, `eval_report_path`, and
`gate_passed` (bool). No `OPENAI_API_KEY` value and no resolved target-app credential anywhere.

### Secret-safety (binding rules)
- `OPENAI_API_KEY` is read **only** from the env (loaded from the **gitignored** `.env`), passed **only**
  into the OpenCode child-process env by the unit-7 adapter, and **never** written to argv, prompts,
  generated tests, the eval report, the manifest, logs, traces, or any committed file. `.env` stays
  gitignored (`.gitignore:154`); this unit **must not** commit `.env` or any file containing the key.
- Target-app Basic-Auth: the reference app's `testuser`/`testpass` are **published fixture credentials**
  (already used by the Phase-0 smoke/eval suites); generated tests may use them the same way. No *platform*
  or *tenant* secret is introduced. `E2B_API_KEY` is untouched (Phase 3).

### App launch (binding — reuse Phase-0 tooling, add nothing new to the app)
- **Live authoring run:** the agent explores the **CLEAN** app → launch via `make dev`'s clean launcher
  (backend `uv run uvicorn reference_app.backend.app:app --host 127.0.0.1 --port 8000` + Vite frontend on
  `:5173` with `VITE_API_BASE_URL=http://127.0.0.1:8000`).
- **Scoring + verification:** reuse the eval `webServer` pattern (`eval/buggy_backend.py` honoring
  `EVAL_BUG` for clean + the 3 buggy variants + the Vite frontend, fresh process per run) via the pinned
  `playwright.agent.config.ts`. The scorer clears ports 8000/5173 between runs (existing behavior).

## Definition of Done
- **G1–G6** achieved by the one-time live run; **V1–V8** hold against the committed artifacts with no key.
- The **first agent-generated TS Playwright + API tests** are committed at
  `reference_app/e2e/tests/generated/`, are runnable, **pass on the clean app**, and are genuinely
  DOM/schema-grounded (Reviewer-audited, not gamed).
- The committed **eval report** (`eval/reports/p1-agent-authoring-gate.eval.json` + `.txt`) shows, via
  `eval/score.py`'s metrics over the generated suite, `bug_catch_rate > 0.0` (≥1 of 3 caught),
  `false_positive_rate == 0.0`, `flake_rate == 0.0`, `assertion_meaningfulness_rate > 0.0` — beating the
  pinned naive floor.
- The **provenance manifest** (`eval/reports/p1-agent-authoring-gate.run.json`) stamps CLI+version /
  model / MCP version / app version / metrics / thresholds / `gate_passed`, secret-free.
- `make authoring` (live, with key) and `make authoring-gate` + `uv run pytest eval/tests -q` (verify, no
  key) exist and work; the generated-suite scoring path does **not** break the baseline `make eval`.
- **No regressions (V7):** baseline `make eval` still passes the Phase-0 gate; `make test` green; units
  1–7 suites + the unit-7 adapter tests green (including after any item-8 adjustment); the clean
  reference app is unchanged; no protected file changed (`DESIGN.md`, `META_PLAN.md`, `AGILE_PLAN.md`,
  `CLAUDE.md`, `.harness/**`).
- **Secret-safety:** `OPENAI_API_KEY` never committed/logged; `.env` stays gitignored. Consistent with
  `DESIGN.md §4/§5.1/§6/§11.4/§11.5/§11.10/§12/§13`, `META_PLAN.md` Phase 1, and `AGILE_PLAN.md` D8.
- **This is the Phase 1 EXIT GATE:** on APPROVE + green, the phase closes; Phase 2 (reliability layer)
  is re-planned next, including re-evaluating `gpt-4o-mini` against the stricter thresholds.

## Roles (how this live/measurement unit fits the TDD harness — READ before running the cycle)
> This unit is a **live demonstration + measurement**, not an ordinary red/green code unit. The role
> mapping is adapted (flagged for the plan gate, Interpretation #2):
- **Tester (TDD red):** writes the **deterministic verification harness** (`V1–V8`) that binds to the
  **committed** generated suite + eval report + manifest and re-runs the committed suite on the clean app
  — **without** calling the live model or needing the key. Initially **red** (artifacts absent).
- **Developer (TDD green):** performs the **one-time live authoring run** (with `OPENAI_API_KEY`) via
  `make authoring` to produce + commit the generated suite, eval report, and manifest; adds the minimal
  gate-runner + generated-suite scoring glue (item 6) and, only if the live run proves it necessary, the
  smallest unit-7 adapter adjustment (item 8, re-flowing through unit-7's tests). The Developer does
  **not** edit the Tester's verification harness. Once the artifacts are committed, the Tester's harness
  goes **green**.
- **Reviewer:** independently **re-runs** the committed generated suite on the clean app, **re-scores** it
  (reproducing `bug_catch > naive`), inspects the eval report + manifest, and **audits grounding /
  meaningfulness** (V6) — confirming the tests are genuinely grounded and the pass is not gamed. No key
  needed to review.

## Interpretations flagged (for the plan gate)
1. **Naive-baseline floor definition.** Pinned as `NAIVE_BUG_CATCH_FLOOR = 0.0` — a trivial/empty/
   page-load-only suite catches 0 of the 3 injected variants. "Better than naive" = the generated suite's
   `bug_catch_rate` **strictly > 0.0**, i.e. catches **≥1** of 3 (≥ 1/3 ≈ 0.334), **with a clean pass**
   (`false_positive == 0`) and ≥1 *meaningful* test. This is deliberately achievable by a modest
   `gpt-4o-mini` agent while still being a real bar (a suite that does nothing, or passes clean but
   discriminates no bug, fails). Committing an actual trivial suite to *empirically* show 0.0 is optional;
   the gate binds to the pinned constant.
2. **"Developer performs the live run" role-fit.** Standard harness has the Developer only make the
   Tester's tests green. Here the green transition is achieved by the Developer **executing a one-time,
   credit-spending live model run** and committing its outputs (plus minimal glue). This is a sanctioned
   adaptation because the unit is inherently a live demonstration; the Tester's verification stays
   model-free and binds to committed artifacts, preserving unbiasedness (Tester never runs the model;
   Reviewer re-verifies independently). If the harness prefers, the **orchestrator** (not the Developer
   subagent) may perform the live run and hand the committed artifacts to the Developer step — either is
   acceptable; the artifacts are the handoff.
3. **`eval/score.py` scores the baseline suite today.** To score the **generated** suite this unit adds
   the smallest glue — a `playwright.agent.config.ts` (`testDir ./tests/generated`, eval `webServer`
   pattern) + a scorer selection option/env — **without** changing the baseline path (`make eval` stays
   the Phase-0 gate). The four metric **definitions are reused verbatim**. This is a minimal Phase-0-
   artifact extension that flows through TDD.
4. **Adapter may need headless-emit flags.** OpenCode's headless `run` likely needs `--auto`
   (auto-approve tool permissions so it can write files), `--dir <workspace>`, and possibly `-c/--continue`
   + `-s/--session` to carry the Planner's plan into the Generator run. If the live run shows the unit-7
   adapter does not actually emit files without these, the **smallest** adapter fix is in scope and
   **re-flows through unit-7's tests** (which must stay green). This is the only sanctioned edit to a
   completed unit, and only if the live run proves it necessary.
5. **Live cost + non-determinism.** The live model run is performed **once**; its outputs are committed;
   all verification/re-verification is deterministic and model-free (V8), so the gate never re-spends
   credit and is reproducible after the fact. If the first live run misses the bar (e.g. catches 0, or
   fails on clean), the Developer may re-run/adjust the prompt-delivery/orchestration within units 6/7's
   contracts (and re-commit artifacts) until G1–G6 hold — the modest bar is chosen to make this feasible
   for `gpt-4o-mini`.
</content>

---

## Adapter headless-execution fix (Interpretation #4, concrete)

> This section makes Interpretation flag #4 concrete and testable. It supersedes the
> speculative language in flag #4 above wherever the two differ; flag #4's *authorization*
> ("the smallest adapter fix is in scope, re-flows through unit-7's tests") still stands.
> These facts were confirmed by live-run debugging of OpenCode v1.18.33 (`opencode run --help`
> + `~/.local/share/opencode/log/opencode.log`), not chosen as a design preference — they pin
> concrete, observable behavior of the unit-7 `OpenCodeRunner` adapter, testable **without** a
> live OpenCode process, model key, or network (same injected-command-runner / mock pattern
> unit 7's existing tests already use).

### Scope of this amendment (binding)
- Touches **only**: `runner/opencode_runner.py` (source) and `runner/tests/**` (new/extended
  tests, e.g. `runner/tests/test_opencode_runner.py` and/or `runner/tests/opencode_helpers.py`,
  and/or a new `runner/tests/test_opencode_runner_headless_fix.py`).
- Does **NOT** touch: `connectors/opencode/opencode.json` (must remain byte-unmodified on
  disk — verify via before/after byte comparison, the same pattern already used for
  `agent_config/qa_system_prompt.md` in unit 7's `test_c5_does_not_modify_shared_prompt_file`),
  `.opencode/agent/*.md`, `agent_config/qa_system_prompt.md`, `runner/authoring.py`, or any
  other unit 1–7.5 file.
- All of unit 7's existing tests (`runner/tests/test_opencode_runner.py`,
  `test_opencode_runner_credential_exception.py`) must stay green, unmodified in their existing
  assertions (extension/addition is fine; changing an existing assertion's meaning is not).

### Acceptance criteria (enumerated, testable — AF1–AF6)

- **AF1. `--auto` and `--dir` on every invocation.** For **both** the Planner and the Generator
  OpenCode invocations (every call the mock command-runner records for one run), the constructed
  argv includes the auto-approve-permissions flag `--auto`, and includes `--dir <workspace>`
  where `<workspace>` is the same directory passed to the command-runner as that call's `cwd`
  (i.e. `--dir` is present in argv and its value, resolved, equals the call's `cwd`, resolved).

- **AF2. `--continue` only on the Generator's (second) invocation.** Across the two ordered
  invocations of one run (Planner first, Generator second — unit 7's existing ordering,
  `test_c7_planner_precedes_generator`), the **first** (Planner) invocation's argv does **NOT**
  contain a continue-session flag (`--continue` or `-c`); the **second** (Generator) invocation's
  argv **DOES** contain one (`--continue` or `-c`). This must hold whichever of unit 7's two
  accepted invocation shapes (two-ordered-runs vs single-orchestrator, per
  `test_c7_planner_precedes_generator`) the implementation uses, insofar as two ordered
  `opencode run` invocations are made per run (session/plan continuation only makes sense across
  two calls).

- **AF3. Materialized, workspace-local config (not the shipped file).** For every invocation in
  a run, the value passed via the `OPENCODE_CONFIG` env var (`OPENCODE_CONFIG_ENV`) in that
  call's `env`:
  - is a file path located **inside** that run's workspace (the same directory tree as the
    call's `cwd` — i.e. not the shipped `connectors/opencode/opencode.json` resolved path, and
    not any other repo-root path);
  - is identical across both invocations of the same run (one materialization per run, shared
    by Planner and Generator);
  - names a file that exists and parses as valid JSON;
  - the materialized JSON preserves the shipped config's `model` value and `mcp` block content
    unchanged from `connectors/opencode/opencode.json`;
  - **AF3a (agent-role files).** every `{file:...}` reference appearing anywhere in the
    materialized config (i.e. under `agent.*.prompt`, referencing the qa-planner/qa-generator
    agent definitions), when resolved **relative to the materialized config file's own parent
    directory**, points to a file that **exists on disk inside the workspace** and whose content
    is **byte-identical** to the content of the shipped source it stands in for
    (`.opencode/agent/qa-planner.md` / `.opencode/agent/qa-generator.md` respectively) — these
    files never change at runtime, so an exact copy is correct here.
  - **AF3b (system-prompt instructions).** every string in the materialized config's top-level
    `instructions` list, when resolved **relative to the materialized config file's own parent
    directory**, points to a file that **exists on disk inside the workspace** and whose content
    is the run's **`invocation.system_prompt`** (the already BRD-injected, token-free final
    prompt assembled by unit 6's glue before the adapter ever sees it) — **explicitly NOT** a
    byte-copy of the shipped `agent_config/qa_system_prompt.md` template. The shipped template
    still contains the literal, unresolved `{{BRD}}` placeholder and must **never** appear
    verbatim inside the workspace — doing so would contradict unit 7's frozen
    `test_c5_delivers_brd_injected_prompt_and_seven_fields` (in
    `runner/tests/test_opencode_runner.py`, not to be touched by this amendment), which — via the
    shared helper `agent_visible_text`, a recursive scan of every file under the call's
    `cwd`/workspace — already asserts the literal `{{BRD}}` token is absent from everything
    visible to the agent.
  - **Negative check:** the shipped `connectors/opencode/opencode.json` file's bytes on disk are
    unchanged before vs. after the run (it is read, never written).

- **AF4. `permission.external_directory` is `"deny"` — never `"allow"`.** The materialized
  config from AF3 contains a `permission` object whose `external_directory` key is the exact
  string `"deny"`. Pin the negative invariant as its own test: across every code path /
  constructor-knob combination exercised by the adapter's tests (default construction, model
  override, custom `opencode_config_path`, etc.), the materialized config's
  `permission.external_directory` is **never** `"allow"` (nor absent-and-defaulting-to-allow, if
  the adapter sets the key at all it must be `"deny"`).

- **AF5. Mock-only verifiability, no live process.** AF1–AF4 are fully verifiable using the same
  injected-command-runner seam (`CommandRunner` / `FakeCommandRunner`) unit 7's existing tests
  use — inspecting the recorded `argv`, `cwd`, and `env` of each mock call, plus reading the
  materialized config file(s) the run left on disk in the injected/temp workspace. No real
  `opencode` process, no network egress, no `OPENAI_API_KEY` value is required for these
  assertions to hold (a placeholder/sentinel credential value, as unit 7's tests already use, is
  sufficient to satisfy the adapter's pre-spawn credential check).

- **AF6. No regression to unit 7's pinned behaviors.** All of unit 7's existing pinned
  behaviors (argv starts with `opencode run`; `--model`/`--agent` selection; MCP wiring via the
  governing config; BRD+prompt+seven-fields delivery; workspace distinct from `output_dir`;
  output capture; credential injected into child env only and never in argv/prompt/logs/output;
  named-error behavior for missing credential/config; non-zero-exit and no-tests-produced
  handling; determinism; pinned public constants/import path) continue to hold unchanged after
  this fix — i.e. `runner/tests/test_opencode_runner.py` and
  `test_opencode_runner_credential_exception.py` pass without modification to their existing
  assertions.

### Definition of Done (this amendment)
AF1–AF6 hold, verified by the mock-command-runner pattern with no live OpenCode process, no
network, and no model key beyond a placeholder sentinel; only `runner/opencode_runner.py` and
`runner/tests/**` changed; `connectors/opencode/opencode.json` byte-unmodified; unit 7's and
unit 7.5's existing test suites remain green.

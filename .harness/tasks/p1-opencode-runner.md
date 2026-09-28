# Task: `p1-opencode-runner` — OpenCode runner adapter (concrete `AgentRunner`, mock/dry-run-verified)

## Title
The **OpenCode runner adapter** for Phase 1: Python (`uv`) code that **implements the unit-6 injectable
`AgentRunner` seam** — a callable `runner(AuthoringInvocation) -> AgentRunOutput` — by binding the
**OpenCode** headless coding agent (open-source terminal agent) driving the OpenAI model
**`gpt-4o-mini`** to that seam. Given the assembled per-run invocation from `runner.authoring`, it
**constructs and drives an OpenCode headless run** that (a) reads the platform-owned model credential
from the `OPENAI_API_KEY` **reference** (never inlined, never logged), (b) wires the Playwright-MCP
config into OpenCode's own config format, (c) translates the **Planner → Generator** flow (under the
generic QA system prompt — into which the glue has already injected the BRD — plus the seven structured
Planner fields) into OpenCode's invocation mechanism at `model=openai/gpt-4o-mini`, and (d) **captures
the generated TS Playwright + API test files** and returns them as `AgentRunOutput.generated_tests` for
the glue to write. It **ships the OpenCode connector config** (an `opencode.json`-format file wiring the
model + the Playwright MCP server) and **OpenCode-format Planner/Generator agent definitions** that
reference the *same* portable `agent_config/qa_system_prompt.md`. It is **unit-tested WITHOUT the key**
by **injecting the subprocess/command runner** and asserting the **constructed OpenCode invocation**
(command, args, `--model openai/gpt-4o-mini`, the MCP-config wiring, the prompt carrying the injected
BRD + fields, and the output capture) — **no live network, no model call, no browser, and no real
OpenCode process** in tests. The live run is unit 8 (`p1-agent-authoring-gate`, needs `OPENAI_API_KEY`).

## Context (plan item)
- **AGILE_PLAN.md → Phase 1 → D7** ("OpenCode runner adapter (key-free, mock/dry-run tested) — ACTIVE
  (unit 7, `p1-opencode-runner`)"). Also the Phase 1 locked-units table (unit 7), and the exit-gate
  clause "Units 1–7 (all key-free) merged and green … the mock/dry-run-verified OpenCode runner adapter".
- **AGILE_PLAN.md → Conflicts / deviations** — the **human-authorized 2026-09-28 CLI/model swap** to
  **OpenCode + OpenAI `gpt-4o-mini`** (platform-owned `OPENAI_API_KEY`) in place of the default Claude
  Code + `claude-sonnet-5`. This unit is that deviation made concrete at the runner seam. The model is a
  **bumpable config value** (module constant); `gpt-4o-mini`'s weakness is a **Phase-2 risk flag**, not a
  Phase-1 blocker.
- **Backlog unit 7** (`p1-opencode-runner`, status `spec-ready (active)`).
- **DESIGN.md §2 — "configure the brain, don't build it"** — the orchestrator is an *off-the-shelf*
  coding-agent CLI; the CLI **and** model are **per-app configurable** behind a **generic sandbox
  contract** so an open-source agent CLI can "swap into the same slot." This unit binds OpenCode into
  that slot via the unit-6 seam — the design-sanctioned swap, exercised early.
- **META_PLAN.md Phase 7 — "open-agent CLI swap (Copilot/open CLI via the generic sandbox contract)"** —
  the intended capability this unit prototypes ahead of schedule; the seam is the swap point.
- **DESIGN.md §4** — the product pipeline **BRD/prompt → Planner → Generator → …**. This unit drives the
  **Planner → Generator** authoring portion through OpenCode. Execution/Healer/Verifier/Reports/PR are
  later phases.
- **DESIGN.md §5.1 (Grounding)** — selectors come from the live DOM snapshot via Playwright MCP; API
  assertions are grounded in the schema. This unit's job is to **hand OpenCode the grounding inputs**
  (the MCP config wired into OpenCode's config, the normalized API surface, the reliability-bearing
  system prompt with the BRD, the Planner/Generator roles) and to **run** OpenCode so it snapshots the
  DOM live. The actual DOM snapshotting happens inside the live OpenCode+MCP run (unit 8); this unit is
  verified with a **mock** OpenCode process.
- **DESIGN.md §6** — one generic system prompt + the per-run **BRD** (already injected by the glue into
  `invocation.system_prompt`) + the seven structured Planner fields (`invocation.planner_fields`). This
  unit **delivers** those to OpenCode; it does **not** re-inject or re-author the prompt.
- **DESIGN.md §11.5 — model/CLI credentials are platform-owned**, metered per tenant, behind the egress
  allowlist, **never tenant-supplied, never exposed to the agent's readable context.** The OpenAI key is
  therefore **not** part of the invocation bundle; the runner reads it from a **platform** env-var
  reference (`OPENAI_API_KEY`) and injects it only into the OpenCode child-process environment — never
  into argv, prompts, logs, traces, artifacts, or the returned output.
- **DESIGN.md §11.4 — target-app Basic-Auth** is a **reference** injected at runtime, egress-scoped,
  "never in prompts, logs, traces, or artifacts." The invocation carries only
  `basic_auth_credential_ref`; this unit keeps that guarantee (never places the resolved secret in argv,
  prompt, logs, or output). The concrete browser-login wiring is exercised live in unit 8.
- **DESIGN.md §11.10 (supply chain)** — pin the OpenCode CLI version and the MCP server version. The
  Playwright MCP server stays pinned to `@playwright/mcp@0.0.41` (matching unit-3's
  `connectors/mcp/playwright.mcp.json`); the targeted OpenCode CLI version is pinned in this unit.
- **DESIGN.md §12** — control-plane glue/orchestration is **Python (`uv`)**; test artifacts stay
  TypeScript Playwright. This adapter is Python tooling that *drives* OpenCode to *produce* TS artifacts.
- **DESIGN.md §13 — repo layout** — this is run-invocation code → lives under `runner/` alongside the
  unit-6 glue; the OpenCode connector config + agent defs are placed per **Interfaces §Paths** below.

**Given app state (contracts this unit builds on — do NOT re-derive, duplicate, or modify):**
- **Unit 6 — the seam this unit implements** at `runner/authoring.py` (public import `runner.authoring`),
  merged `c3694e0`:
  - Entry point `run_authoring(config_source, *, agent_runner, output_dir=None, source_type="auto") -> RunResult`.
  - **Runner seam:** `AgentRunner` is a callable `agent_runner(invocation: AuthoringInvocation) -> AgentRunOutput`.
  - `AuthoringInvocation` (frozen dataclass) fields: `system_prompt` (str — final, **BRD already
    injected**), `api_surface` (dict — unit-1 `ApiSurface.to_dict()`), `target_url` (str),
    `planner_fields` (Mapping[str,str] — the seven fields), `mcp_config_path` (str =
    `connectors/mcp/playwright.mcp.json`), `planner_agent` (str = `"qa-planner"`), `generator_agent`
    (str = `"qa-generator"`), `basic_auth_credential_ref` (str — the target-app auth **reference name**
    only), `output_dir` (str — resolved).
  - `AgentRunOutput` (dataclass) fields: `status` (str — `"ok"` on success; any other value = non-success,
    on which the glue writes **no** artifacts), `generated_tests` (Mapping[str,str] — **relative filename
    → file content**), `detail` (Optional[str]). The glue writes `generated_tests` to `output_dir` **only**
    when `status == "ok"`, and **surfaces** (never swallows) a runner exception.
- **Unit 3 — Playwright-MCP config** at `connectors/mcp/playwright.mcp.json`: `{ "mcpServers": {
  "playwright": { "command": "npx", "args": ["-y", "@playwright/mcp@0.0.41", "--headless", "--browser",
  "chromium"] } } }`. Merged `8f0ac6a`. (This is **Claude/MCP-native** shape; OpenCode uses a different
  MCP shape — see Interfaces. The pinned server identity/version must match.)
- **Unit 4 — QA system prompt** at `agent_config/qa_system_prompt.md` with the named reliability rules
  (`DOM_GROUNDING`, `MEANINGFUL_ASSERTIONS`, `API_CROSS_CHECK`, `HEAL_VS_REGRESSION`,
  `UNTRUSTED_APP_CONTENT`) and the `{{BRD}}` injection token. Merged `22c9954`. (The glue has **already**
  injected the BRD into `invocation.system_prompt`; this unit does not touch the token.)
- **Unit 5 — product sub-agents** `.claude/agents/qa-planner.md` + `.claude/agents/qa-generator.md`
  (Claude-CLI frontmatter, bound to the QA prompt + MCP config). Merged `f7bee09`. **These stay** (the
  Claude-CLI path, kept for the Phase-7 multi-CLI story). This unit **adds** the OpenCode-format
  equivalents (Interfaces §Paths) — it does **not** modify the `.claude/agents/*` files.
- **`reference_app/BRD.md`**, the running reference app (UI `:5173`, API `:8000/openapi.json`, Basic
  Auth `testuser`/`testpass`), and the Phase 0 `eval/` harness exist and are green.
- Root project uses `uv` (`pyproject.toml`); suites run via `uv run pytest <dir> -q`.

## Scope

### In scope
1. **An OpenCode runner adapter module** at the pinned home (Interfaces §Paths) exposing a documented,
   stable public API (Interfaces §Public API): a concrete runner satisfying the unit-6 `AgentRunner`
   seam — callable `(AuthoringInvocation) -> AgentRunOutput` — that constructs and drives an OpenCode
   headless run and returns the captured generated tests. It **composes**, and does not re-implement,
   the unit-6 types (`AuthoringInvocation`, `AgentRunOutput`) — importing them from `runner.authoring`.
2. **An injectable subprocess/command-runner seam (the crux for key-free testing).** The adapter must
   invoke OpenCode **only** through an injected command-runner (Interfaces §Command-runner seam) — a
   callable that takes the argv, cwd, environment, and optional stdin and returns a completed-command
   result (returncode, stdout, stderr). The adapter **must not** hard-code a direct `subprocess`/exec
   call that the unit tests cannot substitute; a real default (spawning `opencode`) may ship but must be
   **replaceable** and **never exercised** by any unit-7 test.
3. **Model selection = `openai/gpt-4o-mini`, as a bumpable config value.** The model is a documented
   module constant (Interfaces §Constants), default `"openai/gpt-4o-mini"`, overridable at construction.
   The constructed OpenCode invocation selects this model explicitly (assertable in the argv, e.g.
   `--model openai/gpt-4o-mini`).
4. **Ship the OpenCode connector config** at the pinned path (Interfaces §Paths): an `opencode.json`-
   format file (valid JSON) that declares (a) the model `openai/gpt-4o-mini`, and (b) the Playwright MCP
   server in **OpenCode's MCP format** (Interfaces §OpenCode MCP), pinned to `@playwright/mcp@0.0.41`
   (matching unit 3). It references the shared generic QA prompt as OpenCode instructions and/or the
   OpenCode agent definitions (Interfaces §OpenCode config).
5. **Ship OpenCode-format Planner/Generator agent definitions** at the pinned paths (Interfaces §Paths):
   the OpenCode equivalents of unit-5's Planner/Generator, in OpenCode's agent format, that **reference
   the same portable `agent_config/qa_system_prompt.md`** and the same reliability rules and MCP
   grounding — the portable core is shared; only the CLI-specific wrapper differs. Names align with the
   invocation's `planner_agent` / `generator_agent` identities (`qa-planner` / `qa-generator`). This unit
   **does not modify** the `.claude/agents/*` files.
6. **Make the OpenCode config discoverable to the run** (Interfaces §OpenCode invocation): the adapter
   ensures the connector config governs the OpenCode run (via the pinned discovery mechanism — see the
   flagged interpretation), so the run uses the wired model + MCP + agents.
7. **Translate the Planner → Generator flow** (Interfaces §OpenCode invocation): the adapter drives
   OpenCode so that the **Planner role runs before the Generator role**, both under the generic QA
   system prompt (with the BRD already injected, carried from `invocation.system_prompt`) and the seven
   `planner_fields`, pointed at the `target_url` and the MCP config, producing grounded TS Playwright +
   API tests. The concrete OpenCode mechanism (a single orchestrating primary run vs. two sequential
   `opencode run --agent …` invocations) is the developer's choice, **but** the constructed invocation(s)
   must carry the pinned, assertable facts in Interfaces §OpenCode invocation.
8. **Deliver the system prompt + fields to OpenCode** without re-authoring them: materialize
   `invocation.system_prompt` (already BRD-injected) as OpenCode instructions/agent prompt and pass the
   seven `planner_fields` into the run context/message. No re-injection of `{{BRD}}`; no editing of the
   unit-4 prompt file.
9. **Capture generated tests → `AgentRunOutput.generated_tests`.** After a successful OpenCode run, the
   adapter collects the produced test files from the run's workspace by the pinned globs (Interfaces
   §Output capture) and returns them as a mapping of **relative filename → file content**, so the unit-6
   glue writes them to `output_dir`. The adapter operates OpenCode in a **workspace** distinct from the
   glue's `output_dir` (the glue remains the single writer of `output_dir`) — see the flagged
   interpretation.
10. **Model-credential handling (reference only; §11.5).** Read the OpenAI key from the `OPENAI_API_KEY`
    env-var **reference** (constant, Interfaces §Constants) at run time; inject it **only** into the
    OpenCode child-process environment; **never** place it in argv, the prompt/instructions, stdout/
    stderr echoes, the `AgentRunOutput` (`status`/`generated_tests`/`detail`), logs, or any artifact. If
    the reference is **unset** at a real spawn, raise the named error (Interfaces §Errors).
11. **Target-app Basic-Auth safety (reference only; §11.4).** The invocation's `basic_auth_credential_ref`
    is carried as a **reference**; the adapter never places the resolved target-app secret in argv, the
    prompt/instructions, logs, or the returned output. (The concrete browser-login wiring is exercised
    live in unit 8; here the secret-safety rule is the contract.)
12. **Error / non-success behavior (surfaced, never swallowed).** A non-zero OpenCode exit, or a run
    that produces no capturable tests, results in a **non-`"ok"` `AgentRunOutput.status`** with a
    **secret-scrubbed** `detail` (so the unit-6 glue writes no artifacts and surfaces the failure);
    misconfiguration (missing connector config, missing model credential at real spawn) raises a
    **named adapter error** (Interfaces §Errors). No secret ever appears in any error message/detail.
13. **A pytest test suite** at the pinned test dir proving every acceptance criterion using an **injected
    mock command-runner** + fixtures + `tmp_path` workspaces, runnable via `uv run pytest <dir> -q`. **No
    model key, no network, no browser, no real OpenCode process.**
14. **Docs**: a short `README.md` (or documented module docstring) at the adapter's home documenting the
    public import path, the runner class/factory + its constructor knobs (command-runner, model,
    config path, workspace), the command-runner seam, the OpenCode invocation contract, the connector-
    config + agent-def paths, the credential-reference + secret-safety rules, the constants, and the
    named errors.

### Out of scope (defer)
- **The REAL OpenCode run** — spawning `opencode` for real against the running reference app with
  `OPENAI_API_KEY`, producing *real* tests, committing them, and `eval/` scoring vs. the naive baseline —
  is **unit 8** (`p1-agent-authoring-gate`, needs the key).
- **Any live OpenCode process, browser/MCP launch, network egress, or model call** at unit-test time.
- **Modifying** the unit-6 glue, unit-1..5 artifacts, or the `.claude/agents/*` files. This unit **adds**
  a new module + connector config + OpenCode agent defs + tests + docs, and imports the unit-6 seam types.
- **Verifier / Healer / assertion-audit / API cross-check / self-heal / deterministic replay** — Phase 2.
- **E2B sandboxing, egress allowlist, git proxy, PR delivery** — Phase 3.
- **Real secret vaulting / rotation / metering** — only env-var **reference** resolution is used here.
- **Bumping the model** beyond making it a construction knob (Phase-2 concern).

## Acceptance criteria (enumerated, testable — all verifiable with a MOCK command-runner; no key/network/browser/OpenCode-process)

### Seam conformance
1. **Satisfies the unit-6 `AgentRunner` seam.** The adapter is a callable `(AuthoringInvocation) ->
   AgentRunOutput` (importing both types from `runner.authoring`), such that
   `runner.authoring.run_authoring(config_source, agent_runner=<this adapter>, output_dir=tmp)` runs
   end-to-end with a mock command-runner and the glue writes the captured tests. (May be a class instance
   with `__call__`, or a factory returning such a callable — Interfaces §Public API.)

### Constructed OpenCode invocation (asserted on the argv/env/cwd/input handed to the mock command-runner)
2. **Invokes the OpenCode binary in headless/run mode.** The constructed argv starts with the pinned
   OpenCode binary (constant, default `"opencode"`) and its non-interactive **run** subcommand (the
   pinned `opencode run …` form — Interfaces §OpenCode invocation).
3. **Selects `openai/gpt-4o-mini`.** The argv explicitly selects the model (e.g. `--model
   openai/gpt-4o-mini`), matching the module constant; constructing the adapter with an overridden model
   changes the argv accordingly (proves the bumpable-config-value property).
4. **Wires the MCP config.** The run is governed by the shipped OpenCode connector config that declares
   the Playwright MCP server (OpenCode MCP format, `@playwright/mcp@0.0.41`) — via the pinned discovery
   mechanism (config path present in argv `--config`/`OPENCODE_CONFIG` env / workspace `opencode.json`,
   per the flagged interpretation). Assertable: the connector config path (or its materialized copy) is
   referenced by the invocation, and that config file exists and declares the pinned MCP server.
5. **Delivers the BRD-injected system prompt + the seven fields.** The `invocation.system_prompt` text
   (which contains the injected BRD) reaches OpenCode as instructions/agent-prompt/message, and the seven
   `planner_fields` are present in the run context/message. Assertable: the prompt text (or its
   materialized instructions file) contains a stable marker from `invocation.system_prompt` **and** the
   BRD content, and the field values appear. The adapter does **not** re-inject `{{BRD}}` or edit
   `agent_config/qa_system_prompt.md`.
6. **Points at the target URL.** The `invocation.target_url` reaches the run (in the message/context) so
   OpenCode+MCP knows which app to explore.
7. **Planner precedes Generator.** The Planner role (`invocation.planner_agent` = `qa-planner`) is
   exercised **before** the Generator role (`invocation.generator_agent` = `qa-generator`) — whether via
   two ordered `opencode run --agent …` calls (assert call order + `--agent` values) or a single primary
   orchestrator that references both (assert both identities present in the governing config/message and
   the ordering encoded). Both identities are distinct and both present.
8. **Runs in a workspace distinct from `output_dir`.** The command-runner is invoked with `cwd` set to
   the adapter's workspace directory, which is **not** `invocation.output_dir` (the glue is the single
   writer of `output_dir`). Assertable via the `cwd` passed to the mock.

### Output capture
9. **Captures generated tests into the mapping.** Given a mock command-runner that simulates a successful
   OpenCode run by writing canned test files into the run workspace (e.g. `cart.spec.ts`,
   `orders.api.spec.ts`) and returning exit code 0, the adapter returns `AgentRunOutput(status="ok",
   generated_tests={<relative filename>: <byte-exact content>, …})` for files matching the pinned globs
   (Interfaces §Output capture). The relative filenames are workspace-relative.
10. **End-to-end through the glue.** Driving `run_authoring(..., agent_runner=<adapter>, output_dir=tmp)`
    with that mock command-runner results in the glue writing exactly those captured files under `tmp`
    with byte-exact content (proves the adapter's mapping is consumed correctly by unit 6).

### Credential handling & secret-safety (§11.5, §11.4)
11. **Model key injected into the child env only, from the reference.** With a **sentinel** value placed
    in the environment under `OPENAI_API_KEY`, the env dict handed to the command-runner contains
    `OPENAI_API_KEY=<sentinel>`, while the sentinel appears in **none** of: the argv, the prompt/
    instructions/message, the run workspace files, the returned `AgentRunOutput` (`status`/`detail`/
    `generated_tests`), or any log/print/stdout the adapter emits.
12. **Missing model credential → named error at spawn.** With `OPENAI_API_KEY` **unset**, a real spawn is
    refused with the named adapter error (Interfaces §Errors), raised **before** any OpenCode process
    would start; the error message contains the reference **name** but **no** secret value. (Testable
    without a key: assert the named error is raised when the reference env var is absent.)
13. **Target-app auth stays a reference.** With a **sentinel** placed under the config's
    `basic_auth_credential_ref` name, that sentinel appears in **none** of the argv, the prompt/
    instructions/message, logs, or the returned output. (The adapter carries only the reference name.)

### Error / non-success behavior (surfaced, never swallowed)
14. **Non-zero exit → non-`ok` status, scrubbed detail.** A mock command-runner returning a non-zero exit
    code (with stderr) yields `AgentRunOutput` with a **non-`"ok"` status** and a `detail` that (a) is
    present/human-readable and (b) contains **no** secret value. The adapter does **not** raise for a
    normal run failure — it returns the non-success status so the unit-6 glue surfaces it and writes no
    artifacts.
15. **No tests produced → non-`ok` status.** A mock run that exits 0 but writes no matching test files
    yields a **non-`"ok"` status** (and empty/omitted `generated_tests`), so the glue writes nothing and
    the failure is visible.
16. **Missing connector config → named error.** If the pinned OpenCode connector config cannot be found,
    the adapter raises the named adapter error (Interfaces §Errors), not a silent success.

### Determinism, placement, no-regression
17. **Deterministic construction.** Constructing the OpenCode invocation twice from the same invocation +
    same constructor knobs yields identical argv (modulo an unavoidable per-run temp workspace path),
    identical governing config content, and identical delivered prompt/fields. No nondeterministic
    content baked into argv/config/prompt.
18. **Correct home + runnable tests.** New code lives at the pinned home with the pinned public import
    path; the connector config + OpenCode agent defs live at the pinned paths; tests live at the pinned
    test dir and pass via `uv run pytest <dir> -q` with **no** key, network, browser, or real OpenCode
    process (mock command-runner only).
19. **No regressions / no side effects beyond the workspace.** No change to the unit-6 glue, units 1–5
    artifacts, the `.claude/agents/*` files, `reference_app/**`, or any protected file. The adapter
    performs **no network egress** and, in tests, **no writes** outside the injected/`tmp_path` workspace;
    it **never** logs/persists either credential value. Units 1–6 tests, Phase 0 `make test` / `make
    eval` / backend pytest still pass.

## Interfaces / contracts (pin these precisely)

### Paths (binding)
- **Module home:** `runner/` (existing package). **Public import path (binding):** `runner.opencode_runner`.
  The public runner class/factory, the command-runner seam type, the completed-command result type, the
  named errors, and the module constants are importable from `runner.opencode_runner`. (Internal file
  layout is the developer's choice; this import path is stable.)
- **OpenCode connector config (binding path):** `connectors/opencode/opencode.json` — the shipped
  `opencode.json`-format config (model + MCP + instructions/agents). Placed under `connectors/`
  alongside the Playwright-MCP config, per `DESIGN.md §13`.
- **OpenCode-format agent definitions (binding paths):** `.opencode/agent/qa-planner.md` and
  `.opencode/agent/qa-generator.md` (OpenCode's project-agent location + format). They reference the
  shared `agent_config/qa_system_prompt.md`. (If the developer instead defines the agents **inline** in
  `connectors/opencode/opencode.json` under OpenCode's `agent` key, that is acceptable **provided** the
  two roles are present, named `qa-planner`/`qa-generator`, and reference the shared prompt — but the
  markdown-file location above is the pinned default; flag any deviation.)
- **Tests:** `runner/tests/` (pytest) — runnable as `uv run pytest runner/tests -q`. (New test module(s)
  for this unit; do not disturb the existing unit-6 tests in that dir.)
- **Docs:** `runner/README.md` (extend it) or a documented module docstring.
- **Referenced (read-only) artifact paths:** QA system prompt `agent_config/qa_system_prompt.md`;
  Playwright-MCP (Claude/native) config `connectors/mcp/playwright.mcp.json` (source of the pinned MCP
  server identity/version to mirror into the OpenCode config); unit-6 seam `runner.authoring`.

### Public API (names below are binding; internal structure the developer's choice)
- **Runner (satisfies unit-6 `AgentRunner`):** a class **`OpenCodeRunner`** whose instances are callable
  `__call__(self, invocation: AuthoringInvocation) -> AgentRunOutput` (imported types from
  `runner.authoring`). Constructor knobs (keyword, all with sane defaults so a default construction is
  possible):
  - `command_runner` — the injected command-runner (Command-runner seam). Default = a real subprocess
    runner (never exercised by unit-7 tests).
  - `model` — default the module constant `DEFAULT_MODEL` (`"openai/gpt-4o-mini"`).
  - `opencode_config_path` — default the module constant `OPENCODE_CONFIG_PATH`
    (`connectors/opencode/opencode.json`).
  - `workspace_dir` — default `None` (adapter creates/uses a per-run workspace distinct from `output_dir`).
  - `credential_env` — default the module constant `OPENAI_API_KEY_ENV` (`"OPENAI_API_KEY"`).
  - `opencode_bin` — default the module constant `OPENCODE_BIN` (`"opencode"`).
  - (optional) `timeout` — a run timeout.
  - A thin factory `make_opencode_runner(**knobs) -> OpenCodeRunner` is acceptable but not required.

### Command-runner seam (the injectable interface — binding shape; concrete type the developer's choice, documented)
- A single callable the adapter invokes to run OpenCode, e.g. `CommandRunner(argv: list[str], *, cwd:
  str, env: Mapping[str, str], input: Optional[str] = None, timeout: Optional[float] = None) ->
  CompletedCommand`. `CompletedCommand` exposes `returncode` (int), `stdout` (str), `stderr` (str)
  (attribute names binding). Expressed as a `typing.Protocol`, a callable, or a small ABC — documented
  and stable so unit-8's real runner and unit-7's mock both satisfy it. The adapter **must** route every
  OpenCode invocation through this seam.

### Constants (module-level, documented; names binding)
- `DEFAULT_MODEL = "openai/gpt-4o-mini"` (bumpable later, e.g. `"openai/gpt-4o"`, `"openai/gpt-4.1"`).
- `OPENAI_API_KEY_ENV = "OPENAI_API_KEY"` (the platform model-credential **reference name**, §11.5).
- `OPENCODE_CONFIG_PATH = "connectors/opencode/opencode.json"` (repo-root-relative).
- `OPENCODE_BIN = "opencode"`.
- `PLANNER_AGENT = "qa-planner"`, `GENERATOR_AGENT = "qa-generator"` (align with the invocation).
- Generated-test capture globs (e.g. `("**/*.spec.ts", "**/*.test.ts", "**/*.api.spec.ts")`) — the
  pinned patterns used to collect tests from the workspace; documented.

### OpenCode invocation contract (binding facts; concrete phrasing the developer's choice)
- **Binary + mode:** `opencode run` — OpenCode's non-interactive/headless run. The message/prompt is
  supplied as positional argument(s) and/or piped stdin.
- **Model:** `--model openai/gpt-4o-mini` (the `DEFAULT_MODEL` constant), assertable in argv.
- **Agent selection:** the Planner and Generator roles are selected via OpenCode's `--agent` mechanism
  (`--agent qa-planner`, `--agent qa-generator`) if two ordered runs are used; or referenced by a single
  primary orchestrator agent otherwise. Planner **before** Generator.
- **Config governance:** the run is governed by `connectors/opencode/opencode.json` via the pinned
  discovery mechanism (see flagged interpretation) — model + Playwright MCP + agents.
- **Environment:** the child env includes the resolved `OPENAI_API_KEY` (from the reference) **only**;
  the model key is never in argv/prompt/logs/output. If the discovery mechanism uses `OPENCODE_CONFIG`,
  it is set in the child env to the connector-config path.
- **Prompt/fields delivery:** `invocation.system_prompt` (BRD already injected) is delivered as OpenCode
  instructions/agent-prompt; the seven `planner_fields` + `target_url` are delivered in the message/
  context. No re-injection of `{{BRD}}`.
- **Working directory:** a per-run workspace distinct from `invocation.output_dir`.

### OpenCode MCP format (binding shape — mirror unit-3's pinned server)
- OpenCode declares MCP servers under a top-level **`mcp`** key (not `mcpServers`). Local (stdio) server
  shape (as targeted): `"mcp": { "playwright": { "type": "local", "command": ["npx", "-y",
  "@playwright/mcp@0.0.41", "--headless", "--browser", "chromium"], "enabled": true } }`. The **server
  identity + version must match** unit-3's `connectors/mcp/playwright.mcp.json`
  (`@playwright/mcp@0.0.41`, headless chromium). (See flagged interpretation on OpenCode's exact MCP key
  shape / version.)

### OpenCode config format (binding shape)
- `connectors/opencode/opencode.json` is valid JSON declaring at least: `"$schema"` (OpenCode's config
  schema URL), `"model": "openai/gpt-4o-mini"`, the `"mcp"` block above, and either an `"instructions"`
  reference to the shared QA prompt (`agent_config/qa_system_prompt.md`) and/or an `"agent"` block /
  `.opencode/agent/*.md` files for `qa-planner` + `qa-generator`. The two OpenCode agent roles reference
  the shared portable prompt + reliability rules + MCP grounding (mirroring unit-5's intent).

### Output capture (binding)
- After a `returncode == 0` run, the adapter collects files under the run workspace matching the pinned
  globs into `generated_tests` (relative-filename → content). Zero matches ⇒ non-`"ok"` status
  (criterion 15). The adapter operates the workspace **separately** from `invocation.output_dir`; the
  unit-6 glue writes the mapping to `output_dir`.

### Errors (named, documented)
- A module-level **adapter error base** (e.g. `OpenCodeRunnerError`; exact name the developer's choice,
  documented) with the failure cases: **missing model credential at real spawn** (criterion 12; message
  names the **reference**, never a value) and **missing connector config** (criterion 16). Distinct named
  subclasses are allowed but not required. **No error message ever contains a secret value.**
- **Normal run failure is NOT an exception:** a non-zero OpenCode exit / no-tests-produced returns a
  **non-`"ok"` `AgentRunOutput.status`** with a scrubbed `detail` (criteria 14–15), matching the unit-6
  glue's contract (glue writes nothing on non-`"ok"`).

### Secret-safety (binding rules)
- **Model key (§11.5):** platform-owned; read from the `OPENAI_API_KEY` reference; injected only into the
  child env; never in argv, prompt/instructions, workspace files, `AgentRunOutput`, logs, or artifacts.
- **Target-app auth (§11.4):** only `invocation.basic_auth_credential_ref` (a name) flows; the resolved
  secret never appears in argv, prompt/instructions, logs, or output. The Tester proves both via env-var
  sentinels asserted absent from every surface.

### Fixtures (guidance for the Tester — not implementation)
- **Mock command-runner:** a test-local callable satisfying the command-runner seam that records the
  argv/cwd/env/input it received and can (a) write canned test files into `cwd` and return `returncode
  0` (drives 9–10, 17), (b) return a non-zero `returncode` with stderr (drives 14), (c) exit 0 writing no
  test files (drives 15). It never spawns a process.
- **Invocation:** build an `AuthoringInvocation` directly, or via `runner.authoring.run_authoring` using
  the shipped `connectors/examples/reference_app.target.json` with `load_api_spec`/`load_spec`
  monkeypatched (no network) — drives 1, 5–8, 10.
- **Secrets:** env-var sentinels under `OPENAI_API_KEY` and under the config's `basic_auth_credential_ref`
  drive 11, 13; unsetting `OPENAI_API_KEY` drives 12.
- **Config presence:** the shipped `connectors/opencode/opencode.json` drives 4; a redirected/missing
  path drives 16.

## Definition of Done
- All acceptance criteria **1–19** pass.
- The adapter exists at `runner/opencode_runner.py`-equiv with public import path
  `runner.opencode_runner`, exposing `OpenCodeRunner` (callable satisfying the unit-6 `AgentRunner`
  seam), the command-runner seam + completed-command result type, the pinned constants (`DEFAULT_MODEL`
  = `openai/gpt-4o-mini`, `OPENAI_API_KEY_ENV`, `OPENCODE_CONFIG_PATH`, `OPENCODE_BIN`, agent names,
  capture globs), and the named adapter error(s) — all documented in `runner/README.md` (or docstring).
- The OpenCode connector config exists at `connectors/opencode/opencode.json` (model + Playwright MCP in
  OpenCode format, pinned `@playwright/mcp@0.0.41`, references the shared QA prompt/agents), and the
  OpenCode-format Planner/Generator agent definitions exist at `.opencode/agent/qa-planner.md` +
  `.opencode/agent/qa-generator.md` (or inline per the pinned exception), referencing
  `agent_config/qa_system_prompt.md`.
- `uv run pytest runner/tests -q` is green from a clean checkout under `uv`, with **no** model key, **no**
  network, **no** browser, and **no** real OpenCode process (mock command-runner only). Units 1–6 tests
  still pass; the adapter drives cleanly through `runner.authoring.run_authoring`.
- No protected file changed (`DESIGN.md`, `META_PLAN.md`, `AGILE_PLAN.md`, `CLAUDE.md`, `.harness/**`);
  no change to the unit-6 glue, units 1–5 artifacts, the `.claude/agents/*` files, or `reference_app/**`
  behavior. Phase 0 `make test` / `make eval` / backend pytest still pass. Consistent with `DESIGN.md
  §2/§4/§5.1/§6/§11.4/§11.5/§11.10/§12/§13`, `META_PLAN.md` Phase 1 + Phase 7, and `AGILE_PLAN.md` D7.
- **Tester-can-author-from-this-alone:** from this spec alone — the pinned import path + `OpenCodeRunner`
  callable satisfying the unit-6 seam, the **command-runner seam** (argv/cwd/env/input →
  returncode/stdout/stderr) the mock substitutes, the pinned OpenCode invocation contract (binary+`run`,
  `--model openai/gpt-4o-mini`, `--agent` planner-before-generator, config governance, prompt+fields
  delivery, workspace≠output_dir), the constants, the connector-config + OpenCode-agent-def paths + MCP
  format, the output-capture globs, the credential-reference + secret-safety rules, and the named
  errors + non-`"ok"`-status behavior — the Tester can author the failing verification tests with a
  **mock command-runner** **without reading the implementation and without a key/network/browser**.

## Interpretation flagged (for the plan gate — OpenCode's actual CLI/config, verify against the pinned OpenCode version)
> OpenCode's CLI/config surface evolves; the developer must **pin the targeted OpenCode CLI version**
> (§11.10 supply-chain) and reconcile these interpretations against it. None of these change the
> unit-testable contract (the seam is a **mock command-runner**), but they pin the *shape* the Tester
> asserts and the live unit-8 must honor.
1. **Headless run form = `opencode run <message>` with `--model` / `--agent`.** Interpreted from
   OpenCode's non-interactive `run` subcommand: model via `-m/--model provider/model`, agent via
   `--agent <name>`, message as positional/stdin. If the installed OpenCode uses a different flag/
   subcommand, the adapter's constructed argv is adjusted — the *assertable facts* (binary, run mode,
   model=`openai/gpt-4o-mini`, planner-before-generator, prompt/fields delivered) stay.
2. **Config discovery mechanism.** Interpreted options, in order of preference: (a) `OPENCODE_CONFIG`
   env var pointing at `connectors/opencode/opencode.json`; (b) a `--config <path>` flag if supported;
   (c) placing/copying `opencode.json` into the run workspace cwd (OpenCode auto-loads project config).
   The developer picks the mechanism the pinned OpenCode version supports; the connector config path is
   pinned regardless.
3. **MCP key + local-server shape.** Interpreted as OpenCode's top-level `mcp` key with a `type:"local"`
   + `command:[...]` (+ `enabled:true`) entry (vs. unit-3's Claude-native `mcpServers`/`command`+`args`).
   The **server identity/version must match** `@playwright/mcp@0.0.41`; the exact JSON keys are
   reconciled to the pinned OpenCode config schema.
4. **System-prompt / instructions delivery.** Interpreted as OpenCode `instructions` (file reference)
   and/or the agent `prompt` field / `AGENTS.md`, carrying `invocation.system_prompt` (BRD already
   injected). The developer picks the mechanism the pinned version honors; the fact that the BRD-injected
   prompt + reliability rules govern the run is the contract.
5. **Planner→Generator orchestration.** Two ordered `opencode run --agent …` calls (planner then
   generator, passing the plan forward) **or** a single primary orchestrator agent referencing both —
   developer's choice; the pinned fact is planner-before-generator with both roles present.
6. **Workspace vs. `output_dir`.** The adapter runs OpenCode in a **separate workspace** and returns the
   captured tests as a mapping; the unit-6 glue remains the single writer of `output_dir`. (Alternative:
   point OpenCode directly at `output_dir` and let the glue re-write identical content — rejected to keep
   a single writer and keep the adapter's tests hermetic in a `tmp_path`.)
7. **OpenCode agent-def location.** Pinned to `.opencode/agent/qa-planner.md` + `.opencode/agent/
   qa-generator.md` (OpenCode's project-agent convention), mirroring `.claude/agents/*`. Inline `agent`
   entries in `opencode.json` are an accepted alternative if the two named roles + shared-prompt
   reference are preserved.
</content>

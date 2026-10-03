# Task: `p1-agent-run-glue` — Agent-run glue (per-run authoring invocation, mock-verified)

## Title
The **agent-run glue** for Phase 1: Python (`uv`) code that **assembles a single per-run authoring
invocation** from the already-built Phase 1 pieces and drives it through an **injectable agent
runner**, writing the generated test artifacts to a **pinned output path** and returning a structured
run result. It **composes** — it does not re-implement — unit 1 (spec loader), unit 2 (target config),
unit 3 (MCP config), unit 4 (QA system prompt), and unit 5 (Planner/Generator sub-agents). It is
**unit-tested with a MOCK agent runner** substituted for the real Claude Code call, so the entire
assembly/wiring/output contract is verified **without a model key, without any network, without a
browser, and without launching the real Claude Code or Playwright MCP.** The real (live) run is unit 7.

## Context (plan item)
- **AGILE_PLAN.md → Phase 1 → D6** ("Agent-run glue — unit 6 (`p1-agent-run-glue`)"): "The glue that
  **assembles a per-run authoring invocation** from the above: reads a target config (D2) + loads its
  spec (D1), injects the BRD into the generic prompt (D4), and composes the headless-agent invocation
  pointed at the MCP config (D3) + Planner/Generator (D5), writing the generated test artifacts to a
  pinned output location. **Unit-tested with a MOCK agent** substituted for the real Claude Code call…
  Acceptance = deterministic prompt/config bundle from fixtures + correct artifact placement under the
  mock. No model key." Also the Phase 1 unit table, unit 6, and the Phase 1 acceptance clause "Units
  1–6 (all key-free) merged and green."
- **Backlog unit 6** (`p1-agent-run-glue`, status `spec-ready (active)`).
- **DESIGN.md §4** — the canonical product pipeline **BRD/prompt → Planner → Generator → Execution →
  Healer → Reports → PR**. This unit wires the **Planner → Generator** authoring portion of that
  pipeline for a single run; Execution/Healer/Verifier/Reports/PR are later phases.
- **DESIGN.md §5.1 (Reliability layer → Grounding)** — selectors come from the live DOM snapshot via
  Playwright MCP and API assertions are grounded in the OpenAPI schema. This unit's job is to *hand
  the runner the grounding inputs* (the MCP config + the normalized API surface + the reliability-
  bearing system prompt + the Planner/Generator agents); it does not itself snapshot the DOM or run
  the browser (that is the runner's/live job, unit 7).
- **DESIGN.md §6** — one generic system prompt with a per-run **BRD** injected + the seven structured
  Planner fields. This unit performs the **BRD injection** into the unit-4 prompt and carries the
  unit-2 planner fields into the invocation.
- **DESIGN.md §11.4** — the Basic-Auth credential is a **reference** injected at runtime, "never in
  prompts, logs, traces, or artifacts." This unit passes only the credential **reference name**; it
  does not resolve, embed, log, or persist any secret value.
- **DESIGN.md §12** — control-plane glue/orchestration is **Python (`uv`)**; test artifacts stay
  TypeScript Playwright. This glue is Python tooling that *produces/handles* TS Playwright artifacts;
  it is not itself a test artifact.
- **DESIGN.md §13 — repo layout** — the home-directory choice is pinned in Interfaces §Paths below;
  see **Interpretation flagged** for the reasoning and the flag for human review at the plan gate.

**Given app state (contracts this unit composes — do NOT re-derive, duplicate, or modify):**
- **Unit 1 — spec loader** at import path `connectors.spec_loader`: `load_spec(source, source_type="auto")
  -> ApiSurface`; `ApiSurface` has `.to_dict()` (deterministic, operations sorted by `(path, method)`);
  named errors `SpecLoadError`, `UnsupportedSourceError` (subclass of `SpecLoadError`). Merged `97f9b53`.
- **Unit 2 — target config** at import path `connectors.target_config`:
  `load_target_config(source, source_type="auto") -> TargetConfig`; `TargetConfig` (frozen dataclass)
  fields `target_url`, `api_spec_source`, `brd_path`, `basic_auth_credential_ref`,
  `planner_fields` (the seven pinned fields incl. `depth`); methods `TargetConfig.load_api_spec()`
  (delegates to `spec_loader.load_spec(self.api_spec_source)` → `ApiSurface`),
  `TargetConfig.resolve_credential()` (reads the env var named by `basic_auth_credential_ref` at call
  time, returns the value to the caller, never stores it, raises `CredentialUnsetError` if unset),
  `TargetConfig.to_dict()` / secret-free `__repr__`; named errors `TargetConfigError`,
  `CredentialUnsetError`. Reference example config committed at
  `connectors/examples/reference_app.target.json` (`target_url` `http://127.0.0.1:5173`,
  `api_spec_source` `http://127.0.0.1:8000/openapi.json`, `brd_path` `reference_app/BRD.md`,
  `basic_auth_credential_ref` `REF_APP_BASIC_AUTH`, all seven planner fields populated,
  `depth` = `regression`). Merged `151af60`.
- **Unit 3 — Playwright-MCP config** at `connectors/mcp/playwright.mcp.json` (an `mcpServers` object;
  server `playwright` pinned to `@playwright/mcp@0.0.41`, headless chromium). Merged `8f0ac6a`.
- **Unit 4 — QA system prompt** at `agent_config/qa_system_prompt.md`: the single generic prompt with
  the BRD-injection placeholder token **`{{BRD}}`** appearing **exactly once** (in the final
  "Business requirements (BRD) — per-run context" section). Merged `22c9954`.
- **Unit 5 — Planner/Generator product sub-agents**: `qa-planner` at `.claude/agents/qa-planner.md`
  and `qa-generator` at `.claude/agents/qa-generator.md` (valid sub-agent frontmatter; each bound to
  the QA system prompt + MCP config; carry `PRODUCT_AGENT` markers). Documented in
  `agent_config/product_agents.md`. Merged `f7bee09`.
- **`reference_app/BRD.md`** exists (the freeform BRD the example config points at).
- Root project uses `uv` (`pyproject.toml`); suites run via `uv run pytest <dir> -q`.

## Scope

### In scope
1. **A Python agent-run-glue module** at the pinned home (Interfaces §Paths) exposing a documented,
   stable public API (Interfaces §Public API): a single **entry point** that, given a target-config
   source and an **injectable agent runner**, assembles the invocation, drives the runner, writes
   generated tests to the output path, and returns a structured **run result**.
2. **Config load (compose unit 2).** Load the per-run target config from the given source via
   `connectors.target_config.load_target_config(...)`. Do not re-parse or re-validate config fields
   here — reuse unit 2; its `TargetConfigError` propagates on invalid/missing config.
3. **API-surface load (compose units 1+2).** Obtain the normalized API surface for the config's
   `api_spec_source` via the config's `TargetConfig.load_api_spec()` (which delegates to unit 1's
   `load_spec`). Do not re-implement spec parsing; unit 1's `SpecLoadError` / `UnsupportedSourceError`
   propagate unchanged.
4. **BRD injection (compose unit 4).** Read the unit-4 QA system prompt at
   `agent_config/qa_system_prompt.md`, read the BRD file at the config's `brd_path`, and produce the
   **final system prompt** by replacing the **`{{BRD}}`** token with the BRD file's contents. The
   token must be replaced **exactly once**; the final prompt must contain the BRD text and must
   contain **no** residual `{{BRD}}` token. The rest of the prompt is carried through unchanged.
5. **Reference the MCP config + sub-agents (compose units 3+5).** The assembled invocation must
   reference/point at the Playwright-MCP config path `connectors/mcp/playwright.mcp.json` and the two
   product sub-agents by their pinned identities — Planner `qa-planner` (`.claude/agents/qa-planner.md`)
   and Generator `qa-generator` (`.claude/agents/qa-generator.md`). These are passed to the runner via
   the invocation bundle; the glue does not redefine them.
6. **Injectable agent-runner seam (the crux).** Define a single **injectable runner interface**
   (Interfaces §Runner seam) — a callable/object the *real* Claude Code + Playwright-MCP + Planner→
   Generator run will implement in unit 7, but which the unit-6 tests substitute with a **mock** that
   returns canned generated-test content. The glue **must not hard-code a live Claude Code / MCP /
   browser call**; it invokes only the injected runner. The entry point accepts the runner as a
   parameter (dependency injection), with **no live default that would require a key/network** at
   unit-test time (a live default, if provided, must not be exercised by any unit-6 test).
7. **Write generated tests to a pinned output path (Interfaces §Paths/§Output).** Take the generated
   test artifacts returned by the runner (a mapping of relative filename → file content) and write
   each to the resolved output directory (the caller-supplied `output_dir`, else the pinned default),
   creating the directory if needed. Return the list of written paths in the run result.
8. **Structured run result (Interfaces §RunResult).** Return an object capturing **what was
   assembled** (the loaded config, the final BRD-injected system prompt, the loaded API surface, the
   referenced MCP config path, the two sub-agent identities, the credential **reference name** only),
   **where tests were written** (the output dir + the list of written test paths), and **the runner's
   status** (surfaced, not swallowed).
9. **Error behavior (Interfaces §Errors).** Missing/invalid config → unit-2 `TargetConfigError`
   propagates; unloadable/malformed spec → unit-1 `SpecLoadError`/`UnsupportedSourceError` propagates
   unchanged; a **missing/unreadable BRD file** → a **named glue error** naming the BRD path; a prompt
   whose `{{BRD}}` token count is not exactly one → a **named glue error**; a **runner failure**
   (runner raises, or returns an error status) is **surfaced** — never silently swallowed and never
   reported as a successful write.
10. **Secret-safety (compose unit 2's guarantee; §11.4).** The glue passes only the credential
    **reference name** into the invocation/run result; it does **not** resolve the secret by default,
    and if resolution is ever needed it uses only `TargetConfig.resolve_credential()` and never stores
    or logs the value. No secret value ever appears in the assembled prompt, the invocation, the run
    result, the written artifacts, or any log/print output.
11. **A pytest test suite** at the pinned test dir (Interfaces §Paths) proving every acceptance
    criterion using a **mock runner** + fixtures + `tmp_path` output dirs, runnable via
    `uv run pytest <glue-test-dir> -q`. No model key, no network, no browser.
12. **Docs**: a short `README.md` (or documented module docstring) at the glue's home documenting the
    public import path, the entry-point signature, the runner-seam interface, the `RunResult` shape,
    the pinned default output path, and the named errors.

### Out of scope (defer)
- **The REAL agent run** — headless Claude Code + Playwright MCP + Planner→Generator against the live
  reference app; producing *real* generated tests; committing them — is **unit 7** (`p1-agent-authoring-gate`,
  needs a model key).
- **Any live browser / MCP server launch, any network egress, any Claude Code invocation** at
  unit-test time. The seam is mock-only here.
- **Eval scoring** (`eval/score.py`, naive-baseline comparison) — unit 7.
- **Verifier / Healer / assertion-audit / API cross-check / self-heal / deterministic replay** —
  Phase 2.
- **Re-implementing** spec parsing (unit 1), config validation (unit 2), the MCP config (unit 3), the
  prompt content (unit 4), or the sub-agent definitions (unit 5). This unit only **composes** them.
- **Real secret vaulting / rotation / injection plumbing** — only unit 2's reference + at-call-time
  resolution mechanism is reused.
- **Any change** to `reference_app/**`, to units 1–5 public artifacts/APIs, or to protected files
  (`DESIGN.md`, `META_PLAN.md`, `AGILE_PLAN.md`, `CLAUDE.md`, `.harness/**`, `.claude/agents/**`,
  `agent_config/**`, `connectors/**`). This unit **adds** a new module + tests + a README at its home.

## Acceptance criteria (enumerated, testable — all verifiable with the mock runner, no key/network/browser)

### Assembly — config, spec, prompt
1. **Loads the target config via unit 2.** Given a valid config source (mapping or file path), the
   entry point loads it through `connectors.target_config.load_target_config` and the run result
   reflects that config's fields (e.g. `target_url`, the seven planner fields, `basic_auth_credential_ref`).
2. **Loads the API surface via units 1+2.** The glue obtains the normalized API surface for the
   config's `api_spec_source` through the config's `load_api_spec()` hand-off, and the run result
   carries that surface (its `.to_dict()` form). The Tester may monkeypatch
   `connectors.spec_loader.load_spec` / `TargetConfig.load_api_spec` (or use an in-memory mapping
   `api_spec_source`) so **no network** is required.
3. **Reads and injects the BRD (exactly once).** The final system prompt is the unit-4 prompt with the
   single `{{BRD}}` token replaced by the contents of the file at the config's `brd_path`. Assertable:
   (a) the final prompt **contains** the BRD file's text; (b) the final prompt contains **no**
   `{{BRD}}` substring; (c) the replacement happened exactly once (a BRD body containing the literal
   `{{BRD}}` is not double-substituted — only the original single placeholder is replaced); (d) the
   non-BRD portions of the prompt are preserved (e.g. a stable marker such as the version comment or a
   reliability-rule heading still present).
4. **Deterministic assembly.** Running the entry point twice with the same inputs and an equivalent
   mock runner yields byte-identical assembled artifacts (final prompt + the API surface `to_dict()`
   + the invocation bundle's referenced paths/identities). No non-deterministic content.

### Referencing MCP config + sub-agents
5. **MCP config referenced.** The assembled invocation (and/or the run result) references the pinned
   Playwright-MCP config path `connectors/mcp/playwright.mcp.json`, and that path is passed to the
   runner. (Presence/shape of the path; the glue need not launch the server.)
6. **Planner & Generator referenced.** The assembled invocation references both product sub-agents by
   their pinned identities — `qa-planner` (`.claude/agents/qa-planner.md`) and `qa-generator`
   (`.claude/agents/qa-generator.md`) — and passes them to the runner (so the runner would drive
   Planner→Generator). The two identities are distinct and both present.

### Runner seam (mock-substitutable) + output writing
7. **Runner is invoked with the assembled invocation.** The injected runner receives an invocation
   bundle (Interfaces §Runner seam) carrying at least: the final BRD-injected system prompt, the API
   surface, the target URL, the seven planner fields, the MCP config path, the two sub-agent
   identities, the credential **reference name**, and the resolved output dir. A mock runner can
   assert it received these fields with the expected values.
8. **No hard-coded live call.** With **no** runner-related env var / key set and **no** network
   available, every unit-6 test still passes because the glue calls only the **injected** runner. No
   test triggers a real Claude Code / MCP / browser / HTTP call. (A live default runner, if the module
   ships one, is never exercised by these tests.)
9. **Generated tests written to the pinned output path.** Given a mock runner returning a mapping of
   relative filename → content (e.g. `{"cart.spec.ts": "...", "orders.api.spec.ts": "..."}`), the glue
   writes each file, with the given content, under the resolved output directory (the caller-supplied
   `output_dir`; the Tester uses a `tmp_path`). Files exist on disk with byte-exact content.
10. **Default output path pinned.** When no `output_dir` is supplied, the glue resolves to the pinned
    default (Interfaces §Paths); the run result reports that resolved directory. (The Tester may assert
    the documented default value and/or exercise it against a redirected/temp base — no requirement to
    pollute the real default in the test run.)
11. **RunResult correct.** The returned run result (Interfaces §RunResult) exposes, under pinned
    names: the loaded config (or its `to_dict`), the final system prompt, the API surface (`to_dict`),
    the referenced MCP config path, the Planner and Generator identities, the resolved output dir, the
    list of written test paths, and the runner status. All values match the inputs/mock.

### Error behavior (surfaced, never swallowed)
12. **Invalid/missing config → unit-2 error.** A config missing a required field (or otherwise
    invalid) raises `connectors.target_config.TargetConfigError` (propagated, not swallowed, not
    rewrapped into a glue error); no runner is invoked and no files are written.
13. **Spec load failure → unit-1 error unchanged.** If the API-surface load raises `SpecLoadError` /
    `UnsupportedSourceError`, it propagates unchanged; no runner is invoked and no files are written.
14. **Missing/unreadable BRD → named glue error.** If the file at `brd_path` cannot be read, a
    **named glue error** (Interfaces §Errors) is raised, its message naming the BRD path; no runner is
    invoked and no files are written.
15. **Bad prompt placeholder → named glue error.** If the QA system prompt does not contain **exactly
    one** `{{BRD}}` token (zero or more than one), a **named glue error** is raised; no runner is
    invoked and no files are written.
16. **Runner failure surfaced.** If the injected runner raises, the exception is **not swallowed** (it
    propagates, or is re-raised with added context — never suppressed); if the runner instead returns
    an **error status**, the run result reflects that error status and the glue does **not** falsely
    report a successful write. Either way a mock runner that fails is observably surfaced to the
    caller.

### Secret-safety (§11.4)
17. **Only the credential reference name flows through.** With a **sentinel secret** placed in the
    environment under the config's `basic_auth_credential_ref` name, the sentinel value appears in
    **none** of: the assembled final prompt, the invocation bundle handed to the runner, the run
    result (`repr`/serialization), the written test artifacts, or any log/print output — while the
    credential **reference name** may appear. The glue does **not** call `resolve_credential()` by
    default; if it ever resolves the secret it uses only that unit-2 method and never stores/logs it.

### Placement, tests, no-regression
18. **Correct home + runnable tests.** New code lives at the pinned home (Interfaces §Paths) with the
    pinned public import path; tests live at the pinned test dir and pass via `uv run pytest
    <glue-test-dir> -q`. All of units 1–5's existing tests still pass unchanged.
19. **No regressions / no side effects beyond the output dir.** No change to `reference_app/**`, to
    units 1–5 public APIs/artifacts, or to any protected file; Phase 0 `make test` / `make eval` /
    backend pytest still pass. The glue performs **no network egress** and **no writes** other than the
    generated-test files under the resolved output directory, and **never** logs/persists any
    credential value.

## Interfaces / contracts (pin these precisely)

### Paths (binding)
- **Module home:** `runner/` (new package; reuse/create `runner/__init__.py`). Rationale + flag: see
  **Interpretation flagged** below.
- **Public import path (binding):** `runner.authoring`. The public entry point, runner-seam type,
  invocation type, `RunResult`, named errors, and the default output path constant are importable from
  `runner.authoring`. (Exact internal file layout is the developer's choice, but this public import
  path must be documented and kept stable.)
- **Tests:** `runner/tests/` (pytest), runnable as `uv run pytest runner/tests -q`.
- **Pinned default output directory (binding):** `runner/generated/` — the directory generated test
  files are written to when the caller supplies no `output_dir`. Exposed as a documented module-level
  constant (name the developer's choice, e.g. `DEFAULT_OUTPUT_DIR`) so tests can assert it.
- **Docs:** a `runner/README.md` (or a documented module docstring) covering the public contract.
- **Referenced (read-only) artifact paths the glue points at:** QA system prompt
  `agent_config/qa_system_prompt.md`; MCP config `connectors/mcp/playwright.mcp.json`; Planner
  `.claude/agents/qa-planner.md` (`name: qa-planner`); Generator `.claude/agents/qa-generator.md`
  (`name: qa-generator`). BRD token: **`{{BRD}}`**.

### Public API (signatures — names below are binding; internal structure the developer's choice)
- **Entry point:**
  `run_authoring(config_source, *, agent_runner, output_dir=None, source_type="auto") -> RunResult`
  - `config_source`: a mapping or a file path — forwarded to `load_target_config(config_source, source_type)`.
  - `agent_runner`: the injected runner (Interfaces §Runner seam). **Required** (keyword) — no live
    default is exercised by unit-6 tests.
  - `output_dir`: optional output directory for generated tests; defaults to `DEFAULT_OUTPUT_DIR`
    (`runner/generated/`).
  - `source_type`: forwarded to unit-2's loader (`"auto"` default).
  - Returns a `RunResult`; raises the named errors below on the failure paths.

### Runner seam (the injectable interface — binding shape; concrete type the developer's choice, documented)
- A single **runner** interface the entry point invokes exactly once with the assembled **invocation
  bundle**, returning a **runner output**. It may be expressed as a callable
  `AgentRunner(invocation) -> AgentRunOutput` (a `typing.Protocol`, a callable, or a small ABC — the
  developer's choice, but documented and stable so unit 7's real runner and unit 6's mock both satisfy
  it).
- **Invocation bundle** (fields the glue must populate and hand to the runner; pinned names):
  `system_prompt` (str — final, BRD-injected), `api_surface` (the unit-1 `ApiSurface` or its
  `to_dict()`), `target_url` (str), `planner_fields` (mapping of the seven fields),
  `mcp_config_path` (str = `connectors/mcp/playwright.mcp.json`), `planner_agent` (identity/path for
  `qa-planner`), `generator_agent` (identity/path for `qa-generator`),
  `basic_auth_credential_ref` (str — the **reference name** only), `output_dir` (str — resolved).
- **Runner output** (what the runner returns; pinned names): `status` (str — e.g. `"ok"` on success,
  or an error status), `generated_tests` (mapping of **relative filename → file content string**), and
  an optional `detail`/`message`. The glue writes `generated_tests` to `output_dir` and reflects
  `status` in the `RunResult`.

### RunResult (returned object — pinned attribute names; concrete type the developer's choice, documented)
- `config` — the loaded `TargetConfig` (or its `to_dict()`), i.e. what was assembled.
- `system_prompt` — the final BRD-injected system prompt (str).
- `api_surface` — the loaded API surface as `to_dict()`.
- `mcp_config_path` — the referenced MCP config path (str).
- `planner_agent`, `generator_agent` — the two referenced sub-agent identities.
- `output_dir` — the resolved output directory (str).
- `written_test_paths` — list of paths (str) actually written.
- `runner_status` — the runner's returned `status`, surfaced (not swallowed).
- Its `repr()`/serialization must be **secret-free** (criterion 17): no resolved credential value.

### Errors (named, documented)
- A module-level **glue error base** (e.g. `AuthoringError`-style class; exact name the developer's
  choice, documented) with the failure cases: **BRD unreadable/missing** (criterion 14; message names
  the BRD path) and **bad `{{BRD}}` placeholder count** (criterion 15). Distinct, named subclasses are
  allowed but not required.
- **Propagated unchanged (not rewrapped):** `connectors.target_config.TargetConfigError` (invalid/
  missing config, criterion 12), `connectors.spec_loader.SpecLoadError` /
  `UnsupportedSourceError` (spec failure, criterion 13). A **runner** exception propagates or is
  re-raised with context — never suppressed (criterion 16).
- **Not resolved here:** `CredentialUnsetError` is unit 2's; the glue does not resolve the credential
  by default, so it neither raises nor depends on this at unit-test time.

### Secret-safety (binding rule, per `DESIGN.md §11.4`)
- The glue passes only the credential **reference name**; a resolved secret value is **never** placed
  in the prompt, the invocation, the `RunResult`, the written artifacts, or any log. The Tester proves
  this by putting a sentinel secret in the environment under the referenced name and asserting the
  sentinel appears in **none** of those surfaces.

### Fixtures (guidance for the Tester — not implementation)
- **Mock runner:** a test-local callable/object satisfying the runner seam that records the invocation
  it received and returns a canned `generated_tests` mapping + a `status`; variants that (a) succeed,
  (b) raise, and (c) return an error status drive criteria 7–11 and 16.
- **Config:** the shipped `connectors/examples/reference_app.target.json` and/or small hand-crafted
  config mappings (valid + invalid variants) drive criteria 1, 12.
- **Spec:** monkeypatch `connectors.spec_loader.load_spec` (or `TargetConfig.load_api_spec`) or use an
  in-memory dict `api_spec_source` so no network is needed (criteria 2, 13).
- **Prompt/BRD:** the real `agent_config/qa_system_prompt.md` (single `{{BRD}}` token) plus a
  temp/fixture BRD file drive criteria 3, 14; a temp prompt with zero/two tokens drives criterion 15.
- **Output:** `tmp_path` output dirs drive criteria 9–11; the pinned default is asserted as a constant
  (criterion 10).
- **Secret:** an env-var sentinel under the config's `basic_auth_credential_ref` drives criterion 17.

## Definition of Done
- All acceptance criteria **1–19** pass.
- The glue module exists at the pinned home `runner/` with the public import path `runner.authoring`
  exposing: `run_authoring(config_source, *, agent_runner, output_dir=None, source_type="auto") ->
  RunResult`, the runner-seam interface + invocation bundle + runner-output shape, the `RunResult`
  type with the pinned attribute names, the pinned `DEFAULT_OUTPUT_DIR` = `runner/generated/`, and the
  named glue error(s) — all documented in `runner/README.md` (or module docstring).
- `uv run pytest runner/tests -q` is green from a clean checkout under `uv`, with **no** model key,
  **no** network, and **no** browser, using a mock runner. Units 1–5's existing tests still pass.
- No protected file changed (`DESIGN.md`, `META_PLAN.md`, `AGILE_PLAN.md`, `CLAUDE.md`, `.harness/**`);
  no change to `reference_app/**` behavior, to units 1–5 public APIs/artifacts, or to
  `connectors/**` / `agent_config/**` / `.claude/agents/**`. Phase 0 `make test` / `make eval` /
  backend pytest still pass. Consistent with `DESIGN.md §4/§5.1/§6/§11.4/§12/§13` and `AGILE_PLAN.md` D6.
- **Tester-can-author-from-this-alone:** from this spec alone — the pinned import path + entry-point
  signature, the runner-seam interface (invocation bundle + runner-output shape) that a mock
  substitutes, the `RunResult` attribute names, the pinned default output path, the BRD-injection
  contract (token `{{BRD}}`, replaced exactly once, no residue), the composed unit-1/2 error
  propagation + named glue errors, and the secret-safety env-var-sentinel proof — the Tester can
  author the failing verification tests with a mock runner **without reading the implementation**.

## Interpretation flagged (for the plan gate)
- **Module home choice — `runner/` (chosen) vs `agent_config/`.** `DESIGN.md §13` lists
  `runner/  # execution + reporting + failure triage` and `agent_config/  # generic QA system prompt,
  .claude/agents/ sub-agents, hooks, reliability skill pack (portable across CLIs)`. This unit is
  **run-invocation/orchestration code** (it *assembles and drives* a per-run authoring invocation and
  writes run outputs), which matches `runner/` ("execution … + reporting") far better than
  `agent_config/` (portable *config/prompt/agent* artifacts, not Python glue). I have therefore pinned
  the home to `runner/` with public import path `runner.authoring` and default output
  `runner/generated/`. This is consistent with — not a deviation from — `META_PLAN`/`DESIGN`; it is a
  placement choice within the existing §13 layout, flagged here for explicit human confirmation at the
  plan gate. No conflict with `META_PLAN.md`/`DESIGN.md` was found (so no top-of-`AGILE_PLAN.md`
  conflict entry was needed); the active Phase 1 plan in `AGILE_PLAN.md` remains as previously locked.

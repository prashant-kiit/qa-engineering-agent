# `runner/` — authoring glue + agent-runner adapters (Phase 1)

This package assembles a single per-run **authoring invocation** from the already-built
Phase 1 pieces (target config, API spec, QA system prompt + BRD injection, MCP config,
product sub-agents) and drives it through an **injectable agent runner**.

## Public contract

```python
from runner.authoring import run_authoring

run_authoring(
    config_source,
    *,
    agent_runner,
    output_dir=None,
    source_type="auto",
    expose_credential_for_exploration: bool = False,
) -> RunResult
```

* `config_source` / `source_type` — forwarded to `connectors.target_config.load_target_config`.
* `agent_runner` — required, keyword-only: a callable `agent_runner(invocation) ->
  AgentRunOutput`. `runner.opencode_runner.OpenCodeRunner` is the concrete (unit-7)
  implementation of this seam.
* `output_dir` — where generated tests are written; defaults to
  `runner.authoring.DEFAULT_OUTPUT_DIR`.
* `expose_credential_for_exploration` — see **Credential-exposure opt-in**, below.

`run_authoring` assembles an `AuthoringInvocation` (a frozen dataclass) and hands it to
`agent_runner`. `RunResult`, the return value, is a **secret-free**, structured summary of
the run (config, prompts, paths, written test paths, runner status) — it never carries a
resolved credential value.

## Credential-exposure opt-in (`expose_credential_for_exploration`)

### Default behavior (unchanged, 100% of call sites today)

By default (`expose_credential_for_exploration=False`, or simply omitted),
`AuthoringInvocation` carries only the target app's Basic-Auth credential **reference
name** (`basic_auth_credential_ref`, e.g. an env-var name) — **never** a resolved secret
value. `OpenCodeRunner._compose_message` composes the model-visible message accordingly:
it names the reference (e.g. `"Basic-Auth is provided at runtime via the credential
reference 'REF_APP_BASIC_AUTH' (reference name only)."`) and nothing more. This is the
correct, general-purpose behavior per `DESIGN.md §11` items 4–5: target-app Basic-Auth
secrets are injected at **runtime**, egress-scoped, **never in prompts, logs, traces, or
artifacts**, and this default holds for every future login-gated **customer** app
(Phase 5+) whose credential is a real, private, rotatable secret.

### The opt-in

`AuthoringInvocation` also carries an additional, optional field:

```python
basic_auth_credential_value: Optional[str] = None
```

When `run_authoring(..., expose_credential_for_exploration=True)` is called,
`run_authoring` calls the config's existing, unmodified
`TargetConfig.resolve_credential()` (unit 2 — no new resolution logic is introduced) and
places the resolved value onto this field. `CredentialUnsetError` still propagates,
unchanged, if the referenced env var is unset. The resolved value flows **only** into the
`AuthoringInvocation` handed to `agent_runner` — it is **never** threaded into the
returned `RunResult`, never logged, never persisted.

`OpenCodeRunner._compose_message` branches on this field:

* `basic_auth_credential_value is None` (default) — the composed message is
  byte-identical to the reference-only default described above.
* `basic_auth_credential_value` set (a non-`None` string; only reachable via the explicit
  opt-in) — the composed message **additionally** includes that resolved value, in a form
  the exploring agent can act on to actually submit it through a login form, for **both**
  the Planner and Generator roles. The existing reference-name sentence is **retained**,
  not replaced — the value is a supplement, not a substitute.

### Why this exists

While attempting a live OpenCode + `gpt-4o-mini` authoring run, the reference app's login
was found to be a **real in-app form**
(`reference_app/frontend/src/views/LoginView.tsx`): credentials live only in local React
`useState`, are sent as an HTTP Basic-Auth header on submit, and are **never persisted**
to a cookie, `localStorage`, or session. There is therefore no way to pre-authenticate the
exploring agent's browser session ahead of a run — the agent must actually submit real
credentials through the form to get past login and explore the authenticated parts of the
app (cart, checkout, orders).

### Why THIS value is exempt from the general secret-safety rule

The reference app's fixed dev/test account, **`testuser` / `testpass`**, is not a secret
in any meaningful sense for this build: it is already committed in **plaintext**,
publicly, across multiple Phase-0 artifacts — `reference_app/e2e/tests/smoke.spec.ts`,
`reference_app/e2e/tests/eval/helpers.ts`, `eval/tests/test_eval_harness_verification.py`
— and documented as the authentication mechanism in `reference_app/BRD.md`. It cannot be
exfiltrated in any sense that matters (it is already public), it is not rotated, and it
gates nothing but a local, disposable, non-production reference app. Letting the exploring
agent read this one already-public value in order to submit it through a real login form
carries none of the risk `DESIGN.md §11` items 4–5 exist to prevent.

### Why the exemption does NOT generalize

Every future login-gated **customer** app (starting Phase 5, real multi-tenant tenants)
has a real, private, rotatable Basic-Auth credential. The reference-only default holds
**unconditionally** there. This opt-in is therefore (a) off by default, (b) restricted by
**documented usage constraint, not code**, to the reference app's known-public fixture
account, and (c) does not touch, weaken, or bypass `connectors.target_config`'s existing
`CredentialUnsetError` / env-var-reference resolution mechanism — it only decides, per
call, whether the already-designed `resolve_credential()` result is additionally placed on
the invocation.

**Documented (non-code-enforced) usage constraint:** the unit-8 live-gate script
(`runner/authoring_gate.py`) is the **only** caller permitted to pass
`expose_credential_for_exploration=True`, and only for the reference app's published
fixture account (`testuser` / `testpass`). Nothing in this package code-enforces caller
identity or which credential values may flow through the flag — that would be brittle and
was explicitly deferred (see `AGILE_PLAN.md` → Phase 1 → Conflicts / deviations,
2026-09-29 entry, and `.harness/tasks/p1-agent-authoring-gate-credential-exception.md`).
A durable named-reference secrets-passthrough mechanism (so the model never sees a raw
value, for this and future customer apps) is a real Phase 2+ backlog candidate, not built
by this opt-in.

## `OpenCodeRunner` (unit 7)

`runner.opencode_runner.OpenCodeRunner` is a concrete `AgentRunner` that drives the
open-source OpenCode CLI (model `openai/gpt-4o-mini` by default) through an injected
command-runner seam. It reads the platform model credential (`OPENAI_API_KEY`) into the
child process environment only — never into argv, prompt, logs, or output — independently
of, and unaffected by, the target-app credential-exposure opt-in described above.

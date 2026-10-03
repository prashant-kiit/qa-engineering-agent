# Task: `p1-agent-authoring-gate-credential-exception` — Scoped, opt-in credential-exposure carve-out for the live authoring gate

## Title
A narrow, **opt-in, default-off** amendment to the already-`done` unit-6 authoring glue
(`runner/authoring.py`) and unit-7 OpenCode adapter (`runner/opencode_runner.py`) that lets the unit-8
live-gate script deliver the reference app's **published, non-secret** Basic-Auth credential **value**
(not just its reference name) to the exploring agent — and *only* when explicitly asked to — so the
agent can pass the reference app's real in-app login form. Every existing behavior, including the
reference-only default that unit 7's reviewed test `test_c13_target_auth_stays_reference_only` pins, must
remain **exactly as it is today** unless the new opt-in is explicitly exercised.

## Context (which plan item)

- **`AGILE_PLAN.md` → Phase 1 → Conflicts / deviations (2026-09-29 entry)** and **→ D7.5** — this unit
  implements the human-authorized carve-out. **`.harness/backlog.md` → unit 7.5.**
- **The finding.** While attempting the live unit-8 OpenCode + `gpt-4o-mini` authoring run, the reference
  app's login was found to be a **real in-app form**: `reference_app/frontend/src/views/LoginView.tsx`
  holds `username`/`password` only in local React `useState`, sends them as an HTTP Basic-Auth header on
  submit (`fetch(apiUrl("/cart"), { headers: authHeaders(creds) })`), and **never persists** them to a
  cookie, `localStorage`, or session (verified by reading the file — confirmed lines 14–40). There is
  therefore **no way to pre-authenticate** the exploring agent's browser session ahead of the run; the
  agent must actually submit real credentials through the form to get past login and explore the
  authenticated parts of the app (cart, checkout, orders).
- **Why this conflicts with the current default (and why that default is right).** Unit-6's
  `run_authoring` assembles `AuthoringInvocation` carrying **only**
  `basic_auth_credential_ref` — the credential's **reference name** (e.g. an env-var name) — never a
  resolved value (`runner/authoring.py`, `AuthoringInvocation` docstring: "Carries only the credential
  **reference name** (never a resolved secret value)"). Unit-7's `OpenCodeRunner._compose_message`
  composes the model-visible message from the invocation and, today, only ever writes the reference name
  into a fixed sentence ("Basic-Auth is provided at runtime via the credential reference `<ref>`
  (reference name only)."). This is **not an oversight** — it is deliberately pinned by unit-7's
  Reviewer-approved test `test_c13_target_auth_stays_reference_only`
  (`runner/tests/test_opencode_runner.py`), and it is the **correct** behavior per
  `DESIGN.md §11` items 4–5: target-app Basic-Auth secrets are injected at **runtime**, egress-scoped,
  **never in prompts, logs, traces, or artifacts** (item 4), and model/CLI credentials are
  platform-owned and never exposed to the agent's readable context (item 5). This default **must stay
  correct** for every real target-app credential from Phase 5+ (multi-tenant customer apps) onward —
  those are private, rotatable secrets, and a model that can read them in its own prompt is exactly the
  exfiltration/confidentiality risk `§11` exists to prevent.
- **Why THIS specific value is exempt from that concern.** The reference app's fixed dev/test account,
  **`testuser` / `testpass`**, is not a secret in any meaningful sense for this build: it is already
  committed in **plaintext**, publicly, across multiple Phase-0 artifacts that predate this unit —
  `reference_app/e2e/tests/smoke.spec.ts` (`USERNAME = 'testuser'`, `PASSWORD = 'testpass'`),
  `reference_app/e2e/tests/eval/helpers.ts` (same), and
  `eval/tests/test_eval_harness_verification.py` (`VALID_AUTH = ("testuser", "testpass")`) — and it is
  documented as *the* authentication mechanism in `reference_app/BRD.md`'s Authentication section, with
  the concrete values pinned in `.harness/tasks/p0-shop-backend.md` (`username: testuser`,
  `password: testpass`). It cannot be exfiltrated in any sense that matters (it is already public), it is
  not rotated, and it gates nothing but a local, disposable, non-production reference app. Letting the
  `gpt-4o-mini` exploring agent read this one already-public value in order to submit it through a real
  login form carries **none** of the risk `DESIGN.md §11` items 4–5 are written to prevent.
- **Why the exemption does NOT generalize.** Every future login-gated **customer** app (starting Phase 5,
  real multi-tenant tenants) has a **real, private, rotatable** Basic-Auth credential. The reference-only
  default must hold **unconditionally** there. This unit's opt-in is therefore (a) off by default, (b)
  documented as a usage constraint restricting its caller to the reference app's known-public fixture
  account (see Scope/Out-of-scope below), and (c) does not touch, weaken, or bypass
  `connectors.target_config`'s existing `CredentialUnsetError` / env-var-reference resolution mechanism —
  it only decides, per-call, whether the *already-designed* `resolve_credential()` result is additionally
  placed on the invocation.
- **The human's explicit decision (recorded, not an agent's self-authorization).** The human was asked,
  via this session's `AskUserQuestion` tool, to choose between (a) this scoped opt-in carve-out,
  (b) building the full `@playwright/mcp --secrets`-file passthrough mechanism now (so the model
  references secrets by name and never sees the raw value — for this AND future customer apps), or
  (c) deferring the live gate entirely. **The human chose (a).** Option (b) is **deferred, not
  abandoned** — see `AGILE_PLAN.md` → Conflicts (2026-09-29 entry) and → Verification, which flag it as a
  real **Phase 2+ backlog candidate**: a durable named-reference secrets-passthrough mechanism belongs in
  `connectors/`/`runner/` before Phase 5's real multi-tenant customer credentials are in play, since every
  future login-gated customer app hits this exact problem. This unit does **not** build that mechanism.
- **DESIGN.md §11** (Security model) items 4–5, quoted above — the general secret-safety intent this unit
  narrowly and explicitly carves an exception into, for one non-secret, already-public fixture value,
  under an opt-in flag that defaults to preserving the existing behavior exactly.

**Given app state (contracts this unit amends — read, do not re-derive):**
- `runner/authoring.py` (unit 6, done): `run_authoring(config_source, *, agent_runner, output_dir=None,
  source_type="auto") -> RunResult`; `AuthoringInvocation` is a **frozen** dataclass with fields
  `system_prompt, api_surface, target_url, planner_fields, mcp_config_path, planner_agent,
  generator_agent, basic_auth_credential_ref, output_dir` (see file for full definitions).
- `connectors/target_config.py` (unit 2, done): `TargetConfig.resolve_credential() -> str` reads the env
  var named by `basic_auth_credential_ref` and returns its value; raises `CredentialUnsetError` if unset.
  This unit **reuses this existing method as-is** — it does not add a new resolution mechanism.
- `runner/opencode_runner.py` (unit 7, done): `OpenCodeRunner._compose_message(invocation, role) -> str`
  (a `@staticmethod`) composes the deterministic per-role message; `runner/tests/test_opencode_runner.py`
  has the pinned, Reviewer-approved `test_c13_target_auth_stays_reference_only` (and the parallel
  secret-safety test `test_c11_model_key_injected_into_child_env_only`) which must keep passing
  **unmodified**.
- `runner/tests/opencode_helpers.py`: `make_invocation(output_dir, *, system_prompt=None,
  target_url=None) -> AuthoringInvocation` — the shared test helper; constructs `AuthoringInvocation`
  with **keyword arguments only** (no positional construction anywhere in the current test suite), which
  is why an additional, defaulted, keyword field is a safe, non-breaking addition.
- `.harness/tasks/p1-agent-authoring-gate.md` (unit 8, spec-ready): its own `runner/authoring_gate.py`
  live-gate script is the intended caller of this unit's new opt-in flag; that spec is **not modified** by
  this unit (this unit only prepares the mechanism unit 8 will use).

## Scope

### In scope
1. **A new keyword-only parameter on `run_authoring`**: `expose_credential_for_exploration: bool =
   False`. Default `False` preserves **100%** of existing behavior — every currently-passing unit-6 test
   must keep passing **unmodified**.
2. **When `expose_credential_for_exploration=True`**: `run_authoring` calls the config's existing
   `resolve_credential()` (the unit-2 method — no new resolution logic) and sets the resolved value onto
   a **new, optional** `AuthoringInvocation` field, `basic_auth_credential_value: Optional[str] = None`
   (default `None`). The existing `CredentialUnsetError` behavior for an unset env var is **unchanged** —
   it still propagates, now also from this call site when the flag is `True` and the referenced env var
   is unset.
3. **`RunResult` must never expose `basic_auth_credential_value`** — not in its `__repr__`, not as an
   attribute, not via any serialization. The exposure is scoped **only** to the `AuthoringInvocation`
   object handed to the injected `agent_runner` callable — never to the returned `RunResult`, never to
   logs, never to any persisted artifact.
4. **`OpenCodeRunner._compose_message` gains the opt-in behavior**:
   - When `invocation.basic_auth_credential_value` is `None` (the default, and the value for every
     existing call site/test), the composed message is **byte-identical** to today's output. The existing
     `test_c13_target_auth_stays_reference_only` must pass **unmodified**, proving the default path is
     untouched.
   - When `invocation.basic_auth_credential_value` is set (a non-`None` string; only reachable via the
     new explicit opt-in), the composed message **additionally includes** that resolved value (in a form
     the model can act on to actually submit it through a login form) — this is the deliberate,
     human-approved behavior for that explicit path only.
5. **Secret-safety must hold for every other secret path, unaffected by this change**: the
   `OPENAI_API_KEY` model-credential handling (`_build_env`, `_scrub`, `test_c11_model_key_injected_into_
   child_env_only`, `test_c12_missing_model_credential_raises_named_error`) is untouched and its tests
   must keep passing **unchanged**. Nothing in this unit alters how `OPENAI_API_KEY` is read, injected, or
   scrubbed.
6. **Documented (not code-enforced) usage constraint**: the live-gate script (`runner/authoring_gate.py`,
   unit 8) is the **only** caller permitted to pass `expose_credential_for_exploration=True`, and only for
   the reference app's published fixture account. This is a documented constraint on unit 8's future
   implementation — it is explicitly **out of scope** to code-enforce caller identity or to restrict which
   credential values may be passed (see Out of scope, below).
7. Update `runner/README.md` (or wherever unit 6/7's public contract is documented) to describe the new
   parameter, the new field, and the default-preserving/opt-in behavior, including the same "why THIS
   value is exempt / why it doesn't generalize" framing as this spec and `AGILE_PLAN.md`.

### Out of scope (defer)
- **Building the durable `--secrets`-file (or equivalent named-reference) passthrough mechanism** for
  target-app credentials in general — deferred to Phase 2+ (flagged in `AGILE_PLAN.md` → Conflicts /
  Verification). This unit is the narrow, reference-app-only stopgap, not that mechanism.
- **Code-enforcing which caller may pass `expose_credential_for_exploration=True`** or which credential
  values may flow through it (e.g. restricting it to a literal `testuser`/`testpass` check, or checking
  the caller's module identity). Out of scope — pin this as a documented usage constraint only. Any
  caller *can* pass `True` for any target config; the contract is narrowed by convention/documentation
  (this spec + `AGILE_PLAN.md` + unit 8's spec), not by code, because code-enforcing caller identity is
  brittle and not requested by the human's decision.
- **Changing `connectors.target_config`'s credential-reference schema, `resolve_credential()`'s
  resolution mechanism, or `CredentialUnsetError`'s behavior.** This unit only *calls* the existing
  method from a new call site under a new flag — it does not modify unit 2.
- **Changing unit-8's spec (`p1-agent-authoring-gate.md`) or unit-8's file (`runner/authoring_gate.py`,
  not yet built).** This unit only prepares the mechanism; wiring it into the live-gate script is unit 8's
  job under its own (already-written, unmodified) spec.
- **Any change to the reference app** (`reference_app/frontend/**`, `reference_app/backend/**`) — the
  login form, its in-memory-only credential handling, and the Basic-Auth mechanism stay exactly as they
  are; this is a runner/glue-side amendment only.
- **Re-authoring the QA system prompt, the seven planner fields, the sub-agent defs, or any other part of
  the unit-6/unit-7 contract** not named above.

## Acceptance criteria (enumerated, testable)

1. **AC1 — Default behavior fully preserved (unit-6).** With `expose_credential_for_exploration` omitted
   (or passed as `False`), `run_authoring(...)` behaves **identically** to before this unit in every
   observable way: the returned `AuthoringInvocation`'s `basic_auth_credential_value` is `None` (or the
   field is absent from any positional-arg expectation — but present as an optional field defaulting to
   `None`), and every existing unit-6 test in `runner/tests/` (e.g. wherever `run_authoring`'s existing
   contract is exercised) passes **unmodified**.
2. **AC2 — Opt-in resolves and carries the value, nowhere else.** With
   `expose_credential_for_exploration=True` and the referenced credential env var **set**,
   `run_authoring(...)` calls `config.resolve_credential()` and the `AuthoringInvocation` passed to
   `agent_runner` has `basic_auth_credential_value` equal to the resolved value. The `RunResult` returned
   by `run_authoring` does **not** expose this value anywhere: not as an attribute, not in `repr(result)`,
   not in any dict/JSON produced by inspecting `RunResult`.
3. **AC3 — Unset credential still raises, unchanged.** With `expose_credential_for_exploration=True` and
   the referenced env var **unset**, `run_authoring(...)` raises `connectors.target_config.
   CredentialUnsetError` (the existing, unmodified exception type/message shape) — proving no new,
   parallel error path was introduced.
4. **AC4 — `AuthoringInvocation` field is additive and keyword-compatible.** `AuthoringInvocation` gains
   `basic_auth_credential_value: Optional[str] = None` such that every existing keyword-argument
   construction of `AuthoringInvocation` in the current test suite (e.g. `runner/tests/opencode_helpers.
   py::make_invocation`) continues to work **unmodified** (i.e. the new field must not be a required
   positional argument with no default, and must not require reordering any existing field).
5. **AC5 — `OpenCodeRunner._compose_message` default path is byte-identical.** For any invocation with
   `basic_auth_credential_value is None`, the string returned by `_compose_message(invocation, role)` is
   **identical** to what unit-7's shipped implementation produces today. The existing
   `test_c13_target_auth_stays_reference_only` test passes **without modification** (this is the
   strongest, most direct proof of this criterion — the test file itself must not need to change for this
   unit).
6. **AC6 — `OpenCodeRunner._compose_message` opt-in path delivers the value.** For an invocation with
   `basic_auth_credential_value` set to a non-`None` string, the composed message for **both** roles
   (Planner and Generator) includes that exact value in a way a downstream reader could act on to submit
   it via a login form (e.g. present alongside the existing reference-name sentence, not instead of it) —
   and continues to include the existing reference-name text as well (the reference name is not removed,
   only supplemented).
7. **AC7 — No `OPENAI_API_KEY` regression.** Every existing unit-7 test exercising the model-credential
   path (at minimum `test_c11_model_key_injected_into_child_env_only`,
   `test_c12_missing_model_credential_raises_named_error`) passes **unmodified**, proving this unit made
   no change to that path.
8. **AC8 — Full existing suite green, unmodified.** The complete existing `runner/tests/` suite (unit 6 +
   unit 7 tests, e.g. `test_c1` through `test_c19` and unit-6's own tests) passes with **zero** test files
   modified by this unit (new tests may be **added**; no existing test's body/assertions may change to
   accommodate this unit — if an existing test would need to change, that is a signal to stop and report,
   not to alter it).
9. **AC9 — Documentation.** `runner/README.md` (or the unit-6/7 contract doc) is updated to describe
   `expose_credential_for_exploration`, `basic_auth_credential_value`, their default-off/opt-in nature,
   and the documented (non-code-enforced) constraint that only the unit-8 live-gate script, for the
   reference app's published fixture account, is permitted to set the flag `True`.

## Interfaces / contracts (pin these precisely)

- **New parameter (binding name):** `run_authoring(config_source, *, agent_runner, output_dir=None,
  source_type="auto", expose_credential_for_exploration: bool = False) -> RunResult` — keyword-only,
  appended after the existing keyword-only parameters; default `False`.
- **New field (binding name):** `AuthoringInvocation.basic_auth_credential_value: Optional[str] = None` —
  appended after the existing fields on the frozen dataclass, with a default so all existing
  keyword-argument construction sites remain valid without modification.
- **`RunResult`:** no new attribute is added for the resolved value; its existing `__slots__` /
  `__repr__` are unchanged by this unit (the value is never threaded into `RunResult` at all).
- **`OpenCodeRunner._compose_message(invocation, role)`:** signature unchanged; behavior branches
  internally on `invocation.basic_auth_credential_value is None`.
- **Errors:** no new exception type is introduced. `connectors.target_config.CredentialUnsetError`
  propagates unchanged from the new call site.
- **Files this unit is expected to touch:** `runner/authoring.py`, `runner/opencode_runner.py`, and their
  documentation (`runner/README.md` or equivalent) — plus new/extended test files under `runner/tests/`
  written by the Tester. No other source file (and no `reference_app/**`, `connectors/**`,
  `agent_config/**`, `eval/**`) should need to change for this unit.

## Definition of Done
- AC1–AC9 all hold.
- Zero existing test in `runner/tests/` was modified (only new tests added) — this is the single
  strongest signal that the default behavior is byte-for-byte preserved and the opt-in is additive only.
- `uv run pytest runner/tests -q` is fully green.
- No secret (`OPENAI_API_KEY` value, nor the resolved `testuser`/`testpass` value) appears in any log,
  `RunResult`, or persisted artifact produced by this unit's own test suite.
- `runner/README.md` (or equivalent) documents the new opt-in mechanism and its scope/rationale.
- No protected file changed (`DESIGN.md`, `META_PLAN.md`, `AGILE_PLAN.md`, `CLAUDE.md`, `.harness/**`,
  `reference_app/**`).
- This unit, once done, unblocks unit 8 (`p1-agent-authoring-gate`) to proceed (still additionally
  gated on `OPENAI_API_KEY` being supplied).

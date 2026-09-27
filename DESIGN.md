# Agentic QA Engineer — SaaS Design

**Status:** Ratified design (SaaS scope). Implementation planning pending (do not start until approved).
**Last updated:** 2026-09-27
**Owner:** prashant

---

## 1. Objective

A **multi-tenant SaaS** where an **Agentic QA Engineer** reliably owns the end-to-end (E2E) test slice of the QA lifecycle for each customer's web app. Customers connect their app (target URL, API spec, repo, BRD source); on each release — or on demand — the platform spins up an isolated sandbox in which an off-the-shelf coding-agent CLI drives the Playwright **Planner → Generator → Healer** agents to author, run, self-heal, and open a PR with tests, with a human-in-the-loop (HITL) review surface.

The design derives from the "End-to-End Agentic QA Workflow with AI Agents, MCP & Playwright" video, productized into SaaS. The core principle behind every decision: **the reliability layer is the product.** Wiring an agent to Playwright over MCP is easy; making its generated tests trustworthy enough to run unattended, per tenant, at scale, is the hard and valuable part.

### Functional scope

- **Lifecycle slice:** E2E test **authoring + execution** (Planner → Generator → Healer).
- **System under test:** each tenant's web **UI + REST/GraphQL API**. API assertions (more deterministic) anchor flaky UI steps.
- **Delivery:** multi-tenant SaaS — pooled data plane, per-run isolated execution, self-serve React control plane.

### Success bar (measured, not vibes)

Generated tests are **low-flake** across re-runs and carry **real, non-vacuous assertions**; the agent **catches injected bugs** with a low false-positive rate. Measured continuously by an internal `eval/` harness against a reference app, and surfaced per tenant as quality metrics.

### Non-goals

- Full 9-stage QA lifecycle breadth. We go **deep on trust, not wide on coverage.**
- Building a custom agent runtime — we **configure an off-the-shelf coding-agent CLI** (§2).
- Hosting customers' apps. Customers point us at their running app + API spec + repo; we test against them.

> Positioning note: agentic MCP test infra pays off above ~200 tests — informs go-to-market and pricing tiers.

---

## 2. Key Principle: configure the brain, don't build it

The orchestrator inside each sandbox is **an existing agentic coding-agent CLI** — the same kind of tool an engineer drives by hand in the video — not custom agent-loop code.

- **Default CLI:** **Claude Code** (headless), **default model `claude-sonnet-5`** — both **configurable per app** (CLI *and* model). Claude Code brings native MCP, sub-agents (`.claude/agents/`), hooks, skills, system-prompt injection, permission modes.
- **Generic sandbox contract** so GitHub Copilot CLI or an open-source agent CLI can swap into the same slot. **"Open agent" is the cost lever** (whole-CLI swap), and therefore a **pricing-tier dimension**: cheaper/open CLIs and models for lower tiers, strongest (e.g. Opus 4.8) for the hardest work / enterprise — traded off against measured reliability.
- What we build is a **QA agent-configuration package** (portable across CLIs): the generic system prompt, sub-agent definitions, hooks, and a reliability skill/instruction pack that turns a general coding CLI into a dependable QA engineer.

---

## 3. System architecture — control plane / data plane

```
  Customers / QA teams              Customer repo (GitHub Actions)
        │                                │  release event
        ▼                                ▼
  ┌──────────────────────────────────────────────────────────────┐
  │                      CONTROL PLANE (pooled)                    │
  │  React app ── API/backend ── AuthN/RBAC ── Audit log           │
  │  Tenant DB (org/app/run, row-level scoped)                     │
  │  Secrets vault · Memory store · Artifact/object store          │
  │  Orchestration service + run queue + sandbox pool manager      │
  │  HITL review queue (checkpoint/resume)                         │
  └──────────────────────────────────────────────────────────────┘
        │ provisions + injects config/secrets            ▲ events, artifacts, HITL asks
        ▼                                                │
  ┌──────────────────────────────────────────────────────────────┐
  │              DATA PLANE — E2B sandbox, ONE per run             │
  │  Coding-agent CLI (default Claude Code) · generic QA sys prompt│
  │     Planner → Generator → Healer  (+ Verifier)                 │
  │     over Playwright MCP (browser) + API tool (OpenAPI/GraphQL) │
  │  Deny-by-default egress · runtime-injected secrets · non-root  │
  └──────────────────────────────────────────────────────────────┘
        │ opens a PR with durable TS Playwright + API tests (via git proxy)
        ▼
  Tenant's Git repo (PR) ──▶ CI (GitHub Actions) deterministic replay ──▶ report ──▶ control plane
```

**Two planes:**

- **Control plane (pooled, multi-tenant):** the React app + API, tenant DB, secrets vault, memory store, artifact store, orchestration/queue, sandbox pool manager, HITL queue, RBAC + audit. Shared infrastructure with strict `org_id`/`app_id` row-level scoping.
- **Data plane (siloed per run):** one **E2B sandbox per run per tenant**, holding the coding-agent CLI + MCP servers + scoped access to that tenant's app. Destroyed after the run (or checkpointed at a HITL gate — see §7). No shared browser state, no cross-tenant network.

**Critical decoupling:** the LLM is used only at **authoring** time. The **deliverable is generated test code** (TS Playwright + API) delivered as a **PR** on the tenant's repo; at **execution** time those tests run as plain, deterministic code (in the tenant's GitHub Actions CI) with **no LLM in the loop**. This is what makes "low-flake + real assertions" achievable at scale.

---

## 4. Sub-agents (the Playwright Agents — "what the video says")

Playwright 1.56 (Oct 2025) shipped three specialized agents, run via a coding CLI over Playwright MCP. Canonical pipeline: **BRD/prompt → Planner → Generator → Execution → Healer → Reports → PR to Git.**

| Agent | Job |
|---|---|
| **🧭 Planner** | Explores the running app; turns the BRD/prompt into a structured test plan. |
| **🛠️ Generator** | Turns the plan into executable **TS Playwright** test code (+ API tests). |
| **🩹 Healer** | Runs tests; self-heals broken ones (distinguishing real regressions from selector drift). |
| **✅ Verifier** *(our addition)* | Reliability gate: audits that assertions are meaningful and selectors are grounded. Sub-agent + hooks. |

---

## 5. Reliability layer (the actual product)

Implemented **through the CLI's mechanisms** (Claude Code hooks/sub-agents/skills), not as custom loop code:

1. **Grounding** — selectors from the live DOM snapshot observed via Playwright MCP (role/label/test-id locators), never invented; API assertions grounded in the OpenAPI/GraphQL schema. Kills the #1 flake source.
2. **Assertion audit** — verifier sub-agent + hooks enforce meaningful assertions, so a "passing" test can't be vacuous.
3. **API cross-check** — deterministic API assertions anchor flaky UI steps (e.g. UI "order placed" confirmed by `GET /orders/{id}`).
4. **Self-heal vs. regression** — on re-run failure, re-snapshot the DOM and decide *drift* (heal) vs *real regression* (surface).
5. **HITL gate + deterministic replay** — new/changed tests enter the review queue before joining the trusted suite; the trusted suite runs headless and deterministic (tenant CI).
6. **Persistent lessons** — mistakes/corrections from past runs are stored and consulted on future runs (§8), so the same error isn't repeated.

**Measurement:** an internal `eval/` injected-bug harness (against a reference app) scores flake rate, assertion meaningfulness, bug-catch rate, and false-positive rate continuously; per-tenant quality metrics surface in the control plane.

---

## 6. Prompt layer

- **One generic system prompt, identical across both trigger flows** — the QA-engineer persona + testing methodology + reliability rules (grounding, meaningful assertions, API-anchoring, self-heal-vs-regression discipline), **written from a genuine senior-QA standpoint.** A first-class deliverable, versioned centrally and applied to every tenant run.
- **BRD** is **unstructured/freeform** (content-hashed for change detection).
- **Structured field set** (drives the Planner; biggest lever on assertion quality):

  | Field | Purpose |
  |---|---|
  | Target scope (feature/flow) | Focuses the Planner; avoids aimless crawling |
  | Intent / goal | What outcome to verify |
  | Expected behavior / acceptance criteria | Grounds *real* assertions |
  | Priority / risk areas | What's most critical or recently changed |
  | Test data / preconditions | Accounts, cart state, sample inputs |
  | Out-of-scope / constraints | What NOT to touch (destructive/prod-like actions) |
  | Depth (smoke / regression / exhaustive) | Breadth vs. effort |

- **Case 1 (autonomous):** the seven fields are **auto-synthesized** from BRD + code diff.
- **Case 2 (on-demand):** the seven fields are **human-filled via a structured React form**, which **hard-gates** the start.

Same field shape feeds the Planner in both flows — machine-derived vs. human-authored.

---

## 7. Trigger flows

| | Trigger | Inputs | Prompt | Start gate |
|---|---|---|---|---|
| **Case 1 — Autonomous** | Tenant **release event** (via **GitHub Actions**) | BRD + new app code **from that release** | Generic system prompt + **auto-synthesized** fields | Fires on release |
| **Case 2 — On-demand / human-in-command** | **QA engineer's query/command** — anytime, **no release required** | BRD + code **from the latest release** | Generic system prompt + **engineer's structured-form** input | **Hard-gated: does not start until the engineer submits the form** |

HITL is inserted wherever the lifecycle needs a human decision: plan approval, ambiguous assertion, destructive step, heal-vs-regression call.

**HITL uses a checkpoint model:** at a gate the run **checkpoints and the sandbox is torn down** while awaiting a human answer; on answer, it **resumes in a fresh sandbox** from the checkpoint. No idle-sandbox cost. HITL asks stream to the control-plane review queue.

---

## 8. Memory, versioning & consistency

- **Memory is store-backed (control plane), hybrid + episodic.** Structured app-scoped records (look up by `app_id`) **plus** semantic retrieval of relevant past lessons — implemented via **mem0** if it fits the need. **Episodic:** entries age out; very old / irrelevant lessons are **dropped** so memory stays current, relevant, and cheap. Two tiers:
  - **Per-app private lessons** — factual, tenant-scoped (e.g. "login moved to a modal"). Stops repeated mistakes across runs/sessions.
  - **Global heuristics** — cross-tenant QA meta-lessons (e.g. "login flows need an explicit wait for post-auth redirect"). A product **moat**: the agent gets better for everyone as usage grows. **Not opt-in — on by default, with a clear disclaimer to tenants. Strict anonymization is mandatory:** no tenant identifiers, URLs, data, or selectors ever leave the app scope — only generalized QA heuristics.
- **Versioning & hashing** — content-hash each tenant's BRD and each generated test case; version them. On a new release, **diff hashes → regenerate/heal only what changed** (consistency + regression efficiency + cost control).

---

## 9. Evaluation & reference app

- **Internal reference app = shop domain** — tiny **real backend** (cart, checkout, orders, auth; mutable UI + API) we control, version, and "release." Used as the **eval testbed** and as an onboarding demo tenant.
- **`eval/` injected-bug harness** — plant known bugs on the reference app across releases; measure bug-catch rate, false positives, flake, and assertion quality. This is the regression suite **for the agent itself** — it gates changes to prompts, sub-agents, and reliability logic before they reach tenants.
- Customers bring their **own** apps; the reference app never mixes with tenant data.

---

## 10. Multi-tenancy

```
Org / QA team   (billing, users, RBAC boundary)
  └── App / project   (target URL, API spec, BRD source, repo, secrets, memory, test suite,
                       coding-agent CLI choice + pinned version, model/tier)
        └── Run / session   (one authoring or execution pass against one app version;
                             records the CLI + version + model used — reproducibility, audit, cost)
```

- **Pooled data + siloed execution.** Control-plane data shares infrastructure with `org_id`/`app_id` **row-level scoping**; **execution is one E2B sandbox per run per tenant.**
- **React control plane** owns: Org → Team → App management, per-app config (target URL, API spec, BRD, repo, secrets, **coding-agent CLI + version, model/tier**), triggering (**release via GitHub Actions** + **on-demand query**), the **HITL review queue**, results/reports/quality metrics, billing/usage, and RBAC + audit.
- **Sandbox pool manager** reads the app's CLI/model choice to provision the correct sandbox image, injects per-run config + scoped secrets, enforces time/resource limits, checkpoints/tears-down/resumes across HITL gates, and stamps the run with the CLI + version + model used.
- **Sandbox substrate = E2B** (generic container that hosts a swappable coding-agent CLI). **Not** Managed Agents — that runs Anthropic's own agent loop and cannot host a third-party CLI as the brain.

---

## 11. Security model (first-class)

Running an autonomous coding agent, per tenant, against customer apps raises specific threats:

1. **Prompt injection from the app under test — the sharpest risk.** The agent reads app DOM/content (app- and partly attacker-controllable). Treat **all app content as untrusted data, never instructions**; keep secrets out of the agent's readable context; HITL-gate anything sensitive.
2. **Egress allowlist (deny-by-default).** A sandbox may reach only: the model/CLI API, that tenant's target app, and the artifact/git endpoints. Primary exfiltration defense.
3. **Isolation.** One sandbox per run per tenant; microVM/gVisor-class isolation; non-root; read-only rootfs where feasible; resource + time limits; no host mounts; destroyed after the run.
4. **Secrets.** Per-tenant vault; target-app login is **Basic Auth (username/password)** stored in the vault and injected at **runtime**, egress-scoped, **never in prompts, logs, traces, or artifacts**; ephemeral; rotated.
5. **Model/CLI credentials are platform-owned**, metered per tenant, and live behind the egress allowlist — never tenant-supplied, never exposed to the agent's readable context.
6. **VCS credentials.** Scoped per-tenant, write-only to that tenant's own repo/branch (PR), injected via a **git proxy** (token never sits in the container).
7. **Tenant data isolation.** Row-level scoping across DB, memory store, and artifact buckets; traces/screenshots may hold the app's real PII — encrypted at rest, per-tenant scoped, retention-limited.
8. **Global-heuristics anonymization.** Mandatory scrubbing so no tenant identifiers/URLs/data/selectors ever enter the shared tier — only generalized heuristics. Backed by a tenant disclaimer.
9. **RBAC + audit.** Org → team → app roles, least privilege; full audit log of who triggered what and what each agent run did.
10. **Supply chain.** Pinned/verified sandbox image, CLI version, and MCP servers; signed builds.
11. **Tenant abuse / cost controls.** Per-org quotas, rate limits, and run budgets to bound spend and blast radius.

---

## 12. Tech stack

| Concern | Choice |
|---|---|
| In-sandbox orchestrator | **Claude Code** (headless) **default**, **per-app configurable**; generic sandbox contract for CLI swaps |
| Model | **Default `claude-sonnet-5`**; Opus 4.8 for hardest tasks / higher tiers; **per-app configurable**; open models gated by eval |
| Sub-agents | Playwright **Planner / Generator / Healer** + **Verifier**, over **Playwright MCP** |
| API testing | Schema-driven assertions from **OpenAPI/GraphQL** |
| Test artifacts | **TypeScript Playwright** (`playwright test`) + API tests — durable, LLM-free at runtime; delivered as a **PR** |
| CI / release trigger | **GitHub Actions** (release event → Case 1; also runs the deterministic replay in tenant CI) |
| Control-plane services | **Python** backend/orchestration (glue, queue, sandbox manager) |
| Frontend | **React** control plane (tenancy, config, triggers, HITL, metrics, RBAC/audit) |
| Data stores | Tenant **DB** (row-level scoped) · **secrets vault** · **memory store (hybrid + episodic, mem0 if needed)** · **artifact/object store** |
| Execution sandbox | **E2B** (per-tenant, per-run; checkpoint/resume across HITL) |
| Target-app auth | **Basic Auth (username/password)** from the per-tenant vault |
| Reference app | Tiny **real backend** (shop) + frontend, for eval/demo |

---

## 13. Repo / service layout

```
qa-engineering-agent/
  agent_config/     # generic QA system prompt, .claude/agents/ sub-agents, hooks, reliability skill pack (portable across CLIs)
  connectors/       # playwright-mcp config, api-spec loader, per-run target config
  reliability/      # grounding, assertion-audit, self-heal, deterministic replay helpers
  runner/           # execution + reporting + failure triage
  eval/             # injected-bug harness — the agent's own regression suite
  reference_app/    # shop: real backend (UI + mutable API) for eval/demo
  control_plane/
    api/            # backend: auth, RBAC, tenancy, triggers, HITL, billing/usage
    orchestration/  # run queue + sandbox pool manager (provision E2B, inject secrets, checkpoint/resume, teardown)
    stores/         # tenant DB schema, memory store (mem0), artifact store, vault integration
    frontend/       # React: org/team/app, config, triggers, HITL queue, metrics, audit
  sandbox/          # E2B image + generic CLI contract + git proxy + egress policy
  DESIGN.md
```

---

## 14. Delivery roadmap (build sequence — detailed task plan pending approval)

Built as a thin vertical slice first, then hardened into the full SaaS:

- **Phase 0** — Reference shop app (UI + real API + BRD) + `eval/` injected-bug harness + repo scaffolding.
- **Phase 1** — In-sandbox authoring loop: Claude Code + Playwright MCP running Planner→Generator against the reference app; grounded TS Playwright + API tests; generic QA system prompt.
- **Phase 2** — Reliability layer: assertion audit, API cross-check, Healer self-heal, deterministic replay; prove the success bar on `eval/`.
- **Phase 3** — E2B execution + single-tenant control-plane spine: sandbox pool manager, secrets injection, egress policy, git proxy, PR delivery, checkpoint/resume.
- **Phase 4** — Memory (mem0 hybrid + episodic) + BRD/test hashing & change-detection on release.
- **Phase 5** — Multi-tenancy + React control plane: Org→Team→App, RBAC/audit, config (incl. CLI/model), triggers (GitHub Actions release + on-demand query), HITL review queue.
- **Phase 6** — Trigger flows end-to-end (Case 1 + Case 2), quality metrics, billing/usage, quotas.
- **Phase 7** — Hardening: full security model, open-agent CLI swap, global-heuristics tier + disclaimer + anonymization.

> The detailed, task-level implementation plan will be produced **only when explicitly requested.**

---

## 15. Open / deferred items

- Which cheap/open model + CLI per pricing tier (eval-driven).
- Global-heuristics **anonymization implementation** — the guarantee that no tenant identifiers/URLs/data/selectors leak into the shared tier — plus tenant disclaimer wording.
- Exact GitHub Actions integration shape (workflow/app, how BRD + code diff are delivered per release, PR/checks wiring).
- Target-app auth beyond **Basic Auth** (SSO/MFA test accounts) for later tiers.
- Data residency / retention policy per tenant tier; memory episodic-decay thresholds.

> **Explicitly post-v1 (not in first SaaS release):** (a) target-app auth beyond Basic Auth — SSO/MFA;
> (b) data residency & retention policy per tenant tier.
> All other §15 items are implemented in-phase; only their fine detail / eval-driven choice is deferred.

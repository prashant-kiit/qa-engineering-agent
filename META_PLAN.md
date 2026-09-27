# Meta Plan — Agentic QA Engineer (SaaS)

> North-star plan: all phases detailed. Source of truth for architecture is `DESIGN.md`.
> Working detail per phase lives in `AGILE_PLAN.md` and is revised each iteration.

## Context
A multi-tenant SaaS where an Agentic QA Engineer authors, runs, self-heals, and PRs Playwright
E2E + API tests for each customer's web app. Guiding principle: **the reliability layer is the
product.** The `eval/` injected-bug harness is the objective gate every phase is measured against.

Each phase: **Goal · Key deliverables · Acceptance gate.** Phases are additive; the reference app
and `eval/` harness from Phase 0 gate everything after.

## Phase 0 — Testbed & scaffolding  (executable detail in AGILE_PLAN.md)
- **Goal:** something real to test + a way to measure reliability.
- **Deliverables:** reference shop app (FastAPI + React + SQLite, auto-OpenAPI), freeform BRD,
  release convention, `eval/` injected-bug harness, repo scaffolding + tooling, Playwright TS
  project + smoke test.
- **Gate:** app runs; OpenAPI served; ≥3 injected bugs; eval scorer produces catch / false-positive
  / flake metrics against a baseline hand-written suite; one-command reproducible.

## Phase 1 — In-sandbox authoring loop (local first)
- **Goal:** Claude Code (headless) + Playwright MCP running **Planner → Generator** to emit
  **grounded** TS Playwright + API tests against the reference app; BRD injected as the generic QA
  system prompt.
- **Deliverables:** `agent_config/` (generic QA system prompt v1, `.claude/agents/` for Planner &
  Generator, Playwright-MCP config), `connectors/` (OpenAPI/GraphQL spec loader, per-run target
  config), first agent-generated tests committed.
- **Gate:** from BRD + running app, the agent produces runnable, DOM/schema-grounded tests that
  pass on the clean app; eval shows a baseline injected-bug catch rate better than naive.

## Phase 2 — Reliability layer
- **Goal:** hit the success bar (low flake, real assertions, high bug-catch, low false-positive).
- **Deliverables:** **Verifier** sub-agent + hooks (assertion audit + grounding enforcement),
  **API cross-check** anchoring, **Healer** self-heal (drift vs regression), deterministic headless
  replay in `runner/`.
- **Gate:** on `eval/`: injected-bug catch ≥ target, false-positive ≤ target, re-run flake ≤ target,
  assertion-audit pass-rate ≥ target (thresholds set at Phase 2 start against baseline).

## Phase 3 — E2B execution + single-tenant control-plane spine
- **Goal:** run the Phase 1–2 loop **inside E2B** instead of locally.
- **Deliverables:** `sandbox/` (E2B image, generic CLI contract, git proxy, deny-by-default egress);
  `control_plane/orchestration/` (run queue + sandbox pool manager: provision, inject config +
  Basic-Auth secrets, checkpoint/tear-down/resume across HITL gates, teardown, stamp run with
  CLI+version+model); **PR delivery** to a test repo.
- **Gate:** a run executes end-to-end in E2B, opens a PR, checkpoints+resumes across a simulated
  HITL gate, secrets never in logs/artifacts, egress allowlisted.

## Phase 4 — Memory & versioning
- **Goal:** stop repeating mistakes; regenerate only what changed on release.
- **Deliverables:** `control_plane/stores/` memory (**mem0**, hybrid structured + semantic,
  **episodic** age-out) — per-app private lessons recorded from failures and consulted next run;
  BRD + test **content-hashing** and change-detection.
- **Gate:** a mistake in run N is demonstrably avoided in run N+1; a release with a small change
  regenerates/heals only affected tests (hash-diff proven).

## Phase 5 — Multi-tenancy + React control plane
- **Goal:** self-serve, isolated tenants.
- **Deliverables:** tenant DB (Org → Team → App, row-level scoping), AuthN + RBAC + audit; per-app
  config (target URL, API spec, BRD, repo, secrets, **CLI + version, model/tier**); triggers
  (**GitHub Actions** release + **on-demand** query); `control_plane/frontend/` React app incl.
  **HITL review queue**.
- **Gate:** two isolated orgs; a run each from the UI (on-demand) and from a GitHub Actions release;
  HITL handled in-UI; zero cross-tenant leakage (verified).

## Phase 6 — Trigger flows end-to-end + metrics/billing
- **Goal:** both flows productionized.
- **Deliverables:** **Case 1** (release-triggered, auto-synthesized fields) and **Case 2**
  (on-demand, human structured-form, hard-gated) fully wired; per-tenant quality metrics;
  usage/billing + quotas/rate-limits.
- **Gate:** both cases run end-to-end for a demo tenant; metrics visible; quotas enforced.

## Phase 7 — Hardening
- **Goal:** security + extensibility + moat.
- **Deliverables:** full `DESIGN.md §11` security model (isolation, egress, supply-chain pinning,
  abuse/cost controls); **open-agent CLI swap** (Copilot/open CLI via the generic sandbox contract);
  **global anonymized-heuristics** tier + disclaimer + mandatory anonymization.
- **Gate:** security review passes; a second CLI runs a job via the generic contract; global-
  heuristics tier populated only with verified-anonymized entries.

## Post-v1 (explicitly out of first release)
- Target-app auth beyond Basic Auth — SSO/MFA.
- Data residency & retention policy per tenant tier.

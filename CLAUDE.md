# qa-engineering-agent

Multi-tenant SaaS: an **Agentic QA Engineer** that authors, runs, self-heals, and PRs Playwright
E2E + API tests for each customer's web app.

## Read first (source of truth)
- `DESIGN.md` — ratified architecture (SaaS scope).
- `META_PLAN.md` — all phases (0–7) detailed.
- `AGILE_PLAN.md` — Phase 0 executable detail + the per-phase revise loop.

## Build harness — TDD with role-separated agents
Development uses a **test-driven, multi-agent** harness. Five subagents, **each in its own context**
for unbiasedness; handoffs are **artifact-only** (files on disk), never one agent's reasoning.

| Role | Subagent | Does | Must NOT |
|---|---|---|---|
| Technical PM | `tpm` | Pick next unit; write task spec + acceptance criteria (WHAT, not HOW) | write tests or source |
| Tester | `tester` | Write **failing** tests first from the spec (TDD red) | read/modify implementation |
| Developer | `developer` | Implement minimum to make tests pass (TDD green) | modify tests or the spec |
| Reviewer | `reviewer` | Independently review diff vs spec + tests + quality | edit code |
| Git Deployer | `git-deployer` | Commit approved + green work to a feature branch | push, or commit to the default branch |

### Run a cycle (any session)
```
/tdd [task-id or short description]
```
Runs one TDD cycle: **TPM → Tester → Developer → run tests → Reviewer → (loop Developer↔Reviewer
until APPROVE & green) → Git Deployer**, pausing at human gates. Handoff artifacts live in
`.harness/` (see `.harness/README.md`). Omit the argument to let the TPM pick the next unit from
`AGILE_PLAN.md` + `.harness/backlog.md`.

### Unbiasedness rules (enforced by the orchestrator)
- Never pass an agent the previous agent's chat/reasoning — pass only the **artifact files**.
- The Tester writes tests **before** the Developer implements, and does not see the implementation.
- The Developer may not edit tests; if a test looks wrong, it **stops and reports** (does not "fix").
- The Reviewer runs the suite itself and judges independently.

## Conventions
- Test artifacts: **TypeScript Playwright** (per `DESIGN.md`).
- Commits: Conventional Commits, reference the task-id; feature branch only; end with
  `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>`.

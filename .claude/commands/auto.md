---
description: Autonomous build — run the full TDD cycle for every backlog unit until the phase exit gate passes (auto-approves gates).
---

Build in **AUTO mode**: **$ARGUMENTS**
(If empty, build the current/active phase in `.harness/backlog.md`.)

You are the **orchestrator**. Loop over `.harness/backlog.md` top-to-bottom, respecting deps. For
each not-`done` unit whose deps are met, run the **full TDD cycle exactly as
`.claude/commands/tdd.md` defines it**:

> TPM locks `AGILE_PLAN.md` (from `META_PLAN.md` + current app state) & specs the unit → Tester writes
> failing tests → **Tester⇄Developer loop to green** → Reviewer → **Reviewer⇄Developer⇄Tester loop to
> APPROVE** → Git Deployer commits + pushes a `harness/<id>` feature branch.

Obey the same **unbiased, artifact-only handoff** rules (pass agents only the files — spec, tests,
diff, review — never another agent's reasoning). You do none of the roles' work yourself.

## How AUTO differs from `/tdd`
- **Auto-approve** the plan gate and the deploy gate — do **not** pause for them.
- **Do not stop after one unit** — advance to the next until the active phase's **exit gate** in
  `AGILE_PLAN.md` is satisfied.

## Stop and ask the human ONLY when
- a genuine blocker (missing dependency / credential / tool / spec ambiguity), **or**
- the TPM flags a conflict with `DESIGN.md` / `META_PLAN.md`, **or**
- a Loop A cap (5) or Loop B cap (3) is hit.

The **deploy-gate hook** still enforces review-before-push (`.harness/state/APPROVED`) — never bypass
it with `HARNESS_BYPASS`.

## When the phase exit gate passes
Stop and summarize each unit built: task-id, branch, commit hash, pushed ref, and eval status.

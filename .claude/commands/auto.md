---
description: Autonomous build. `/auto` builds the active phase to its exit gate; `/auto all` chains phases 0→7 to build the whole product.
---

Build in **AUTO mode**: **$ARGUMENTS**
- empty or a phase name → build that / the active phase to its exit gate.
- **`all`** → build the **entire product, phases 0→7**, chaining phase after phase until the final
  phase's exit gate passes (see "Scope: all" below).

You are the **orchestrator**. Loop over `.harness/backlog.md` top-to-bottom, respecting deps. For
each not-`done` unit whose deps are met, run the **full TDD cycle exactly as
`.claude/commands/tdd.md` defines it**:

> TPM locks `AGILE_PLAN.md` (from `META_PLAN.md` + current app state) & specs the unit → Tester writes
> failing tests → **Tester⇄Developer loop to green** → Reviewer → **Reviewer⇄Developer⇄Tester loop to
> APPROVE** → Git Deployer commits + pushes.

Obey the same **unbiased, artifact-only handoff** rules (pass agents only the files — spec, tests,
diff, review — never another agent's reasoning). You do none of the roles' work yourself.

## How AUTO differs from `/tdd`
- **Auto-approve** the plan gate and the deploy gate — do **not** pause for them.
- **Do not stop after one unit** — advance to the next until the phase's **exit gate** in
  `AGILE_PLAN.md` is satisfied.

## Stop and ask the human ONLY when
- a genuine blocker (missing dependency / credential / tool / spec ambiguity), **or**
- the TPM flags a conflict with `DESIGN.md` / `META_PLAN.md`, **or**
- a Loop A cap (5) or Loop B cap (3) is hit, **or**
- (scope `all`) a hard external prerequisite or a session/context limit is reached (see below).

The **deploy-gate hook** still enforces review-before-push (`.harness/state/APPROVED`) — never bypass
it with `HARNESS_BYPASS`.

## Scope: `all` — whole product (phases 0→7)
When invoked as `/auto all`:
- **Chain phases.** After a phase's exit gate passes, advance to the next phase: the TPM locks that
  phase in `AGILE_PLAN.md` from `META_PLAN.md` + current app state and seeds `.harness/backlog.md`
  with its units; then build them. Repeat until **Phase 7's** exit gate passes.
- **Integration branch.** Commit every unit to one shared branch **`harness/build`** (create it from
  `master` on first use) instead of per-unit branches, so work accumulates. Instruct `git-deployer`
  to use `harness/build`. Never commit to `master` — a human merges `harness/build → master` at the end.
- **Hard external stops — you CANNOT self-provision these; stop and ask the human with an exact ask:**
  an **E2B API key** (Phase 3), the **in-sandbox coding-agent model API key/credits**, and
  **GitHub Actions** wiring (Phases 5–6).
- **Session/context limit.** If the session is ending or context is exhausted, checkpoint state in
  `.harness/` + the backlog, then tell the human to **re-run `/auto all` to resume**. Never fabricate
  completion or skip units.

## When the final phase exit gate passes
Stop and summarize each unit built (task-id, commit, eval status). For `/auto all`, also tell the
human to merge **`harness/build → master`**. Do not claim done unless every phase's exit gate in
`AGILE_PLAN.md` has actually passed and `eval/` metrics back it up.

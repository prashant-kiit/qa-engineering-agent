---
description: Run one TDD cycle with the role-separated agents (TPM → Tester → Developer → Reviewer → Git Deployer).
---

Run **one** test-driven build cycle for: **$ARGUMENTS**
(If empty, let the TPM pick the next unit from `AGILE_PLAN.md` + `.harness/backlog.md`.)

You are the **orchestrator**. Delegate each step to the matching subagent via the Task tool. The
whole point is **unbiased, artifact-only handoffs** — obey these rules:

- Pass each agent **only the artifact file paths** it needs (spec, tests, diff), **never** the prior
  agent's reasoning, summary, or chat. Each agent reads the files itself.
- Do not do any role's work yourself. You only coordinate, run gates, and relay artifacts.

## Cycle
1. **TPM** (`tpm`) → produces `.harness/tasks/<id>.md`. Capture the `task-id`.
2. **Human gate (spec):** show the spec path and pause for the human to approve/adjust before build.
3. **Tester** (`tester`) → writes failing tests from the spec; confirms legitimate **red**.
4. **Developer** (`developer`) → implements to **green**. If it reports a bad test, **stop** and
   surface to the human / re-invoke `tpm`/`tester` — never let the developer edit tests.
5. **Run the suite** to confirm green.
6. **Reviewer** (`reviewer`) → writes `.harness/reviews/<id>.md` with `APPROVE` or `CHANGES_REQUESTED`.
7. If `CHANGES_REQUESTED`: re-invoke **Developer** with the review file + tests only, then loop to
   step 5. Cap at 3 loops, then escalate to the human.
8. On `APPROVE` + green → **Human gate (commit):** confirm, then **Git Deployer** (`git-deployer`)
   commits to a feature branch (no push).
9. Report: task-id, branch, commit hash, and what's next in the backlog.

Stop after one cycle. Do not auto-start the next task.

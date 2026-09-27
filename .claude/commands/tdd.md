---
description: Run one full TDD cycle with role-separated agents — TPM locks the plan, Tester⇄Developer to green, Reviewer⇄Developer⇄Tester to APPROVE, then push.
---

Build one unit for: **$ARGUMENTS**
(If empty, the TPM picks the next unit from the locked `AGILE_PLAN.md` + `.harness/backlog.md`.)

You are the **orchestrator**. You do **none** of the roles' work yourself — you only delegate (via
the Task tool), run gates, and relay **artifact file paths** between agents. **Never** pass an agent
another agent's chat/reasoning — only the files (spec, tests, diff, review). This is what keeps the
roles unbiased.

## State machine (do the steps in order; do not skip)

1. **Plan (TPM).** Invoke `tpm`. It locks the active phase into `AGILE_PLAN.md` from `META_PLAN.md` +
   current app state, and writes `.harness/tasks/<id>.md`. Capture `<id>`.
2. **Gate — plan lock (human).** Show the AGILE_PLAN.md diff + the spec path; pause for approval/edits.
3. **Red (Tester).** Invoke `tester` with the spec path only → failing tests + `.harness/tasks/<id>.tests.md`.
4. **Loop A — Tester⇄Developer → green.** Invoke `developer` with the spec + test paths only.
   - If the developer reaches **all tests green**, exit Loop A.
   - If the developer reports a **wrong/impossible test** (it must NOT edit tests), route that report
     to `tester` to revise the test, then re-invoke `developer`. Repeat.
   - Cap Loop A at **5 iterations**, then escalate to the human.
5. **Confirm green.** Run the full relevant suite yourself; it must be green.
6. **Review (Reviewer).** Invoke `reviewer` with spec + tests + the diff → `.harness/reviews/<id>.md`
   with `APPROVE` or `CHANGES_REQUESTED`, each item tagged **[dev]** and/or **[tester]**.
7. **Loop B — Reviewer⇄Developer⇄Tester → APPROVE.** If `CHANGES_REQUESTED`:
   - Route **[dev]** items to `developer`, **[tester]** items to `tester` (each gets only the review
     file + the artifacts it owns).
   - Re-confirm green (step 5), then re-invoke `reviewer` (step 6). Repeat.
   - Cap Loop B at **3 iterations**, then escalate to the human.
8. **Gate — deploy (human).** On `APPROVE` + green, show the summary and pause for confirmation.
9. **Push (Git Deployer).** Invoke `git-deployer` → commits the unit to a feature branch and **pushes**.
10. **Report:** `<id>`, branch, commit hash, pushed ref, and the next backlog unit. **Stop** — do not
    auto-start the next unit.

## Invariants (enforced here; see .claude/settings.json for the hard gate)
- Only the `tester` writes/edits tests. The `developer` never edits tests or the spec.
- No commit/push happens before an `APPROVE` review and a green suite.
- Building this project happens **only through this command** — do not hand-write app code outside a cycle.

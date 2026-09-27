# .harness/ — TDD build-harness workspace

Artifact-only handoff between the role agents (`.claude/agents/*.md`). Keeping handoffs on disk is
what makes the roles **unbiased**: each agent reads the previous role's *output files*, never its
reasoning. It also makes cycles **resumable across sessions**.

## Layout
```
.harness/
  backlog.md          # ordered units of work + status (spec-ready | in-progress | done)
  tasks/<id>.md       # TPM's task spec: context, scope, acceptance criteria, contracts, DoD
  tasks/<id>.tests.md # Tester's coverage note: acceptance criterion -> test(s), red output
  reviews/<id>.md     # Reviewer's verdict: APPROVE | CHANGES_REQUESTED + actionable items
```

## Flow
`/tdd [task]` orchestrates: **TPM → (spec gate) → Tester(red) → Developer(green) → Reviewer →
(loop if changes) → (commit gate) → Git Deployer(feature branch, no push)**.

## Handoff contract (per file)
| Producer | File | Consumer(s) |
|---|---|---|
| tpm | `tasks/<id>.md` | tester, developer, reviewer |
| tester | test files + `tasks/<id>.tests.md` | developer, reviewer |
| developer | source diff | reviewer, git-deployer |
| reviewer | `reviews/<id>.md` | developer (if changes), git-deployer |

`<id>` is a short slug, e.g. `p0-shop-backend`, `p0-eval-harness`.

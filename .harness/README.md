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

## Deploy gate (hard enforcement)
A `PreToolUse` hook (`.claude/hooks/deploy-gate.sh`, wired in `.claude/settings.json`) **blocks
`git commit`/`git push` unless `.harness/state/APPROVED` exists**. The Reviewer writes that marker
(the task-id) on `APPROVE`; the Git Deployer deletes it after a successful push. This makes
"no push before a passing review" deterministic, not just instructed.

- `state/` is transient and **git-ignored** — never committed.
- **Escape hatch:** intentional non-harness commits use `HARNESS_BYPASS=1 git commit …`.
- The hook activates in a **new session** (or after opening `/hooks` once) — Claude Code loads
  `.claude/settings.json` at session start.

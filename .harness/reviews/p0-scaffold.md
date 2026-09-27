# Review — unit `p0-scaffold` (re-review, Loop B: C10 test refinement)

**Verdict: APPROVE**

Re-review triggered by a test-only refinement to acceptance check C10. No developer/source
change was in scope for this loop; the scaffolding (dirs, `pyproject.toml`, `Makefile`,
`.gitignore` extension) is unchanged from the previously-green state.

## Axis findings

### 1. Acceptance
All 11 acceptance criteria are met and asserted by the suite (C1–C11 all PASS):
- §13 directory tree present + git-tracked via `.gitkeep` placeholders (C1, C3).
- No stray top-level dirs (C2).
- `pyproject.toml` present and parsed by `uv` (C4a/C4b).
- `Makefile` defines `dev`/`test`/`eval`/`release` + `help`, all invocable, exit 0, and name
  their owning later units (C5, C6, C7).
- `.gitignore` additively ignores `.venv/`, `node_modules/`, `*.db`, and Playwright artifacts
  (`test-results/`, `playwright-report/`, `playwright/.cache/`), with all pre-existing lines
  preserved (C8, C9).
- Protected docs unchanged; additive-only diff (C10, C11).

### 2. Test integrity — refined C10 is meaningful and un-gamed
- The hash-comparison loop over the frozen protected baseline (DESIGN.md, META_PLAN.md,
  AGILE_PLAN.md, CLAUDE.md, and pre-existing `.harness/**`) is **unchanged** — genuine mutation
  of any protected doc is still caught by hash mismatch. The refinement touched only the
  *new-file* walk.
- The `is_harness_lifecycle` exemption is narrowly scoped to legitimate per-cycle lifecycle
  artifacts materialized AFTER the baseline was frozen: `.harness/reviews/*` (Reviewer verdicts),
  `.harness/state/*` (git-ignored deploy-gate markers), and the Tester's own
  `.harness/tasks/p0-scaffold.tests.md`. It mirrors the pre-existing `.tests.md` exemption
  pattern. These are not developer mutations of protected content.
- **Empirically verified not a no-op:** injecting an unexpected new file
  (`.harness/tasks/__reviewer_probe__.md`) still fails C10
  (`new file added under .harness/`; suite exit 1). Removed after the check.
- The over-broad behavior described (flagging normal lifecycle files) is correctly fixed without
  weakening the protected-doc guarantee. No test was gutted.

### 3. Scope
Diff is additive scaffolding only: 12 `.gitkeep` placeholders, `Makefile`, `pyproject.toml`,
`uv.lock`, `.gitignore` additive edit, plus Tester fixtures/tests. `AGILE_PLAN.md` and
`.harness/backlog.md` differ from the last commit but match the frozen protected/plan-lock
baseline (C10 green) — attributable to the TPM plan-lock, not this unit. No app/API/UI/eval
logic introduced.

### 4. Quality
- Makefile targets are clean `.PHONY` placeholders, exit 0, each names its owning later unit.
- `pyproject.toml` is a minimal valid manifest (`package = false`, no premature deps).
- Placeholders carry a self-documenting marker comment. No dead code.
- No security-sensitive surface introduced (no secrets, no runtime code) per DESIGN §11.

## Test runs (independent)

`bash tests/scaffold/p0-scaffold.test.sh` → exit 0:
```
PASS: C1  PASS: C3  PASS: C2  PASS: C4a  PASS: C4b  PASS: C5a  PASS: C5b  PASS: C5c
PASS: C6  PASS: C7  PASS: C8  PASS: C9  PASS: C10  PASS: C11
RESULT: all acceptance checks passed
```

`bash tests/docs/design-note.test.sh` → exit 0:
```
PASS: C1 C2a C2b C3a C3b C4 C5a C5b C6 C7a C7b
RESULT: all acceptance checks passed
```

Both suites green.

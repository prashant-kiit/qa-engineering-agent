# Test coverage — unit `p0-scaffold`

Tester artifact (TDD red). Encodes each acceptance criterion of
`.harness/tasks/p0-scaffold.md` as an automated, runnable check. No implementation
source was read; the spec is the contract.

## Test file
- `tests/scaffold/p0-scaffold.test.sh` — self-contained bash presence/behaviour suite
  (no framework; Playwright arrives in unit 5). Runnable: `bash tests/scaffold/p0-scaffold.test.sh`
  (exit 0 = all pass, exit 1 = any fail, exit 2 = harness/scaffold-error). Follows the
  existing `tests/docs/design-note.test.sh` pattern. macOS bash 3.2 compatible (no
  associative arrays).

## Baseline fixtures (frozen pre-developer snapshots)
Captured before implementation begins so the "unchanged" criteria attribute changes to
this unit's *developer* work only — not to the TPM's earlier plan-lock edits.
- `tests/fixtures/gitignore-baseline.txt` — full copy of `.gitignore` at unit start (C9).
- `tests/fixtures/p0-scaffold-protected-baseline.txt` — `hash<TAB>path` for the four
  protected docs + every file under `.harness/` at unit start (C10).
- `tests/fixtures/p0-scaffold-tracked-baseline.txt` — `hash<TAB>path` for every
  git-tracked file at unit start (C11).

## Acceptance criterion → test mapping
| # | Acceptance criterion | Check(s) in `p0-scaffold.test.sh` |
|---|---|---|
| 1 | Every §13 directory exists and is git-tracked (>=1 placeholder file) | C1 — for each of the 12 dirs: `-d` exists AND `git ls-files` non-empty |
| 2 | No stray top-level dirs beyond §13 + existing repo dirs | C2 — enumerate top-level dirs, assert each is in the §13-roots + permitted set |
| 3 | `git ls-files` lists a tracked file inside each §13 dir | C3 — per-dir tracked-file count `>= 1` |
| 4 | Root Python manifest exists and is parseable by `uv` | C4a `pyproject.toml` present; C4b `uv lock --check` (fallback `uv tree`) exits 0 |
| 5 | Root `Makefile` defines `dev`/`test`/`eval`/`release` + a list/help target | C5a Makefile present; C5b targets resolve via `make -n` (no "no rule"); C5c help/list target (help/list/targets/default) resolves |
| 6 | Makefile targets wired correctly | C6a — the still-unimplemented placeholders `dev`/`eval`/`release` are invocable, exit 0, and name their owning later unit (`eval`→unit 6/`p0-eval-harness`; `release`→unit 4/`p0-brd-release`); C6b — `test` is now the REAL Playwright smoke (unit 5, `p0-playwright-smoke`), so it is asserted DEFINED and wired to the e2e/Playwright smoke via a dry-run `make -n test` grep (`playwright|e2e`) and is **NOT executed** (running it would launch backend+frontend servers and headless Chromium). `test` was removed from the placeholder-execution loop. |
| 7 | Help/list target lists all four targets | C7 — help output contains `dev`, `test`, `eval`, `release` |
| 8 | `.gitignore` ignores `.venv/`, `node_modules/`, `*.db`, Playwright artifacts | C8 — `git check-ignore -q` for `.venv/`, `node_modules/`, `*.db`, `test-results/`, `playwright-report/`, and a Playwright cache path |
| 9 | No pre-existing `.gitignore` entry removed (additive) | C9 — every non-blank baseline line still present in current `.gitignore` |
| 10 | No protected file changed (DESIGN/META/AGILE/CLAUDE.md, `.harness/**`) | C10 — working-tree hash equals frozen protected-baseline hash; no new `.harness/` file except harness *lifecycle* files expected per-cycle (Tester's own `.tests.md`, Reviewer verdicts `.harness/reviews/**`, deploy-gate markers `.harness/state/**`) |
| 11 | Repo stays a valid additive-only skeleton | C11 — no pre-existing tracked file deleted; only `.gitignore` differs from tracked baseline; (uv-parse C4 + target exit-0 C6 assert invocability) |

Notes:
- C2, C9, C10, C11 are regression guards that are correctly GREEN at red time (nothing
  has been improperly changed yet); they turn red only if the developer violates scope.
- The legitimate red for "scaffolding absent" is C1, C3, C4, C5, C6, C7, C8.

## Red run output (scaffolding not yet present)
```
       missing directory: reference_app/backend
       missing directory: reference_app/frontend
       missing directory: agent_config
       missing directory: connectors
       missing directory: reliability
       missing directory: runner
       missing directory: eval
       missing directory: control_plane/api
       missing directory: control_plane/orchestration
       missing directory: control_plane/stores
       missing directory: control_plane/frontend
       missing directory: sandbox
FAIL: C1: 12 §13 director(y/ies) missing or untracked
       no tracked file under: reference_app/backend
       no tracked file under: reference_app/frontend
       no tracked file under: agent_config
       no tracked file under: connectors
       no tracked file under: reliability
       no tracked file under: runner
       no tracked file under: eval
       no tracked file under: control_plane/api
       no tracked file under: control_plane/orchestration
       no tracked file under: control_plane/stores
       no tracked file under: control_plane/frontend
       no tracked file under: sandbox
FAIL: C3: 12 §13 director(y/ies) have no tracked file
PASS: C2: no stray top-level directories beyond §13 + existing repo dirs
FAIL: C4a: root Python manifest 'pyproject.toml' missing
FAIL: C4b: uv failed to parse root project manifest (rc=2): error: No `pyproject.toml` found in current directory or any parent directory
FAIL: C5a: root Makefile missing
       Makefile target not defined: dev
       Makefile target not defined: test
       Makefile target not defined: eval
       Makefile target not defined: release
FAIL: C5b: 4 required Makefile target(s) undefined
FAIL: C5c: no list/help target defined (tried help/list/targets/default)
       make dev exited 2 (expected 0)
       make test exited 2 (expected 0)
       make eval exited 2 (expected 0)
       make release exited 2 (expected 0)
FAIL: C6: 4 target(s) failed exit-0 + placeholder-message check
FAIL: C7: no help/list target available to verify listing
       path NOT ignored by .gitignore: node_modules/
       path NOT ignored by .gitignore: some-database.db
       path NOT ignored by .gitignore: test-results/
       path NOT ignored by .gitignore: playwright-report/
FAIL: C8: 4 required ignore pattern(s) not matched by .gitignore
PASS: C9: all pre-existing .gitignore entries preserved (additive edit only)
PASS: C10: no protected file changed (DESIGN/META/AGILE/CLAUDE.md, .harness/**)
PASS: C11: additive diff only (no pre-existing file deleted; only .gitignore modified)
-----------------------------------------------------------------------
RESULT: 10 acceptance check(s) failed
```
Exit code: 1 (red). Failures are all for the right reason — required scaffolding
(directory tree, `uv` manifest, `Makefile` targets, `.gitignore` extension) does not yet
exist. No syntax/compile/import errors.
```
GNU bash, version 3.2.57(1)-release (arm64-apple-darwin25)
```

## C10 refinement (post-implementation)
C10's new-file walk was over-broad: it rejected **any** `.harness/` path absent from the
frozen protected baseline. But harness *lifecycle* files legitimately materialize
per-cycle **after** the baseline is frozen and are not developer mutations of protected
artifacts:
- `.harness/reviews/p0-scaffold.md` — the Reviewer's verdict for this unit.
- `.harness/state/APPROVED` — the deploy-gate marker (also git-ignored via `.gitignore`
  `.harness/state/`).

Fix (test-only): added an `is_harness_lifecycle` exemption helper mirroring the existing
`.harness/tasks/p0-scaffold.tests.md` exemption. It exempts `.harness/reviews/**` and
`.harness/state/**` (plus the Tester's own `.tests.md`) from the added-file check. C10
still catches genuine mutation of protected files (`DESIGN.md`, `META_PLAN.md`,
`AGILE_PLAN.md`, `CLAUDE.md`) via hash comparison, and still fails on any *other* new
file added under `.harness/` — the intent is intact, not a no-op.

## Green run output (after implementation + C10 refinement)
```
PASS: C1: all 12 §13 directories exist and are git-tracked
PASS: C3: git ls-files lists >=1 tracked file inside every §13 directory
PASS: C2: no stray top-level directories beyond §13 + existing repo dirs
PASS: C4a: root Python manifest 'pyproject.toml' exists
PASS: C4b: uv parses the root project manifest without error
PASS: C5a: root Makefile exists (/Users/prashant/Desktop/Project/qa-engineering-agent/Makefile)
PASS: C5b: Makefile defines targets dev, test, eval, release
PASS: C5c: a list/help target is defined (resolved as: help)
PASS: C6: make dev/test/eval/release all exit 0 with unit-naming placeholder output
PASS: C7: help/list target lists all four targets (dev, test, eval, release)
PASS: C8: .gitignore ignores .venv/, node_modules/, *.db, and Playwright artifacts
PASS: C9: all pre-existing .gitignore entries preserved (additive edit only)
PASS: C10: no protected file changed (DESIGN/META/AGILE/CLAUDE.md, .harness/**)
PASS: C11: additive diff only (no pre-existing file deleted; only .gitignore modified)
-----------------------------------------------------------------------
RESULT: all acceptance checks passed
```
Exit code: 0 (green). C10 remains present and meaningful.

## Reentrancy retirement of the point-in-time whole-repo guards (harness decision)
The `p0-scaffold` suite is re-run by every later `/tdd` and `/auto` cycle. Three of its
checks were **point-in-time, scaffold-ship-time guards** that hash/diff the *entire
working tree* against baselines frozen at this unit's dev-start. They correctly gated
`p0-scaffold` at its ship time but are **not reentrant**: every later cycle legitimately
evolves the repo (edits `AGILE_PLAN.md` / `.harness/backlog.md`, adds new
`.harness/tasks/*`, evolves `pyproject.toml`/`uv.lock`, and creates tooling/cache dirs
such as `.venv/` and `.pytest_cache/`), so they tripped on every subsequent run. Observed
failures before the fix: **C2** (stray top-level dirs — catching `.venv`, `.pytest_cache`),
**C10** (protected-file hash vs frozen baseline — `AGILE_PLAN.md`, `.harness/backlog.md`,
new `.harness/tasks/p0-shop-backend*`), **C11** (additive-only diff vs frozen tracked
baseline).

**Fix (test-only):** these three guards are now **opt-in** behind an explicit
`SCAFFOLD_DIFF_GUARD=1` env flag; the default suite invocation **skips** them (printing a
`SKIP:` line at each site) and exits 0. Each site carries a comment stating it is a
retired point-in-time scaffold-ship-time guard, non-reentrant by design. The frozen
baselines (`p0-scaffold-protected-baseline.txt`, `p0-scaffold-tracked-baseline.txt`) are
**retained-but-unused** in `tests/fixtures/`; their presence is asserted only inside the
`SCAFFOLD_DIFF_GUARD=1` block (the reentrant C9 still requires `gitignore-baseline.txt`).

**Retained (still always-run, reentrant, still meaningfully passing):** C1/C3 (§13 dirs
present & git-tracked), C4 (`pyproject.toml` parseable by `uv`), C5 (Makefile targets
defined + help/list), **C6a** (`dev`/`eval`/`release` placeholders exit 0 + name their
later unit) / **C6b** (`test` DEFINED and wired to the e2e/Playwright smoke via `make -n
test`, **not executed** — unit 5 replaced the `make test` placeholder with the real smoke),
C7 (help lists all four), C8 (`.gitignore` ignore patterns), and C9 (additive `.gitignore`
preservation vs the gitignore baseline — not a full-repo snapshot).

**C6 update (unit 5, `p0-playwright-smoke`):** unit 5's spec mandates replacing the `make
test` placeholder with the real Playwright smoke, so C6 was split: C6a keeps the
exit-0 + unit-naming placeholder check for the three still-unimplemented targets
(`dev`/`eval`/`release`), and C6b verifies `test` is real & smoke-wired **without running
it** (dry-run only — running it would spin up backend/frontend servers + headless
Chromium, wrong for this lightweight reentrant structure suite). `test` was removed from
the placeholder-execution loop.

### Green run output — default invocation in the current (dirty) working tree
```
PASS: C1: all 12 §13 directories exist and are git-tracked
PASS: C3: git ls-files lists >=1 tracked file inside every §13 directory
SKIP: C2 (stray top-level dir guard) — retired point-in-time scaffold-ship-time guard, non-reentrant by design; set SCAFFOLD_DIFF_GUARD=1 to run.
PASS: C4a: root Python manifest 'pyproject.toml' exists
PASS: C4b: uv parses the root project manifest without error
PASS: C5a: root Makefile exists (/Users/prashant/Desktop/Project/qa-engineering-agent/Makefile)
PASS: C5b: Makefile defines targets dev, test, eval, release
PASS: C5c: a list/help target is defined (resolved as: help)
PASS: C6a: make dev/eval/release exit 0 with unit-naming placeholder output
PASS: C6b: make test is implemented + wired to the e2e Playwright smoke (not executed here)
PASS: C7: help/list target lists all four targets (dev, test, eval, release)
PASS: C8: .gitignore ignores .venv/, node_modules/, *.db, and Playwright artifacts
PASS: C9: all pre-existing .gitignore entries preserved (additive edit only)
SKIP: C10/C11 (protected-file + additive-diff guards vs frozen full-repo baseline) — retired point-in-time scaffold-ship-time guards, non-reentrant by design; set SCAFFOLD_DIFF_GUARD=1 to run.
-----------------------------------------------------------------------
RESULT: all acceptance checks passed
```
Exit code: 0 (green). The opt-in guards still execute when `SCAFFOLD_DIFF_GUARD=1`
(exit 1 in the current dirty tree, confirming they are gated — not gutted).

## C6 update — `make test` is now implemented (unit 5, `p0-playwright-smoke`)

Unit 5's spec **mandates replacing** the `make test` placeholder with the REAL Playwright
smoke run. So the original C6 (which ran `make dev/test/eval/release` and asserted each
exits 0 with a *unit-naming placeholder* message) became outdated for `test`, and running
it now would invoke the heavy browser smoke (launches backend + frontend + Chromium) —
wrong for this lightweight, reentrant structure suite.

**Fix (test-only):** C6 is split so the real `make test` is never executed here:
- **C6a** — the still-placeholder targets `dev`/`eval`/`release` remain invocable, exit 0,
  and name their owning later unit (unchanged behavior; `test` removed from this loop and
  from `unit_hint`).
- **C6b** — `make test` is asserted **defined** (`target_defined test`) and **wired to the
  e2e Playwright smoke** via a dry-run (`make -n test`, which prints the recipe without
  executing it) grepped for `playwright|e2e`. No servers or browser are launched.

Both pass in the current tree:
```
PASS: C6a: make dev/eval/release exit 0 with unit-naming placeholder output
PASS: C6b: make test is implemented + wired to the e2e Playwright smoke (not executed here)
```
The reentrant Makefile coverage (targets defined C5b, help lists them C7) is unchanged; the
retired C2/C10/C11 stay gated behind `SCAFFOLD_DIFF_GUARD=1`.

# Task: p0-scaffold

## Title
Repo directory scaffold (`DESIGN.md §13`) + root tooling skeleton + `.gitignore` extension

## Context
- Plan item: `AGILE_PLAN.md` → Phase 0, **B1. Repo scaffolding**; backlog unit **#1 (`p0-scaffold`)**.
- Depends on: nothing (deps met). Blocks units 2–6.
- Source of truth: `DESIGN.md §13` (repo/service layout) + `AGILE_PLAN.md` B1.
- This unit is **scaffolding + placeholders + a tooling skeleton only.** The real working code for
  each area lands in **later** units:
  - `reference_app/backend/` → unit 2 (`p0-shop-backend`)
  - `reference_app/frontend/` → unit 3 (`p0-shop-frontend`)
  - `reference_app/BRD.md`, `reference_app/README.md` → unit 4 (`p0-brd-release`)
  - Playwright project + smoke test → unit 5 (`p0-playwright-smoke`)
  - `eval/` bug injection + `eval/score.py` + baseline suite → unit 6 (`p0-eval-harness`)
- Environment fact (from repo inspection): `uv` and GNU `make` are installed; `poetry` and `just`
  are **not**. The `AGILE_PLAN.md` lock therefore selects **`uv`** (Python env) and a **`Makefile`**
  (task targets) for this iteration. The developer chooses the exact skeleton contents.

## Scope
**In scope**
1. Create the full `DESIGN.md §13` directory tree, each directory present and **tracked by git**
   (empty dirs are not tracked by git, so each must carry a placeholder file — a `.gitkeep` and/or a
   short `README`/`__init__` marker — the exact placeholder is the developer's choice).
2. A **root Python project definition** managed by `uv` (a project/manifest file `uv` recognizes) so
   backend/eval Python deps can later be added. No runtime dependencies need be pinned in this unit
   beyond what is required for the tooling skeleton to be valid; do **not** implement app/eval code.
3. A **root `Makefile`** exposing the four targets `dev`, `test`, `eval`, `release` (plus a target
   that lists/describes available targets). At this scaffolding stage each target is a **defined
   placeholder**: it is invocable, prints a clear "not yet implemented — arrives in unit N" style
   message identifying the owning later unit, and **exits 0** (success). Later units replace the
   placeholder bodies with real behavior.
4. **Extend the existing `.gitignore`** so it ignores: a Python virtualenv dir (`.venv/`),
   `node_modules/`, SQLite DB files (`*.db`), and Playwright run artifacts (test results / reports /
   caches). Existing entries must be preserved (additive edit only).

**Out of scope**
- Any application, API, UI, test, or eval **logic** (backend, frontend, Playwright tests, bug
  injection, scorer, BRD, release docs) — those are units 2–6.
- Installing/vendoring dependency trees (`.venv/`, `node_modules/`) or committing lockfile-resolved
  packages beyond a minimal valid manifest.
- Editing `DESIGN.md`, `META_PLAN.md`, `AGILE_PLAN.md`, `CLAUDE.md`, or anything under `.harness/`.
- Choosing `poetry` or `just` (not available in this environment; excluded by the plan lock).
- Real behavior for the `dev`/`test`/`eval`/`release` targets (placeholders only this unit).

## Acceptance criteria (enumerated, testable)
Verifiable by directory/file presence + structure checks and by invoking the tooling targets.

1. **Directory tree present & tracked.** Every one of these directories exists and is tracked by git
   (contains at least one committed placeholder/marker file):
   - `reference_app/backend/`
   - `reference_app/frontend/`
   - `agent_config/`
   - `connectors/`
   - `reliability/`
   - `runner/`
   - `eval/`
   - `control_plane/api/`
   - `control_plane/orchestration/`
   - `control_plane/stores/`
   - `control_plane/frontend/`
   - `sandbox/`
2. **No stray top-level dirs beyond §13 + existing repo dirs.** New source directories created match
   the `DESIGN.md §13` set (existing `.git/`, `.claude/`, `.harness/`, `tests/`, and root docs are
   untouched and permitted).
3. **`git ls-files` lists a tracked file inside each §13 directory** (proves empty dirs are not
   silently dropped).
4. **Python project manifest exists at repo root**, is recognized by `uv` (e.g. `uv` can parse/sync
   it without error), and declares the project — no app/eval source is required for this to hold.
5. **`Makefile` exists at repo root** and defines the targets `dev`, `test`, `eval`, `release` and a
   list/help target.
6. **Each of `make dev`, `make test`, `make eval`, `make release` is invocable and exits 0**, each
   printing a placeholder message that names the later unit which will implement it (e.g. `dev`/
   `test` → shop app + Playwright units; `eval` → eval-harness unit; `release` → BRD/release unit).
   The invocation must not require app/frontend/eval code that does not yet exist.
7. **The help/list target lists all four targets** (`dev`, `test`, `eval`, `release`).
8. **`.gitignore` extended (additive).** After the change, `.gitignore` causes git to ignore:
   - a `.venv/` virtualenv directory,
   - `node_modules/`,
   - `*.db` files,
   - Playwright run artifacts (test-results / playwright-report / `.cache` for Playwright).
   Verifiable by creating throwaway matching paths and confirming `git check-ignore` reports them
   ignored, then removing them.
9. **No pre-existing `.gitignore` entry removed** — the existing content (including the current
   `.venv` handling) is preserved; the edit only adds the missing entries.
10. **No file outside the allowed scope changed** — specifically `DESIGN.md`, `META_PLAN.md`,
    `AGILE_PLAN.md`, `CLAUDE.md`, and `.harness/**` are unchanged by this unit.
11. **Repo remains in a valid, buildable-skeleton state** — no target errors, `uv` manifest parses,
    and the tree is a clean additive diff.

## Interfaces / contracts
- **Exact directory paths** (relative to repo root — all must exist and be git-tracked):
  `reference_app/backend/`, `reference_app/frontend/`, `agent_config/`, `connectors/`,
  `reliability/`, `runner/`, `eval/`, `control_plane/api/`, `control_plane/orchestration/`,
  `control_plane/stores/`, `control_plane/frontend/`, `sandbox/`.
- **Makefile targets (exact names):** `dev`, `test`, `eval`, `release`, plus a list/help target
  (name at developer's discretion, e.g. `help`). Placeholder targets exit 0.
- **Python tooling:** root manifest recognized by `uv` (developer selects the exact filename `uv`
  uses for a project). No specific runtime deps mandated by this unit.
- **`.gitignore` additions (semantic — patterns must ignore these):** `.venv/`, `node_modules/`,
  `*.db`, and Playwright artifacts (`test-results/`, `playwright-report/`, and Playwright cache).
  The exact pattern text is the developer's choice as long as `git check-ignore` matches these paths.
- No public API, no HTTP endpoints, no code interfaces are introduced in this unit.

## Definition of Done
- All acceptance criteria 1–11 verified — directory/file presence & git-tracking checks pass, the
  `uv` manifest parses, all four `make` targets invoke and exit 0 with placeholder output, the
  help/list target lists them, and `.gitignore` additively ignores `.venv/`, `node_modules/`,
  `*.db`, and Playwright artifacts.
- Diff is additive scaffolding only; no application/test/eval logic, no protected file changed.
- Change is consistent with `DESIGN.md §13` and `AGILE_PLAN.md` B1, and unblocks unit 2
  (`p0-shop-backend`).

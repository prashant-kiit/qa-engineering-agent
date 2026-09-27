#!/usr/bin/env bash
# Acceptance test for unit `p0-scaffold`.
# Scaffolding + tooling-skeleton unit: DESIGN.md §13 directory tree, uv Python
# manifest, root Makefile placeholder targets, and additive .gitignore extension.
# Each acceptance criterion (1-11) from .harness/tasks/p0-scaffold.md is asserted below.
#
# Runnable: `bash tests/scaffold/p0-scaffold.test.sh` (exit 0 = all pass, exit 1 = any fail).
# No framework dependency (this unit precedes the Playwright setup, which is unit 5).

set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT" || { echo "SCAFFOLD ERROR: cannot cd to repo root $REPO_ROOT"; exit 2; }

FIX_DIR="$REPO_ROOT/tests/fixtures"
GITIGNORE_BASELINE="$FIX_DIR/gitignore-baseline.txt"
# Frozen pre-developer snapshots (captured by the Tester before implementation starts),
# so C10/C11 attribute changes to THIS unit's developer work only — not to the TPM's
# plan-lock edits (AGILE_PLAN.md / .harness/backlog.md) that predate development.
PROTECTED_BASELINE="$FIX_DIR/p0-scaffold-protected-baseline.txt"   # hash<TAB>path
TRACKED_BASELINE="$FIX_DIR/p0-scaffold-tracked-baseline.txt"       # hash<TAB>path

FAILS=0
pass() { printf 'PASS: %s\n' "$1"; }
fail() { printf 'FAIL: %s\n' "$1"; FAILS=$((FAILS + 1)); }

# --- scaffolding sanity (must be healthy so failures below are legitimate) ---
if ! command -v git >/dev/null 2>&1; then
  echo "SCAFFOLD ERROR: git not on PATH"; exit 2
fi
# Only the gitignore baseline is required by the always-run suite (reentrant C9).
# The frozen full-repo snapshots (PROTECTED_BASELINE / TRACKED_BASELINE) are used
# ONLY by the retired, opt-in point-in-time diff guards (C2-stray / C10 / C11); their
# presence is asserted inside the SCAFFOLD_DIFF_GUARD block, not here.
if [[ ! -f "$GITIGNORE_BASELINE" ]]; then
  echo "SCAFFOLD ERROR: baseline fixture missing at $GITIGNORE_BASELINE"; exit 2
fi
if ! command -v make >/dev/null 2>&1; then
  echo "SCAFFOLD ERROR: 'make' not installed (required by the plan lock)"; exit 2
fi
if ! command -v uv >/dev/null 2>&1; then
  echo "SCAFFOLD ERROR: 'uv' not installed (required by the plan lock)"; exit 2
fi

# The exact DESIGN.md §13 directory set (interface contract from the spec).
SEC13_DIRS=(
  "reference_app/backend"
  "reference_app/frontend"
  "agent_config"
  "connectors"
  "reliability"
  "runner"
  "eval"
  "control_plane/api"
  "control_plane/orchestration"
  "control_plane/stores"
  "control_plane/frontend"
  "sandbox"
)

# ---------------------------------------------------------------------------
# Criterion 1: Directory tree present & tracked. Every §13 directory exists and
# is tracked by git (contains >=1 committed/staged placeholder/marker file).
# ---------------------------------------------------------------------------
c1_fails=0
for d in "${SEC13_DIRS[@]}"; do
  if [[ ! -d "$REPO_ROOT/$d" ]]; then
    c1_fails=$((c1_fails + 1)); printf '       missing directory: %s\n' "$d"; continue
  fi
  # tracked = git ls-files reports at least one file under the dir
  if [[ -z "$(git ls-files -- "$d" 2>/dev/null)" ]]; then
    c1_fails=$((c1_fails + 1)); printf '       directory not git-tracked (no placeholder file): %s\n' "$d"
  fi
done
if [[ "$c1_fails" -eq 0 ]]; then
  pass "C1: all 12 §13 directories exist and are git-tracked"
else
  fail "C1: $c1_fails §13 director(y/ies) missing or untracked"
fi

# ---------------------------------------------------------------------------
# Criterion 3: `git ls-files` lists a tracked file inside each §13 directory.
# (Explicit restatement of the tracking guarantee; proves empty dirs not dropped.)
# ---------------------------------------------------------------------------
c3_fails=0
for d in "${SEC13_DIRS[@]}"; do
  n="$(git ls-files -- "$d" 2>/dev/null | grep -c .)"
  if [[ "$n" -lt 1 ]]; then
    c3_fails=$((c3_fails + 1)); printf '       no tracked file under: %s\n' "$d"
  fi
done
if [[ "$c3_fails" -eq 0 ]]; then
  pass "C3: git ls-files lists >=1 tracked file inside every §13 directory"
else
  fail "C3: $c3_fails §13 director(y/ies) have no tracked file"
fi

# ---------------------------------------------------------------------------
# Criterion 2: No stray top-level source dirs beyond §13 + existing repo dirs.
#
# RETIRED FROM THE ALWAYS-RUN SUITE (harness decision).
# This is a point-in-time, scaffold-ship-time whole-repo guard: it enumerates the
# entire working tree's top-level dirs and rejects anything not on a frozen allow-list.
# It is NOT reentrant — every later cycle legitimately introduces new top-level dirs
# (tooling/cache dirs like .venv/ / .pytest_cache/, and future §13-adjacent additions),
# which would trip it forever. It gated p0-scaffold correctly at ship time only.
# Now opt-in: runs only when SCAFFOLD_DIFF_GUARD=1. The reentrant structural coverage
# (required §13 dirs present & tracked) lives in C1/C3 and still runs unconditionally.
# ---------------------------------------------------------------------------
if [[ "${SCAFFOLD_DIFF_GUARD:-0}" == "1" ]]; then
  ALLOWED_TOP=(
    # §13 top-level roots
    "reference_app" "agent_config" "connectors" "reliability" "runner" "eval"
    "control_plane" "sandbox"
    # pre-existing / permitted repo dirs
    ".git" ".claude" ".harness" "tests"
  )
  is_allowed_top() {
    local x="$1"
    for a in "${ALLOWED_TOP[@]}"; do [[ "$x" == "$a" ]] && return 0; done
    return 1
  }
  c2_fails=0
  while IFS= read -r entry; do
    entry="${entry%/}"
    [[ -z "$entry" ]] && continue
    if ! is_allowed_top "$entry"; then
      c2_fails=$((c2_fails + 1)); printf '       stray top-level directory: %s\n' "$entry"
    fi
  done < <(find "$REPO_ROOT" -mindepth 1 -maxdepth 1 -type d -exec basename {} \;)
  if [[ "$c2_fails" -eq 0 ]]; then
    pass "C2: no stray top-level directories beyond §13 + existing repo dirs"
  else
    fail "C2: $c2_fails stray top-level director(y/ies) present"
  fi
else
  printf 'SKIP: C2 (stray top-level dir guard) — retired point-in-time scaffold-ship-time guard, non-reentrant by design; set SCAFFOLD_DIFF_GUARD=1 to run.\n'
fi

# ---------------------------------------------------------------------------
# Criterion 4: Python project manifest at repo root, recognized/parseable by uv.
# ---------------------------------------------------------------------------
if [[ -f "$REPO_ROOT/pyproject.toml" ]]; then
  pass "C4a: root Python manifest 'pyproject.toml' exists"
else
  fail "C4a: root Python manifest 'pyproject.toml' missing"
fi
# uv must be able to parse the project without error. `uv lock --dry-run` reads &
# resolves the manifest without mutating the tree; a valid project => exit 0.
UV_OUT="$(cd "$REPO_ROOT" && uv lock --check 2>&1)"; UV_RC=$?
if [[ "$UV_RC" -ne 0 ]]; then
  # `uv lock --check` fails when no lock exists yet; fall back to a pure parse via
  # `uv tree`, which still requires a parseable project manifest.
  UV_OUT="$(cd "$REPO_ROOT" && uv tree 2>&1)"; UV_RC=$?
fi
if [[ "$UV_RC" -eq 0 ]]; then
  pass "C4b: uv parses the root project manifest without error"
else
  fail "C4b: uv failed to parse root project manifest (rc=$UV_RC): ${UV_OUT}"
fi

# ---------------------------------------------------------------------------
# Criterion 5: root Makefile exists and defines dev/test/eval/release + a help target.
# ---------------------------------------------------------------------------
MAKEFILE=""
for m in Makefile makefile GNUmakefile; do
  [[ -f "$REPO_ROOT/$m" ]] && { MAKEFILE="$REPO_ROOT/$m"; break; }
done
if [[ -n "$MAKEFILE" ]]; then
  pass "C5a: root Makefile exists ($MAKEFILE)"
else
  fail "C5a: root Makefile missing"
fi

# `make -qp`-independent presence check: query the target list via dry-run per target.
target_defined() {
  # exit 0 if `make <t>` is a known target (dry-run resolves without 'No rule' error)
  local t="$1"
  local out
  out="$(cd "$REPO_ROOT" && make -n "$t" 2>&1)"
  local rc=$?
  if [[ $rc -ne 0 ]] && printf '%s' "$out" | grep -qiE "no rule to make target"; then
    return 1
  fi
  return 0
}
c5_missing=0
for t in dev test eval release; do
  if ! target_defined "$t"; then
    c5_missing=$((c5_missing + 1)); printf '       Makefile target not defined: %s\n' "$t"
  fi
done
if [[ "$c5_missing" -eq 0 ]]; then
  pass "C5b: Makefile defines targets dev, test, eval, release"
else
  fail "C5b: $c5_missing required Makefile target(s) undefined"
fi
# a list/help target must exist (name at developer's discretion; try common names)
HELP_TARGET=""
for h in help list targets; do
  if target_defined "$h"; then HELP_TARGET="$h"; break; fi
done
# also accept the default target (bare `make`) as the help/list surface
if [[ -z "$HELP_TARGET" ]]; then
  if (cd "$REPO_ROOT" && make -n >/dev/null 2>&1); then HELP_TARGET="__default__"; fi
fi
if [[ -n "$HELP_TARGET" ]]; then
  pass "C5c: a list/help target is defined (resolved as: $HELP_TARGET)"
else
  fail "C5c: no list/help target defined (tried help/list/targets/default)"
fi

# ---------------------------------------------------------------------------
# Criterion 6: each of make dev/test/eval/release is invocable, exits 0, and
# prints a placeholder message naming the later unit that will implement it.
# ---------------------------------------------------------------------------
# per-target regex naming the later unit that will implement the placeholder
unit_hint() {
  case "$1" in
    dev|test) printf '%s' "p0-(shop-(backend|frontend)|playwright-smoke)|unit ?[2-5]" ;;
    eval)     printf '%s' "p0-eval-harness|unit ?6" ;;
    release)  printf '%s' "p0-brd-release|unit ?4" ;;
  esac
}
c6_fails=0
for t in dev test eval release; do
  out="$(cd "$REPO_ROOT" && make "$t" 2>&1)"; rc=$?
  if [[ $rc -ne 0 ]]; then
    c6_fails=$((c6_fails + 1)); printf '       make %s exited %d (expected 0)\n' "$t" "$rc"; continue
  fi
  # must print a not-yet-implemented style placeholder that names the owning later unit
  if ! printf '%s' "$out" | grep -qiE "$(unit_hint "$t")"; then
    c6_fails=$((c6_fails + 1))
    printf '       make %s output does not name its later unit; got: %s\n' "$t" "$out"
  fi
done
if [[ "$c6_fails" -eq 0 ]]; then
  pass "C6: make dev/test/eval/release all exit 0 with unit-naming placeholder output"
else
  fail "C6: $c6_fails target(s) failed exit-0 + placeholder-message check"
fi

# ---------------------------------------------------------------------------
# Criterion 7: the help/list target lists all four targets.
# ---------------------------------------------------------------------------
if [[ -n "${HELP_TARGET:-}" ]]; then
  if [[ "$HELP_TARGET" == "__default__" ]]; then
    help_out="$(cd "$REPO_ROOT" && make 2>&1)"
  else
    help_out="$(cd "$REPO_ROOT" && make "$HELP_TARGET" 2>&1)"
  fi
  c7_missing=0
  for t in dev test eval release; do
    printf '%s' "$help_out" | grep -qE "\b${t}\b" || { c7_missing=$((c7_missing + 1)); printf '       help output omits target: %s\n' "$t"; }
  done
  if [[ "$c7_missing" -eq 0 ]]; then
    pass "C7: help/list target lists all four targets (dev, test, eval, release)"
  else
    fail "C7: help/list target omits $c7_missing target name(s)"
  fi
else
  fail "C7: no help/list target available to verify listing"
fi

# ---------------------------------------------------------------------------
# Criterion 8: .gitignore additively ignores .venv/, node_modules/, *.db, and
# Playwright artifacts (test-results/, playwright-report/, Playwright .cache).
# Verified by creating throwaway matching paths and confirming git check-ignore.
# ---------------------------------------------------------------------------
declare -a MUST_IGNORE=(
  ".venv/"
  "node_modules/"
  "some-database.db"
  "test-results/"
  "playwright-report/"
)
c8_fails=0
for p in "${MUST_IGNORE[@]}"; do
  if ! git check-ignore -q "$p"; then
    c8_fails=$((c8_fails + 1)); printf '       path NOT ignored by .gitignore: %s\n' "$p"
  fi
done
# Playwright cache: accept either a dedicated .cache or a Playwright cache path.
if git check-ignore -q ".cache/" || git check-ignore -q "test-results/.cache/" || git check-ignore -q "playwright/.cache/"; then
  : # ok
else
  c8_fails=$((c8_fails + 1)); printf '       Playwright cache path NOT ignored\n'
fi
if [[ "$c8_fails" -eq 0 ]]; then
  pass "C8: .gitignore ignores .venv/, node_modules/, *.db, and Playwright artifacts"
else
  fail "C8: $c8_fails required ignore pattern(s) not matched by .gitignore"
fi

# ---------------------------------------------------------------------------
# Criterion 9: no pre-existing .gitignore entry removed (additive edit only).
# Every non-blank line from the baseline snapshot must still be present.
# ---------------------------------------------------------------------------
c9_missing=0
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  if ! grep -Fqx -- "$line" "$REPO_ROOT/.gitignore"; then
    c9_missing=$((c9_missing + 1)); printf '       removed pre-existing .gitignore line: %s\n' "$line"
  fi
done < "$GITIGNORE_BASELINE"
if [[ "$c9_missing" -eq 0 ]]; then
  pass "C9: all pre-existing .gitignore entries preserved (additive edit only)"
else
  fail "C9: $c9_missing pre-existing .gitignore line(s) removed"
fi

# ---------------------------------------------------------------------------
# Criterion 10 & 11: point-in-time, whole-repo diff guards vs frozen full-repo
# baselines captured at p0-scaffold's dev-start.
#
# RETIRED FROM THE ALWAYS-RUN SUITE (harness decision).
# C10 (protected-file hash-compare) and C11 (additive-only tracked-file diff) both
# compare the ENTIRE working tree against snapshots frozen when p0-scaffold began
# development. They correctly gated that one unit at ship time, but they are NOT
# reentrant: every later cycle legitimately edits AGILE_PLAN.md / .harness/backlog.md,
# adds new .harness/tasks/*, evolves pyproject.toml / uv.lock, etc. — so they trip on
# every subsequent run forever. Now opt-in: run only when SCAFFOLD_DIFF_GUARD=1.
# The frozen baselines are RETAINED in tests/fixtures/ but consumed only here.
# ---------------------------------------------------------------------------
if [[ "${SCAFFOLD_DIFF_GUARD:-0}" == "1" ]]; then
for bl in "$PROTECTED_BASELINE" "$TRACKED_BASELINE"; do
  if [[ ! -f "$bl" ]]; then
    echo "SCAFFOLD ERROR: baseline fixture missing at $bl (required by SCAFFOLD_DIFF_GUARD=1)"; exit 2
  fi
done

# --- Criterion 10: no protected file changed by this unit's development
# (DESIGN.md, META_PLAN.md, AGILE_PLAN.md, CLAUDE.md, and .harness/**).
c10_fails=0
while IFS=$'\t' read -r base_hash rel; do
  [[ -z "$rel" ]] && continue
  if [[ ! -f "$REPO_ROOT/$rel" ]]; then
    c10_fails=$((c10_fails + 1)); printf '       protected file deleted: %s\n' "$rel"; continue
  fi
  cur_hash="$(git hash-object "$REPO_ROOT/$rel" 2>/dev/null)"
  if [[ "$cur_hash" != "$base_hash" ]]; then
    c10_fails=$((c10_fails + 1)); printf '       protected file modified: %s\n' "$rel"
  fi
done < "$PROTECTED_BASELINE"
# detect newly-added files under .harness/ not present in the snapshot.
# Harness *lifecycle* files legitimately materialize per-cycle AFTER the baseline
# is frozen — they are NOT developer mutations of protected artifacts, so they are
# exempt (mirrors the .tests.md exemption). Everything else new under .harness/
# (i.e. tampering with pre-existing protected content) still fails C10.
is_harness_lifecycle() {
  case "$1" in
    # the Tester's own coverage artifact is a harness process file
    .harness/tasks/p0-scaffold.tests.md) return 0 ;;
    # the Reviewer's verdict for this unit, written during the review phase
    .harness/reviews/*) return 0 ;;
    # deploy-gate markers (git-ignored via .gitignore `.harness/state/`)
    .harness/state/*) return 0 ;;
    *) return 1 ;;
  esac
}
while IFS= read -r hf; do
  [[ -z "$hf" ]] && continue
  rel="${hf#"$REPO_ROOT"/}"
  is_harness_lifecycle "$rel" && continue
  if ! grep -qF -- "	$rel" "$PROTECTED_BASELINE"; then
    c10_fails=$((c10_fails + 1)); printf '       new file added under .harness/: %s\n' "$rel"
  fi
done < <(find "$REPO_ROOT/.harness" -type f 2>/dev/null)
if [[ "$c10_fails" -eq 0 ]]; then
  pass "C10: no protected file changed (DESIGN/META/AGILE/CLAUDE.md, .harness/**)"
else
  fail "C10: $c10_fails protected file/area changed by this unit"
fi

# --- Criterion 11: repo remains a valid buildable skeleton — additive diff only.
# Against the frozen tracked-file snapshot: no pre-existing tracked file may be
# deleted, and the only pre-existing file whose content may differ is .gitignore.
# Scaffold files are NEW paths (absent from the snapshot) and are allowed additions.
# uv-parse (C4) and target exit-0 (C6) already assert the skeleton is invocable.
c11_fails=0
while IFS=$'\t' read -r base_hash rel; do
  [[ -z "$rel" ]] && continue
  if [[ ! -e "$REPO_ROOT/$rel" ]]; then
    c11_fails=$((c11_fails + 1)); printf '       pre-existing tracked file deleted: %s\n' "$rel"; continue
  fi
  cur_hash="$(git hash-object "$REPO_ROOT/$rel" 2>/dev/null)"
  if [[ "$cur_hash" != "$base_hash" ]]; then
    case "$rel" in
      .gitignore) : ;;  # the one permitted (additive) modification
      *) c11_fails=$((c11_fails + 1)); printf '       non-additive modification to pre-existing file: %s\n' "$rel" ;;
    esac
  fi
done < "$TRACKED_BASELINE"
if [[ "$c11_fails" -eq 0 ]]; then
  pass "C11: additive diff only (no pre-existing file deleted; only .gitignore modified)"
else
  fail "C11: $c11_fails non-additive change(s) detected"
fi
else
  printf 'SKIP: C10/C11 (protected-file + additive-diff guards vs frozen full-repo baseline) — retired point-in-time scaffold-ship-time guards, non-reentrant by design; set SCAFFOLD_DIFF_GUARD=1 to run.\n'
fi

echo "-----------------------------------------------------------------------"
if [[ "$FAILS" -eq 0 ]]; then
  echo "RESULT: all acceptance checks passed"
  exit 0
else
  echo "RESULT: $FAILS acceptance check(s) failed"
  exit 1
fi

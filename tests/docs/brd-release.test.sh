#!/usr/bin/env bash
# Presence/structure test for unit `p0-brd-release`.
# Doc + documented-convention acceptance: a freeform reference-shop BRD, a top-level
# reference_app README documenting the release convention, and a machine-readable VERSION marker.
# Each acceptance criterion (1-20) from .harness/tasks/p0-brd-release.md is asserted below via
# presence / structure / grep checks (no code executed).
#
# Runnable: `bash tests/docs/brd-release.test.sh` (exit 0 = all pass, exit 1 = any fail,
# exit 2 = scaffolding error). No framework dependency (matches tests/docs/design-note.test.sh).

set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REFAPP="$REPO_ROOT/reference_app"
BRD="$REFAPP/BRD.md"
README="$REFAPP/README.md"
VERSION_FILE="$REFAPP/VERSION"
FIX_DIR="$REPO_ROOT/tests/fixtures"
README_BASELINE="$FIX_DIR/p0-brd-release-readme-baseline.sha256"
PROTECTED_BASELINE="$FIX_DIR/p0-brd-release-protected-baseline.sha256"

FAILS=0
pass() { printf 'PASS: %s\n' "$1"; }
fail() { printf 'FAIL: %s\n' "$1"; FAILS=$((FAILS + 1)); }

# --- scaffolding sanity (must be healthy so failures below are legitimate red) ---
if [[ ! -d "$REFAPP" ]]; then
  echo "SCAFFOLD ERROR: reference_app/ not found at $REFAPP"; exit 2
fi
# The frozen baseline fixtures + pre-existing sub-READMEs are consumed ONLY by the
# retired, opt-in point-in-time diff guards (C19/C20); their presence is asserted inside
# the BRD_DIFF_GUARD block, not here, so the always-run content suite (C1-C18) stays
# independent of them.

# case-insensitive extended-regex grep against a file (safe if file missing).
file_has() { [[ -f "$1" ]] && grep -qiE "$2" "$1"; }

# ===========================================================================
# BRD -- reference_app/BRD.md  (criteria 1-9)
# ===========================================================================

# Criterion 1: BRD.md exists and is non-empty.
if [[ -f "$BRD" && -s "$BRD" ]]; then
  pass "C1: reference_app/BRD.md exists and is non-empty"
else
  fail "C1: reference_app/BRD.md exists and is non-empty"
fi

# Criterion 2: prose/freeform -- contains NO fenced code blocks (```), i.e. no source/OpenAPI/test
# code dump. (A well-formed prose BRD has zero triple-backtick fences.)
if [[ -f "$BRD" ]]; then
  fences="$(grep -cE '^[[:space:]]*```' "$BRD" || true)"
  if [[ "$fences" -eq 0 ]]; then
    pass "C2: BRD is prose/freeform (no fenced code blocks)"
  else
    fail "C2: BRD contains $fences fenced-code-block delimiter line(s) (should be prose only)"
  fi
else
  fail "C2: BRD is prose/freeform (no fenced code blocks) -- file missing"
fi

# Criterion 3: authentication flow -- sign in with credentials; valid grant / invalid rejected.
if file_has "$BRD" '(sign[ -]?in|log[ -]?in|authenticat)' \
   && file_has "$BRD" 'credential' \
   && file_has "$BRD" '(invalid|incorrect|wrong|reject|denied|unauthori)'; then
  pass "C3: BRD describes authentication (sign-in w/ credentials, invalid rejected)"
else
  fail "C3: BRD describes authentication (sign-in w/ credentials, invalid rejected)"
fi

# Criterion 4: products -- a catalog of products, each with a name and a price.
if file_has "$BRD" 'product' \
   && file_has "$BRD" '(catalog|browse|list)' \
   && file_has "$BRD" 'price'; then
  pass "C4: BRD describes products (catalog with name & price)"
else
  fail "C4: BRD describes products (catalog with name & price)"
fi

# Criterion 5: cart / add-to-cart -- adding the same product again increases quantity cumulatively.
if file_has "$BRD" 'cart' \
   && file_has "$BRD" '(add|adding)' \
   && file_has "$BRD" 'quantit' \
   && file_has "$BRD" '(cumulativ|increase|increment|adds? to|sum|accumulat|existing)'; then
  pass "C5: BRD describes cart / add-to-cart with cumulative quantity"
else
  fail "C5: BRD describes cart / add-to-cart with cumulative quantity"
fi

# Criterion 6: checkout -- non-empty cart -> order created; empty-cart checkout not allowed.
if file_has "$BRD" 'checkout|check out' \
   && file_has "$BRD" 'empty' \
   && file_has "$BRD" '(not allowed|cannot|can.?t|reject|forbidden|prevent|disallow|refuse)'; then
  pass "C6: BRD describes checkout (empty cart not allowed -> creates order)"
else
  fail "C6: BRD describes checkout (empty cart not allowed -> creates order)"
fi

# Criterion 7: orders -- an order can be retrieved afterward and reflects the purchased items.
if file_has "$BRD" 'order' \
   && file_has "$BRD" '(retriev|view|fetch|look ?up|history|confirmation|afterward|later)' \
   && file_has "$BRD" '(item|line|product)'; then
  pass "C7: BRD describes orders (retrievable, reflects purchased items)"
else
  fail "C7: BRD describes orders (retrievable, reflects purchased items)"
fi

# Criterion 8: order-total rule -- sum over lines of price * quantity; order total == cart total.
if file_has "$BRD" 'total' \
   && file_has "$BRD" 'price' \
   && file_has "$BRD" 'quantit' \
   && file_has "$BRD" '(sum|times|multipl|per line|each line|line item|\*|x quantity)'; then
  pass "C8: BRD describes order-total rule (sum of price * quantity)"
else
  fail "C8: BRD describes order-total rule (sum of price * quantity)"
fi

# Criterion 9: consistency with shipped app -- the two behaviors that could contradict the backend
# (cumulative add + empty-cart rejection) are stated the way the backend contract pins them.
# (Positive structural proxy: both invariants must be present & phrased consistently.)
if file_has "$BRD" '(cumulativ|increase|increment|accumulat|adds? to (the )?existing)' \
   && file_has "$BRD" 'empty' \
   && file_has "$BRD" '(not allowed|cannot|can.?t|reject|forbidden|prevent|disallow|refuse)'; then
  pass "C9: BRD is consistent w/ backend (cumulative-add & empty-cart-rejection invariants present)"
else
  fail "C9: BRD is consistent w/ backend (cumulative-add & empty-cart-rejection invariants present)"
fi

# ===========================================================================
# Release README -- reference_app/README.md  (criteria 10-15)
# ===========================================================================

# Criterion 10: README.md exists and is non-empty.
if [[ -f "$README" && -s "$README" ]]; then
  pass "C10: reference_app/README.md exists and is non-empty"
else
  fail "C10: reference_app/README.md exists and is non-empty"
fi

# Criterion 11: a clearly identifiable heading about releases / versioning.
if [[ -f "$README" ]] && grep -qiE '^#{1,6}[[:space:]].*(release|version)' "$README"; then
  pass "C11: README has a release/versioning section heading"
else
  fail "C11: README has a release/versioning section heading"
fi

# Criterion 12: names the version marker -- exact location (reference_app/VERSION) AND format
# (MAJOR.MINOR.PATCH semver).
if file_has "$README" 'VERSION' \
   && file_has "$README" '(MAJOR\.MINOR\.PATCH|semantic version|semver|[0-9]+\.[0-9]+\.[0-9]+)'; then
  pass "C12: README names the version marker location (VERSION) + format (semver)"
else
  fail "C12: README names the version marker location (VERSION) + format (semver)"
fi

# Criterion 13: documents the git tag scheme refapp-v<MAJOR.MINOR.PATCH>.
if file_has "$README" 'refapp-v'; then
  pass "C13: README documents the git tag scheme 'refapp-v<...>'"
else
  fail "C13: README documents the git tag scheme 'refapp-v<...>'"
fi

# Criterion 14: explains how a release yields a code+BRD diff (two releases compared).
if file_has "$README" 'diff' \
   && file_has "$README" '(between|compar|two releases|previous release|prior release|from that release)'; then
  pass "C14: README explains how two releases yield a code+BRD diff"
else
  fail "C14: README explains how two releases yield a code+BRD diff"
fi

# Criterion 15: references BRD.md as part of the release bundle (BRD released alongside code).
if file_has "$README" 'BRD' \
   && file_has "$README" '(bundle|together with|alongside|includes|part of (the )?release|code[ +]*(and|&|\+)[ ]*BRD|BRD[ ]*(and|&|\+)[ ]*code)'; then
  pass "C15: README references BRD.md as part of the release bundle (code + BRD)"
else
  fail "C15: README references BRD.md as part of the release bundle (code + BRD)"
fi

# ===========================================================================
# Version marker -- reference_app/VERSION  (criteria 16-18)
# ===========================================================================

# Criterion 16: VERSION exists at the pinned path.
if [[ -f "$VERSION_FILE" ]]; then
  pass "C16: reference_app/VERSION exists at the pinned path"
else
  fail "C16: reference_app/VERSION exists at the pinned path"
fi

# Criterion 17: content is a SINGLE semver line MAJOR.MINOR.PATCH (digits & dots only).
# Exactly one non-empty line, matching ^[0-9]+\.[0-9]+\.[0-9]+$ (trailing newline allowed).
VER_STR=""
if [[ -f "$VERSION_FILE" ]]; then
  nonempty_lines="$(grep -cE '[^[:space:]]' "$VERSION_FILE" || true)"
  first_line="$(grep -m1 -E '[^[:space:]]' "$VERSION_FILE" | tr -d '[:space:]')"
  if [[ "$nonempty_lines" -eq 1 && "$first_line" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    VER_STR="$first_line"
    pass "C17: VERSION is a single semver line ($first_line)"
  else
    fail "C17: VERSION must be a single 'MAJOR.MINOR.PATCH' line (found ${nonempty_lines} non-empty line(s): '${first_line}')"
  fi
else
  fail "C17: VERSION is a single semver line -- file missing"
fi

# Criterion 18: the version string in VERSION is documented consistently in README.
if [[ -n "$VER_STR" ]]; then
  if grep -qF -- "$VER_STR" "$README" 2>/dev/null; then
    pass "C18: README documents the same version string as VERSION ($VER_STR)"
  else
    fail "C18: README does not mention the VERSION value '$VER_STR'"
  fi
else
  fail "C18: cannot verify README/VERSION consistency (VERSION not a valid semver)"
fi

# ===========================================================================
# No regressions  (criteria 19-20)
#
# RETIRED FROM THE ALWAYS-RUN SUITE (harness decision) — mirrors the p0-scaffold suite's
# SCAFFOLD_DIFF_GUARD treatment. C19 (sub-README hash-compare) and C20 (protected-doc +
# backend/frontend source hash-compare) are point-in-time diff guards against baselines
# frozen at this unit's dev-start. They correctly gated p0-brd-release at ship time, but
# they are NOT reentrant: every later /tdd|/auto cycle legitimately mutates harness-managed
# protected files (the TPM's plan-lock edits AGILE_PLAN.md; .harness/** evolves), so a
# frozen whole-set hash-compare trips on every subsequent run forever. Now opt-in: they run
# only when BRD_DIFF_GUARD=1; the default invocation SKIPs them (printing a SKIP: line) and
# stays green. The genuinely-reentrant BRD/README/VERSION content & structure checks
# (C1-C18) always run. Gated, not gutted — BRD_DIFF_GUARD=1 fully executes them.
# ===========================================================================
if [[ "${BRD_DIFF_GUARD:-0}" == "1" ]]; then
  # baseline fixtures + pre-existing sub-READMEs must exist for a meaningful guard run.
  if [[ ! -f "$README_BASELINE" || ! -f "$PROTECTED_BASELINE" ]]; then
    echo "SCAFFOLD ERROR: baseline fixtures missing under $FIX_DIR (required by BRD_DIFF_GUARD=1)"; exit 2
  fi
  if [[ ! -f "$REFAPP/backend/README.md" || ! -f "$REFAPP/frontend/README.md" ]]; then
    echo "SCAFFOLD ERROR: pre-existing sub-READMEs missing (baseline invalid)"; exit 2
  fi

  # Criterion 19: pre-existing backend/frontend READMEs unchanged (content sha256 vs baseline).
  if ( cd "$REPO_ROOT" && shasum -a 256 -c "$README_BASELINE" ) >/dev/null 2>&1; then
    pass "C19: backend/README.md & frontend/README.md unchanged (additive docs)"
  else
    fail "C19: a pre-existing sub-README changed vs baseline (should be untouched)"
    ( cd "$REPO_ROOT" && shasum -a 256 -c "$README_BASELINE" 2>&1 | grep -v ': OK$' | sed 's/^/       /' )
  fi

  # Criterion 20: no protected file & no backend/frontend source modified (content sha256 vs baseline).
  if ( cd "$REPO_ROOT" && shasum -a 256 -c "$PROTECTED_BASELINE" ) >/dev/null 2>&1; then
    pass "C20: protected docs & backend/frontend source unchanged"
  else
    fail "C20: a protected/source file changed vs baseline (must not be modified by this unit)"
    ( cd "$REPO_ROOT" && shasum -a 256 -c "$PROTECTED_BASELINE" 2>&1 | grep -v ': OK$' | sed 's/^/       /' )
  fi
else
  printf 'SKIP: C19/C20 (sub-README + protected-doc/source hash-compare vs frozen baseline) — retired point-in-time diff guards, non-reentrant by design (harness plan-lock edits AGILE_PLAN.md per cycle); set BRD_DIFF_GUARD=1 to run.\n'
fi

echo "-----------------------------------------------------------------------"
if [[ "$FAILS" -eq 0 ]]; then
  echo "RESULT: all acceptance checks passed"
  exit 0
else
  echo "RESULT: $FAILS acceptance check(s) failed"
  exit 1
fi

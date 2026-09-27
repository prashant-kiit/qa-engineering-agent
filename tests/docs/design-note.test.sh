#!/usr/bin/env bash
# Presence/regression test for unit `p0-design-note`.
# Doc-only acceptance: DESIGN.md §15 must gain an explicit post-v1 scope note.
# Each acceptance criterion (1-7) from .harness/tasks/p0-design-note.md is asserted below.
#
# Runnable: `bash tests/docs/design-note.test.sh` (exit 0 = all pass, exit 1 = any fail).
# No framework dependency (this unit precedes p0-scaffold / Playwright setup).

set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
DESIGN="$REPO_ROOT/DESIGN.md"
FIX_DIR="$REPO_ROOT/tests/fixtures"
HEADINGS_BASELINE="$FIX_DIR/design-headings-baseline.txt"
BULLETS_BASELINE="$FIX_DIR/design-section15-bullets-baseline.txt"

FAILS=0
pass() { printf 'PASS: %s\n' "$1"; }
fail() { printf 'FAIL: %s\n' "$1"; FAILS=$((FAILS + 1)); }

# --- scaffolding sanity (must be healthy so failures below are legitimate) ---
if [[ ! -f "$DESIGN" ]]; then
  echo "SCAFFOLD ERROR: DESIGN.md not found at $DESIGN"; exit 2
fi
if [[ ! -f "$HEADINGS_BASELINE" || ! -f "$BULLETS_BASELINE" ]]; then
  echo "SCAFFOLD ERROR: baseline fixtures missing under $FIX_DIR"; exit 2
fi

# Extract the §15 section body (from the "## 15." heading up to the next "## " heading).
SECTION15="$(awk '
  /^## 15\./ {insec=1; buf=$0 ORS; next}
  /^## / && insec {insec=0}
  insec {buf=buf $0 ORS}
  END {printf "%s", buf}
' "$DESIGN")"

# case-insensitive fixed-ish regex helper against the §15 section only
sec_has() { printf '%s' "$SECTION15" | grep -qiE "$1"; }

# Isolate "the note": the maximal run of consecutive non-empty lines within §15
# that contains a "post-v1" phrase. Criteria 3-5 must hold *inside this note*, not
# merely somewhere in §15 (items (a)/(b) are already listed elsewhere in §15).
NOTE="$(printf '%s' "$SECTION15" | awk '
  BEGIN{RS=""}                      # paragraph mode (records split on blank lines)
  tolower($0) ~ /post-?v1/ {print}  # emit the paragraph that mentions post-v1
')"
note_has() { printf '%s' "$NOTE" | grep -qiE "$1"; }

# ---------------------------------------------------------------------------
# Criterion 1: Section 15 heading "## 15. Open / deferred items" exists (unchanged).
# ---------------------------------------------------------------------------
if grep -qE '^## 15\. Open / deferred items[[:space:]]*$' "$DESIGN"; then
  pass "C1: heading '## 15. Open / deferred items' present"
else
  fail "C1: heading '## 15. Open / deferred items' present"
fi

# ---------------------------------------------------------------------------
# Criterion 2: a note in §15 explicitly designates scope as post-v1 AND states
# it is not in the first SaaS release.
# ---------------------------------------------------------------------------
if sec_has 'post-?v1'; then
  pass "C2a: §15 note contains a 'post-v1' phrase"
else
  fail "C2a: §15 note contains a 'post-v1' phrase"
fi
if sec_has 'not in (the )?first SaaS release'; then
  pass "C2b: §15 note states 'not in first SaaS release'"
else
  fail "C2b: §15 note states 'not in first SaaS release'"
fi

# ---------------------------------------------------------------------------
# Criterion 3: note references item (a) — target-app auth beyond Basic Auth, naming SSO/MFA.
# ---------------------------------------------------------------------------
if note_has 'auth beyond Basic Auth'; then
  pass "C3a: post-v1 note references 'auth beyond Basic Auth'"
else
  fail "C3a: post-v1 note references 'auth beyond Basic Auth'"
fi
if note_has 'SSO/MFA'; then
  pass "C3b: post-v1 note names 'SSO/MFA'"
else
  fail "C3b: post-v1 note names 'SSO/MFA'"
fi

# ---------------------------------------------------------------------------
# Criterion 4: note references item (b) — data residency & retention policy per tenant tier.
# ---------------------------------------------------------------------------
if note_has 'data residency' && note_has 'retention' && note_has 'per tenant tier'; then
  pass "C4: post-v1 note references 'data residency & retention policy per tenant tier'"
else
  fail "C4: post-v1 note references 'data residency & retention policy per tenant tier'"
fi

# ---------------------------------------------------------------------------
# Criterion 5: note states all other §15 items are implemented in-phase and only
# their fine detail / eval-driven choice is deferred.
# ---------------------------------------------------------------------------
if note_has 'all other .*items are implemented in-phase'; then
  pass "C5a: post-v1 note states other items are 'implemented in-phase'"
else
  fail "C5a: post-v1 note states other items are 'implemented in-phase'"
fi
if note_has 'fine detail' && note_has 'eval-driven choice'; then
  pass "C5b: post-v1 note defers only 'fine detail / eval-driven choice'"
else
  fail "C5b: post-v1 note defers only 'fine detail / eval-driven choice'"
fi

# ---------------------------------------------------------------------------
# Criterion 6: additive — every pre-existing §15 bullet remains present.
# ---------------------------------------------------------------------------
missing_bullets=0
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  if ! grep -Fqx -- "$line" <(printf '%s' "$SECTION15"); then
    missing_bullets=$((missing_bullets + 1))
    printf '       missing pre-existing §15 bullet: %s\n' "$line"
  fi
done < "$BULLETS_BASELINE"
if [[ "$missing_bullets" -eq 0 ]]; then
  pass "C6: all pre-existing §15 bullets still present (additive change)"
else
  fail "C6: $missing_bullets pre-existing §15 bullet(s) removed"
fi

# ---------------------------------------------------------------------------
# Criterion 7: DESIGN.md remains well-formed Markdown — no broken/duplicated
# section headings; the full "## " heading set is preserved and unique.
# ---------------------------------------------------------------------------
CURRENT_HEADINGS="$(grep -E '^## ' "$DESIGN" | sed -E 's/^[0-9]+://')"
BASELINE_HEADINGS="$(sed -E 's/^[0-9]+://' "$HEADINGS_BASELINE")"
if [[ "$CURRENT_HEADINGS" == "$BASELINE_HEADINGS" ]]; then
  pass "C7a: '## ' heading set unchanged (none added/removed/renumbered)"
else
  fail "C7a: '## ' heading set changed vs baseline"
fi
dupes="$(grep -E '^## ' "$DESIGN" | sort | uniq -d)"
if [[ -z "$dupes" ]]; then
  pass "C7b: no duplicated section headings"
else
  fail "C7b: duplicated section heading(s): $dupes"
fi

echo "-----------------------------------------------------------------------"
if [[ "$FAILS" -eq 0 ]]; then
  echo "RESULT: all acceptance checks passed"
  exit 0
else
  echo "RESULT: $FAILS acceptance check(s) failed"
  exit 1
fi

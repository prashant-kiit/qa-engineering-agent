#!/usr/bin/env bash
# Deploy gate for the TDD harness.
# Blocks `git commit` / `git push` unless an APPROVE review marker is present.
#   - Marker: .harness/state/APPROVED  (written by the reviewer on APPROVE,
#     cleared by the git-deployer after a successful push).
#   - Escape hatch for intentional NON-harness commits: HARNESS_BYPASS=1
set -uo pipefail

input="$(cat)"

# Extract the bash command from the PreToolUse payload.
if command -v jq >/dev/null 2>&1; then
  cmd="$(printf '%s' "$input" | jq -r '.tool_input.command // ""')"
else
  cmd="$input"
fi

# Only gate commit / push. Everything else (status, add, branch, diff, ...) is allowed.
case "$cmd" in
  *"git commit"*|*"git push"*) : ;;
  *) exit 0 ;;
esac

# Explicit human escape hatch for deliberate manual commits.
if [ "${HARNESS_BYPASS:-}" = "1" ]; then
  exit 0
fi

# Approval marker (non-empty) means the reviewer APPROVED this unit.
marker="${CLAUDE_PROJECT_DIR:-.}/.harness/state/APPROVED"
if [ -s "$marker" ]; then
  exit 0
fi

# Block, surfacing the reason to the model.
cat <<'JSON'
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"Deploy gate: no APPROVE marker at .harness/state/APPROVED. A git commit/push in the TDD harness requires the Reviewer's APPROVE verdict and a green suite. Complete the Reviewer step first, or run with HARNESS_BYPASS=1 for an intentional manual (non-harness) commit."}}
JSON
exit 0

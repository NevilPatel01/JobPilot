#!/usr/bin/env bash
# Request GitHub Copilot code review on the current branch's PR
set -euo pipefail

PR_NUMBER="${1:-$(gh pr view --json number -q .number 2>/dev/null || true)}"

if [ -z "$PR_NUMBER" ]; then
  echo "Usage: ./scripts/request-copilot-review.sh [PR_NUMBER]"
  echo "Or run from a branch with an open PR."
  exit 1
fi

REPO="${GITHUB_REPOSITORY:-$(gh repo view --json nameWithOwner -q .nameWithOwner)}"

echo "Requesting Copilot review on $REPO PR #$PR_NUMBER..."
gh api --method POST "repos/$REPO/pulls/$PR_NUMBER/requested_reviewers" \
  -f 'reviewers[]=copilot-pull-request-reviewer[bot]'

echo "Done. Copilot will review using .github/copilot-instructions.md"

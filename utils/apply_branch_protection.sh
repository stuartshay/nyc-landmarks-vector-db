#!/usr/bin/env bash
# Script to apply branch protection rules to master using GitHub CLI and a JSON config
set -euo pipefail

REPO="stuartshay/nyc-landmarks-vector-db"
BRANCH="master"

cat > branch_protection.json <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "Code scanning results / Bandit",
      "Dependency Review / dependency-review (pull_request)",
      "Dependency Review / security-scan (pull_request)",
      "Pre-commit Checks / pre-commit (pull_request)",
      "Python CI / test (3.12) (pull_request)"
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "required_approving_review_count": 1
  },
  "restrictions": null
}
EOF

gh api --method PUT \
  repos/$REPO/branches/$BRANCH/protection \
  --input branch_protection.json

echo "Branch protection rule applied to $REPO:$BRANCH"

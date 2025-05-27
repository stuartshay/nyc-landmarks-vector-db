#!/usr/bin/env bash
# Script to list all branch protection rules for the repository using GitHub CLI
set -euo pipefail

REPO="stuartshay/nyc-landmarks-vector-db"

echo "Listing branch protection rules for $REPO..."

# Get all branches
branches=$(gh api repos/$REPO/branches --jq '.[].name')

for branch in $branches; do
  echo "\n--- Protection for branch: $branch ---"
  if gh api repos/$REPO/branches/$branch/protection > branch_protection_tmp.json 2>/dev/null; then
    jq . branch_protection_tmp.json
  else
    echo "No protection rule set."
  fi
done

rm -f branch_protection_tmp.json

#!/usr/bin/env bash
# Script to list all branch protection rules for the repository using GitHub CLI
set -euo pipefail

REPO="stuartshay/nyc-landmarks-vector-db"

echo "Listing branch protection rules for $REPO..."

# Get all branches
branches=$(gh api repos/$REPO/branches --jq '.[].name')

echo "$branches" | while IFS= read -r branch; do
  echo -e "\n--- Protection for branch: $branch ---"
  tmp_file=$(mktemp)
  if gh api repos/$REPO/branches/$branch/protection > "$tmp_file" 2>/dev/null; then
    jq . "$tmp_file"
  else
    echo "No protection rule set."
  fi
  rm -f "$tmp_file"
done

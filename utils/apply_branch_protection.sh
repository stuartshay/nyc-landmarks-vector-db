#!/usr/bin/env bash
# Script to apply branch protection rules to master using GitHub CLI and a JSON config
set -euo pipefail

REPO="stuartshay/nyc-landmarks-vector-db"
BRANCH="master"

# Removed inline JSON configuration. The script now assumes the standalone branch_protection.json file exists.

gh api --method PUT \
  repos/$REPO/branches/$BRANCH/protection \
  --input branch_protection.json

echo "Branch protection rule applied to $REPO:$BRANCH"

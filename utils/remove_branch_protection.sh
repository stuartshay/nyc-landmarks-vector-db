#!/usr/bin/env bash
# Script to temporarily remove branch protection
set -euo pipefail

REPO="stuartshay/nyc-landmarks-vector-db"
BRANCH="master"

echo "Removing branch protection from $REPO:$BRANCH"

gh api --method DELETE \
  repos/$REPO/branches/$BRANCH/protection

echo "Branch protection removed from $REPO:$BRANCH"
echo "Remember to re-apply protection after merging!"

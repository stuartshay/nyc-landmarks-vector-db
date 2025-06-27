#!/bin/bash
# Helper script to trigger manual Terraform apply
# Usage: ./scripts/apply-terraform.sh [run-id]

set -e

REPO="stuartshay/nyc-landmarks-vector-db"
WORKFLOW="terraform-manual-apply.yml"

echo "🔧 Terraform Manual Apply Helper"
echo "================================="

# Check if gh CLI is available
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is required but not installed."
    echo "Install it from: https://cli.github.com/"
    exit 1
fi

# Check if user is authenticated
if ! gh auth status &> /dev/null; then
    echo "❌ Please authenticate with GitHub CLI first:"
    echo "gh auth login"
    exit 1
fi

# Get run ID if provided
RUN_ID=${1:-""}

echo "📋 This will trigger a manual Terraform apply."
echo "⚠️  Make sure you have reviewed the plan first!"
echo ""

if [ -n "$RUN_ID" ]; then
    echo "🎯 Will apply plan from run ID: $RUN_ID"
else
    echo "🎯 Will apply the latest plan"
fi

echo ""
read -p "Type 'apply' to confirm you want to proceed: " CONFIRM

if [ "$CONFIRM" != "apply" ]; then
    echo "❌ Apply cancelled."
    exit 1
fi

echo "🚀 Triggering manual apply workflow..."

if [ -n "$RUN_ID" ]; then
    gh workflow run "$WORKFLOW" \
        --repo "$REPO" \
        --field confirm_apply="apply" \
        --field run_id="$RUN_ID"
else
    gh workflow run "$WORKFLOW" \
        --repo "$REPO" \
        --field confirm_apply="apply"
fi

echo "✅ Workflow triggered successfully!"
echo "🔍 Monitor the progress at:"
echo "https://github.com/$REPO/actions/workflows/$(basename $WORKFLOW)"

# Wait a moment and show the latest run
sleep 3
echo ""
echo "📊 Latest workflow runs:"
gh run list --repo "$REPO" --workflow "$WORKFLOW" --limit 3

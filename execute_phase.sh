#!/bin/bash

# Windows Dev Agent Plugin - Phase Execution Script
# This script executes the current phase and reports progress

set -e

REPO_ROOT="/home/user/Windows-Dev-Agent"
PLAN_FILE="$REPO_ROOT/BUILD_PLAN.md"
PHASE_STATE_FILE="$REPO_ROOT/.phase_state"

# Get current phase from state file or default to Phase 1
get_current_phase() {
    if [ -f "$PHASE_STATE_FILE" ]; then
        cat "$PHASE_STATE_FILE"
    else
        echo "1"
    fi
}

# Update phase state
set_current_phase() {
    echo "$1" > "$PHASE_STATE_FILE"
}

# Determine what to build next
get_next_deliverable() {
    local phase=$1
    case $phase in
        1)
            echo "discovery"
            ;;
        2)
            echo "powershell_executor"
            ;;
        3)
            echo "capability_schema"
            ;;
        4)
            echo "workflow_dsl"
            ;;
        5)
            echo "safety_engine"
            ;;
        6)
            echo "mcp_server"
            ;;
        7)
            echo "observability"
            ;;
        8)
            echo "integration"
            ;;
        *)
            echo "complete"
            ;;
    esac
}

# Main execution
cd "$REPO_ROOT"

CURRENT_PHASE=$(get_current_phase)
NEXT_DELIVERABLE=$(get_next_deliverable "$CURRENT_PHASE")

if [ "$NEXT_DELIVERABLE" = "complete" ]; then
    echo "✅ Build complete! All phases finished."
    echo ""
    echo "Next steps:"
    echo "- Review BUILD_PLAN.md for phase details"
    echo "- Run: git log --oneline to see phase commits"
    echo "- Run: python -m pytest tests/ to run test suite"
    echo ""
    exit 0
fi

echo "================================"
echo "Windows Dev Agent Plugin Build"
echo "================================"
echo ""
echo "Current Phase: $CURRENT_PHASE"
echo "Next Deliverable: $NEXT_DELIVERABLE"
echo ""
echo "To execute this phase, you need to:"
echo "1. Review BUILD_PLAN.md Phase $CURRENT_PHASE section"
echo "2. Implement the deliverables listed"
echo "3. Ensure all acceptance criteria are met"
echo "4. Run tests: python -m pytest tests/test_*.py"
echo "5. Commit with the provided template"
echo "6. Push to branch: git push -u origin claude/windows-agent-plugin-EAUGh"
echo "7. Return to continue loop"
echo ""
echo "Current file structure:"
tree -L 2 -I '__pycache__|*.pyc' 2>/dev/null || find . -maxdepth 2 -type d | head -20
echo ""
echo "Build progress:"
grep "^\- \[" "$PLAN_FILE" | head -15
echo ""
echo "Status: Awaiting phase $CURRENT_PHASE implementation"

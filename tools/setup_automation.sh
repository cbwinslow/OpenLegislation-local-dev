#!/bin/bash
# Master Setup Script for OpenLegislation Automation
# This script sets up all automation features

set -e

echo "======================================================================"
echo "OpenLegislation Automation Setup"
echo "======================================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running from repo root
if [ ! -f "pom.xml" ]; then
    echo -e "${RED}Error: Please run this script from the repository root${NC}"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "Checking prerequisites..."
echo ""

MISSING_DEPS=0

if ! command_exists git; then
    echo -e "${RED}✗ git not found${NC}"
    MISSING_DEPS=1
else
    echo -e "${GREEN}✓ git found${NC}"
fi

if ! command_exists python3; then
    echo -e "${RED}✗ python3 not found${NC}"
    MISSING_DEPS=1
else
    echo -e "${GREEN}✓ python3 found${NC}"
fi

if ! command_exists pip3; then
    echo -e "${RED}✗ pip3 not found${NC}"
    MISSING_DEPS=1
else
    echo -e "${GREEN}✓ pip3 found${NC}"
fi

if ! command_exists mvn; then
    echo -e "${YELLOW}⚠ maven not found (needed for Java build)${NC}"
fi

if ! command_exists gh; then
    echo -e "${YELLOW}⚠ GitHub CLI not found (recommended for GitHub automation)${NC}"
    echo "  Install from: https://cli.github.com/"
fi

if [ $MISSING_DEPS -eq 1 ]; then
    echo ""
    echo -e "${RED}Missing required dependencies. Please install them and try again.${NC}"
    exit 1
fi

echo ""
echo "======================================================================"
echo "Step 1: Installing Python Dependencies"
echo "======================================================================"
echo ""

cd tools
if [ -f "requirements.txt" ]; then
    echo "Installing from requirements.txt..."
    pip3 install -r requirements.txt --user
    echo -e "${GREEN}✓ Base dependencies installed${NC}"
fi

echo ""
echo "Installing additional automation dependencies..."
pip3 install --user crewai langchain requests 2>/dev/null || echo -e "${YELLOW}⚠ Some optional dependencies may have failed${NC}"

cd ..

echo ""
echo "======================================================================"
echo "Step 2: Setting up Pre-commit Hooks"
echo "======================================================================"
echo ""

if command_exists pre-commit; then
    echo "Installing pre-commit hooks..."
    pre-commit install
    echo -e "${GREEN}✓ Pre-commit hooks installed${NC}"
else
    echo "Installing pre-commit..."
    pip3 install --user pre-commit
    pre-commit install
    echo -e "${GREEN}✓ Pre-commit installed and hooks configured${NC}"
fi

echo ""
echo "======================================================================"
echo "Step 3: GitHub Configuration"
echo "======================================================================"
echo ""

if [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${YELLOW}⚠ GITHUB_TOKEN not set${NC}"
    echo "To enable GitHub automation features, set GITHUB_TOKEN:"
    echo "  export GITHUB_TOKEN=your_token_here"
    echo ""
    echo "Generate a token at: https://github.com/settings/tokens"
    echo "Required scopes: repo, workflow, admin:org"
    echo ""
    SKIP_GITHUB=1
else
    echo -e "${GREEN}✓ GITHUB_TOKEN is set${NC}"
    SKIP_GITHUB=0
fi

if [ $SKIP_GITHUB -eq 0 ]; then
    echo ""
    echo "Would you like to set up GitHub labels, milestones, and projects? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "Running GitHub automation setup..."
        python3 tools/github_automation.py
    fi
fi

echo ""
echo "======================================================================"
echo "Step 4: Workflow Verification"
echo "======================================================================"
echo ""

echo "Checking GitHub Actions workflows..."
if [ -d ".github/workflows" ]; then
    WORKFLOW_COUNT=$(find .github/workflows -name "*.yml" -o -name "*.yaml" | wc -l)
    echo -e "${GREEN}✓ Found $WORKFLOW_COUNT workflow files${NC}"
    echo ""
    echo "Available workflows:"
    find .github/workflows -name "*.yml" -o -name "*.yaml" | xargs -I {} basename {} | sed 's/^/  - /'
else
    echo -e "${RED}✗ No workflows directory found${NC}"
fi

echo ""
echo "======================================================================"
echo "Step 5: Documentation"
echo "======================================================================"
echo ""

echo "Available documentation:"
echo "  - docs/AUTOMATION_GUIDE.md - Complete automation guide"
echo "  - docs/github-rulesets-guide.md - Repository rulesets setup"
echo "  - docs/wiki-automation-guide.md - Wiki management guide"
echo "  - .github/copilot-instructions-detailed.md - Copilot instructions"

echo ""
echo "======================================================================"
echo "Setup Complete!"
echo "======================================================================"
echo ""

echo -e "${GREEN}✓ Automation setup complete!${NC}"
echo ""
echo "Next steps:"
echo ""
echo "1. Review and customize workflows in .github/workflows/"
echo "2. Set up GitHub secrets in repository settings"
echo "3. Configure repository rulesets (see docs/github-rulesets-guide.md)"
echo "4. Review docs/AUTOMATION_GUIDE.md for full feature list"
echo ""

if [ $SKIP_GITHUB -eq 1 ]; then
    echo -e "${YELLOW}Note: GitHub automation features were skipped${NC}"
    echo "Set GITHUB_TOKEN and run: python3 tools/github_automation.py"
    echo ""
fi

echo "To test workflows locally:"
echo "  gh workflow list"
echo "  gh workflow run <workflow-name>"
echo ""

echo "To test pre-commit hooks:"
echo "  pre-commit run --all-files"
echo ""

echo "For help:"
echo "  - Read docs/AUTOMATION_GUIDE.md"
echo "  - Create an issue with label 'automation'"
echo ""

echo "======================================================================"
echo "Automation Features Summary"
echo "======================================================================"
echo ""
echo "✓ GitHub Actions Workflows (11+ workflows)"
echo "  - CI/CD pipeline with testing and deployment"
echo "  - Security scanning (CodeQL, OWASP, Trivy)"
echo "  - Code formatting and linting"
echo "  - Issue and project automation"
echo "  - AI-powered code analysis"
echo ""
echo "✓ Issue Management"
echo "  - Auto-labeling based on content"
echo "  - Auto-assignment to team members"
echo "  - Project board integration"
echo "  - Stale issue management"
echo ""
echo "✓ Code Quality"
echo "  - Pre-commit hooks"
echo "  - Automated formatting (Java, Python, YAML)"
echo "  - Security pattern detection"
echo "  - Test coverage reporting"
echo ""
echo "✓ AI Agent Teams (CrewAI)"
echo "  - Software Development Crew"
echo "  - Legislative Policy Crew"
echo "  - Database Programming Crew"
echo "  - Documentation Crew"
echo ""
echo "✓ Documentation"
echo "  - Comprehensive guides"
echo "  - Wiki automation tools"
echo "  - Copilot instructions"
echo ""

echo "======================================================================"
echo "Happy automating! 🚀"
echo "======================================================================"

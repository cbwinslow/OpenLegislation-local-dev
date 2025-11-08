#!/bin/bash

# AI Agent Rules Management Script
# ================================
# This script helps manage the AI agent rules file with chezmoi
# across multiple machines and environments.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
RULES_FILE=".ai_agent_rules.md"
CHEZMOI_SOURCE="$HOME/.local/share/chezmoi"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if chezmoi is installed
check_chezmoi() {
    if ! command -v chezmoi &> /dev/null; then
        log_error "chezmoi is not installed. Please install it first:"
        echo "  curl -sfL https://git.io/chezmoi | sh"
        echo "  sudo mv ./bin/chezmoi /usr/local/bin/"
        exit 1
    fi
}

# Check if we're in the right directory
check_directory() {
    if [[ ! -f "$RULES_FILE" ]]; then
        log_error "AI agent rules file not found: $RULES_FILE"
        log_error "Please run this script from the OpenLegislation-local-dev directory"
        exit 1
    fi
}

# Add or update the rules file in chezmoi
add_to_chezmoi() {
    log_info "Adding AI agent rules to chezmoi management..."

    if chezmoi managed | grep -q "$RULES_FILE"; then
        log_warning "File already managed by chezmoi. Updating..."
        chezmoi add "$RULES_FILE"
    else
        log_info "Adding file to chezmoi for the first time..."
        chezmoi add "$RULES_FILE"
    fi

    log_success "AI agent rules added to chezmoi"
}

# Check status of the managed file
check_status() {
    log_info "Checking status of AI agent rules file..."

    if chezmoi status | grep -q "$RULES_FILE"; then
        log_warning "Local file differs from chezmoi version"
        chezmoi diff "$RULES_FILE"
    else
        log_success "AI agent rules file is in sync with chezmoi"
    fi
}

# Apply changes from chezmoi to local
apply_changes() {
    log_info "Applying chezmoi changes to local file..."

    if chezmoi status | grep -q "$RULES_FILE"; then
        chezmoi apply "$RULES_FILE"
        log_success "Changes applied successfully"
    else
        log_info "No changes to apply - file is already in sync"
    fi
}

# Update chezmoi with local changes
update_chezmoi() {
    log_info "Updating chezmoi with local changes..."

    if [[ -f "$RULES_FILE" ]]; then
        chezmoi add "$RULES_FILE"
        log_success "Local changes saved to chezmoi"
    else
        log_error "Rules file not found: $RULES_FILE"
        exit 1
    fi
}

# Show diff between local and chezmoi
show_diff() {
    log_info "Showing differences between local and chezmoi versions..."

    if chezmoi status | grep -q "$RULES_FILE"; then
        chezmoi diff "$RULES_FILE"
    else
        log_success "No differences - files are in sync"
    fi
}

# Edit the rules file
edit_rules() {
    local editor="${EDITOR:-nano}"

    log_info "Opening AI agent rules file for editing..."
    log_info "Using editor: $editor"

    if [[ -f "$RULES_FILE" ]]; then
        "$editor" "$RULES_FILE"
        log_success "File edited. Remember to run '$0 update' to save changes to chezmoi"
    else
        log_error "Rules file not found: $RULES_FILE"
        exit 1
    fi
}

# Show help
show_help() {
    cat << EOF
AI Agent Rules Management Script
================================

This script manages the AI agent rules file (.ai_agent_rules.md) with chezmoi
for synchronization across multiple machines.

USAGE:
    $0 [COMMAND]

COMMANDS:
    add         Add/update the rules file in chezmoi management
    status      Check if local file differs from chezmoi version
    apply       Apply chezmoi changes to local file
    update      Update chezmoi with local changes
    diff        Show differences between local and chezmoi versions
    edit        Open the rules file for editing
    help        Show this help message

EXAMPLES:
    $0 add      # Add file to chezmoi for the first time
    $0 status   # Check if file needs updating
    $0 edit     # Edit the rules file
    $0 update   # Save local changes to chezmoi
    $0 apply    # Apply chezmoi changes to local

WORKFLOW:
    1. Make changes to .ai_agent_rules.md
    2. Run '$0 update' to save changes
    3. On other machines, run '$0 apply' to get latest version

CHEZMOI SOURCE: $CHEZMOI_SOURCE
RULES FILE: $RULES_FILE

EOF
}

# Main script logic
main() {
    check_chezmoi
    check_directory

    case "${1:-help}" in
        add)
            add_to_chezmoi
            ;;
        status)
            check_status
            ;;
        apply)
            apply_changes
            ;;
        update)
            update_chezmoi
            ;;
        diff)
            show_diff
            ;;
        edit)
            edit_rules
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $1"
            echo
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
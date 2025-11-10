#!/bin/bash
# UV Dependency Management Script for OpenLegislation
# This script provides common uv commands for managing dependencies

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "🔧 UV Dependency Management for OpenLegislation"
echo "=============================================="

case "${1:-help}" in
    "install")
        echo "📦 Installing dependencies..."
        uv sync
        ;;
    "install-dev")
        echo "📦 Installing dependencies with dev tools..."
        uv sync --group dev
        ;;
    "install-test")
        echo "📦 Installing dependencies with test tools..."
        uv sync --group test
        ;;
    "install-all")
        echo "📦 Installing all dependencies (dev, test, docs)..."
        uv sync --all-groups
        ;;
    "add")
        if [ -z "$2" ]; then
            echo "❌ Error: Please specify a package to add"
            echo "Usage: $0 add <package> [version]"
            exit 1
        fi
        echo "➕ Adding package: $2 ${3:-latest}"
        uv add "$2${3:+==$3}"
        ;;
    "add-dev")
        if [ -z "$2" ]; then
            echo "❌ Error: Please specify a package to add"
            echo "Usage: $0 add-dev <package> [version]"
            exit 1
        fi
        echo "➕ Adding dev package: $2 ${3:-latest}"
        uv add --group dev "$2${3:+==$3}"
        ;;
    "remove")
        if [ -z "$2" ]; then
            echo "❌ Error: Please specify a package to remove"
            echo "Usage: $0 remove <package>"
            exit 1
        fi
        echo "➖ Removing package: $2"
        uv remove "$2"
        ;;
    "update")
        echo "🔄 Updating all dependencies..."
        uv lock --upgrade
        uv sync
        ;;
    "update-package")
        if [ -z "$2" ]; then
            echo "❌ Error: Please specify a package to update"
            echo "Usage: $0 update-package <package>"
            exit 1
        fi
        echo "🔄 Updating package: $2"
        uv lock --upgrade-package "$2"
        uv sync
        ;;
    "run")
        if [ -z "$2" ]; then
            echo "❌ Error: Please specify a command to run"
            echo "Usage: $0 run <command> [args...]"
            exit 1
        fi
        shift
        echo "🚀 Running: $@"
        uv run "$@"
        ;;
    "shell")
        echo "🐚 Starting uv shell..."
        uv shell
        ;;
    "clean")
        echo "🧹 Cleaning cache and temporary files..."
        uv cache clean
        rm -rf .venv
        ;;
    "status")
        echo "📊 Dependency status:"
        echo "Lock file: $(ls -lh uv.lock | awk '{print $5}')"
        echo "Python version: $(python --version)"
        echo "Virtual environment: $(uv venv --python-preference only-managed 2>/dev/null && echo "managed by uv" || echo "external")"
        ;;
    "help"|*)
        echo "Usage: $0 <command> [options]"
        echo ""
        echo "Commands:"
        echo "  install          Install production dependencies"
        echo "  install-dev      Install with dev dependencies"
        echo "  install-test     Install with test dependencies"
        echo "  install-all      Install all dependency groups"
        echo "  add <pkg> [ver]  Add a production dependency"
        echo "  add-dev <pkg>    Add a dev dependency"
        echo "  remove <pkg>     Remove a dependency"
        echo "  update           Update all dependencies"
        echo "  update-package <pkg> Update specific package"
        echo "  run <cmd>        Run command in uv environment"
        echo "  shell            Start uv shell"
        echo "  clean            Clean cache and virtual env"
        echo "  status           Show dependency status"
        echo "  help             Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 install"
        echo "  $0 add requests 2.31.0"
        echo "  $0 add-dev black"
        echo "  $0 run python -m pytest"
        echo "  $0 update-package crewai"
        ;;
esac
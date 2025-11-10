#!/bin/bash

# Charm Suite Launcher
echo "Charm Suite - TUI Applications for OpenLegislation"
echo "=================================================="
echo

cd "$(dirname "$0")"

echo "Available applications:"
echo "1. SSH Key Manager"
echo "2. Markdown Repository Renderer"
echo "3. Secrets Manager"
echo "4. Component Manager"
echo "5. Exit"
echo

read -p "Select an application (1-5): " choice

case $choice in
    1)
        echo "Launching SSH Key Manager..."
        if [ -f "ssh-manager" ]; then
            ./ssh-manager
        else
            echo "Building SSH Key Manager..."
            go build -C . ./cmd/ssh-manager && ./ssh-manager
        fi
        ;;
    2)
        echo "Launching Markdown Repository Renderer..."
        if [ -f "markdown-renderer" ]; then
            ./markdown-renderer
        else
            echo "Building Markdown Repository Renderer..."
            go build -C . ./cmd/markdown-renderer && ./markdown-renderer
        fi
        ;;
    3)
        echo "Secrets Manager - Coming Soon!"
        ;;
    4)
        echo "Component Manager - Coming Soon!"
        ;;
    5)
        echo "Goodbye!"
        exit 0
        ;;
    *)
        echo "Invalid choice. Please select 1-5."
        ;;
esac
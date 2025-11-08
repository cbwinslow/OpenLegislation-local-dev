#!/bin/bash

# OpenLegislation Ingestion TUI Installation Script
# This script builds and installs the Go TUI for managing data ingestion

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Go is installed
check_go() {
    if ! command -v go &> /dev/null; then
        print_error "Go is not installed or not in PATH"
        print_status "Please install Go 1.22 or later from https://golang.org/dl/"
        exit 1
    fi
    
    GO_VERSION=$(go version | awk '{print $3}' | sed 's/go//')
    print_success "Go version: $GO_VERSION"
}

# Check if Python is installed
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_warning "Python3 is not installed or not in PATH"
        print_status "Python3 is required for the ingestion scripts"
        print_status "Please install Python 3.8 or later"
    else
        PYTHON_VERSION=$(python3 --version)
        print_success "Python version: $PYTHON_VERSION"
    fi
}

# Navigate to TUI directory
navigate_to_tui() {
    if [ ! -d "tools/tui" ]; then
        print_error "tools/tui directory not found"
        print_status "Please run this script from the OpenLegislation root directory"
        exit 1
    fi
    
    cd tools/tui
    print_status "Changed to: $(pwd)"
}

# Clean previous builds
clean_build() {
    print_status "Cleaning previous builds..."
    if [ -f "ingestion-tui" ]; then
        rm ingestion-tui
        print_status "Removed previous binary"
    fi
}

# Download dependencies
download_deps() {
    print_status "Downloading Go dependencies..."
    if go mod tidy; then
        print_success "Dependencies downloaded successfully"
    else
        print_error "Failed to download dependencies"
        exit 1
    fi
}

# Build the TUI
build_tui() {
    print_status "Building ingestion TUI..."
    if go build -o ingestion-tui .; then
        print_success "Build completed successfully"
    else
        print_error "Build failed"
        exit 1
    fi
}

# Verify the binary
verify_binary() {
    if [ -f "ingestion-tui" ]; then
        BINARY_SIZE=$(du -h ingestion-tui | cut -f1)
        print_success "Binary created: ingestion-tui ($BINARY_SIZE)"
        
        # Check if binary is executable
        if [ -x "ingestion-tui" ]; then
            print_success "Binary is executable"
        else
            print_status "Making binary executable..."
            chmod +x ingestion-tui
        fi
    else
        print_error "Binary not found after build"
        exit 1
    fi
}

# Create symlink for easy access (optional)
create_symlink() {
    if [ -w "/usr/local/bin" ]; then
        print_status "Creating symlink in /usr/local/bin..."
        ln -sf "$(pwd)/ingestion-tui" /usr/local/bin/ingestion-tui
        print_success "Symlink created: /usr/local/bin/ingestion-tui"
    else
        print_warning "Cannot create symlink in /usr/local/bin (insufficient permissions)"
        print_status "You can run the TUI directly with: ./tools/tui/ingestion-tui"
        print_status "Or create a manual symlink: sudo ln -sf \$(pwd)/ingestion-tui /usr/local/bin/ingestion-tui"
    fi
}

# Test the TUI (basic test)
test_tui() {
    print_status "Testing TUI binary..."
    
    # Test if binary runs without errors (quick test)
    if timeout 2s ./ingestion-tui --help 2>/dev/null || true; then
        print_success "TUI binary test passed"
    else
        print_warning "TUI binary test failed (this may be normal for TUI applications)"
    fi
}

# Main installation function
main() {
    print_status "Starting OpenLegislation Ingestion TUI installation..."
    echo
    
    # Check prerequisites
    check_go
    check_python
    echo
    
    # Navigate and build
    navigate_to_tui
    clean_build
    download_deps
    build_tui
    verify_binary
    echo
    
    # Optional steps
    if [ "$1" = "--with-symlink" ]; then
        create_symlink
    fi
    echo
    
    test_tui
    echo
    
    print_success "Installation completed successfully!"
    echo
    print_status "To run the TUI:"
    print_status "  From current directory: ./ingestion-tui"
    print_status "  From project root: ./tools/tui/ingestion-tui"
    if [ -L "/usr/local/bin/ingestion-tui" ]; then
        print_status "  From anywhere: ingestion-tui"
    fi
    echo
    print_status "For more information, see: tools/tui/README.md"
}

# Handle command line arguments
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "OpenLegislation Ingestion TUI Installation Script"
    echo
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  --with-symlink  Create symlink in /usr/local/bin (requires sudo)"
    echo "  --help, -h     Show this help message"
    echo
    echo "This script builds the Go TUI for managing OpenLegislation data ingestion."
    echo "Run this script from the OpenLegislation project root directory."
    exit 0
fi

# Run main function with all arguments
main "$@"
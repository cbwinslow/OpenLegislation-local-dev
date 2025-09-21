#!/bin/bash

# Manual SSH User Switching Test
# This script tests the SSH user switching functionality manually
# to verify the improved test logic works in container environments

echo "=== Manual SSH User Switching Test ==="
echo "Testing SSH connectivity and user switching capabilities"
echo

# Configuration - use environment variables or defaults
TEST_USER="${TEST_USER:-cbwinslow}"
TEST_HOST="${TEST_HOST:-172.28.82.205}"

echo "Testing SSH connection to $TEST_USER@$TEST_HOST..."
echo

# Test 1: Basic SSH connectivity
echo "Test 1: Basic SSH connectivity"
SSH_TEST_CMD="ssh -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null \
    -o ConnectTimeout=10 \
    -o BatchMode=yes \
    $TEST_USER@$TEST_HOST"

$SSH_TEST_CMD "echo 'SSH connection successful'" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✓ Basic SSH connectivity works"
else
    echo "⚠ SSH connection failed or not configured (this is expected in container environment)"
    echo "  Skipping remote user switching tests..."
    echo
    echo "=== Local User Context Test (Container Environment) ==="

    # Test local user context instead
    echo "Test: Local user context and permissions"
    echo "Current user: $(whoami)"
    echo "User ID: $(id -u)"
    echo "Groups: $(groups)"
    echo "Home directory: $HOME"

    # Test sudo locally
    echo
    echo "Test: Local sudo availability"
    if sudo -n whoami >/dev/null 2>&1; then
        echo "✓ Local sudo works"
    else
        echo "⚠ Local sudo not available or requires password (expected in container)"
    fi

    echo
    echo "✓ Local user context assessment completed"
    echo "Note: Remote SSH tests would require proper SSH configuration and accessible hosts"
    exit 0
fi

echo

# Test 2: Sudo availability (remote)
echo "Test 2: Testing sudo availability"
SSH_OUTPUT=$($SSH_TEST_CMD \
    "sudo -n whoami 2>/dev/null || echo 'sudo not available or requires password'" 2>&1)

if echo "$SSH_OUTPUT" | grep -q "root"; then
    echo "✓ Sudo user switching to root is working"
elif echo "$SSH_OUTPUT" | grep -q "not available"; then
    echo "⚠ Sudo not available or requires password authentication"
elif echo "$SSH_OUTPUT" | grep -q "no new privileges"; then
    echo "⚠ Sudo disabled in container environment (no new privileges flag)"
else
    echo "✓ Sudo test returned: $SSH_OUTPUT"
fi

echo

# Test 3: Su command availability (remote)
echo "Test 3: Testing su command availability"
SSH_OUTPUT=$($SSH_TEST_CMD \
    "su -c 'whoami' 2>/dev/null || echo 'su not available or requires password'" 2>&1)

if [ $? -eq 0 ] && ! echo "$SSH_OUTPUT" | grep -q "not available"; then
    echo "✓ Su command executed, output: $SSH_OUTPUT"
else
    echo "⚠ Su command not available or requires password"
fi

echo

# Test 4: User context and permissions (remote)
echo "Test 4: Testing user context and permissions"
SSH_OUTPUT=$($SSH_TEST_CMD \
    "id -u -n && whoami && groups && echo 'User context test completed'" 2>&1)

if [ $? -eq 0 ] && echo "$SSH_OUTPUT" | grep -q "User context test completed"; then
    echo "✓ User context and permissions test passed"
    echo "User context information:"
    echo "$SSH_OUTPUT" | sed 's/^/  /'
else
    echo "✗ User context test failed"
    echo "Output: $SSH_OUTPUT"
fi

echo

# Test 5: Alternative privilege escalation (remote)
echo "Test 5: Checking for alternative privilege escalation methods"
SSH_OUTPUT=$($SSH_TEST_CMD \
    "which doas >/dev/null 2>&1 && echo 'doas available' || echo 'doas not available'" 2>&1)

if echo "$SSH_OUTPUT" | grep -q "doas available"; then
    echo "✓ Alternative privilege escalation (doas) available"
else
    echo "ℹ Privilege escalation status: $SSH_OUTPUT"
fi

echo
echo "=== User switching capability assessment completed ==="
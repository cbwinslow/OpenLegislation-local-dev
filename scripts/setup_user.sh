#!/bin/bash
# OpenLegislation User Setup Script

echo "=== OpenLegislation User Setup ==="

# Check current user
echo "Current user: $(whoami)"
echo "Groups: $(groups)"

# Check SSH setup
echo -e "\n=== SSH Configuration ==="
if [ -f ~/.ssh/id_ed25519.pub ]; then
    echo "✓ SSH key exists"
else
    echo "✗ SSH key missing - run: ssh-keygen -t ed25519 -C 'your-email@example.com'"
fi

# Check Java
echo -e "\n=== Java Setup ==="
java -version 2>/dev/null || echo "✗ Java not found"

# Check Maven
echo -e "\n=== Maven Setup ==="
if command -v mvn &> /dev/null; then
    echo "✓ Maven found: $(mvn -version | head -1)"
else
    echo "✗ Maven not found - install with: sudo apt install maven"
fi

# Check database connectivity
echo -e "\n=== Database Connectivity ==="
if PGPASSWORD=opendiscourse123 psql -h 172.28.82.205 -p 5433 -U opendiscourse -d openleg -c "SELECT 1;" &>/dev/null; then
    echo "✓ Database connection successful"
else
    echo "✗ Database connection failed"
fi

# Check SSH to database server
echo -e "\n=== SSH Connectivity ==="
if ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no cbwinslow@172.28.82.205 "echo 'SSH OK'" 2>/dev/null; then
    echo "✓ SSH to database server successful"
else
    echo "✗ SSH to database server failed"
fi

echo -e "\n=== Setup Complete ==="
echo "Run this script after making changes to verify setup"

#!/bin/bash
echo "🔍 Validating webhook server setup..."
echo ""

# Check required files
FILES=("app.py" "Dockerfile" "docker-compose.yml" "requirements.txt" ".env.example" "README.md" "SETUP.md")
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file is missing"
        exit 1
    fi
done

echo ""
echo "📦 Checking requirements.txt..."
if grep -q "flask" requirements.txt && grep -q "requests" requirements.txt; then
    echo "✅ Required dependencies listed"
else
    echo "❌ Missing required dependencies"
    exit 1
fi

echo ""
echo "🐳 Validating Dockerfile..."
if grep -q "FROM python" Dockerfile && grep -q "CMD.*gunicorn" Dockerfile; then
    echo "✅ Dockerfile looks good"
else
    echo "❌ Dockerfile has issues"
    exit 1
fi

echo ""
echo "📋 Checking .env.example..."
REQUIRED_VARS=("GITHUB_TOKEN" "GITHUB_WEBHOOK_SECRET" "OPENROUTER_API_KEY")
for var in "${REQUIRED_VARS[@]}"; do
    if grep -q "$var" .env.example; then
        echo "✅ $var documented"
    else
        echo "❌ $var missing from .env.example"
        exit 1
    fi
done

echo ""
echo "📚 Checking documentation..."
if [ -s "README.md" ] && [ -s "SETUP.md" ]; then
    echo "✅ Documentation complete"
else
    echo "❌ Documentation incomplete"
    exit 1
fi

echo ""
echo "🎉 All validation checks passed!"
echo ""
echo "Next steps:"
echo "1. Copy .env.example to .env and fill in your credentials"
echo "2. Run: docker-compose up -d"
echo "3. Test: curl http://localhost:5000/health"
echo "4. Configure GitHub webhook"

#!/bin/bash
set -e  # Exit on error

# Parse arguments
TEST_MODE=""
TOKEN=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --test)
            TEST_MODE="--test"
            shift
            ;;
        --token)
            TOKEN="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--test] [--token YOUR_TOKEN]"
            exit 1
            ;;
    esac
done

# Build publish command
if [ "$TEST_MODE" == "--test" ]; then
    REPO_FLAG="--repository testpypi"
    echo "🧪 Publishing to TestPyPI..."
else
    REPO_FLAG=""
    echo "🚀 Publishing to PyPI..."
    echo ""
    read -p "Are you sure you want to publish to PyPI? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "❌ Cancelled"
        exit 1
    fi
fi

# Add token if provided
if [ -n "$TOKEN" ]; then
    TOKEN_FLAG="--token $TOKEN"
else
    TOKEN_FLAG=""
fi

echo ""

# Main package
echo "📦 Publishing main package: praisonai-svc"
cd /Users/praison/praisonai-svc
uv publish $REPO_FLAG $TOKEN_FLAG
echo "✅ Main package published"
echo ""

# Defensive packages
DEFENSIVE_PACKAGES=("praisonaisvc" "praisonai_svc" "praisonai-svcs")

for package in "${DEFENSIVE_PACKAGES[@]}"; do
    echo "📦 Publishing defensive package: $package"
    cd /Users/praison/praisonai-svc/defensive-packages/$package
    uv publish $REPO_FLAG $TOKEN_FLAG
    echo "✅ $package published"
    echo ""
done

# Return to root
cd /Users/praison/praisonai-svc

echo "🎉 All packages published successfully!"
echo ""
if [ "$TEST_MODE" == "--test" ]; then
    echo "Test installation:"
    echo "  pip install --index-url https://test.pypi.org/simple/ praisonai-svc"
else
    echo "Installation:"
    echo "  pip install praisonai-svc"
fi

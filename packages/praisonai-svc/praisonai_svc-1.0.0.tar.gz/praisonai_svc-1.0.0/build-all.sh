#!/bin/bash
set -e  # Exit on error

echo "🔨 Building PraisonAI-SVC packages..."
echo ""

# Main package
echo "📦 Building main package: praisonai-svc"
cd /Users/praison/praisonai-svc
uv lock
uv build
echo "✅ Main package built"
echo ""

# Defensive packages
DEFENSIVE_PACKAGES=("praisonaisvc" "praisonai_svc" "praisonai-svcs")

for package in "${DEFENSIVE_PACKAGES[@]}"; do
    echo "📦 Building defensive package: $package"
    cd /Users/praison/praisonai-svc/defensive-packages/$package
    uv build
    echo "✅ $package built"
    echo ""
done

# Return to root
cd /Users/praison/praisonai-svc

echo "🎉 All packages built successfully!"
echo ""
echo "Built packages:"
echo "  - praisonai-svc (main)"
echo "  - praisonaisvc (defensive)"
echo "  - praisonai_svc (defensive)"
echo "  - praisonai-svcs (defensive)"
echo ""
echo "Next steps:"
echo "  1. Test: uv publish --repository testpypi"
echo "  2. Publish: uv publish"

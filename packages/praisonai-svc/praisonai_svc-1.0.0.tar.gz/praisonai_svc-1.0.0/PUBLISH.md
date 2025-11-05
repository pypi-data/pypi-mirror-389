# Publishing to PyPI

## Quick Start (Automated)

### Build All Packages
```bash
./build-all.sh
```

### Publish to TestPyPI (Recommended First)
```bash
# Without token (will use uv's default auth)
./publish-all.sh --test

# With token
./publish-all.sh --test --token YOUR_TESTPYPI_TOKEN
```

### Publish to PyPI
```bash
# Without token (will use uv's default auth)
./publish-all.sh

# With token
./publish-all.sh --token YOUR_PYPI_TOKEN
```

---

## Manual Steps (if needed)

### Prerequisites

uv is already installed (no additional tools needed)

## Build Main Package

```bash
cd /Users/praison/praisonai-svc

# Lock dependencies
uv lock

# Build package
uv build
```

## Test on TestPyPI (Recommended)

```bash
uv publish --repository testpypi
```

## Publish to PyPI

```bash
uv publish
```

## Publish Defensive Packages

```bash
# Package 1: praisonaisvc
cd defensive-packages/praisonaisvc
uv build
uv publish

# Package 2: praisonai_svc
cd ../praisonai_svc
uv build
uv publish

# Package 3: praisonai-svcs
cd ../praisonai-svcs
uv build
uv publish

# Return to root
cd ../..
```

## Post-Publication

1. Enable 2FA on PyPI account
2. Create GitHub release (v1.0.0)
3. Update documentation
4. Announce release

---

**Status:** Ready to publish! 🚀

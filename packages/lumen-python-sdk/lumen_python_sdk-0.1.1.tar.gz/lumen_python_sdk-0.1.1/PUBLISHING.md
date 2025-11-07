# Publishing to PyPI with uv

## Prerequisites

- ✅ PyPI account (you have this)
- ✅ `uv` installed
- ✅ PyPI API token (or username/password)

## Step 1: Get PyPI API Token (Recommended)

1. Go to [https://pypi.org/manage/account/token/](https://pypi.org/manage/account/token/)
2. Click "Add API token"
3. Name: `lumen-python-sdk`
4. Scope: Choose "Entire account" or create project-specific after first upload
5. Copy the token (starts with `pypi-`)

## Step 2: Configure uv with PyPI Credentials

```bash
# Option A: Set environment variable (recommended for CI/CD)
export UV_PUBLISH_TOKEN="pypi-your-token-here"

# Option B: uv will prompt you during publish
# Just have your token ready
```

## Step 3: Pre-Publishing Checklist

```bash
cd /Users/prasoon/work/lumen-python-sdk

# 1. Verify package name is available
# Search: https://pypi.org/search/?q=lumen-python-sdk

# 2. Clean old builds
rm -rf dist/ build/ *.egg-info

# 3. Update version if needed (already at 0.1.0)
# Edit pyproject.toml if you want to change version

# 4. Verify pyproject.toml is correct
cat pyproject.toml | grep -E "name|version|description"
```

## Step 4: Build the Package

```bash
# Build both wheel and source distribution
uv build

# This creates:
# dist/lumen_python_sdk-0.1.0-py3-none-any.whl
# dist/lumen-python-sdk-0.1.0.tar.gz
```

## Step 5: Test the Build (Optional but Recommended)

```bash
# Install from local build to test
uv pip install dist/lumen_python_sdk-0.1.0-py3-none-any.whl

# Test import
uv run python -c "import lumen; print(lumen.__version__)"

# Uninstall test
uv pip uninstall lumen-python-sdk
```

## Step 6: Publish to PyPI

```bash
# Publish to PyPI
uv publish

# You'll be prompted for:
# - Username: __token__
# - Password: pypi-your-token-here (paste your API token)
```

### If Using Environment Variable

```bash
# Set token
export UV_PUBLISH_TOKEN="pypi-your-token-here"

# Publish (no prompt)
uv publish
```

## Step 7: Verify on PyPI

1. Check your package: [https://pypi.org/project/lumen-python-sdk/](https://pypi.org/project/lumen-python-sdk/)
2. Test installation:

```bash
# In a new directory
uv pip install lumen-python-sdk
uv run python -c "import lumen; print(lumen.__version__)"
```

## Publishing Updates

When you have changes to publish:

```bash
# 1. Update version in pyproject.toml
# Change: version = "0.1.1"

# 2. Update CHANGELOG.md

# 3. Commit changes
git add .
git commit -m "Release v0.1.1"
git tag v0.1.1
git push && git push --tags

# 4. Clean and rebuild
rm -rf dist/
uv build

# 5. Publish
uv publish
```

## Troubleshooting

### "File already exists"

You're trying to upload the same version. Bump the version in `pyproject.toml`.

### "Invalid credentials"

- Verify your API token is correct
- Use `__token__` as username, not your PyPI username
- Token should start with `pypi-`

### "Package name already taken"

Someone else owns `lumen-python-sdk`. Options:

1. Contact PyPI support if you own the trademark
2. Choose a different name like `lumen-sdk-python` or `getlumen`

### Build fails

```bash
# Install build dependencies
uv pip install hatchling

# Try building again
uv build
```

## Quick Reference

```bash
# Complete workflow
cd /Users/prasoon/work/lumen-python-sdk
rm -rf dist/
uv build
uv publish
```

## TestPyPI (For Testing)

Test your package on TestPyPI first:

```bash
# Build
uv build

# Publish to TestPyPI
uv publish --publish-url https://test.pypi.org/legacy/

# Install from TestPyPI to test
uv pip install --index-url https://test.pypi.org/simple/ lumen-python-sdk
```

## Automation (GitHub Actions)

Add to `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install uv
        uses: astral-sh/setup-uv@v1

      - name: Build package
        run: uv build

      - name: Publish to PyPI
        env:
          UV_PUBLISH_TOKEN: ${{ secrets.PYPI_TOKEN }}
        run: uv publish
```

Then add `PYPI_TOKEN` to GitHub repository secrets.

## Package URLs After Publishing

- PyPI Page: https://pypi.org/project/lumen-python-sdk/
- Install: `uv pip install lumen-python-sdk`
- Docs: https://github.com/getlumen/lumen-python-sdk

## Version Strategy

Follow semantic versioning:

- `0.1.0` - Initial release
- `0.1.1` - Bug fixes
- `0.2.0` - New features (backward compatible)
- `1.0.0` - Production ready, stable API

---

Need help? Check [uv docs](https://docs.astral.sh/uv/) or reach out!






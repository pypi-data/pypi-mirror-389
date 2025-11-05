# GitHub Actions Workflows

This repository uses three GitHub Actions workflows:

## 1. CI (`ci.yml`)

**Triggers:** On every push to `master` and on all pull requests

**What it does:**
- Runs tests on Python 3.11 and 3.12
- Runs type checking with mypy
- Runs linting with ruff
- Checks code formatting
- Reports test coverage

This ensures code quality on every commit.

## 2. Release (`release.yml`) - **RECOMMENDED**

**Triggers:** When you push a version tag (e.g., `v0.1.0`, `v1.2.3`)

**What it does:**
1. Runs full test suite
2. Builds the package
3. Publishes to PyPI
4. Creates a GitHub Release with release notes

**How to use:**
```bash
# Update version in pyproject.toml
# Commit your changes
git add pyproject.toml
git commit -m "Bump version to 0.2.0"
git push

# Create and push a tag
git tag v0.2.0
git push origin v0.2.0
```

This will automatically publish to PyPI and create a GitHub release.

## 3. Publish (`publish.yml`)

**Triggers:**
- When `pyproject.toml` is changed on `master`
- Manual trigger via GitHub UI

**What it does:**
- Builds and publishes to PyPI immediately

**How to use:**
- Commit changes to `pyproject.toml` on master, or
- Go to Actions tab → Publish to PyPI → Run workflow

⚠️ **Note:** This publishes on every `pyproject.toml` change. Consider using the Release workflow instead for more control.

## Setup: Add PyPI Token

To enable publishing, add your PyPI token as a GitHub secret:

1. Get a PyPI API token:
   - Go to https://pypi.org/manage/account/token/
   - Create a new token with scope "Entire account" or specific to `inquire-py`
   - Copy the token (starts with `pypi-...`)

2. Add to GitHub secrets:
   - Go to repository Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `PYPI_TOKEN`
   - Value: Paste your token
   - Click "Add secret"

## Recommended Publishing Workflow

### Automated Release (Easiest) 🚀

Use the release script:

```bash
# Using the script directly
./scripts/release.sh 0.2.0

# Or using make
make release VERSION=0.2.0
```

This automatically:
- ✅ Validates version format
- ✅ Checks for uncommitted changes
- ✅ Updates `pyproject.toml`
- ✅ Shows diff and asks for confirmation
- ✅ Creates commit and tag
- ✅ Pushes to GitHub

The GitHub Actions workflow then automatically publishes to PyPI.

### Manual Release

If you prefer manual control:

```bash
# 1. Update version in pyproject.toml
vim pyproject.toml  # Change version = "0.1.0" to "0.2.0"

# 2. Commit and push
git add pyproject.toml
git commit -m "Bump version to 0.2.0"
git push

# 3. Create and push tag
git tag v0.2.0
git push origin v0.2.0

# This triggers release.yml which tests, builds, and publishes
```

**For quick hotfixes:**
```bash
# Update version and push to master
# The publish.yml workflow will trigger automatically
```

## Disabling Auto-Publish

If you only want tag-based releases:

1. Delete or disable `publish.yml`
2. Keep only `release.yml` and `ci.yml`
3. Publish by creating tags

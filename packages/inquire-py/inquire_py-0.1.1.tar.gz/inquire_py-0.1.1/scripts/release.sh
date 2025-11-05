#!/usr/bin/env bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
error() {
    echo -e "${RED}❌ Error: $1${NC}" >&2
    exit 1
}

info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check if version argument is provided
if [ $# -eq 0 ]; then
    error "Version number required. Usage: ./scripts/release.sh <version>"
fi

NEW_VERSION="$1"

# Validate version format (e.g., 0.1.0, 1.2.3)
if ! [[ "$NEW_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    error "Invalid version format. Use semantic versioning (e.g., 0.2.0, 1.0.0)"
fi

# Get current version from pyproject.toml
CURRENT_VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')

info "Current version: $CURRENT_VERSION"
info "New version: $NEW_VERSION"

# Check if version is the same
if [ "$CURRENT_VERSION" = "$NEW_VERSION" ]; then
    error "Version $NEW_VERSION is already the current version. No change needed."
fi

# Check if on master branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "master" ]; then
    warn "You are on branch '$CURRENT_BRANCH', not 'master'"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        error "Release cancelled"
    fi
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    error "You have uncommitted changes. Commit or stash them first."
fi

# Check if git is clean
if [ -n "$(git status --porcelain)" ]; then
    error "Working directory is not clean. Commit or stash changes first."
fi

# Check if tag already exists
if git rev-parse "v$NEW_VERSION" >/dev/null 2>&1; then
    error "Tag v$NEW_VERSION already exists"
fi

# Update version in pyproject.toml
info "Updating version in pyproject.toml..."
sed -i.bak "s/^version = \".*\"/version = \"$NEW_VERSION\"/" pyproject.toml
rm pyproject.toml.bak

# Show diff
echo ""
info "Changes to be committed:"
git diff pyproject.toml

echo ""
read -p "Proceed with release v$NEW_VERSION? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    # Revert changes
    git checkout pyproject.toml
    error "Release cancelled"
fi

# Commit version bump
info "Committing version bump..."
git add pyproject.toml
git commit -m "Bump version to $NEW_VERSION"
success "Version bump committed"

# Create git tag
info "Creating tag v$NEW_VERSION..."
git tag -a "v$NEW_VERSION" -m "Release v$NEW_VERSION"
success "Tag created"

# Push commit and tag
info "Pushing to origin..."
git push origin "$CURRENT_BRANCH"
success "Pushed commit to $CURRENT_BRANCH"

git push origin "v$NEW_VERSION"
success "Pushed tag v$NEW_VERSION"

echo ""
success "🚀 Release v$NEW_VERSION completed successfully!"
echo ""
info "GitHub Actions will now:"
echo "  1. Run tests"
echo "  2. Build the package"
echo "  3. Publish to PyPI"
echo "  4. Create a GitHub Release"
echo ""
info "Monitor the release at:"
echo "  https://github.com/daviddl9/inquire/actions"
echo ""
info "Once published, users can install with:"
echo "  pip install inquire-py==$NEW_VERSION"

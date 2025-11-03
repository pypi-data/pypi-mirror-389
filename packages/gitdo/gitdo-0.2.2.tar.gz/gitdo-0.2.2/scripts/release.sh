#!/bin/bash
set -e

# Helper script to create a new release
# Usage: ./scripts/release.sh <version>
# Example: ./scripts/release.sh 0.2.0

if [ -z "$1" ]; then
    echo "Error: Version number required"
    echo "Usage: ./scripts/release.sh <version>"
    echo "Example: ./scripts/release.sh 0.2.0"
    exit 1
fi

VERSION=$1

# Validate version format (x.y.z)
if ! [[ $VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Error: Invalid version format. Use semantic versioning (e.g., 0.2.0)"
    exit 1
fi

echo "Creating release for version $VERSION"

# Check if we're on main branch
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "Warning: You are not on the main branch (current: $CURRENT_BRANCH)"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "Error: You have uncommitted changes. Please commit or stash them first."
    exit 1
fi

# Update version in pyproject.toml
echo "Updating version in pyproject.toml..."
sed -i.bak "s/^version = .*/version = \"$VERSION\"/" pyproject.toml
rm pyproject.toml.bak

# Update version in __init__.py
echo "Updating version in src/gitdo/__init__.py..."
sed -i.bak "s/__version__ = .*/__version__ = \"$VERSION\"/" src/gitdo/__init__.py
rm src/gitdo/__init__.py.bak

# Commit version bump
echo "Committing version bump..."
git add pyproject.toml src/gitdo/__init__.py
git commit -m "Bump version to $VERSION"

# Create and push tag
echo "Creating tag v$VERSION..."
git tag -a "v$VERSION" -m "Release version $VERSION"

echo ""
echo "Release v$VERSION prepared successfully!"
echo ""
echo "To publish to PyPI, push the tag:"
echo "  git push origin main --tags"
echo ""
echo "To cancel this release:"
echo "  git reset --hard HEAD~1"
echo "  git tag -d v$VERSION"

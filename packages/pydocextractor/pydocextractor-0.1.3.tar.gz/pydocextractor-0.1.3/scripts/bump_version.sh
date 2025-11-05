#!/bin/bash
# Version bumping script for pydocextractor
# Usage: ./scripts/bump_version.sh [major|minor|patch]

set -e

BUMP_TYPE=${1:-patch}

if [[ ! "$BUMP_TYPE" =~ ^(major|minor|patch)$ ]]; then
    echo "Error: Invalid bump type '$BUMP_TYPE'. Must be 'major', 'minor', or 'patch'."
    exit 1
fi

# Get current version from pyproject.toml
CURRENT_VERSION=$(uv run python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])")

echo "Current version: $CURRENT_VERSION"

# Parse semantic version
IFS='.' read -r MAJOR MINOR PATCH <<< "$CURRENT_VERSION"

# Bump version based on type
case $BUMP_TYPE in
    major)
        MAJOR=$((MAJOR + 1))
        MINOR=0
        PATCH=0
        ;;
    minor)
        MINOR=$((MINOR + 1))
        PATCH=0
        ;;
    patch)
        PATCH=$((PATCH + 1))
        ;;
esac

NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"

echo "New version: $NEW_VERSION"

# Update version in pyproject.toml
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s/version = \"$CURRENT_VERSION\"/version = \"$NEW_VERSION\"/" pyproject.toml
else
    # Linux
    sed -i "s/version = \"$CURRENT_VERSION\"/version = \"$NEW_VERSION\"/" pyproject.toml
fi

echo "✓ Version bumped from $CURRENT_VERSION to $NEW_VERSION in pyproject.toml"
echo ""
echo "Next steps:"
echo "  1. Review the changes: git diff pyproject.toml"
echo "  2. Commit: git add pyproject.toml && git commit -m 'chore: bump version to $NEW_VERSION'"
echo "  3. Push to main: git push origin main"
echo "  4. The GitHub Action will automatically publish to PyPI"

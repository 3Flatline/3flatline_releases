#!/bin/bash
set -e

# Script to create a new release for 3flatline
# Usage: ./scripts/create_release.sh <version>
# Example: ./scripts/create_release.sh 1.0.0

# Check if version is provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 <version>"
    echo "Example: $0 1.0.0"
    exit 1
fi

VERSION=$1
# Check if the version already starts with 'v'
if [[ $VERSION == v* ]]; then
    TAG="$VERSION"
else
    TAG="v$VERSION"
fi

# Confirm with the user
echo "This will create and push a new release tag: $TAG"
read -p "Continue? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Release creation cancelled."
    exit 1
fi

# Ensure we're in the repository root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$REPO_ROOT"

# Create and push the tag
echo "Creating tag $TAG..."
git tag -a "$TAG" -m "Release $TAG"

echo "Pushing tag to remote..."
git push origin "$TAG"

echo "Tag $TAG has been created and pushed."
echo "The GitHub Action workflow will automatically create the release."
echo "You can check the progress in the 'Actions' tab of your GitHub repository."
echo "Note: For the workflow to run, the tag should match the pattern 'v*' (e.g., v232, v1.0.0, v232-beta)."

exit 0

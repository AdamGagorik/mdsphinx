#!/usr/bin/env bash
set -e

# Bump the version using poetry
poetry version "${BUMP_RULE-minor}"
VERSION=$(rg 'version\s*=\s*"(\d+\.\d+\.\d+.*)"' pyproject.toml | cut -d'"' -f 2)

# Temporarily create a tag to use the dynamic versioning
git tag "v${VERSION}"
poetry dynamic-versioning
git tag -d "v${VERSION}"

# Commit the version in the files
git add pyproject.toml
git add ./mdsphinx/__init__.py
git commit -m "Update version to ${VERSION}"
git push
git tag "v${VERSION}"
git push --tags

# Create the release
gh release create "v${VERSION}" --generate-notes
git pull

# Push to PyPI
poetry build
poetry publish

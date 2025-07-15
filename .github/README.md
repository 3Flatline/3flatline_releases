# GitHub Actions for 3flatline Releases

This directory contains GitHub Actions workflows that automate the release process for 3flatline.

## Release Workflow

The `release.yml` workflow automatically creates a new GitHub release when a new tag with the format `v*.*.*` is pushed to the repository. For example: `v1.0.0`, `v2.3.4`, etc.

### What the workflow does:

1. Creates multiple zip packages:
   - `3flatline-complete.zip`: Contains all binaries, config example, and README
   - `3flatline-mac.zip`: Contains Mac-specific binaries, config example, and README
   - `3flatline-linux.zip`: Contains Linux-specific binaries, config example, and README
   - `3flatline-frontend.zip`: Contains the frontend files (if the frontend directory exists)

2. Creates a GitHub release with:
   - Release notes automatically generated from commits and pull requests
   - All zip packages attached as release assets
   - Installation instructions

### How to create a new release:

#### Option 1: Using the helper script

A helper script is available to simplify the release process:

```bash
# Run from the repository root
./scripts/create_release.sh 1.2.3
```

This will create and push a tag `v1.2.3`, which will trigger the workflow.

#### Option 2: Manual release

If you prefer to create tags manually:

```bash
# Create an annotated tag
git tag -a v1.2.3 -m "Release v1.2.3"

# Push the tag to GitHub
git push origin v1.2.3
```

### Pre-releases

Tags containing `-beta`, `-alpha`, or `-rc` will be automatically marked as pre-releases. For example:

```bash
# Create a beta release
git tag -a v1.2.3-beta.1 -m "Beta release v1.2.3-beta.1"
git push origin v1.2.3-beta.1
```

## Workflow Execution

After pushing a tag:

1. The workflow will start automatically (check the "Actions" tab in GitHub)
2. When complete, the new release will appear in the "Releases" section
3. The release will include all zip packages and automatically generated release notes
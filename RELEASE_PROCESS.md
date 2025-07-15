# 3flatline Release Process

This document describes the process for creating new releases of the 3flatline software.

## Versioning

We follow [Semantic Versioning](https://semver.org/) for version numbering:

- **MAJOR** version when making incompatible API changes
- **MINOR** version when adding functionality in a backward compatible manner
- **PATCH** version when making backward compatible bug fixes

## Release Workflow

### 1. Prepare for Release

Before creating a release:

1. Ensure all desired changes have been merged to the main branch
2. Verify that the software builds correctly and passes all tests
3. Update any version numbers in the codebase (if applicable)
4. Update documentation as needed

### 2. Create the Release

#### Option 1: Using the Helper Script (Recommended)

Run the helper script from the repository root:

```bash
./scripts/create_release.sh 1.2.3
```

Replace `1.2.3` with the appropriate version number.

#### Option 2: Manual Release

If you prefer to create tags manually:

```bash
# Create an annotated tag
git tag -a v1.2.3 -m "Release v1.2.3"

# Push the tag to GitHub
git push origin v1.2.3
```

### 3. Monitor the Release Workflow

After pushing the tag:

1. Go to the GitHub repository's "Actions" tab
2. Monitor the "Create Release" workflow that was triggered by the tag
3. Verify that all steps complete successfully

### 4. Verify the Release

Once the workflow completes:

1. Go to the "Releases" section of the GitHub repository
2. Verify that the new release appears with:
   - The correct version number
   - All expected zip files attached
   - Proper release notes
   - Installation instructions

### 5. Pre-releases

For pre-release versions (alpha, beta, release candidates):

- Use tags like `v1.2.3-beta.1`, `v1.2.3-alpha.2`, or `v1.2.3-rc.1`
- These will be automatically marked as pre-releases in GitHub

## Release Artifacts

Each release includes the following zip files:

- **3flatline-complete.zip**: All binaries, config example, and README
- **3flatline-mac.zip**: Mac-specific binaries, config example, and README
- **3flatline-linux.zip**: Linux-specific binaries, config example, and README
- **3flatline-frontend.zip**: Frontend files (if applicable)
- **3flatline-scripts.zip**: Scripts (if applicable)

## Post-Release Tasks

After a successful release:

1. Announce the release to users through appropriate channels
2. Update the documentation site (if applicable)
3. Create issues for any bugs found during the release process
4. Begin planning for the next release

## Troubleshooting

If the release workflow fails:

1. Check the workflow logs in the "Actions" tab for error messages
2. Make necessary corrections
3. Delete the failed tag: `git tag -d v1.2.3 && git push --delete origin v1.2.3`
4. Create a new tag and retry

## Special Release Types

### Hotfix Releases

For urgent fixes to a stable release:

1. Create a hotfix branch from the release tag: `git checkout -b hotfix/1.2.4 v1.2.3`
2. Make the necessary fixes
3. Follow the normal release process, using an incremented patch version
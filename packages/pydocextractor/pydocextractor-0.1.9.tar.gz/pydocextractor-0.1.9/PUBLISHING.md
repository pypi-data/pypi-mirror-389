# Publishing Guide for pydocextractor

This guide explains how the automated publishing system works and how to manage releases.

## Automated Publishing

The project uses GitHub Actions to automatically bump versions and publish to PyPI whenever code is pushed to the `main` branch.

### How It Works

1. **Automatic on Push to Main**: Every push to `main` triggers the publish workflow
2. **Version Bump**: Automatically increments the patch version (e.g., 0.1.2 → 0.1.3)
3. **Build**: Creates distribution packages using `uv build`
4. **Publish**: Uploads to PyPI using `uv publish`
5. **Commit**: Commits the version bump back to the repository with `[skip ci]` flag
6. **Release**: Creates a GitHub release with the new version tag

### Workflow File

The automation is defined in `.github/workflows/publish.yml`

## GitHub Secrets Setup

**IMPORTANT**: You must configure the following secrets in your GitHub repository:

### Step-by-Step Setup

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** and add:

   - **Name**: `PYPI_API_TOKEN`
   - **Value**: `pypi-AgEIcHlwaS5vcmcCJDE1NTk1MmYwLWFlNDktNDE0Ny1iMzQ2LWQwMjgwMjQxMWY5OQACKlszLCI2OGZmOGJiZS1mYTViLTQwZTAtODJiMS1hZjUxZGJlMTk0M2QiXQAABiDPK6OmG11RrcRFi918cXo6UGNOgSO5pdmHPaaugh-TBw`

   - **Name**: `PYPI_USERNAME`
   - **Value**: `leonardoaraujo.santos.amini`

4. Save the secrets

## Manual Version Bumping (Optional)

If you want to control version bumps manually instead of automatic patch increments:

### Using the Script

```bash
# Bump patch version (0.1.2 → 0.1.3)
./scripts/bump_version.sh patch

# Bump minor version (0.1.2 → 0.2.0)
./scripts/bump_version.sh minor

# Bump major version (0.1.2 → 1.0.0)
./scripts/bump_version.sh major
```

### Manual Steps

1. Bump the version:
   ```bash
   ./scripts/bump_version.sh [major|minor|patch]
   ```

2. Review changes:
   ```bash
   git diff pyproject.toml
   ```

3. Commit and push:
   ```bash
   git add pyproject.toml
   git commit -m "chore: bump version to X.Y.Z"
   git push origin main
   ```

4. The GitHub Action will automatically publish to PyPI

## Disabling Automatic Publishing

If you want to disable automatic publishing on every push to main:

### Option 1: Require Manual Approval

Modify `.github/workflows/publish.yml` to add an environment with required reviewers:

```yaml
jobs:
  publish:
    runs-on: ubuntu-latest
    environment: production  # Add this line
    permissions:
      contents: write
```

Then in GitHub Settings → Environments → Create "production" environment and add required reviewers.

### Option 2: Manual Workflow Trigger

Change the workflow trigger in `.github/workflows/publish.yml`:

```yaml
on:
  workflow_dispatch:  # Manual trigger only
    inputs:
      bump_type:
        description: 'Version bump type'
        required: true
        default: 'patch'
        type: choice
        options:
          - patch
          - minor
          - major
```

### Option 3: Tag-Based Publishing

Trigger publishing only when you create a version tag:

```yaml
on:
  push:
    tags:
      - 'v*.*.*'
```

Then manually create and push tags:
```bash
git tag v0.1.3
git push origin v0.1.3
```

## Testing Before Publishing

### Build Locally

```bash
# Clean previous builds
rm -rf dist/

# Build package
uv build

# Check the built package
ls -lh dist/
```

### Test Installation Locally

```bash
# Install from local wheel
pip install dist/pydocextractor-*.whl

# Test the installation
python -c "import pydocextractor; print(pydocextractor.__version__)"
```

### Publish to TestPyPI (Optional)

```bash
# Build
uv build

# Publish to TestPyPI
uv publish \
  --index testpypi \
  --token <your-testpypi-token> \
  --username <your-testpypi-username>

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ pydocextractor
```

## Troubleshooting

### Build Fails

- Check that all dependencies are properly specified in `pyproject.toml`
- Ensure the build backend (hatchling) is working: `uv build --verbose`

### Publish Fails

- Verify PyPI credentials in GitHub Secrets
- Check if the version already exists on PyPI (versions cannot be reused)
- Ensure the API token has upload permissions

### Version Already Exists

If you need to republish:
1. Bump to a new version
2. PyPI doesn't allow overwriting existing versions for security

### Workflow Permission Errors

If the workflow can't push commits:
1. Go to Settings → Actions → General
2. Under "Workflow permissions", select "Read and write permissions"
3. Check "Allow GitHub Actions to create and approve pull requests"

## Current Configuration

- **Current Version**: Check `pyproject.toml` line 4
- **PyPI Package**: https://pypi.org/project/pydocextractor/
- **Repository**: https://github.com/aminiai/pyDocExtractor
- **Workflow**: `.github/workflows/publish.yml`

## Best Practices

1. **Always test locally** before pushing to main
2. **Use Pull Requests** for code changes (this prevents accidental publishes)
3. **Semantic Versioning**:
   - PATCH (0.0.X): Bug fixes
   - MINOR (0.X.0): New features, backward compatible
   - MAJOR (X.0.0): Breaking changes
4. **Review release notes** in the automatically created GitHub releases
5. **Monitor PyPI** after publishing to ensure the package is available

## Additional Resources

- [uv Documentation](https://docs.astral.sh/uv/)
- [PyPI Publishing Guide](https://packaging.python.org/tutorials/packaging-projects/)
- [GitHub Actions](https://docs.github.com/en/actions)
- [Semantic Versioning](https://semver.org/)

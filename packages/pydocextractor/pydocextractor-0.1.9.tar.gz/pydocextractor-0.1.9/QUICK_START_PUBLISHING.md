# Quick Start: Publishing Setup

## 🚀 One-Time Setup (Do This First!)

### 1. Add GitHub Secrets

Go to: https://github.com/aminiai/pyDocExtractor/settings/secrets/actions

Add these two secrets:

1. **Secret Name**: `PYPI_API_TOKEN`
   **Value**:
   ```
   pypi-AgEIcHlwaS5vcmcCJDE1NTk1MmYwLWFlNDktNDE0Ny1iMzQ2LWQwMjgwMjQxMWY5OQACKlszLCI2OGZmOGJiZS1mYTViLTQwZTAtODJiMS1hZjUxZGJlMTk0M2QiXQAABiDPK6OmG11RrcRFi918cXo6UGNOgSO5pdmHPaaugh-TBw
   ```

2. **Secret Name**: `PYPI_USERNAME`
   **Value**:
   ```
   leonardoaraujo.santos.amini
   ```

### 2. Enable Workflow Permissions

Go to: https://github.com/aminiai/pyDocExtractor/settings/actions

Under "Workflow permissions":
- ✅ Select "Read and write permissions"
- ✅ Check "Allow GitHub Actions to create and approve pull requests"

## ✨ How It Works

Once setup is complete:

1. **Merge PR to main** or **push to main**
2. GitHub Action automatically:
   - Bumps patch version (0.1.2 → 0.1.3)
   - Builds package
   - Publishes to PyPI
   - Commits version bump
   - Creates GitHub release

## 📋 Daily Workflow

```bash
# 1. Make your changes
git checkout -b feature/my-feature

# 2. Commit your changes
git add .
git commit -m "feat: add new feature"

# 3. Push and create PR
git push origin feature/my-feature

# 4. Merge PR to main (via GitHub UI)
# 5. Publishing happens automatically! 🎉
```

## 🔧 Manual Version Bump (Optional)

If you want a specific version bump type:

```bash
# Patch: 0.1.2 → 0.1.3 (bug fixes)
./scripts/bump_version.sh patch

# Minor: 0.1.2 → 0.2.0 (new features)
./scripts/bump_version.sh minor

# Major: 0.1.2 → 1.0.0 (breaking changes)
./scripts/bump_version.sh major

# Then commit and push
git add pyproject.toml
git commit -m "chore: bump version to X.Y.Z"
git push origin main
```

## 🧪 Test Before Publishing

```bash
# Build locally
uv build

# Check output
ls -lh dist/

# Test installation
pip install dist/pydocextractor-*.whl
```

## 📦 Current Status

- **Package**: https://pypi.org/project/pydocextractor/
- **Current Version**: 0.1.2
- **Workflow**: `.github/workflows/publish.yml`

## ❓ Need Help?

See `PUBLISHING.md` for detailed documentation.

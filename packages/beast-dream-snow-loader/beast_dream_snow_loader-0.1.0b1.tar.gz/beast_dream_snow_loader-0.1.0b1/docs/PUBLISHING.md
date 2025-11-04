# Publishing to PyPI and SonarCloud

## Current Status

**Version:** `0.1.0b1` (Beta Pre-Release)

**Why Beta Pre-Release:**
- Pre-releases (versions with `.b1`, `.a1`, `.rc1`) are NOT installed by default
- Users must explicitly use `pip install --pre` to install
- Perfect for "work in progress" status
- Signals that the package is not production-ready yet

## PyPI Publishing

### Prerequisites

1. **PyPI Account**: Create account at https://pypi.org (if not already)
2. **Trusted Publishing**: Configure GitHub Actions for trusted publishing
   - Go to PyPI → Account Settings → API tokens
   - Add new project → "beast-dream-snow-loader"
   - Copy the trusted publishing configuration
   - Add to GitHub repository secrets (if needed)

### Publishing Steps

#### Option 1: GitHub Release (Recommended)

1. **Create GitHub Release:**
   - Go to GitHub repository → Releases → "Draft a new release"
   - Tag: `v0.1.0b1` (must match version in `pyproject.toml`)
   - Title: `v0.1.0b1 - Beta Pre-Release`
   - Description: Copy from [RELEASE_NOTES.md](../RELEASE_NOTES.md)
   - Check "Set as a pre-release" (important!)
   - Click "Publish release"

2. **GitHub Actions Will:**
   - Run quality checks (Ruff, Black, MyPy, pytest)
   - Build the package
   - Publish to PyPI automatically

#### Option 2: Manual Workflow Dispatch

1. **Trigger Workflow:**
   - Go to GitHub Actions → "Publish to PyPI" workflow
   - Click "Run workflow"
   - Enter version: `0.1.0b1`
   - Click "Run workflow"

### Verification

After publishing, verify:

1. **Check PyPI Page:**
   - Visit https://pypi.org/project/beast-dream-snow-loader/
   - Should show version `0.1.0b1`
   - Should show "Beta" development status

2. **Test Installation:**
   ```bash
   # Pre-releases require --pre flag
   pip install --pre beast-dream-snow-loader
   
   # Verify version
   python -c "import beast_dream_snow_loader; print(beast_dream_snow_loader.__version__)"
   # Should output: 0.1.0b1
   ```

3. **Default Installation Should NOT Work:**
   ```bash
   # This should NOT install pre-release
   pip install beast-dream-snow-loader
   # Should install latest stable (none yet, so should fail or warn)
   ```

## SonarCloud Setup

### Initial Setup

1. **Create SonarCloud Account:**
   - Go to https://sonarcloud.io
   - Sign in with GitHub account
   - Authorize SonarCloud access to GitHub repositories

2. **Create Project:**
   - Go to SonarCloud Dashboard → Projects
   - Click "Add Project" → "From GitHub"
   - Select organization: `nkllon`
   - Select repository: `beast-dream-snow-loader`
   - Choose pricing plan (free for open source)

3. **Configure Project:**
   - **Project Key**: `nkllon_beast-dream-snow-loader` (already set in `sonar-project.properties`)
   - **Organization**: `nkllon`
   - **Language**: Python
   - SonarCloud will auto-detect Python settings

4. **Add GitHub Secret:**
   - Go to GitHub repository → Settings → Secrets and variables → Actions
   - Add secret: `SONAR_TOKEN`
   - Get token from SonarCloud → My Account → Security → Generate Token
   - Copy token and add as `SONAR_TOKEN` secret

### Verification

After setup:

1. **Check Workflow:**
   - Go to GitHub Actions tab
   - Verify "SonarCloud Analysis" workflow runs on push to `main`

2. **Check SonarCloud:**
   - Visit https://sonarcloud.io/project/overview?id=nkllon_beast-dream-snow-loader
   - Verify analysis results appear
   - Check code coverage and quality metrics

## Version Management

### Pre-Release Versions

**Format:** `MAJOR.MINOR.PATCH{b|a|rc}N`

Examples:
- `0.1.0b1` - Beta 1 (current)
- `0.1.0b2` - Beta 2 (next beta)
- `0.1.0a1` - Alpha 1 (if needed)
- `0.1.0rc1` - Release Candidate 1
- `0.1.0` - Stable release (final)

**Pre-Release Behavior:**
- Users must use `pip install --pre` to install
- Default `pip install` will NOT install pre-releases
- Perfect for "work in progress" status

### Updating Version

1. **Update `pyproject.toml`:**
   ```toml
   version = "0.1.0b2"  # Next beta
   ```

2. **Update `src/beast_dream_snow_loader/__init__.py`:**
   ```python
   __version__ = "0.1.0b2"
   ```

3. **Update `sonar-project.properties`:**
   ```properties
   sonar.projectVersion=0.1.0b2
   ```

4. **Commit and push:**
   ```bash
   git add -A
   git commit -m "chore: bump version to 0.1.0b2"
   git push
   ```

5. **Create GitHub Release:**
   - Tag: `v0.1.0b2`
   - Mark as pre-release
   - Publish

## Testing GitHub Workflows

### Test CI Workflow

1. **Make a small change:**
   ```bash
   # Make a trivial change
   echo "# Test" >> README.md
   git add README.md
   git commit -m "test: trigger CI workflow"
   git push
   ```

2. **Check GitHub Actions:**
   - Go to Actions tab
   - Verify "CI" workflow runs
   - Check all quality checks pass

### Test Publish Workflow

1. **Create Test Release:**
   - Create GitHub release with tag `v0.1.0b1`
   - Mark as pre-release
   - Publish

2. **Monitor Workflow:**
   - Go to Actions tab
   - Watch "Publish to PyPI" workflow
   - Verify it publishes successfully

### Test SonarCloud Workflow

1. **Push to main:**
   ```bash
   git push origin main
   ```

2. **Check Workflow:**
   - Go to Actions tab
   - Verify "SonarCloud Analysis" workflow runs
   - Check SonarCloud dashboard for results

## Troubleshooting

### PyPI Publishing Issues

**"Package already exists":**
- Increment version number (e.g., `0.1.0b1` → `0.1.0b2`)
- Update version in `pyproject.toml` and `__init__.py`

**"403 Forbidden":**
- Check trusted publishing is configured
- Verify GitHub Actions has correct permissions
- Check PyPI project settings

**"Build fails":**
- Check `pyproject.toml` syntax
- Verify all dependencies are available
- Check quality gates pass

### SonarCloud Issues

**"Analysis not running":**
- Check GitHub Actions workflow is enabled
- Verify `SONAR_TOKEN` secret is set
- Check SonarCloud project exists

**"Token errors":**
- Verify `SONAR_TOKEN` secret is correct
- Regenerate token in SonarCloud if needed
- Check token has correct permissions

**"Project not found":**
- Verify project exists in SonarCloud dashboard
- Check project key matches `sonar-project.properties`
- Verify organization is correct

## Next Steps After First Release

1. **Monitor PyPI:**
   - Check download statistics
   - Monitor for issues
   - Review feedback

2. **Monitor SonarCloud:**
   - Address code quality issues
   - Improve test coverage
   - Fix security vulnerabilities

3. **Plan Next Release:**
   - Collect feedback
   - Address known limitations
   - Plan stable release (0.1.0)


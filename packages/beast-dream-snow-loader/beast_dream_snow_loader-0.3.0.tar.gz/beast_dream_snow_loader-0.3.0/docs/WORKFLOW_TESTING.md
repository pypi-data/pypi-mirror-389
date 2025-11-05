# Workflow Testing Guide

## Current Status

**Version:** `0.3.0` (Stable Release)

**Workflows Ready:**
- ✅ CI workflow (runs on push/PR)
- ✅ Publish workflow (runs on release)
- ✅ SonarCloud workflow (runs on push/PR)
- ✅ Test workflow (manual trigger for testing)

## Testing Workflows

### 1. CI Workflow (Automatically Triggered)

**Trigger:** Push to `main` or `develop` branch, or PR

**What It Does:**
- Runs quality checks (Ruff, Black, MyPy, pytest)
- Tests Python 3.10, 3.11, 3.12
- Builds package to verify it works

**To Test:**
1. Make a small change:
   ```bash
   echo "# Test" >> README.md
   git add README.md
   git commit -m "test: trigger CI workflow"
   git push
   ```

2. Check GitHub Actions:
   - Go to GitHub → Actions tab
   - Should see "CI" workflow running
   - Verify all checks pass

**Expected Result:**
- ✅ Quality checks pass
- ✅ Tests pass on all Python versions
- ✅ Package builds successfully

### 2. Publish Workflow (Manual or Release)

**Trigger:** 
- GitHub release (automatic)
- Manual workflow dispatch (testing)

**What It Does:**
- Runs quality checks
- Builds package
- Publishes to PyPI (if release)

**To Test (Dry Run):**
1. Go to GitHub → Actions → "Publish to PyPI"
2. Click "Run workflow"
3. Enter version: `0.3.0`
4. Click "Run workflow"
5. Watch it run (should stop before actually publishing if not a release)

**To Test (Actual Release):**
1. Create GitHub release:
   - Tag: `v0.3.0`
   - Title: `v0.3.0 - Documentation and Requirements Maturity`
   - Publish
2. Workflow will automatically run and publish to PyPI

**Expected Result:**
- ✅ Quality checks pass
- ✅ Package builds
- ✅ Publishes to PyPI (if release)
- ✅ Package available at https://pypi.org/project/beast-dream-snow-loader/

### 3. SonarCloud Workflow

**Trigger:** Push to `main` or PR

**Prerequisites:**
- SonarCloud project created
- `SONAR_TOKEN` secret added to GitHub

**To Test:**
1. Ensure SonarCloud project exists
2. Ensure `SONAR_TOKEN` secret is set
3. Push to `main`:
   ```bash
   git push origin main
   ```

4. Check GitHub Actions:
   - Should see "SonarCloud Analysis" workflow
   - Check SonarCloud dashboard for results

**Expected Result:**
- ✅ Workflow runs
- ✅ Analysis appears in SonarCloud
- ✅ Code coverage reported

### 4. Test Publish Workflow (Manual Testing)

**Trigger:** Manual workflow dispatch

**What It Does:**
- Runs all quality checks
- Builds package (dry run)
- Verifies version
- Does NOT publish (just tests)

**To Test:**
1. Go to GitHub → Actions → "Test Publish (Dry Run)"
2. Click "Run workflow"
3. Enter test version: `0.2.3`
4. Click "Run workflow"
5. Verify it completes successfully

**Expected Result:**
- ✅ All checks pass
- ✅ Package builds
- ✅ Version verified
- ✅ Summary shows ready for publishing

## Workflow Status

### Currently Running

After pushing the test commit, the CI workflow should be running:
- Check GitHub Actions tab
- Look for "CI" workflow
- Verify all jobs complete successfully

### Next Steps

1. **Verify CI Workflow:**
   - Check Actions tab for completed workflow
   - Ensure all quality checks pass
   - Ensure package builds

2. **Test Publish (Dry Run):**
   - Run "Test Publish (Dry Run)" workflow manually
   - Verify it completes successfully

3. **Set Up SonarCloud:**
   - Create SonarCloud project
   - Add `SONAR_TOKEN` secret
   - Push to trigger analysis

4. **Create GitHub Release:**
   - When ready, create release with tag `v0.2.3`
   - Workflow will publish to PyPI automatically

## Troubleshooting

### Workflow Fails - Missing Dependencies

**Issue:** `ruff`, `black`, `pytest` not found

**Fix:** Ensure dev dependencies are installed:
```bash
uv pip install -e ".[dev]"
```

### Workflow Fails - Package Build

**Issue:** `uv build` fails

**Fix:** Check `pyproject.toml` syntax:
```bash
uv build
```

### SonarCloud Fails - Token Error

**Issue:** `SONAR_TOKEN` not found

**Fix:** Add token to GitHub Secrets:
- Go to Settings → Secrets → Actions
- Add `SONAR_TOKEN` secret
- Get token from SonarCloud

### Publish Fails - Already Exists

**Issue:** "Package already exists"

**Fix:** Increment version:
- Update `pyproject.toml` version
- Update `__init__.py` version
- Create new release

## Verification Checklist

After workflows are set up:

- [ ] CI workflow runs on push to `main`
- [ ] CI workflow passes all quality checks
- [ ] Test matrix runs on Python 3.10, 3.11, 3.12
- [ ] Package builds successfully
- [ ] Publish workflow can be triggered manually
- [ ] SonarCloud project exists
- [ ] SonarCloud token is configured
- [ ] SonarCloud workflow runs on push
- [ ] Ready to create GitHub release for PyPI publishing


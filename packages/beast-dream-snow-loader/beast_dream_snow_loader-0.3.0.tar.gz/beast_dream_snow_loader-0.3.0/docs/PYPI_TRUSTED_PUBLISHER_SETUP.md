# PyPI Trusted Publisher Setup Guide

## What is Trusted Publishing?

**Trusted Publishing** is PyPI's secure way to publish packages **without storing passwords or API tokens** in GitHub secrets.

Instead of storing a long-lived API token:
- GitHub Actions requests a **short-lived token** from PyPI
- PyPI verifies the request is from your trusted repository/workflow
- PyPI issues a temporary token (valid for ~10 minutes)
- Your workflow uses it to publish

**Benefits:**
- ✅ No secrets to manage
- ✅ More secure (tokens expire quickly)
- ✅ Automatic authentication

## Setup Steps

### 1. Go to PyPI Account Settings

Visit: https://pypi.org/manage/account/publishing/

You'll need to be logged into your PyPI account.

### 2. Add a New Trusted Publisher

1. Click **"Add a new trusted publisher"**
2. Select **"GitHub Actions"** as the publisher type

### 3. Configure the Publisher

Fill in these fields:

- **PyPI project name:** `beast-dream-snow-loader`
  - If the project doesn't exist yet, create it first at https://pypi.org/manage/projects/
  
- **Owner (GitHub organization or username):** `nkllon`

- **Repository name:** `beast-dream-snow-loader`

- **Workflow filename:** `.github/workflows/publish.yml`
  - This must match the exact path in your repository

- **Environment name:** (leave empty)
  - Or use `main` if you want to restrict to a specific environment

### 4. Save and Verify

1. Click **"Add"** to save the trusted publisher
2. PyPI will show a confirmation message
3. The trusted publisher will appear in your list

## Verification

After setup, trigger a publish workflow:

1. Go to GitHub Actions → "Publish to PyPI" workflow
2. Click "Run workflow"
3. Enter version: `0.2.3`
4. Click "Run workflow"

**Expected Result:**
- ✅ Workflow runs successfully
- ✅ Package is published to PyPI
- ✅ No authentication errors

**If it fails:**
- Check the workflow logs for specific errors
- Verify the trusted publisher configuration matches exactly:
  - Repository name
  - Workflow filename
  - Environment (if specified)

## Troubleshooting

### "Publisher not found" or "403 Forbidden"

**Cause:** Trusted publisher not configured or configuration mismatch

**Fix:**
1. Verify trusted publisher exists in PyPI account settings
2. Check repository name matches exactly: `nkllon/beast-dream-snow-loader`
3. Check workflow filename matches: `.github/workflows/publish.yml`
4. Ensure PyPI project exists: `beast-dream-snow-loader`

### "Package name mismatch"

**Cause:** PyPI project name doesn't match `pyproject.toml`

**Fix:**
1. Check `pyproject.toml` has: `name = "beast-dream-snow-loader"`
2. Verify trusted publisher is linked to correct PyPI project name

### "Workflow not authorized"

**Cause:** Workflow filename or environment doesn't match

**Fix:**
1. Verify workflow file path: `.github/workflows/publish.yml`
2. Check if environment is specified (should be empty or match)

## Reference

- **PyPI Trusted Publishers Docs:** https://docs.pypi.org/trusted-publishers/
- **GitHub Actions Setup:** https://docs.pypi.org/trusted-publishers/using-a-publisher/
- **Troubleshooting:** https://docs.pypi.org/trusted-publishers/troubleshooting/

## Quick Setup Checklist

- [ ] PyPI account created
- [ ] PyPI project `beast-dream-snow-loader` created
- [ ] Trusted publisher added in PyPI account settings
- [ ] Repository: `nkllon/beast-dream-snow-loader`
- [ ] Workflow: `.github/workflows/publish.yml`
- [ ] Environment: (empty or `main`)
- [ ] Test publish workflow triggered
- [ ] Package appears on https://pypi.org/project/beast-dream-snow-loader/


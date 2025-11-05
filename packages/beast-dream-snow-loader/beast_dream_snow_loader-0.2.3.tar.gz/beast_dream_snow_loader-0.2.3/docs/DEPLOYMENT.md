# Deployment Guide

## PyPI Deployment

### Prerequisites

1. **PyPI Account**: Create account at https://pypi.org
2. **Trusted Publishing**: Configure GitHub Actions for trusted publishing (recommended)
   - Go to PyPI → Account Settings → API tokens
   - Add new project → "beast-dream-snow-loader"
   - Copy the trust publishing configuration
3. **Or API Token**: Generate API token for manual publishing

### Automatic Deployment (GitHub Actions)

The repository includes a GitHub Actions workflow that automatically publishes to PyPI when:

1. **GitHub Release Published**: Create a GitHub release with a tag (e.g., `v0.1.0`)
2. **Manual Workflow Dispatch**: Trigger workflow manually from GitHub Actions UI

**Workflow**: `.github/workflows/publish.yml`

**Steps:**
1. Runs quality checks (Ruff, Black, MyPy, pytest)
2. Builds the package
3. Publishes to PyPI using trusted publishing

### Manual Deployment

```bash
# Install build tools
uv pip install build twine

# Build package
uv build

# Check package
twine check dist/*

# Upload to PyPI (TestPyPI first)
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*
```

### Version Management

- Update version in `pyproject.toml` and `src/beast_dream_snow_loader/__init__.py`
- Use semantic versioning (MAJOR.MINOR.PATCH)
- Create GitHub release with matching tag

## SonarCloud Configuration

### Initial Setup

1. **Create SonarCloud Account**:
   - Go to https://sonarcloud.io
   - Sign in with GitHub account
   - Authorize SonarCloud access to GitHub repositories

2. **Create Project**:
   - Go to SonarCloud Dashboard → Projects
   - Click "Add Project" → "From GitHub"
   - Select organization: `nkllon`
   - Select repository: `beast-dream-snow-loader`
   - Choose pricing plan (free for open source)

3. **Configure Project**:
   - **Project Key**: `nkllon_beast-dream-snow-loader`
   - **Organization**: `nkllon`
   - **Language**: Python
   - SonarCloud will auto-detect Python settings

4. **Add GitHub Secret**:
   - Go to GitHub repository → Settings → Secrets and variables → Actions
   - Add secret: `SONAR_TOKEN`
   - Get token from SonarCloud → My Account → Security → Generate Token
   - Copy token and add as `SONAR_TOKEN` secret

### Workflow Configuration

The repository includes a SonarCloud workflow (`.github/workflows/sonarcloud.yml`) that:
- Runs on push to `main` branch
- Runs on pull requests
- Collects test coverage
- Uploads analysis to SonarCloud

### SonarCloud Project Settings

1. **Quality Gates**:
   - Default quality gate is usually sufficient
   - Can customize rules for project-specific needs

2. **Coverage**:
   - Coverage is collected via pytest with `--cov` flag
   - Coverage reports are automatically uploaded

3. **Analysis**:
   - Analysis runs automatically on each push
   - Results appear in SonarCloud dashboard
   - Issues and code smells are tracked

### Verification

1. **Check Workflow**:
   - Go to GitHub Actions tab
   - Verify "SonarCloud Analysis" workflow runs successfully

2. **Check SonarCloud**:
   - Visit https://sonarcloud.io/project/overview?id=nkllon_beast-dream-snow-loader
   - Verify analysis results appear
   - Check code coverage and quality metrics

## Post-Deployment Verification

### PyPI

1. **Verify Package**:
   ```bash
   pip install beast-dream-snow-loader
   ```

2. **Check PyPI Page**:
   - Visit https://pypi.org/project/beast-dream-snow-loader/
   - Verify version, description, and links

3. **Test Installation**:
   ```bash
   pip install beast-dream-snow-loader
   python -c "import beast_dream_snow_loader; print(beast_dream_snow_loader.__version__)"
   ```

### SonarCloud

1. **Check Analysis Results**:
   - Visit https://sonarcloud.io/project/overview?id=nkllon_beast-dream-snow-loader
   - Verify code analysis appears
   - Check quality gate status

2. **Review Issues**:
   - Go to Issues tab in SonarCloud
   - Review code smells, bugs, and vulnerabilities
   - Address critical issues

3. **Check Coverage**:
   - Go to Coverage tab
   - Verify test coverage is being reported
   - Aim for >80% coverage

## Troubleshooting

### PyPI Deployment Issues

- **403 Forbidden**: Check API token permissions
- **Package already exists**: Increment version number
- **Build fails**: Check `pyproject.toml` syntax and dependencies

### SonarCloud Issues

- **Analysis not running**: Check GitHub Actions workflow is enabled
- **Token errors**: Verify `SONAR_TOKEN` secret is set correctly
- **Coverage not reported**: Ensure pytest runs with `--cov` flag
- **Project not found**: Verify project is created in SonarCloud dashboard

## Security Considerations

1. **API Tokens**: Never commit PyPI API tokens to repository
2. **Trusted Publishing**: Use GitHub Actions trusted publishing when possible
3. **Environment Variables**: Store secrets in GitHub Secrets
4. **SonarCloud Token**: Store `SONAR_TOKEN` in GitHub Secrets (never commit)
5. **Code Quality**: Address security issues found by SonarCloud analysis


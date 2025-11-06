# CI/CD Guide for Python Optimizer

This guide explains the comprehensive CI/CD pipeline setup for the Python Optimizer project.

## 🚀 Overview

The project uses GitHub Actions for automated testing, building, and deployment. The pipeline includes:

- **Automated Testing** across multiple Python versions and operating systems
- **Code Quality Checks** (linting, formatting, type checking)
- **Security Scanning** for vulnerabilities
- **Performance Benchmarking**
- **Automated Package Building and Publishing**
- **Dependency Management** with Dependabot

## 📋 Pipeline Components

### 1. Main CI/CD Pipeline (`.github/workflows/ci.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main`
- Releases
- Daily scheduled runs (2 AM UTC)
- Manual workflow dispatch

**Jobs:**
- **Test Suite**: Runs on Ubuntu, macOS, and Windows with Python 3.11, 3.12, and 3.13
- **Performance Benchmarks**: Measures and tracks performance
- **Security Scanning**: Checks for vulnerabilities with Safety and Bandit
- **Package Building**: Builds distribution packages
- **PyPI Publishing**: Automatically publishes releases

### 2. Dependency Management (`.github/workflows/dependency-updates.yml`)

**Features:**
- Weekly dependency vulnerability scans
- Automated pre-commit hook updates
- Outdated package reporting
- Automated pull requests for updates

### 3. Release Automation (`.github/workflows/release.yml`)

**Features:**
- Manual version release triggers
- Automated changelog generation
- Version bumping in `pyproject.toml` and `__init__.py`
- GitHub release creation
- Post-release testing across platforms

### 4. Dependabot Configuration (`.github/dependabot.yml`)

**Automated updates for:**
- Python dependencies (weekly)
- GitHub Actions (weekly)
- Automatic reviewer assignment
- Proper labeling and commit formatting

## 🛠️ Local Development

### Quick Setup

```bash
# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
make pre-commit-install

# Run all CI/CD checks locally
make ci-check
```

### Available Commands

#### Makefile Commands
```bash
make ci-check          # Run all CI/CD checks
make ci-lint           # Run linting only
make ci-format-check   # Check code formatting
make ci-format-fix     # Fix formatting issues
make ci-test           # Run tests only
make ci-build          # Build package
```

#### Direct Script Usage
```bash
# Run specific steps
python scripts/ci_cd_helper.py --step lint
python scripts/ci_cd_helper.py --step test
python scripts/ci_cd_helper.py --step all

# Fix formatting automatically
python scripts/ci_cd_helper.py --fix
```

### Pre-commit Hooks

The project uses pre-commit hooks to ensure code quality:

```bash
# Install hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files

# Update hooks
pre-commit autoupdate
```

## 🔧 Configuration Files

### Code Quality Configuration

**`.codecov.yml`**: Coverage reporting configuration
- Target: 75% project coverage, 70% patch coverage
- Ignores test, example, and benchmark files

**`pyproject.toml`**: Contains configuration for:
- Black (code formatting)
- isort (import sorting)  
- MyPy (type checking)
- Pytest (testing)
- Coverage (test coverage)

**`.pre-commit-config.yaml`**: Pre-commit hook configuration
- Black, isort, flake8, mypy
- Security scanning with Bandit
- Documentation checks with pydocstyle
- General file hygiene checks

### GitHub Actions Configuration

**Environment Variables:**
```yaml
PYTHON_VERSION: "3.11"          # Primary Python version
PIP_CACHE_DIR: ~/.cache/pip     # Pip cache location
CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}  # Coverage reporting
```

**Required Secrets:**
- `PYPI_API_TOKEN`: For automated PyPI publishing
- `CODECOV_TOKEN`: For coverage reporting (optional)

## 📊 Monitoring and Reports

### Test Results
- **Artifacts**: Test results, coverage reports, and HTML coverage
- **Codecov**: Automated coverage reporting and PR comments
- **JUnit XML**: Test results in standard format

### Security Reports
- **Safety**: Dependency vulnerability scanning
- **Bandit**: Static security analysis for Python code
- **Artifacts**: JSON reports uploaded for each run

### Performance Tracking
- **Benchmark Results**: Performance test outputs
- **Artifacts**: Benchmark data for trend analysis

## 🚀 Release Process

### Automated Release Workflow

1. **Trigger Release**:
   ```bash
   # Go to GitHub Actions → Release workflow
   # Click "Run workflow"
   # Enter version (e.g., "0.2.0")
   # Choose if pre-release
   ```

2. **Automated Steps**:
   - Updates version in `pyproject.toml` and `__init__.py`
   - Generates changelog from git commits
   - Updates `CHANGELOG.md`
   - Creates git tag and GitHub release
   - Triggers package building and PyPI publishing
   - Tests installation across platforms

### Manual Release Process

```bash
# 1. Update version
sed -i 's/version = ".*"/version = "0.2.0"/' pyproject.toml

# 2. Update changelog
# Edit CHANGELOG.md manually

# 3. Commit and tag
git add pyproject.toml CHANGELOG.md
git commit -m "chore: bump version to 0.2.0"
git tag v0.2.0
git push origin main --tags

# 4. Create GitHub release (triggers CI/CD)
gh release create v0.2.0 --title "Release v0.2.0" --notes-file CHANGELOG.md
```

## 🐛 Troubleshooting

### Common Issues

**Tests failing locally but passing in CI:**
```bash
# Run tests exactly like CI
python -m pytest tests/ \
  --cov=python_optimizer \
  --cov-report=xml \
  --cov-report=html \
  --junitxml=test-results.xml \
  --tb=short -v
```

**Formatting issues:**
```bash
# Fix automatically
make ci-format-fix
# Or manually
black python_optimizer/
isort python_optimizer/
```

**Import errors in CI:**
- Check `pyproject.toml` dependencies
- Verify Python version compatibility
- Check import paths and package structure

**PyPI publishing failures:**
- Verify `PYPI_API_TOKEN` secret is set
- Check package version doesn't already exist
- Ensure `twine check dist/*` passes locally

### Debugging CI/CD

1. **Check GitHub Actions logs** for detailed error messages
2. **Run CI/CD helper locally** to reproduce issues
3. **Use draft releases** for testing release process
4. **Check artifact uploads** for test results and logs

## 📈 Metrics and Analytics

### Key Metrics Tracked
- **Test Coverage**: Target 80%+
- **Test Success Rate**: Should be 100%
- **Security Vulnerabilities**: Should be 0
- **Build Success Rate**: Target 95%+
- **Performance Benchmarks**: Track regression

### Dashboard Links
- **GitHub Actions**: `.github/workflows/` status
- **Codecov**: Coverage trends and PR impact
- **Dependabot**: Security and dependency updates
- **PyPI**: Download statistics and version usage

## 🔐 Security

### Security Measures
- **Dependency scanning** with Safety and Dependabot
- **Code security** analysis with Bandit
- **Secret scanning** by GitHub
- **Signed commits** recommended
- **Branch protection** rules on main branch

### Best Practices
- Regular dependency updates
- Security patch prioritization  
- Minimal required permissions for tokens
- Audit logs review for releases
- Vulnerability disclosure process

This CI/CD pipeline ensures high code quality, security, and reliability for the Python Optimizer project.
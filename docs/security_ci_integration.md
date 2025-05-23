# Bandit Security CI Integration

This file provides example configurations for integrating Bandit security scanning into your CI/CD pipeline.

## GitHub Actions Integration

Create `.github/workflows/security.yml`:

```yaml
name: Security Scan

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  security:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install bandit[toml]

    - name: Run Bandit Security Scan
      run: |
        bandit -r . -x ./venv,./nyc_landmarks_vector_db.egg-info -f json -o bandit-report.json
        bandit -r . -x ./venv,./nyc_landmarks_vector_db.egg-info

    - name: Upload security report
      uses: actions/upload-artifact@v4
      if: always()
      with:
        name: bandit-security-report
        path: bandit-report.json
```

## Pre-commit Hook Integration

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/PyCQA/bandit
    rev: '1.7.5'
    hooks:
      - id: bandit
        args: ['-x', './venv,./nyc_landmarks_vector_db.egg-info']
```

## Manual Commands

```bash
# Basic security scan
bandit -r . -x ./venv,./nyc_landmarks_vector_db.egg-info

# Generate JSON report
bandit -r . -x ./venv,./nyc_landmarks_vector_db.egg-info -f json -o security-report.json

# Scan only specific directories
bandit -r ./nyc_landmarks ./scripts

# Show only medium and high severity issues
bandit -r . -x ./venv,./nyc_landmarks_vector_db.egg-info -l
```

## Configuration Options

The project supports bandit configuration in two formats:

### 1. pyproject.toml (Used by pre-commit)

```toml
[tool.bandit]
exclude_dirs = ["venv", "nyc_landmarks_vector_db.egg-info", "__pycache__", ".git"]
skips = ["B101", "B404", "B603"]
```

### 2. .bandit (Used by direct bandit calls)

```ini
[bandit]
exclude_dirs = venv,nyc_landmarks_vector_db.egg-info,__pycache__,.git
skips = B101,B404,B603
```

**Note**: Both configurations contain the same settings:

- **Excluded directories**: venv, build artifacts, cache directories
- **Skipped tests**: B101 (assert usage), B404 (subprocess import), B603 (subprocess call)
- **Focus**: Medium and high severity issues for production code

## Security Standards

1. **All subprocess calls** must be validated and documented
1. **Random generation** must use `secrets` module for cryptographic purposes
1. **IP binding** must be justified and documented in test/dev contexts
1. **Exception handling** must include proper logging, not silent failures
1. **Security annotations** (`# nosec`) must include explanatory comments

## Regular Maintenance

- Run security scans before each release
- Review all `# nosec` annotations during security audits
- Update Bandit configuration as security requirements evolve
- Monitor for new security patterns and vulnerabilities

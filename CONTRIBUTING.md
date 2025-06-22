# Contributing to NYC Landmarks Vector DB

Thank you for considering contributing to the NYC Landmarks Vector Database project!
This document outlines the process and guidelines for contributing.

## Development Process

1. **Fork the repository** and clone your fork locally
1. **Set up the development environment** using one of these methods:
   - **Recommended:** Use VS Code with Dev Containers (see "Development Environment
     Options" in README.md)
   - Alternatively, follow the local setup instructions in README.md
1. **Create a new branch** for your feature or bugfix
   ```bash
   git checkout -b feature/your-feature-name
   ```
   or
   ```bash
   git checkout -b fix/issue-you-are-fixing
   ```
1. **Make your changes** following our code standards
1. **Run tests and linting** to ensure your changes meet our quality standards
   ```bash
   # Run tests
   pytest

   # Run pre-commit checks
   pre-commit run --all-files

   # If secret detection fails, see "Handling Secret Detection" below
   ```
1. **Commit your changes** with clear, descriptive commit messages
   ```bash
   git commit -m "Add feature: your feature description"
   ```
1. **Push to your fork** and submit a pull request

## Pull Request Process

1. Update the README.md or documentation with details of changes if appropriate
1. Make sure all CI checks pass
1. Your PR will be reviewed by at least one maintainer
1. Once approved, a maintainer will merge your changes

## Code Standards

We use several tools to enforce code quality:

### Python Style Guide

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Use [Black](https://black.readthedocs.io/) for code formatting with 88 character line
  length
- Sort imports with [isort](https://pycqa.github.io/isort/)

### Static Type Checking

- Use type hints for all functions and methods
- We use strict mypy checking to validate types

### Documentation

- Document all public modules, functions, classes, and methods
- Use Google-style docstrings
- Keep documentation up-to-date when changing code
- Store project-wide documentation, research, and improvement notes in the
  `memory-bank/` directory
- Use descriptive filenames with hyphens (e.g., `test-improvements.md`, `api-design.md`)

### Testing

- Write unit tests for all new code
- Maintain at least 80% test coverage
- Run the test suite before submitting PRs

### Security

- We use bandit to scan for security issues
- Never commit API keys or secrets
- Use environment variables for configuration

### Dependency Management

- Add new dependencies to `setup.py` in the appropriate section:
  - Runtime dependencies go in the `install_requires` list
  - Development dependencies go in the `extras_require["dev"]` list
  - Always add a comment explaining why the dependency is needed
- After adding a dependency to `setup.py`, update the requirements files:
  ```bash
  # Update requirements.txt for production dependencies
  ./scripts/ci/sync_versions.sh
  ```
- Document any new dependencies in your PR description

### GitHub Copilot Guidelines

- Store relevant project documentation in the `memory-bank/` directory
- When documenting changes or improvements, create or update a file in `memory-bank/`
- Use descriptive filenames with hyphens (e.g., `test-improvements.md`)
- When documenting code changes, include:got
  - Summary of changes
  - Motivation for changes
  - Benefits and improvements
  - Any potential side effects
  - Future considerations
- Update existing documentation rather than creating duplicates

## Setting Up Your Development Environment

### Pre-commit Hooks

We use pre-commit hooks to enforce code quality standards:

```bash
# Install pre-commit
pip install pre-commit

# Install the git hooks
pre-commit install

# Run against all files
pre-commit run --all-files
```

### Code Cleanup Guidelines {#code-cleanup-guidelines}

For detailed steps on code cleanup, please refer to the [Code Cleanup Guidelines](../../CONTRIBUTING.md#code-cleanup-guidelines) section in the `CONTRIBUTING.md` file.

### Security Scanning

The project includes automated security scanning with Bandit:

- **Pre-commit integration**: Security scans run automatically before each commit
- **Configuration**: Security settings are defined in `pyproject.toml` and `.bandit`
- **Excluded issues**: Legitimate usage patterns are excluded (assert in tests, subprocess with validation)
- **Manual scan**: Run `bandit -r . -x ./venv,./nyc_landmarks_vector_db.egg-info` for direct scanning

See `docs/security_ci_integration.md` for complete security documentation.

### Handling Secret Detection

The project uses **gitleaks** to automatically scan for API keys, tokens, and credentials in all files, including documentation. If the pre-commit hook fails with secret detection, follow these steps:

#### Understanding the Error

When secrets are detected, you'll see output like:

```
Detect secrets, API keys, and tokens.....................................Failed
- hook id: gitleaks-scan
- exit code: 1

❌ Secrets detected! Please review and remove any exposed API keys, tokens, or credentials.

Finding: TF_TOKEN_NYC_LANDMARKS=EXAMPLE_DETECTED_TOKEN_HERE
File: memory-bank/terraform_cloud_integration.md
Line: 17
```

#### Resolution Steps

1. **For Real API Keys/Tokens (IMMEDIATE ACTION REQUIRED)**:

   ```bash
   # ❌ NEVER commit real secrets
   OPENAI_API_KEY=sk-REAL_SECRET_KEY_HERE

   # ✅ Use environment variables instead
   OPENAI_API_KEY=your_openai_api_key_here
   ```

   - Remove the real secret immediately
   - Replace with placeholder text
   - Move real values to `.env` file (which is gitignored)

1. **For Documentation Examples**:

   ```bash
   # ❌ Avoid real-looking tokens in docs
   TF_TOKEN=REAL_LOOKING_TOKEN_HERE

   # ✅ Use obviously fake examples
   TF_TOKEN=your_terraform_cloud_token_here
   # or
   TF_TOKEN=example_token_replace_with_real_value
   ```

1. **For Template/Example Files**:

   - Use `.sample` or `.template` file extensions
   - Use obvious placeholders like `your_api_key_here`
   - These patterns are automatically allowlisted

#### Emergency Bypass (Use with Extreme Caution)

If you must temporarily bypass secret detection:

```bash
# Skip only secret scanning
SKIP=gitleaks-scan git commit -m "Your message"

# Skip all pre-commit hooks (NOT RECOMMENDED)
git commit --no-verify -m "Emergency commit"
```

**⚠️ WARNING**: Only use bypass in emergencies and ensure secrets are removed before pushing!

#### Testing Secret Detection

```bash
# Check for secrets manually
gitleaks detect --source=. --config=.gitleaks.toml --no-git

# Test specific file
gitleaks detect --source=path/to/file --config=.gitleaks.toml --no-git

# Run only the secret detection hook
pre-commit run gitleaks-scan --all-files
```

#### Common Issues and Solutions

| Issue                      | Solution                                                               |
| -------------------------- | ---------------------------------------------------------------------- |
| `.env` file with real keys | Move real keys to `.env` (gitignored), use `.env.sample` for templates |
| Documentation with tokens  | Replace with `your_token_here` or `example_token_...`                  |
| Template files detected    | Use `.sample` extension or obvious placeholders                        |
| Service account keys       | Use `YOUR_PRIVATE_KEY_HERE` placeholder                                |

For detailed guidance, see `docs/secret_detection_guide.md`.

## License

By contributing, you agree that your contributions will be licensed under the project's
MIT License.

# Contributing to NYC Landmarks Vector DB

Thank you for considering contributing to the NYC Landmarks Vector Database project! This document outlines the process and guidelines for contributing.

## Development Process

1. **Fork the repository** and clone your fork locally
2. **Set up the development environment** following instructions in the README.md
3. **Create a new branch** for your feature or bugfix
   ```bash
   git checkout -b feature/your-feature-name
   ```
   or
   ```bash
   git checkout -b fix/issue-you-are-fixing
   ```
4. **Make your changes** following our code standards
5. **Run tests and linting** to ensure your changes meet our quality standards
   ```bash
   # Run tests
   pytest

   # Run pre-commit checks
   pre-commit run --all-files
   ```
6. **Commit your changes** with clear, descriptive commit messages
   ```bash
   git commit -m "Add feature: your feature description"
   ```
7. **Push to your fork** and submit a pull request

## Pull Request Process

1. Update the README.md or documentation with details of changes if appropriate
2. Make sure all CI checks pass
3. Your PR will be reviewed by at least one maintainer
4. Once approved, a maintainer will merge your changes

## Code Standards

We use several tools to enforce code quality:

### Python Style Guide

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Use [Black](https://black.readthedocs.io/) for code formatting with 88 character line length
- Sort imports with [isort](https://pycqa.github.io/isort/)

### Static Type Checking

- Use type hints for all functions and methods
- We use strict mypy checking to validate types

### Documentation

- Document all public modules, functions, classes, and methods
- Use Google-style docstrings
- Keep documentation up-to-date when changing code

### Testing

- Write unit tests for all new code
- Maintain at least 80% test coverage
- Run the test suite before submitting PRs

### Security

- We use bandit to scan for security issues
- Never commit API keys or secrets
- Use environment variables for configuration

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

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License.

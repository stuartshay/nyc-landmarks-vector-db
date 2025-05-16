# Type Checking Setup

This project uses two type checkers:

- **mypy**: Primary type checker with stricter rules
- **pyright**: Secondary type checker with additional checks

## Configuration Files

- **mypy**: Configured in `mypy.ini`
- **pyright**: Configured in `pyrightconfig.json`

## Module-specific Overrides

We use module-specific overrides to handle special cases:

### mypy Overrides

```ini
[mypy.tests.*]
disallow_untyped_defs = false
disallow_incomplete_defs = false

[mypy.nyc_landmarks.db.db_client]
disallow_untyped_defs = false

[mypy.nyc_landmarks.models.wikipedia_models]
disallow_untyped_decorators = false
warn_unused_ignores = false
check_untyped_defs = false
```

Note: In our pre-commit configuration, we also disable specific error codes for smoother
integration:

```yaml
- id: mypy
  exclude: ^tests/
  args: ["--config-file=mypy.ini", "--disable-error-code=misc"]
```

### pyright Configuration

```json
{
  "include": ["nyc_landmarks"],
  "exclude": ["**/node_modules", "**/__pycache__", "**/*.pyc", "stubs"],
  "typeCheckingMode": "basic",
  "useLibraryCodeForTypes": true,
  "reportMissingImports": true,
  "reportMissingTypeStubs": false,
  "reportUnknownMemberType": false,
  "pythonVersion": "3.12",
  "pythonPlatform": "Linux",
  "reportGeneralTypeIssues": "none"
}
```

## Inline Type Ignore Comments

When necessary, we use specific type checker directives:

- For mypy: `# type: ignore[error-code]`
- For pyright: `# pyright: ignore[error-code]`

This approach allows us to satisfy both type checkers without unnecessary warnings.

## Running Type Checks

Run type checks for the entire project:

```bash
# Run mypy
mypy nyc_landmarks

# Run pyright
pyright nyc_landmarks
```

Or for specific files:

```bash
mypy path/to/file.py
pyright path/to/file.py
```

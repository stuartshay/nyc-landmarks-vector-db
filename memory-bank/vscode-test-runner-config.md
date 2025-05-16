# VS Code Test Runner Environment Configuration

## Issue

After adding Python environment variables to the `.env` file, the VS Code Test Runner
was no longer able to locate the Python interpreter and pytest executable. This was
because VS Code's settings were trying to use environment variables from the `.env`
file, but the VS Code Test Runner doesn't fully support this approach.

## Solution

We made the following changes to fix this issue:

1. Updated `.vscode/settings.json` to use explicit paths instead of environment
   variables:

   ```json
   "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
   "python.testing.pytestPath": "${workspaceFolder}/venv/bin/pytest"
   ```

1. Updated the `.env` and `.env.sample` files to clarify that the Python path
   environment variables are for scripts, not for VS Code:

   ```
   # Python Environment Paths (for scripts, not used by VS Code)
   PYTHON_PATH=${workspaceFolder}/venv/bin/python
   VENV_PATH=${workspaceFolder}/venv
   PYTEST_PATH=${VENV_PATH}/bin/pytest
   ```

## Best Practices

- VS Code settings should use explicit paths with `${workspaceFolder}` rather than
  relying on environment variables
- Scripts and command-line tools can still use the environment variables from `.env`
- Document clearly which configurations are used by which tools to avoid confusion

## Date

May 4, 2025

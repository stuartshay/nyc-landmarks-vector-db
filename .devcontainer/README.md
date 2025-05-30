# Development Container for NYC Landmarks Vector DB

This directory contains the configuration for the Visual Studio Code Development
Container, which provides a consistent development environment for all contributors.

## Features

- **Python 3.12** pre-configured with all dependencies
- **Pre-commit hooks** auto-installed and configured
- **VS Code extensions** for Python development, testing, and documentation
- **Testing environment** ready to run with pytest
- **Jupyter notebooks** support with JupyterLab
- **Google Cloud CLI** for cloud operations
- **Zsh with Oh My Zsh** for better terminal experience

## Getting Started

1. Install [Visual Studio Code](https://code.visualstudio.com/)
1. Install the
   [Remote - Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
1. Clone the repository
1. Create a `.env` file based on `.env.sample` with your API keys and configuration
1. Open the folder in VS Code and when prompted, click "Reopen in Container"

### Alternative: Manual Container Build

If you prefer not to use VS Code or need to test the container build process:

```bash
# Make the script executable
chmod +x ./start_devcontainer.sh

# Run the script to build and optionally launch VS Code
./start_devcontainer.sh
```

## Container Setup

The container automatically:

- Installs all dependencies from `setup.py` with the `dev` extras
- Configures pre-commit hooks
- Creates necessary directories for testing
- Sets up the Python environment with proper paths

## Running Tests

Tests can be run directly from the VS Code testing interface or via the terminal:

```bash
# Run all tests
python -m pytest tests -v

# Run specific test types
python -m pytest tests/unit -v
python -m pytest tests/functional -v
python -m pytest tests/integration -v
```

## Jupyter Notebooks

Jupyter notebooks can be run directly in VS Code or via JupyterLab:

```bash
# Start JupyterLab
jupyter lab
```

## Customizing

If you need additional tools or extensions, you can modify:

- `Dockerfile` to add system packages or Python libraries
- `devcontainer.json` to add VS Code extensions or settings

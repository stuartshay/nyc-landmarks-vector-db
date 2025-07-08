# Development Container for NYC Landmarks Vector DB

This directory contains the configuration for the Visual Studio Code Development
Container, which provides a consistent development environment for all contributors.

## ⚡ Quick Start: Pre-built Container (Recommended)

**Reduce DevContainer startup time from 3-8 minutes to 30-60 seconds!**

```bash
# Switch to pre-built container
./.devcontainer/manage-devcontainer.sh switch-to-prebuilt

# Then rebuild DevContainer in VS Code (Ctrl+Shift+P → "Dev Containers: Rebuild Container")
```

[📖 Full Pre-built Container Guide](#pre-built-devcontainer-setup)

## Features

- **Python 3.13** pre-configured with all dependencies
- **Pre-commit hooks** auto-installed and configured
- **VS Code extensions** for Python development, testing, and documentation
- **Testing environment** ready to run with pytest
- **Jupyter notebooks** support with JupyterLab
- **Google Cloud CLI** for cloud operations
- **Zsh with Oh My Zsh** for better terminal experience
- **Pre-built images** available on GitHub Container Registry and Docker Hub

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

## Pre-built DevContainer Setup

### Overview

The standard DevContainer build process takes **3-8 minutes** because it:

- Installs system dependencies (Docker, Azure CLI, AWS CLI, Java, etc.)
- Downloads and installs 240+ Python packages
- Sets up development tools and extensions

The pre-built container reduces this to **30-60 seconds** by:

- Pre-installing all dependencies in a container image
- Using GitHub Actions to build and publish the image
- Only installing project-specific code during startup

### Configuration Files

| File                         | Purpose                                         |
| ---------------------------- | ----------------------------------------------- |
| `devcontainer.json`          | Current active configuration                    |
| `devcontainer.prebuilt.json` | Template for pre-built container                |
| `devcontainer.json.backup`   | Backup of original configuration                |
| `Dockerfile.prebuilt`        | Optimized Dockerfile for pre-building           |
| `post-create-prebuilt.sh`    | Simplified setup script for pre-built container |
| `manage-devcontainer.sh`     | Script to switch between configurations         |

### Container Registries

The pre-built images are published to:

- **GitHub Container Registry:** `ghcr.io/stuartshay/nyc-landmarks-devcontainer`
- **Docker Hub:** `stuartshay/nyc-landmarks-devcontainer`

### Available Tags

| Tag        | Description                            |
| ---------- | -------------------------------------- |
| `latest`   | Latest stable build from master branch |
| `dev`      | Latest build from develop branch       |
| `master`   | Latest build from master branch        |
| `develop`  | Latest build from develop branch       |
| `YYYYMMDD` | Daily builds (scheduled)               |

### Management Commands

```bash
# Switch to pre-built container configuration
./.devcontainer/manage-devcontainer.sh switch-to-prebuilt

# Switch back to build-from-source configuration
./.devcontainer/manage-devcontainer.sh switch-to-build

# Check current configuration status
./.devcontainer/manage-devcontainer.sh status

# Build container locally for testing
./.devcontainer/manage-devcontainer.sh build-local

# Test the pre-built container
./.devcontainer/manage-devcontainer.sh test-prebuilt
```

### Performance Comparison

| Setup Type              | Startup Time  | What Happens                      |
| ----------------------- | ------------- | --------------------------------- |
| **Build from Source**   | 3-8 minutes   | Downloads and installs everything |
| **Pre-built Container** | 30-60 seconds | Only installs project code        |

### GitHub Actions Workflow

The `.github/workflows/build-devcontainer.yml` workflow:

1. **Triggers on:**

   - Changes to DevContainer files, requirements.txt, setup.py
   - Weekly schedule (security updates)
   - Manual dispatch

1. **Builds for multiple architectures:**

   - linux/amd64
   - linux/arm64

1. **Publishes to both registries:**

   - GitHub Container Registry (GHCR)
   - Docker Hub

1. **Includes security scanning:**

   - Trivy vulnerability scanner
   - Results uploaded to GitHub Security tab

### Setup Requirements for Docker Hub

Add these secrets to your GitHub repository:

1. Go to **Settings** → **Secrets and variables** → **Actions**
1. Add the following secrets:
   - `DOCKERHUB_USERNAME`: Your Docker Hub username
   - `DOCKERHUB_TOKEN`: Docker Hub access token

### Troubleshooting

**Container Pull Issues:**

- Make repository packages public in GitHub Packages settings
- Or authenticate with GHCR: `echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin`

**Build Failures:**

- Check Actions tab for error logs
- Verify Docker Hub credentials are set
- Check requirements.txt and Dockerfile syntax

**DevContainer Not Using Pre-built Image:**

- Run `./.devcontainer/manage-devcontainer.sh status` to verify configuration
- Force rebuild: `Ctrl+Shift+P` → "Dev Containers: Rebuild Container Without Cache"

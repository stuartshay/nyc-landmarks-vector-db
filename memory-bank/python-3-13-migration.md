# Python 3.13 Migration

## Summary of Changes

This document tracks the migration from Python 3.12 to Python 3.13 across the NYC Landmarks Vector DB project.

## Motivation for Changes

- **Latest Python Features**: Python 3.13 provides the latest language features, performance improvements, and security updates
- **Future-proofing**: Staying current with Python releases ensures long-term maintainability
- **Enhanced Performance**: Python 3.13 includes performance optimizations and better memory management

## Files Updated

### GitHub Actions Workflows

- `.github/workflows/pre-commit.yml` - Updated Python version to 3.13
- `.github/workflows/python-ci.yml` - Updated Python version matrix to [3.13]
- `.github/workflows/process_landmarks.yml` - Updated Python setup to 3.13
- `.github/workflows/sync-versions.yml` - Updated Python setup to 3.13
- `.github/workflows/dependency-review.yml` - Updated Python setup to 3.13

### Docker Configurations

- `Dockerfile` - Updated base image from `python:3.12-slim` to `python:3.13-slim`
- `.devcontainer/Dockerfile` - Updated base image to `python:3.13-slim`
- `.devcontainer/Dockerfile.prebuilt` - Updated base image and Python paths to 3.13

### Configuration Files

- `setup.py` - Already configured for Python 3.13
- `pyproject.toml` - Already configured with `requires-python = ">=3.13"`
- `mypy.ini` - Updated `python_version = 3.13`
- `pyrightconfig.json` - Updated `pythonVersion: "3.13"`
- `pyrightconfig-precommit.json` - Updated `pythonVersion: "3.13"`
- `.sonarqube/sonar-project.properties` - Updated `sonar.python.version=3.13`

### Branch Protection Rules

- `utils/branch_protection.json` - Updated CI check name to reference 3.13
- `utils/branch_protection_no_admin_enforce.json` - Updated CI check name to reference 3.13

## Setting Up Python 3.13 with Conda

### Installing Conda (if not already installed)

```bash
# Download and install Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
chmod +x Miniconda3-latest-Linux-x86_64.sh
./Miniconda3-latest-Linux-x86_64.sh

# Follow the installer prompts, then restart your shell or run:
source ~/.bashrc
```

### Creating a Python 3.13 Environment

```bash
# Create a new conda environment with Python 3.13
conda create -n nyc-landmarks-py313 python=3.13

# Activate the environment
conda activate nyc-landmarks-py313

# Verify Python version
python --version  # Should show Python 3.13.x
```

### Installing Project Dependencies

```bash
# Navigate to the project directory
cd /path/to/nyc-landmarks-vector-db

# Install the project in development mode
pip install -e ".[dev]"

# Or install from requirements.txt
pip install -r requirements.txt

# Install pre-commit hooks
pre-commit install
```

### Managing the Environment

```bash
# Activate the environment
conda activate nyc-landmarks-py313

# Deactivate the environment
conda deactivate

# List all conda environments
conda env list

# Remove the environment (if needed)
conda env remove -n nyc-landmarks-py313
```

### Setting Up in VS Code

1. **Select Python Interpreter**:

   - Open Command Palette (Ctrl+Shift+P)
   - Run "Python: Select Interpreter"
   - Choose the conda environment: `~/miniconda3/envs/nyc-landmarks-py313/bin/python`

1. **Configure Terminal**:

   - VS Code should automatically activate the conda environment in new terminals
   - If not, run `conda activate nyc-landmarks-py313` manually

### Alternative: Using conda-forge

For the latest Python versions, you might need to use conda-forge:

```bash
# Create environment with conda-forge channel
conda create -n nyc-landmarks-py313 -c conda-forge python=3.13

# Or update conda to get latest packages
conda update conda
conda update --all
```

## Benefits and Improvements

- **Performance**: Python 3.13 includes performance optimizations
- **Security**: Latest security patches and improvements
- **Language Features**: Access to newest Python language features
- **Compatibility**: Updated to work with the latest ecosystem packages

## Potential Side Effects

- **Dependencies**: Some packages may not yet support Python 3.13
- **Testing Required**: All functionality should be tested with the new Python version
- **CI/CD**: All workflows have been updated but should be monitored

## Future Considerations

- **Dependency Compatibility**: Monitor for package compatibility issues
- **Performance Testing**: Benchmark performance changes
- **Regular Updates**: Plan for future Python version migrations
- **Documentation**: Keep migration documentation current

## Testing the Migration

After setting up Python 3.13, verify everything works:

```bash
# Run the development environment check
python utils/check_dev_env.py

# Run all tests
python -m pytest tests/ -v

# Run pre-commit checks
pre-commit run --all-files

# Test imports
python -c "import nyc_landmarks; print('Import successful!')"
```

## Notes

- All configuration files have been updated to Python 3.13
- Docker images and CI/CD pipelines now use Python 3.13
- The project maintains backward compatibility requirements (>=3.13)
- Development containers have been updated to use Python 3.13

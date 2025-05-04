#!/usr/bin/env python3
"""
Environment Health Check Script

This script verifies that all required components of the development environment
are properly installed and configured. It checks for:

1. Python version
2. Required packages
3. Pre-commit hooks
4. Directory structure
5. Development tools

Run this script after setting up the environment to confirm everything is working.
"""

import importlib
import os
import subprocess  # nosec B404 - Subprocess is used safely with fixed commands
import sys
from pathlib import Path


def check_python_version() -> bool:
    """Check that Python is at least version 3.11."""
    print(f"Python version: {sys.version}")
    if sys.version_info.major != 3 or sys.version_info.minor < 11:
        print("❌ ERROR: Python 3.11 or higher is required")
        return False
    print("✅ Python version is 3.11+")
    return True


def check_packages() -> bool:
    """Check that required packages are installed."""
    required_packages = [
        "fastapi",
        "uvicorn",
        "openai",
        "pinecone",
        "pypdf",
        "pytest",
        "pre-commit",
        "black",
        "isort",
        "flake8",
        "mypy",
    ]

    all_installed = True
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package} is installed")
        except ImportError:
            print(f"❌ {package} is not installed")
            all_installed = False

    return all_installed


def check_directory_structure() -> bool:
    """Check that required directories exist."""
    required_dirs = [
        "nyc_landmarks",
        "tests",
        "scripts",
        "notebooks",
    ]

    all_dirs_exist = True
    for directory in required_dirs:
        if os.path.isdir(directory):
            print(f"✅ {directory}/ directory exists")
        else:
            print(f"❌ {directory}/ directory does not exist")
            all_dirs_exist = False

    return all_dirs_exist


def check_pre_commit() -> bool:
    """Check that pre-commit hooks are installed."""
    try:
        result = subprocess.run(
            ["pre-commit", "--version"], capture_output=True, text=True, check=True
        )  # nosec B603, B607 - Using fixed command
        print(f"✅ Pre-commit is installed: {result.stdout.strip()}")

        # Check if .git/hooks/pre-commit exists
        if Path(".git/hooks/pre-commit").exists():
            print("✅ Pre-commit hooks are installed")
            return True
        else:
            print("❌ Pre-commit hooks are not installed")
            return False
    except (subprocess.SubprocessError, FileNotFoundError):
        print("❌ Pre-commit is not installed or not working")
        return False


def check_development_tools() -> bool:
    """Check that development tools are working."""
    try:
        # Check pytest
        subprocess.run(
            ["pytest", "--version"], capture_output=True, check=True
        )  # nosec B603, B607 - Using fixed command
        print("✅ pytest is working")

        # Check black
        subprocess.run(
            ["black", "--version"], capture_output=True, check=True
        )  # nosec B603, B607 - Using fixed command
        print("✅ black formatter is working")

        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        print("❌ Some development tools are not installed properly")
        return False


def main() -> int:
    """Run all checks and report status."""
    print("NYC Landmarks Vector DB Environment Health Check")
    print("=" * 50)

    checks = [
        check_python_version(),
        check_packages(),
        check_directory_structure(),
        check_pre_commit(),
        check_development_tools(),
    ]

    print("\nSummary:")
    if all(checks):
        print("✅ All checks passed! Your development environment is ready.")
        return 0
    else:
        print(
            "❌ Some checks failed. Please review the output above and fix any issues."
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())

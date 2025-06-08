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

Examples:
  python utils/check_dev_env.py
"""

import importlib
import json
import os
import subprocess  # nosec B404 - Subprocess is used safely with fixed commands
import sys
from pathlib import Path
from typing import Optional


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
    all_tools_working = True

    # Check pytest
    try:
        subprocess.run(
            ["pytest", "--version"], capture_output=True, check=True
        )  # nosec B603, B607 - Using fixed command
        print("✅ pytest is working")
    except (subprocess.SubprocessError, FileNotFoundError):
        print("❌ pytest is not installed properly")
        all_tools_working = False

    # Check black
    try:
        subprocess.run(
            ["black", "--version"], capture_output=True, check=True
        )  # nosec B603, B607 - Using fixed command
        print("✅ black formatter is working")
    except (subprocess.SubprocessError, FileNotFoundError):
        print("❌ black formatter is not installed properly")
        all_tools_working = False

    # Check pyright
    try:
        result = subprocess.run(
            ["pyright", "--version"], capture_output=True, text=True, check=True
        )  # nosec B603, B607 - Using fixed command
        print(f"✅ pyright is working: {result.stdout.strip()}")
    except (subprocess.SubprocessError, FileNotFoundError):
        print("❌ pyright is not installed or not working")
        all_tools_working = False

    return all_tools_working


def run_command(command: str, description: str) -> Optional[str]:
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, check=True
        )  # nosec B602 - Using shell with validated input
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def check_gcp_service_account_key() -> bool:
    """Check if the GCP service account key file exists and is valid."""
    # Handle different possible paths
    repo_root = Path(__file__).resolve().parent.parent
    possible_paths = [
        repo_root / ".gcp/service-account-key.json",
        Path(os.getenv("GCP_KEY_PATH", "")),  # Fallback to environment variable if set
    ]

    found_key_path: Optional[Path] = None
    for path in possible_paths:
        if path.exists():
            found_key_path = path
            break

    if not found_key_path:
        print("❌ GCP service account key file not found")
        return False

    try:
        with open(found_key_path, 'r') as f:
            key_data = json.load(f)

        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        missing_fields = [field for field in required_fields if field not in key_data]

        if missing_fields:
            print(
                f"❌ GCP service account key missing required fields: {missing_fields}"
            )
            return False

        print("✅ GCP service account key found and valid")
        return True

    except json.JSONDecodeError:
        print("❌ GCP service account key file is not valid JSON")
        return False
    except Exception as e:
        print(f"❌ Error reading GCP service account key: {e}")
        return False


def check_gcp_environment_variables() -> bool:
    """Check if GCP environment variables are properly set."""
    gac_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')

    if not gac_path:
        print("⚠️  GOOGLE_APPLICATION_CREDENTIALS not set (will be set by devcontainer)")
        return True  # This is OK as it gets set by devcontainer

    if not Path(gac_path).exists():
        print(
            f"❌ GOOGLE_APPLICATION_CREDENTIALS points to non-existent file: {gac_path}"
        )
        return False

    print("✅ GOOGLE_APPLICATION_CREDENTIALS environment variable is set")
    return True


def check_gcp_authentication() -> bool:
    """Check GCP authentication status."""
    # Check if gcloud command is available
    if not run_command("which gcloud", "Checking gcloud availability"):
        print("❌ gcloud CLI not found in PATH")
        return False

    print("✅ gcloud CLI is available")

    # Check if gcloud is authenticated
    auth_list = run_command(
        "gcloud auth list --format='value(account)' --filter='status:ACTIVE'",
        "Checking gcloud authentication",
    )

    if not auth_list:
        print(
            "⚠️  No active gcloud authentication found (setup runs automatically in devcontainer)"
        )
        return True  # This is OK as setup runs automatically

    print(f"✅ Active gcloud account: {auth_list}")

    # Check project configuration
    project = run_command("gcloud config get-value project", "Getting active project")
    if project and project != "(unset)":
        print(f"✅ Active project: {project}")
    else:
        print("⚠️  No active project set (will be configured by setup script)")

    return True


def check_gcp_api_access() -> bool:
    """Test basic GCP API access if authentication is available."""
    # Only test if we have active authentication
    auth_list = run_command(
        "gcloud auth list --format='value(account)' --filter='status:ACTIVE'",
        "Checking for active authentication",
    )

    if not auth_list:
        print("⚠️  Skipping GCP API test - no active authentication")
        return True

    # Try to access GCP APIs
    result = run_command(
        "gcloud projects list --limit=1 --format='value(projectId)'",
        "Testing GCP API access",
    )

    if result:
        print("✅ GCP API access working")
        return True
    else:
        print("❌ GCP API access failed")
        return False


def check_gcp_setup() -> bool:
    """Check overall GCP setup."""
    print("\n🔧 Google Cloud Platform Setup")
    print("-" * 30)

    checks = [
        check_gcp_service_account_key(),
        check_gcp_environment_variables(),
        check_gcp_authentication(),
        check_gcp_api_access(),
    ]

    return all(checks)


def _validate_gcp_credentials(value: str) -> bool:
    """Validate Google Cloud credentials file."""
    if not Path(value).exists():
        print(f"   ⚠️  File does not exist: {value}")
        return False
    print("   📁 File exists and accessible")
    return True


def _validate_python_path(value: str) -> None:
    """Validate PYTHONPATH contains current directory."""
    current_dir = str(Path.cwd())
    if current_dir not in value:
        print("   ⚠️  Current directory not in PYTHONPATH")


def _format_display_value(value: str, max_length: int = 80) -> str:
    """Format environment variable value for display."""
    if len(value) <= max_length:
        return value
    return f"{value[:max_length - 3]}..."


def _format_sensitive_value(value: str) -> str:
    """Format sensitive environment variable value for display."""
    return f"{'*' * min(len(value), 20)} (length: {len(value)})"


def _check_important_variables() -> bool:
    """Check and validate important environment variables."""
    important_vars = {
        "PYTHONPATH": "Python module search path",
        "GOOGLE_APPLICATION_CREDENTIALS": "GCP service account key path",
        "PATH": "System executable search path",
        "VIRTUAL_ENV": "Python virtual environment path",
        "HOME": "User home directory",
        "SHELL": "Default shell",
        "TERM": "Terminal type",
    }

    all_good = True

    for var_name, description in important_vars.items():
        value = os.environ.get(var_name)
        if value:
            display_value = _format_display_value(value)
            print(f"✅ {var_name}: {display_value}")

            # Special validation for specific variables
            if var_name == "GOOGLE_APPLICATION_CREDENTIALS":
                if not _validate_gcp_credentials(value):
                    all_good = False
            elif var_name == "PYTHONPATH":
                _validate_python_path(value)
        else:
            if var_name in ["PYTHONPATH", "GOOGLE_APPLICATION_CREDENTIALS"]:
                print(f"❌ {var_name}: Not set (required)")
                all_good = False
            else:
                print(f"⚠️  {var_name}: Not set (optional but recommended)")

    return all_good


def _check_optional_variables() -> None:
    """Check and display optional project variables."""
    optional_vars = {
        "OPENAI_API_KEY": "OpenAI API key for embeddings",
        "PINECONE_API_KEY": "Pinecone vector database API key",
        "PINECONE_ENVIRONMENT": "Pinecone environment",
        "AZURE_STORAGE_CONNECTION_STRING": "Azure storage connection",
        "COREDATASTORE_API_BASE_URL": "CoreDataStore API base URL",
        "ENV": "Application environment (development/staging/production)",
        "LOG_LEVEL": "Application logging level",
        "LOG_PROVIDER": "Logging provider (stdout/google)",
        "LOG_NAME_PREFIX": "Prefix for log names",
    }

    print()
    print("📋 Optional Project Variables:")
    for var_name, description in optional_vars.items():
        value = os.environ.get(var_name)
        if value:
            if "KEY" in var_name or "TOKEN" in var_name or "SECRET" in var_name:
                display_value = _format_sensitive_value(value)
            else:
                display_value = _format_display_value(value, 60)
            print(f"✅ {var_name}: {display_value}")
        else:
            print(f"⚪ {var_name}: Not set ({description})")


def _check_python_environment() -> None:
    """Display Python environment information."""
    print()
    print("🐍 Python Environment Info:")
    print(f"✅ Python executable: {sys.executable}")
    print(f"✅ Python version: {sys.version.split()[0]}")
    print(f"✅ Platform: {sys.platform}")

    # Check if we're in a virtual environment
    if hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    ):
        venv_path = os.environ.get('VIRTUAL_ENV', sys.prefix)
        print(f"✅ Virtual environment: {venv_path}")
    else:
        print("⚠️  No virtual environment detected")


def check_environment_variables() -> bool:
    """Display and validate important environment variables."""
    print("\n🌍 Environment Variables")
    print("-" * 25)

    all_good = _check_important_variables()
    _check_optional_variables()
    _check_python_environment()

    return all_good


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
        check_gcp_setup(),
        check_environment_variables(),
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

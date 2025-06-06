import os
import subprocess  # nosec B404 - Subprocess is used safely with fixed commands

from setuptools import find_packages, setup
from setuptools.command.develop import develop
from setuptools.command.install import install


# Custom command to install pre-commit hooks
class PreCommitCommand:
    """Base class for installing pre-commit hooks."""

    def run_pre_commit_install(self) -> None:
        try:
            print("Installing pre-commit hooks...")
            subprocess.check_call(
                ["pre-commit", "install"]
            )  # nosec B603, B607 - Using fixed command
            print("Pre-commit hooks installed successfully!")
        except subprocess.CalledProcessError:
            print(
                "Failed to install pre-commit hooks. Make sure pre-commit is installed."
            )
        except FileNotFoundError:
            print(
                "Pre-commit not found. Please install it with 'pip install pre-commit'"
            )


class PostDevelopCommand(develop, PreCommitCommand):
    """Post-installation for development mode."""

    def run(self) -> None:
        develop.run(self)
        self.run_pre_commit_install()
        # Create test_output directory
        test_output_dir = os.path.join(os.getcwd(), "test_output")
        notebooks_output_dir = os.path.join(test_output_dir, "notebooks")
        if not os.path.exists(test_output_dir):
            os.makedirs(test_output_dir)
            print(f"Created directory: {test_output_dir}")
        if not os.path.exists(notebooks_output_dir):
            os.makedirs(notebooks_output_dir)
            print(f"Created directory: {notebooks_output_dir}")


class PostInstallCommand(install, PreCommitCommand):
    """Post-installation for installation mode."""

    def run(self) -> None:
        install.run(self)
        # Only install pre-commit hooks in development environments
        if os.environ.get("INSTALL_PRE_COMMIT", "false").lower() == "true":
            self.run_pre_commit_install()

        # Create test_output directory
        test_output_dir = os.path.join(os.getcwd(), "test_output")
        notebooks_output_dir = os.path.join(test_output_dir, "notebooks")
        if not os.path.exists(test_output_dir):
            os.makedirs(test_output_dir)
            print(f"Created directory: {test_output_dir}")
        if not os.path.exists(notebooks_output_dir):
            os.makedirs(notebooks_output_dir)
            print(f"Created directory: {notebooks_output_dir}")


setup(
    name="nyc-landmarks-vector-db",
    version="0.1.0",
    description="Vector database system for NYC landmarks with PDF text extraction and semantic search",
    author="NYC Landmarks Team",
    author_email="your-email@example.com",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.12",
    cmdclass={
        "develop": PostDevelopCommand,
        "install": PostInstallCommand,
    },
    install_requires=[
        "fastapi>=0.115.12",
        "uvicorn>=0.34.2",
        "openai>=1.82.0",
        "pinecone>=7.0.2",  # Updated to Pinecone 7.0.2 with 2025-04 API
        "pypdf>=5.4.0",  # Updated from pypdf2 to pypdf
        "pdfplumber>=0.11.6",
        "azure-storage-blob>=12.25.1",
        "google-cloud-secret-manager>=2.23.3",
        "pydantic>=2.11.4",
        "pydantic-settings>=2.9.1",  # Added for settings module
        "python-dotenv>=1.1.0",
        "tiktoken>=0.9.0",
        "numpy>=2.2.5",  # Added for vector tests - latest version as of May 2025
        "pandas>=2.3.0",  # Updated to latest version - Added for dataframe tests
        "tenacity>=9.1.2",  # Added for retry logic in API calls
        "beautifulsoup4>=4.13.4",  # Added for Wikipedia scraping
        "requests>=2.32.3",  # Added for HTTP requests
        "matplotlib>=3.10.3",  # Added for notebooks
        "folium>=0.19.5",  # Added for map visualizations in notebooks
        "scikit-learn>=1.7.0",  # Updated to latest version - Added for clustering in notebooks
        "transformers>=4.52.3",
        "openpyxl>=3.1.5",  # Added for Excel file manipulation
    ],
    extras_require={
        "dev": [
            "pytest>=8.3.5",
            "black>=25.1.0",
            "isort>=6.0.1",
            "flake8>=7.2.0",
            "mypy>=1.15.0",  # Updated version
            "mypy_extensions>=1.1.0",  # Added for mypy support
            "types-requests>=2.32.0.20250328",  # Added for requests type stubs
            "types-tabulate>=0.9.0.20241207",  # Corrected version constraint
            "types-setuptools>=80.3.0.20250505",  # Added for setuptools types
            "pandas-stubs>=2.2.3.250308",  # Add pandas-stubs - consolidated to higher version
            "nbstripout>=0.6.1",  # Added for notebook cleaning
            "pytest-cov>=6.1.1",  # Added for coverage
            "pytest-dotenv>=0.5.2",  # Added for loading .env files in tests
            "pandas>=2.3.0",  # Updated to match main requirements - Added explicitly for tests
            "numpy>=2.2.5",  # Added explicitly for tests - latest version as of May 2025
            "pytest-asyncio>=0.26.0",  # Added for asyncio support in tests
            "pre-commit>=3.8.0",  # Added for pre-commit hooks
            "pip-tools>=7.4.1",  # Added for managing requirements
            "pyright>=1.1.400",  # Added for static type checking
            "jupyterlab>=4.4.1",  # Added for running notebooks
            "ipywidgets>=8.1.7",  # Added for notebook interactivity
            "plotly>=6.0.1",  # Added for interactive plots in notebooks
            "seaborn>=0.13.2",  # Added for statistical plots in notebooks
            "tqdm>=4.67.1",  # Added for progress bars in notebooks/scripts
        ],
        "lint": ["ruff"],
        "coverage>=7.8.0": ["pytest-cov"],
    },
)

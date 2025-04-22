import os
import subprocess

from setuptools import find_packages, setup
from setuptools.command.develop import develop
from setuptools.command.install import install


# Custom command to install pre-commit hooks
class PreCommitCommand:
    """Base class for installing pre-commit hooks."""

    def run_pre_commit_install(self) -> None:
        try:
            print("Installing pre-commit hooks...")
            subprocess.check_call(["pre-commit", "install"])
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
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.11",
    cmdclass={
        "develop": PostDevelopCommand,
        "install": PostInstallCommand,
    },
    install_requires=[
        "fastapi>=0.115.0",
        "uvicorn>=0.34.0",
        "openai>=1.75.0",
        "pinecone>=2.0.0",  # Updated from pinecone-client to pinecone
        "pypdf2>=3.0.1",
        "pdfplumber>=0.11.0",
        "azure-storage-blob>=12.25.0",
        "google-cloud-secret-manager>=2.23.0",
        "pydantic>=2.11.0",
        "pydantic-settings>=2.2.0",  # Added for settings module
        "python-dotenv>=1.1.0",
        "tiktoken>=0.9.0",
        "numpy>=1.26.0",  # Added for vector tests
        "pandas>=2.2.0",  # Added for dataframe tests
        "tenacity>=8.2.0",  # Added for retry logic in API calls
    ],
    extras_require={
        "dev": [
            "pytest>=7.3.1",
            "black>=23.3.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.2.0",
            "pytest-cov>=6.1.1",  # Added for coverage
            "pandas>=2.2.0",  # Added explicitly for tests
            "numpy>=1.26.0",  # Added explicitly for tests
        ],
        "lint": ["ruff"],
        "coverage": ["pytest-cov"],
    },
)

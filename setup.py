import os
import subprocess

from setuptools import find_packages, setup
from setuptools.command.develop import develop
from setuptools.command.install import install


# Custom command to install pre-commit hooks
class PreCommitCommand:
    """Base class for installing pre-commit hooks."""

    def run_pre_commit_install(self):
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

    def run(self):
        develop.run(self)
        self.run_pre_commit_install()


class PostInstallCommand(install, PreCommitCommand):
    """Post-installation for installation mode."""

    def run(self):
        install.run(self)
        # Only install pre-commit hooks in development environments
        if os.environ.get("INSTALL_PRE_COMMIT", "false").lower() == "true":
            self.run_pre_commit_install()


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
        "fastapi>=0.95.0",
        "uvicorn>=0.21.0",
        "openai>=1.0.0",
        "pinecone-client>=2.2.1",
        "pypdf2>=3.0.0",
        "pdfplumber>=0.9.0",
        "azure-storage-blob>=12.16.0",
        "google-cloud-secret-manager>=2.16.1",
        "sqlalchemy>=2.0.0",
        "psycopg2-binary>=2.9.5",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "tiktoken>=0.5.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.3.1",
            "black>=23.3.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.2.0",
        ],
    },
)

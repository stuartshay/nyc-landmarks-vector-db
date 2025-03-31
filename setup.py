from setuptools import find_packages, setup

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

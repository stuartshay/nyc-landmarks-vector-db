# syntax=docker/dockerfile:1

FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ENV=production
ENV PIP_CACHE_DIR=/var/cache/pip

# Set work directory
WORKDIR /app

# Install system dependencies first for better layer caching
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies - copy only what's needed for dependency installation
COPY requirements.txt constraints.txt ./
COPY setup.py pyproject.toml ./

# Create pip cache directory with proper permissions
RUN mkdir -p $PIP_CACHE_DIR && \
    pip install --upgrade pip && \
    pip install --no-cache-dir -e . && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project files
COPY . .

# Pre-compile Python modules to save startup time
RUN python -m compileall -q nyc_landmarks/

# Install the package in development mode to ensure imports work
RUN pip install -e .

# Default command (adjust if needed)
CMD ["python", "-m", "nyc_landmarks.main"]

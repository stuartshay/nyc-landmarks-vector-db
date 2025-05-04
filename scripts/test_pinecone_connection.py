#!/usr/bin/env python3
"""
Simple script to test Pinecone DB connectivity.

Purpose:
    - Used as a pre-check in GitHub Actions workflow or other CI/CD pipelines.
    - Provides a fast, direct check of Pinecone API connectivity using only the official SDK.
    - Returns exit code 0 on success, 1 on failure, for easy integration with automation tools.
    - Does not depend on project-specific code or configuration, making it robust for infrastructure checks.

Usage:
    python scripts/test_pinecone_connection.py

Environment:
    Requires the PINECONE_API_KEY environment variable to be set.
"""

import os
import sys

try:
    from pinecone import Pinecone

    print("Initializing Pinecone connection...")
    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    print("Listing Pinecone indexes to verify connectivity...")
    indexes = pc.list_indexes()
    index_names = (
        [idx.name for idx in indexes]
        if hasattr(indexes, "__iter__")
        else getattr(indexes, "names", [])
    )
    print(f"Successfully connected to Pinecone. Available indexes: {index_names}")
    sys.exit(0)
except Exception as e:
    print(f"Failed to connect to Pinecone: {str(e)}")
    sys.exit(1)

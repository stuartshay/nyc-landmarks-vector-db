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

import sys

try:
    from nyc_landmarks.vectordb.pinecone_db import PineconeDB

    print("Initializing PineconeDB connection...")
    pinecone_db = PineconeDB()

    print("Testing Pinecone connection...")
    if pinecone_db.test_connection():
        index_names = pinecone_db.list_indexes()
        print(f"Successfully connected to Pinecone. Available indexes: {index_names}")
        sys.exit(0)
    else:
        print("Failed to connect to Pinecone index")
        sys.exit(1)
except Exception as e:
    print(f"Failed to connect to Pinecone: {str(e)}")
    sys.exit(1)

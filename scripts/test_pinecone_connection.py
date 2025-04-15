#!/usr/bin/env python3
"""
Simple script to test Pinecone DB connectivity.
Used as a pre-check in GitHub Actions workflow.
"""

import os
import sys

try:
    import pinecone

    print("Initializing Pinecone connection...")
    pinecone.init(
        api_key=os.environ["PINECONE_API_KEY"],
        environment=os.environ["PINECONE_ENVIRONMENT"],
    )
    print("Listing Pinecone indexes to verify connectivity...")
    indexes = pinecone.list_indexes()
    print(f"Successfully connected to Pinecone. Available indexes: {indexes}")
    sys.exit(0)
except Exception as e:
    print(f"Failed to connect to Pinecone: {str(e)}")
    sys.exit(1)

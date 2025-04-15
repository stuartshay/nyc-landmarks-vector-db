#!/usr/bin/env python3
"""
Simple script to test Pinecone DB connectivity.
Used as a pre-check in GitHub Actions workflow.
"""

import os
import sys

try:
    from pinecone import Pinecone

    print("Initializing Pinecone connection...")
    pc = Pinecone(
        api_key=os.environ["PINECONE_API_KEY"]
    )
    print("Listing Pinecone indexes to verify connectivity...")
    indexes = pc.list_indexes()
    print(f"Successfully connected to Pinecone. Available indexes: {indexes.names()}")
    sys.exit(0)
except Exception as e:
    print(f"Failed to connect to Pinecone: {str(e)}")
    sys.exit(1)

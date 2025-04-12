#!/usr/bin/env python
"""
Utility script to process landmark PDFs and store embeddings in Pinecone.

This script extracts text from landmark PDFs in Azure Blob Storage,
chunks the text, generates embeddings, and stores them in Pinecone.
"""

import argparse
import logging
import os
import sys
import time
from typing import Any, Dict, Optional

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nyc_landmarks.config.settings import settings
from nyc_landmarks.db.coredatastore_api import CoreDataStoreAPI
from nyc_landmarks.embeddings.generator import EmbeddingGenerator
from nyc_landmarks.pdf.extractor import PDFExtractor
from nyc_landmarks.pdf.text_chunker import TextChunker
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL.value,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("landmark_processing.log"),
    ],
)
logger = logging.getLogger(__name__)


def process_landmark(
    landmark_id: str,
    pdf_extractor: PDFExtractor,
    text_chunker: TextChunker,
    embedding_generator: EmbeddingGenerator,
    vector_db: PineconeDB,
    api_client: CoreDataStoreAPI,
    delete_existing: bool = False,
) -> Dict[str, Any]:
    """Process a landmark PDF and store embeddings.

    Args:
        landmark_id: ID of the landmark
        pdf_extractor: PDFExtractor instance
        text_chunker: TextChunker instance
        embedding_generator: EmbeddingGenerator instance
        vector_db: PineconeDB instance
        api_client: CoreDataStoreAPI instance
        delete_existing: Whether to delete existing vectors for this landmark

    Returns:
        Dictionary with processing results
    """
    result = {
        "landmark_id": landmark_id,
        "success": False,
        "chunks_count": 0,
        "vectors_stored": 0,
        "errors": [],
    }

    try:
        logger.info(f"Processing landmark: {landmark_id}")

        # Get landmark metadata from CoreDataStore API
        landmark_metadata = api_client.get_landmark_metadata(landmark_id)

        # Delete existing vectors if requested
        if delete_existing:
            logger.info(f"Deleting existing vectors for landmark: {landmark_id}")
            vector_db.delete_by_metadata({"landmark_id": landmark_id})

        # Extract text from PDF
        pdf_result = pdf_extractor.process_landmark_pdf(landmark_id)

        if not pdf_result.get("success"):
            error = pdf_result.get("error", "Unknown error extracting PDF")
            result["errors"].append(error)
            logger.error(f"Error processing landmark {landmark_id}: {error}")
            return result

        # Chunk text
        text = pdf_result.get("text", "")
        chunks = text_chunker.process_landmark_text(
            text=text,
            landmark_id=landmark_id,
            additional_metadata=landmark_metadata,
        )

        result["chunks_count"] = len(chunks)

        if not chunks:
            error = "No chunks generated from text"
            result["errors"].append(error)
            logger.error(f"Error processing landmark {landmark_id}: {error}")
            return result

        # Generate embeddings and store in Pinecone
        processed_chunks = embedding_generator.process_chunks(chunks)

        # Store vectors in Pinecone
        vector_ids = vector_db.store_chunks(
            processed_chunks, id_prefix=f"{landmark_id}-"
        )

        result["vectors_stored"] = len(vector_ids)

        if vector_ids:
            result["success"] = True
            logger.info(
                f"Successfully processed landmark {landmark_id}: {len(vector_ids)} vectors stored"
            )
        else:
            error = "No vectors stored in Pinecone"
            result["errors"].append(error)
            logger.error(f"Error processing landmark {landmark_id}: {error}")

        return result

    except Exception as e:
        error = str(e)
        result["errors"].append(error)
        logger.error(f"Error processing landmark {landmark_id}: {error}", exc_info=True)
        return result


def process_all_landmarks(
    limit: Optional[int] = None,
    delete_existing: bool = False,
) -> Dict[str, Any]:
    """Process all landmarks.

    Args:
        limit: Maximum number of landmarks to process
        delete_existing: Whether to delete existing vectors before processing

    Returns:
        Dictionary with processing results
    """
    # Initialize components
    pdf_extractor = PDFExtractor()
    text_chunker = TextChunker()
    embedding_generator = EmbeddingGenerator()
    vector_db = PineconeDB()
    api_client = CoreDataStoreAPI()

    results = {
        "total_landmarks": 0,
        "successful_landmarks": 0,
        "failed_landmarks": 0,
        "total_chunks": 0,
        "total_vectors": 0,
        "landmark_results": [],
    }

    try:
        # Get landmarks from CoreDataStore API
        landmarks = api_client.get_all_landmarks(limit=limit)

        results["total_landmarks"] = len(landmarks)

        # Process each landmark
        for landmark in landmarks:
            landmark_id = landmark.get("id")

            if not landmark_id:
                logger.warning(f"Landmark missing ID: {landmark}")
                continue

            # Process landmark
            result = process_landmark(
                landmark_id=landmark_id,
                pdf_extractor=pdf_extractor,
                text_chunker=text_chunker,
                embedding_generator=embedding_generator,
                vector_db=vector_db,
                api_client=api_client,
                delete_existing=delete_existing,
            )

            # Add result to results
            results["landmark_results"].append(result)

            # Update counts
            if result["success"]:
                results["successful_landmarks"] += 1
            else:
                results["failed_landmarks"] += 1

            results["total_chunks"] += result["chunks_count"]
            results["total_vectors"] += result["vectors_stored"]

            # Sleep to avoid rate limits
            time.sleep(0.5)

        return results

    except Exception as e:
        logger.error(f"Error processing landmarks: {e}", exc_info=True)
        return results


def process_specific_landmark(
    landmark_id: str,
    delete_existing: bool = False,
) -> Dict[str, Any]:
    """Process a specific landmark.

    Args:
        landmark_id: ID of the landmark to process
        delete_existing: Whether to delete existing vectors before processing

    Returns:
        Dictionary with processing results
    """
    # Initialize components
    pdf_extractor = PDFExtractor()
    text_chunker = TextChunker()
    embedding_generator = EmbeddingGenerator()
    vector_db = PineconeDB()
    api_client = CoreDataStoreAPI()

    # Process landmark
    return process_landmark(
        landmark_id=landmark_id,
        pdf_extractor=pdf_extractor,
        text_chunker=text_chunker,
        embedding_generator=embedding_generator,
        vector_db=vector_db,
        api_client=api_client,
        delete_existing=delete_existing,
    )


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Process landmark PDFs and store embeddings in Pinecone"
    )

    # Add command-line arguments
    parser.add_argument(
        "--landmark-id",
        help="ID of a specific landmark to process",
    )

    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of landmarks to process",
    )

    parser.add_argument(
        "--delete-existing",
        action="store_true",
        help="Delete existing vectors before processing",
    )

    # Parse arguments
    args = parser.parse_args()

    # Process landmarks
    if args.landmark_id:
        logger.info(f"Processing landmark: {args.landmark_id}")
        result = process_specific_landmark(
            landmark_id=args.landmark_id,
            delete_existing=args.delete_existing,
        )

        if result["success"]:
            logger.info(f"Successfully processed landmark {args.landmark_id}")
            logger.info(
                f"Chunks: {result['chunks_count']}, Vectors: {result['vectors_stored']}"
            )
        else:
            logger.error(f"Failed to process landmark {args.landmark_id}")
            logger.error(f"Errors: {result['errors']}")

        return result
    else:
        logger.info("Processing all landmarks")
        results = process_all_landmarks(
            limit=args.limit,
            delete_existing=args.delete_existing,
        )

        logger.info(f"Total landmarks: {results['total_landmarks']}")
        logger.info(
            f"Successful: {results['successful_landmarks']}, Failed: {results['failed_landmarks']}"
        )
        logger.info(
            f"Total chunks: {results['total_chunks']}, Total vectors: {results['total_vectors']}"
        )

        return results


if __name__ == "__main__":
    main()

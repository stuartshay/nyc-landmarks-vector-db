#!/usr/bin/env python
"""
Process All Landmarks Script

This script processes all NYC landmark records and stores them in Pinecone for vector search.
It will check which landmarks are already in the database and only process the unprocessed ones.

Usage:
    python -m scripts.process_all_landmarks [--limit N] [--batch-size N]

Options:
    --limit N        Limit processing to N landmarks (for testing)
    --batch-size N   Process landmarks in batches of N (default: 10)
"""

import argparse
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import numpy as np
from tqdm import tqdm

from nyc_landmarks.config.settings import settings
from nyc_landmarks.db.db_client import get_db_client
from nyc_landmarks.embeddings.generator import EmbeddingGenerator
from nyc_landmarks.pdf.extractor import PDFExtractor
from nyc_landmarks.pdf.text_chunker import TextChunker
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=settings.LOG_LEVEL.value,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            f"logs/process_all_landmarks_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        ),
    ],
)


def fetch_all_landmark_ids(
    db_client: Any, page_size: int = 100, limit: Optional[int] = None
) -> Set[str]:
    """
    Fetch all landmark IDs from the CoreDataStore API.

    Args:
        db_client: Database client
        page_size: Number of landmarks per page
        limit: Maximum number of landmarks to fetch (for testing)

    Returns:
        Set of unique landmark IDs
    """
    all_landmark_ids = set()
    current_page = 1
    total_pages_fetched = 0

    logger.info("Fetching landmark IDs from CoreDataStore API")

    try:
        with tqdm(desc="Fetching landmark IDs", unit="page") as pbar:
            while True:
                # Fetch landmarks for the current page
                try:
                    landmarks = db_client.get_landmarks_page(page_size, current_page)
                except Exception as e:
                    logger.error(f"Error fetching page {current_page}: {e}")
                    # Try to continue with next page
                    current_page += 1
                    total_pages_fetched += 1
                    pbar.update(1)
                    continue

                # If no landmarks found, we've reached the end
                if not landmarks:
                    logger.info(
                        f"No landmarks found on page {current_page}, ending fetch"
                    )
                    break

                # Process the landmarks
                for landmark in landmarks:
                    landmark_id = landmark.get("id", "") or landmark.get("lpNumber", "")
                    if landmark_id:
                        all_landmark_ids.add(landmark_id)

                # Update progress
                pbar.set_postfix(
                    {
                        "page": current_page,
                        "landmarks": len(landmarks),
                        "total": len(all_landmark_ids),
                    }
                )
                pbar.update(1)

                # Move to next page
                current_page += 1
                total_pages_fetched += 1

                # Apply limit if specified
                if limit and len(all_landmark_ids) >= limit:
                    logger.info(f"Reached specified limit of {limit} landmarks")
                    break

                # Small delay to avoid rate limiting
                time.sleep(0.5)
    except Exception as e:
        logger.error(f"Error fetching landmark IDs: {e}")

    logger.info(
        f"Completed fetching {len(all_landmark_ids)} landmark IDs from {total_pages_fetched} pages"
    )
    return all_landmark_ids


def check_processing_status(
    pinecone_db: PineconeDB, landmark_ids: Set[str], batch_size: int = 10
) -> Tuple[Set[str], Set[str]]:
    """
    Check which landmarks already have vectors in Pinecone.

    Args:
        pinecone_db: PineconeDB instance
        landmark_ids: Set of landmark IDs to check
        batch_size: Number of landmarks to check in parallel batches

    Returns:
        Tuple containing:
            processed_landmarks: Set of landmark IDs that have vectors
            unprocessed_landmarks: Set of landmark IDs that don't have vectors
    """
    # Generate a random query vector for searching
    random_vector = np.random.rand(pinecone_db.dimensions).tolist()

    processed_landmarks = set()
    unprocessed_landmarks = set()

    # Convert set to list for iteration with tqdm
    landmark_ids_list = list(landmark_ids)

    logger.info(f"Checking processing status for {len(landmark_ids)} landmarks")

    with tqdm(total=len(landmark_ids_list), desc="Checking processing status") as pbar:
        for i in range(0, len(landmark_ids_list), batch_size):
            # Get the current batch
            batch = landmark_ids_list[i : i + batch_size]

            # Check each landmark in the batch
            for landmark_id in batch:
                # Query Pinecone for vectors with this landmark_id
                filter_dict = {"landmark_id": landmark_id}
                try:
                    # We only need to know if vectors exist, so top_k=1 is sufficient
                    vectors = pinecone_db.query_vectors(
                        query_vector=random_vector, top_k=1, filter_dict=filter_dict
                    )

                    # If vectors found, mark as processed, otherwise unprocessed
                    if vectors:
                        processed_landmarks.add(landmark_id)
                    else:
                        unprocessed_landmarks.add(landmark_id)
                except Exception as e:
                    logger.error(f"Error checking landmark {landmark_id}: {e}")
                    # If we can't check, assume unprocessed to be safe
                    unprocessed_landmarks.add(landmark_id)

            # Update progress
            pbar.update(len(batch))
            pbar.set_postfix(
                {
                    "processed": len(processed_landmarks),
                    "unprocessed": len(unprocessed_landmarks),
                }
            )

            # Small delay to avoid rate limiting
            time.sleep(0.2)

    logger.info(
        f"Found {len(processed_landmarks)} processed landmarks and {len(unprocessed_landmarks)} unprocessed landmarks"
    )
    return processed_landmarks, unprocessed_landmarks


def process_landmark(
    db_client: Any,
    pinecone_db: PineconeDB,
    embedding_generator: EmbeddingGenerator,
    pdf_extractor: PDFExtractor,
    text_chunker: TextChunker,
    landmark_id: str,
) -> Tuple[bool, int, Optional[str]]:
    """
    Process a single landmark and store its vectors in Pinecone.

    Args:
        db_client: Database client for fetching landmark details
        pinecone_db: PineconeDB instance for storing vectors
        embedding_generator: Embedding generator for creating embeddings
        pdf_extractor: PDF extractor for extracting text from PDFs
        text_chunker: Text chunker for chunking text
        landmark_id: ID of the landmark to process

    Returns:
        Tuple containing:
            success: Boolean indicating if processing succeeded
            chunk_count: Number of chunks processed
            error: Error message if any, None otherwise
    """
    try:
        # Get landmark details from API
        landmark = db_client.get_lpc_report(landmark_id)
        if not landmark:
            return False, 0, f"Landmark {landmark_id} not found in API"

        # Check if the landmark has a PDF report
        pdf_url = landmark.get("pdfReportUrl")
        if not pdf_url:
            return False, 0, f"Landmark {landmark_id} has no PDF report"

        # Extract text from PDF
        text = pdf_extractor.extract_text_from_url(pdf_url)
        if not text:
            return (
                False,
                0,
                f"Failed to extract text from PDF for landmark {landmark_id}",
            )

        # Chunk the text
        chunks = text_chunker.chunk_text_by_tokens(text)
        if not chunks:
            return False, 0, f"Failed to chunk text for landmark {landmark_id}"

        # Create metadata and get embeddings
        processed_chunks = []
        for i, chunk in enumerate(chunks):
            # Create metadata
            metadata = {
                "landmark_id": landmark_id,
                "name": landmark.get("name", ""),
                "borough": landmark.get("borough", ""),
                "chunk_index": i,
                "total_chunks": len(chunks),
                "source": "pd",
                "pdf_url": pdf_url,
            }

            # Generate embedding
            embedding = embedding_generator.generate_embedding(chunk)

            # Add to processed chunks
            processed_chunks.append(
                {
                    "text": chunk,
                    "metadata": metadata,
                    "embedding": embedding,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                }
            )

        # Store in Pinecone with fixed IDs
        vector_ids = pinecone_db.store_chunks_with_fixed_ids(
            chunks=processed_chunks, landmark_id=landmark_id
        )

        if not vector_ids:
            return False, 0, f"Failed to store vectors for landmark {landmark_id}"

        return True, len(processed_chunks), None
    except Exception as e:
        return False, 0, str(e)


def process_landmarks_batch(
    db_client: Any,
    pinecone_db: PineconeDB,
    embedding_generator: EmbeddingGenerator,
    pdf_extractor: PDFExtractor,
    text_chunker: TextChunker,
    landmarks_to_process: List[str],
    batch_size: int = 10,
) -> Dict[str, Any]:
    """
    Process a batch of landmarks and store their vectors in Pinecone.

    Args:
        db_client: Database client for fetching landmark details
        pinecone_db: PineconeDB instance for storing vectors
        embedding_generator: Embedding generator for creating embeddings
        pdf_extractor: PDF extractor for extracting text from PDFs
        text_chunker: Text chunker for chunking text
        landmarks_to_process: List of landmark IDs to process
        batch_size: Size of each batch to process at once

    Returns:
        Dict with processing statistics
    """
    results: Dict[str, Any] = {
        "total": len(landmarks_to_process),
        "successful": 0,
        "failed": 0,
        "total_chunks": 0,
        "failures": {},
    }

    logger.info(f"Processing {len(landmarks_to_process)} landmarks")

    with tqdm(total=len(landmarks_to_process), desc="Processing landmarks") as pbar:
        # Process in batches to avoid memory issues
        for i in range(0, len(landmarks_to_process), batch_size):
            batch = landmarks_to_process[i : i + batch_size]
            batch_success = 0
            batch_failures = 0
            batch_chunks = 0

            # Process each landmark in the batch
            for landmark_id in batch:
                success, chunk_count, error = process_landmark(
                    db_client,
                    pinecone_db,
                    embedding_generator,
                    pdf_extractor,
                    text_chunker,
                    landmark_id,
                )

                if success:
                    batch_success += 1
                    batch_chunks += chunk_count
                    logger.info(
                        f"Successfully processed landmark {landmark_id} with {chunk_count} chunks"
                    )
                else:
                    batch_failures += 1
                    results["failures"][landmark_id] = error
                    logger.error(f"Failed to process landmark {landmark_id}: {error}")

            # Update results
            results["successful"] += batch_success
            results["failed"] += batch_failures
            results["total_chunks"] += batch_chunks

            # Update progress
            pbar.update(len(batch))
            pbar.set_postfix(
                {
                    "successful": results["successful"],
                    "failed": results["failed"],
                    "chunks": results["total_chunks"],
                }
            )

            # Small delay to avoid rate limiting
            time.sleep(1)

    return results


def save_results(
    results: Dict[str, Any], output_dir: Optional[Union[str, Path]] = None
) -> None:
    """
    Save processing results to files.

    Args:
        results: Processing results dictionary
        output_dir: Output directory for result files
    """
    if output_dir is None:
        output_dir = Path("data/processing_results")

    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save full results
    results_file = output_dir / f"processing_results_{timestamp}.json"
    import json

    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)

    logger.info(f"Saved processing results to {results_file}")

    # Save failures list for easier retry
    if results["failures"]:
        failures_file = output_dir / f"failed_landmarks_{timestamp}.json"
        with open(failures_file, "w") as f:
            json.dump(
                {
                    "failed_landmarks": list(results["failures"].keys()),
                    "failure_reasons": results["failures"],
                },
                f,
                indent=2,
            )
        logger.info(f"Saved failed landmarks list to {failures_file}")


def main() -> None:
    """
    Main entry point.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Process all NYC landmarks and store in Pinecone"
    )
    parser.add_argument("--limit", type=int, help="Limit to N landmarks (for testing)")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Process landmarks in batches of N (default: 10)",
    )
    args = parser.parse_args()

    # Create log directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)

    # Initialize clients and utilities
    logger.info("Initializing clients and utilities")
    db_client = get_db_client()
    pinecone_db = PineconeDB()
    embedding_generator = EmbeddingGenerator()
    pdf_extractor = PDFExtractor()
    text_chunker = TextChunker()

    # Check if Pinecone connection was successful
    if not pinecone_db.index:
        logger.error(
            "Failed to connect to Pinecone. Check your credentials and network connection."
        )
        return

    logger.info(f"Successfully connected to Pinecone index: {pinecone_db.index_name}")

    # Fetch landmarks
    all_landmark_ids = fetch_all_landmark_ids(db_client, limit=args.limit)

    if not all_landmark_ids:
        logger.error("No landmarks found. Exiting.")
        return

    # Check processing status
    processed_landmarks, unprocessed_landmarks = check_processing_status(
        pinecone_db, all_landmark_ids, batch_size=args.batch_size
    )

    # Print status
    logger.info(f"Total landmarks: {len(all_landmark_ids)}")
    logger.info(
        f"Processed landmarks: {len(processed_landmarks)} ({len(processed_landmarks) / len(all_landmark_ids) * 100:.2f}%)"
    )
    logger.info(
        f"Unprocessed landmarks: {len(unprocessed_landmarks)} ({len(unprocessed_landmarks) / len(all_landmark_ids) * 100:.2f}%)"
    )

    # Process unprocessed landmarks
    if unprocessed_landmarks:
        logger.info(f"Processing {len(unprocessed_landmarks)} unprocessed landmarks")

        start_time = time.time()
        results = process_landmarks_batch(
            db_client,
            pinecone_db,
            embedding_generator,
            pdf_extractor,
            text_chunker,
            list(unprocessed_landmarks),
            batch_size=args.batch_size,
        )
        elapsed_time = time.time() - start_time

        # Save results
        save_results(results)

        # Print summary
        logger.info(f"\nProcessing completed in {elapsed_time:.2f} seconds")
        logger.info(f"Total landmarks processed: {results['total']}")
        logger.info(
            f"Successfully processed: {results['successful']} "
            f"({results['successful'] / results['total'] * 100:.2f}%)"
        )
        logger.info(
            f"Failed to process: {results['failed']} "
            f"({results['failed'] / results['total'] * 100:.2f}%)"
        )
        logger.info(f"Total chunks created: {results['total_chunks']}")

        # Verify final status
        if results["successful"] == results["total"]:
            logger.info("✅ All landmarks processed successfully!")
        else:
            logger.warning(
                f"⚠️ {results['failed']} landmarks failed to process. "
                "Check logs and failures file for details."
            )

            # Print first few failures
            if results["failures"]:
                logger.info("\nFirst 5 failures:")
                for i, (landmark_id, error) in enumerate(
                    list(results["failures"].items())[:5]
                ):
                    logger.info(f"  {landmark_id}: {error}")
    else:
        logger.info(
            "No unprocessed landmarks found. All landmarks are already processed."
        )


if __name__ == "__main__":
    main()

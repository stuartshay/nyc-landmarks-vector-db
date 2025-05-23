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


def extract_landmark_id(landmark: Any) -> Optional[str]:
    """
    Extract landmark ID from either a Pydantic model or dictionary.

    Args:
        landmark: A landmark object or dictionary

    Returns:
        The landmark ID or None if it couldn't be extracted
    """
    # Handle both dictionary and Pydantic model responses
    if hasattr(landmark, "lpNumber"):
        # It's a Pydantic model
        lp_number = landmark.lpNumber
        # Convert to string if non-empty, otherwise return None
        return str(lp_number) if lp_number else None
    elif isinstance(landmark, dict):
        # It's a dictionary
        # Get the value from either key
        id_val = landmark.get("id")
        lp_val = landmark.get("lpNumber")

        # Use the first non-empty value or return None
        if id_val:
            return str(id_val)
        elif lp_val:
            return str(lp_val)
        else:
            return None
    else:
        # Unknown type, log and return None
        logger.warning(f"Unknown landmark type: {type(landmark)}")
        return None


def fetch_landmarks_page(
    db_client: Any, page_size: int, current_page: int
) -> List[Any]:
    """
    Fetch a single page of landmarks from the API.

    Args:
        db_client: Database client
        page_size: Number of landmarks per page
        current_page: Current page number

    Returns:
        List of landmarks from the current page or empty list on error
    """
    try:
        landmarks_page = db_client.get_landmarks_page(page_size, current_page)
        return list(landmarks_page)  # Ensure it's a list
    except Exception as e:
        logger.error(f"Error fetching page {current_page}: {e}")
        return []


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
                landmarks = fetch_landmarks_page(db_client, page_size, current_page)

                # If no landmarks found, we've reached the end
                if not landmarks:
                    logger.info(
                        f"No landmarks found on page {current_page}, ending fetch"
                    )
                    break

                # Process the landmarks
                for landmark in landmarks:
                    landmark_id = extract_landmark_id(landmark)
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


def safe_get_attribute(obj: Any, attr_name: str, default: Any = None) -> Any:
    """
    Safely get an attribute from an object, whether it's a dictionary or an object with attributes.

    Args:
        obj: The object to get the attribute from
        attr_name: The name of the attribute to get
        default: The default value to return if the attribute doesn't exist

    Returns:
        The attribute value if it exists, otherwise the default value
    """
    if obj is None:
        return default

    # If it's a dictionary, use .get()
    if isinstance(obj, dict):
        return obj.get(attr_name, default)

    # Otherwise try to access it as an attribute
    return getattr(obj, attr_name, default)


def get_landmark_pdf_url(
    landmark_response: Any, landmark_id: str, is_problematic: bool = False
) -> Optional[str]:
    """
    Extract the PDF URL from a landmark response.

    Args:
        landmark_response: The landmark response object or dictionary
        landmark_id: The landmark ID for logging
        is_problematic: Whether this is a problematic landmark that needs detailed logging

    Returns:
        The PDF URL or None if not found
    """
    # Use safe_get_attribute to handle both dict and object types
    pdf_url = safe_get_attribute(landmark_response, "pdfReportUrl")

    # Convert to string if it's not None
    pdf_url_str = str(pdf_url) if pdf_url else None

    if is_problematic:
        logger.info(f"Landmark {landmark_id} pdf_url extracted: {pdf_url_str}")

    return pdf_url_str


def create_chunk_metadata(
    landmark_id: str,
    landmark_response: Any,
    pdf_url: str,
    chunk_index: int,
    total_chunks: int,
) -> Dict[str, Any]:
    """
    Create metadata for a chunk.

    Args:
        landmark_id: The landmark ID
        landmark_response: The landmark response object or dictionary
        pdf_url: The PDF URL
        chunk_index: The index of the current chunk
        total_chunks: The total number of chunks

    Returns:
        A dictionary containing metadata for the chunk
    """
    # Create base metadata
    metadata = {
        "landmark_id": landmark_id,
        "chunk_index": chunk_index,
        "total_chunks": total_chunks,
        "source": "pdf",
        "pdf_url": pdf_url,
    }

    # Add additional metadata using safe_get_attribute
    metadata.update(
        {
            "name": safe_get_attribute(landmark_response, "name", ""),
            "borough": safe_get_attribute(landmark_response, "borough", ""),
        }
    )

    return metadata


def generate_and_validate_embedding(
    embedding_generator: EmbeddingGenerator, chunk_text: str, chunk_index: int
) -> List[float]:
    """
    Generate an embedding for a chunk and validate it.

    Args:
        embedding_generator: The embedding generator
        chunk_text: The text to generate an embedding for
        chunk_index: The index of the current chunk for logging

    Returns:
        The generated embedding, or a dummy embedding if generation failed
    """
    # Generate embedding
    embedding = embedding_generator.generate_embedding(chunk_text)

    # Check embedding validity
    is_valid_embedding = (
        embedding and len(embedding) > 0 and not all(v == 0 for v in embedding)
    )

    if is_valid_embedding:
        logger.info(
            f"Generated valid embedding for chunk {chunk_index} with dimensions: {len(embedding)}"
        )
        # Ensure we're returning a List[float]
        return [float(v) for v in embedding]
    else:
        logger.error(f"Invalid or empty embedding generated for chunk {chunk_index}!")
        # Create a dummy embedding if generation failed
        return [0.0] * settings.OPENAI_EMBEDDING_DIMENSIONS


def _process_text_chunk(
    embedding_generator: EmbeddingGenerator,
    chunk_text: str,
    landmark_id: str,
    landmark_response: Any,
    pdf_url: str,
    chunk_index: int,
    total_chunks: int,
) -> Dict[str, Any]:
    """
    Process a single text chunk to create metadata and generate embedding.

    Args:
        embedding_generator: The embedding generator to use
        chunk_text: The text chunk to process
        landmark_id: The landmark ID
        landmark_response: The landmark response object or dictionary
        pdf_url: The URL of the PDF
        chunk_index: The index of the current chunk
        total_chunks: Total number of chunks

    Returns:
        A dictionary with the processed chunk data
    """
    # Create metadata
    metadata = create_chunk_metadata(
        landmark_id, landmark_response, pdf_url, chunk_index, total_chunks
    )

    # Generate embedding
    embedding = generate_and_validate_embedding(
        embedding_generator, chunk_text, chunk_index
    )

    # Return the processed chunk
    return {
        "text": chunk_text,
        "metadata": metadata,
        "embedding": embedding,
        "chunk_index": chunk_index,
        "total_chunks": total_chunks,
    }


def _log_chunk_details(chunks: List[Dict[str, Any]]) -> None:
    """
    Log details about the processed chunks.

    Args:
        chunks: List of processed chunks
    """
    for i, chunk in enumerate(chunks):
        embedding = safe_get_attribute(chunk, "embedding", [])
        is_valid = (
            embedding and len(embedding) > 0 and not all(v == 0 for v in embedding)
        )
        logger.info(
            f"Chunk {i} ready for storage - has valid embedding: {is_valid}, length: {len(embedding)}"
        )

        # Log the first 3 values of the embedding for debugging
        if embedding and len(embedding) > 3:
            first_values = embedding[:3]
            logger.info(f"Chunk {i} embedding first 3 values: {first_values}")


def _get_landmark_data(
    db_client: Any, landmark_id: str, is_problematic: bool
) -> Tuple[Any, str, bool]:
    """
    Get landmark data from the database.

    Args:
        db_client: Database client
        landmark_id: The landmark ID
        is_problematic: Whether this is a problematic landmark

    Returns:
        Tuple of (landmark_response, pdf_url, success)
    """
    # Get landmark details from API
    landmark_response = db_client.get_landmark_by_id(landmark_id)
    if not landmark_response:
        return None, "", False

    if is_problematic:
        logger.info(f"Landmark {landmark_id} response type: {type(landmark_response)}")

    # Get PDF URL
    pdf_url = get_landmark_pdf_url(landmark_response, landmark_id, is_problematic)
    if not pdf_url:
        return landmark_response, "", False

    return landmark_response, pdf_url, True


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
        # Special logging for problematic landmark IDs
        is_problematic = landmark_id in ["LP-00048", "LP-00112", "LP-00012"]
        if is_problematic:
            logger.info(f"Processing previously problematic landmark: {landmark_id}")

        # Get landmark data
        landmark_response, pdf_url, success = _get_landmark_data(
            db_client, landmark_id, is_problematic
        )

        if not success:
            error_msg = "No PDF report" if landmark_response else "Not found in API"
            return False, 0, f"Landmark {landmark_id} {error_msg}"

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

        # Process all chunks
        processed_chunks = [
            _process_text_chunk(
                embedding_generator,
                chunk_text,
                landmark_id,
                landmark_response,
                pdf_url,
                i,
                len(chunks),
            )
            for i, chunk_text in enumerate(chunks)
        ]

        # Log chunk details
        _log_chunk_details(processed_chunks)

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
    parser.add_argument(
        "landmark_ids",
        nargs="*",
        help="Optional: Specific landmark IDs to process (e.g., LP-00048 LP-00112)",
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

    # If specific landmark IDs are provided, use them
    if args.landmark_ids:
        logger.info(f"Processing specific landmark IDs: {args.landmark_ids}")
        all_landmark_ids = set(args.landmark_ids)
    else:
        # Otherwise, fetch all landmarks
        all_landmark_ids = fetch_all_landmark_ids(db_client, limit=args.limit)

    if not all_landmark_ids:
        logger.error("No landmarks found. Exiting.")
        return

    # If specific landmark IDs are provided, force processing regardless of status
    if args.landmark_ids:
        unprocessed_landmarks = all_landmark_ids
        processed_landmarks: Set[str] = set()
        logger.info(f"Forcing processing of specific landmark IDs: {args.landmark_ids}")
    else:
        # Check processing status for fetched landmarks
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

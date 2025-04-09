"""
NYC Landmarks Pipeline Script

This script implements a processing pipeline for NYC landmarks data:
1. Fetches landmark data from the CoreDataStore API
2. Extracts PDF URLs and downloads PDF reports
3. Processes PDFs to extract text
4. Chunks text into manageable segments
5. Generates embeddings from text chunks
6. Stores embeddings in Pinecone vector database with enhanced metadata

Usage:
  python scripts/process_landmarks.py --pages 2 --download
"""

import argparse
import json
import os
import sys
import time
import uuid
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, cast

import requests
from tqdm import tqdm

# Add the project root to the path so we can import nyc_landmarks modules
sys.path.append(str(Path(__file__).resolve().parent.parent))
from nyc_landmarks.config.settings import settings
from nyc_landmarks.db.db_client import get_db_client
from nyc_landmarks.embeddings.generator import EmbeddingGenerator
from nyc_landmarks.pdf.extractor import PDFExtractor
from nyc_landmarks.pdf.text_chunker import TextChunker
from nyc_landmarks.utils.logger import get_logger
from nyc_landmarks.vectordb.enhanced_metadata import get_metadata_collector
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Configure logger for this script
logger = get_logger(name="process_landmarks")


class LandmarkPipeline:
    """Pipeline for processing NYC landmark data."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the pipeline components.

        Args:
            api_key: Optional API key for CoreDataStore API
        """
        # Set up database client using the abstraction layer
        self.db_client = get_db_client()

        # Initialize other components
        self.pdf_extractor = PDFExtractor()
        self.text_chunker = TextChunker(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP
        )
        self.embedding_generator = EmbeddingGenerator()
        self.pinecone_db = PineconeDB()
        self.metadata_collector = get_metadata_collector()

        # Set up directories
        self.data_dir = Path("data")
        self.pdfs_dir = self.data_dir / "pdfs"
        self.text_dir = self.data_dir / "text"

        # Ensure directories exist
        self.data_dir.mkdir(exist_ok=True)
        self.pdfs_dir.mkdir(exist_ok=True)
        self.text_dir.mkdir(exist_ok=True)

        # Initialize statistics
        self.stats: Dict[str, Any] = {
            "landmarks_fetched": 0,
            "pdfs_downloaded": 0,
            "pdfs_processed": 0,
            "chunks_created": 0,
            "embeddings_generated": 0,
            "vectors_stored": 0,
            "errors": [],
            "processed_landmarks": []
        }

    def get_landmarks(
        self, page_size: int = 10, pages: int = 1
    ) -> List[Dict[str, Any]]:
        """Get landmark reports from the API.

        Args:
            page_size: Number of landmarks per page
            pages: Number of pages to fetch

        Returns:
            List of landmark dictionaries
        """
        all_landmarks = []

        for page in range(1, pages + 1):
            logger.info(f"Fetching page {page} of {pages}")
            try:
                # Use the database client to get landmarks
                landmarks = self.db_client.get_landmarks_page(page_size, page)

                if landmarks:
                    all_landmarks.extend(landmarks)
                    logger.info(f"Found {len(landmarks)} landmarks on page {page}")
                else:
                    logger.warning(f"No results found on page {page}")
                    break

                # Add a small delay to avoid rate limiting
                time.sleep(0.5)

            except Exception as e:
                error_msg = f"Error fetching landmarks on page {page}: {str(e)}"
                logger.error(error_msg)
                self.stats["errors"].append(error_msg)
                break

        self.stats["landmarks_fetched"] = len(all_landmarks)
        return all_landmarks

    def download_pdfs(
        self, landmarks: List[Dict[str, Any]], limit: Optional[int] = None
    ) -> List[Tuple[str, Path, Dict[str, Any]]]:
        """Download PDFs for landmarks.

        Args:
            landmarks: List of landmark dictionaries
            limit: Maximum number of PDFs to download

        Returns:
            List of tuples with (landmark_id, pdf_path, landmark_data)
        """
        downloaded = []

        # Filter landmarks that have PDF URLs
        landmarks_with_pdfs = [
            landmark for landmark in landmarks
            if landmark.get("pdfReportUrl") or self.db_client.get_landmark_pdf_url(landmark.get("id", ""))
        ]

        # Apply limit if specified
        if limit is not None and limit > 0:
            landmarks_with_pdfs = landmarks_with_pdfs[:limit]

        for landmark in tqdm(landmarks_with_pdfs, desc="Downloading PDFs"):
            try:
                # Get landmark ID
                landmark_id = landmark.get("id", "") or landmark.get("lpNumber", "")
                if not landmark_id:
                    logger.warning(f"Landmark missing ID: {landmark}")
                    continue

                # Get PDF URL - either from the landmark data directly or using the client
                pdf_url = landmark.get("pdfReportUrl")
                if not pdf_url:
                    pdf_url = self.db_client.get_landmark_pdf_url(landmark_id)

                if not pdf_url:
                    logger.warning(f"No PDF URL found for landmark {landmark_id}")
                    continue

                # Generate filename
                filename = f"{landmark_id.replace('/', '_')}.pdf"
                filepath = self.pdfs_dir / filename

                # Skip if already downloaded
                if filepath.exists():
                    logger.info(f"PDF for {landmark_id} already exists at {filepath}")
                    downloaded.append((landmark_id, filepath, landmark))
                    continue

                # Download the PDF
                logger.info(f"Downloading PDF for {landmark_id} from {pdf_url}")
                response = requests.get(pdf_url, stream=True, timeout=30)
                response.raise_for_status()

                with open(filepath, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                downloaded.append((landmark_id, filepath, landmark))
                logger.info(f"Successfully downloaded {filepath}")

                # Add a small delay
                time.sleep(0.5)

            except Exception as e:
                error_msg = f"Error downloading PDF for landmark {landmark.get('id', '') or landmark.get('lpNumber', 'unknown')}: {str(e)}"
                logger.error(error_msg)
                self.stats["errors"].append(error_msg)

        self.stats["pdfs_downloaded"] = len(downloaded)
        return downloaded

    def extract_text(
        self, pdf_items: List[Tuple[str, Path, Dict[str, Any]]]
    ) -> List[Tuple[str, str, Dict[str, Any]]]:
        """Extract text from PDFs.

        Args:
            pdf_items: List of tuples with (landmark_id, pdf_path, landmark_data)

        Returns:
            List of tuples with (landmark_id, text_content, landmark_data)
        """
        extracted_texts = []

        for landmark_id, pdf_path, landmark_data in tqdm(pdf_items, desc="Extracting text from PDFs"):
            try:
                # Extract text from PDF
                text = self.pdf_extractor.extract_text(pdf_path)

                if text:
                    # Save text to file
                    text_filename = pdf_path.stem + ".txt"
                    text_filepath = self.text_dir / text_filename
                    with open(text_filepath, "w", encoding="utf-8") as f:
                        f.write(text)

                    extracted_texts.append((landmark_id, text, landmark_data))
                    logger.info(f"Successfully extracted text from {pdf_path}")
                else:
                    logger.warning(f"No text extracted from {pdf_path}")

            except Exception as e:
                error_msg = f"Error extracting text from PDF {pdf_path}: {str(e)}"
                logger.error(error_msg)
                self.stats["errors"].append(error_msg)

        self.stats["pdfs_processed"] = len(extracted_texts)
        return extracted_texts

    def chunk_texts(
        self, text_items: List[Tuple[str, str, Dict[str, Any]]]
    ) -> List[Tuple[str, List[Dict[str, Any]], Dict[str, Any]]]:
        """Chunk text into smaller segments.

        Args:
            text_items: List of tuples with (landmark_id, text_content, landmark_data)

        Returns:
            List of tuples with (landmark_id, chunks, landmark_data)
        """
        all_chunked_items = []

        for landmark_id, text, landmark_data in tqdm(text_items, desc="Chunking text"):
            try:
                # Create chunks from text
                chunks = self.text_chunker.create_chunks(text)

                # Add metadata to each chunk
                enriched_chunks = []
                for i, chunk in enumerate(chunks):
                    chunk_dict = {
                        "text": chunk,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "metadata": {
                            "landmark_id": landmark_id,
                            "chunk_index": i,
                            "total_chunks": len(chunks),
                            "source_type": "pdf",
                            "processing_date": time.strftime("%Y-%m-%d"),
                        }
                    }
                    enriched_chunks.append(chunk_dict)

                all_chunked_items.append((landmark_id, enriched_chunks, landmark_data))
                logger.info(f"Created {len(chunks)} chunks for landmark {landmark_id}")

                # Update statistics
                self.stats["chunks_created"] += len(chunks)

            except Exception as e:
                error_msg = f"Error chunking text for landmark {landmark_id}: {str(e)}"
                logger.error(error_msg)
                self.stats["errors"].append(error_msg)

        return all_chunked_items

    def generate_embeddings(
        self, chunked_items: List[Tuple[str, List[Dict[str, Any]], Dict[str, Any]]]
    ) -> List[Tuple[str, List[Dict[str, Any]], Dict[str, Any]]]:
        """Generate embeddings for text chunks.

        Args:
            chunked_items: List of tuples with (landmark_id, chunks, landmark_data)

        Returns:
            List of tuples with (landmark_id, chunks_with_embeddings, landmark_data)
        """
        items_with_embeddings = []

        for landmark_id, chunks, landmark_data in tqdm(chunked_items, desc="Generating embeddings"):
            try:
                # Prepare texts for embedding
                texts = [chunk["text"] for chunk in chunks]

                # Generate embeddings in batch
                embeddings = self.embedding_generator.generate_embeddings(texts)

                # Add embeddings to chunks
                chunks_with_embeddings = chunks.copy()
                for i, embedding in enumerate(embeddings):
                    chunks_with_embeddings[i]["embedding"] = embedding

                items_with_embeddings.append((landmark_id, chunks_with_embeddings, landmark_data))
                logger.info(f"Generated {len(embeddings)} embeddings for landmark {landmark_id}")

                # Update statistics
                self.stats["embeddings_generated"] += len(embeddings)

            except Exception as e:
                error_msg = f"Error generating embeddings for landmark {landmark_id}: {str(e)}"
                logger.error(error_msg)
                self.stats["errors"].append(error_msg)

        return items_with_embeddings

    def store_in_vector_db(
        self, items_with_embeddings: List[Tuple[str, List[Dict[str, Any]], Dict[str, Any]]]
    ) -> bool:
        """Store embeddings in vector database with enhanced metadata.

        Args:
            items_with_embeddings: List of tuples with (landmark_id, chunks_with_embeddings, landmark_data)

        Returns:
            Success status
        """
        all_success = True

        for landmark_id, chunks_with_embeddings, _ in tqdm(items_with_embeddings, desc="Storing vectors"):
            try:
                # Create a prefix with landmark ID for better vector organization
                id_prefix = f"{landmark_id}-"

                # Store chunks with enhanced metadata from landmark_id
                vector_ids = self.pinecone_db.store_chunks(
                    chunks=chunks_with_embeddings,
                    id_prefix=id_prefix,
                    landmark_id=landmark_id
                )

                if vector_ids:
                    logger.info(f"Stored {len(vector_ids)} vectors for landmark {landmark_id}")
                    self.stats["vectors_stored"] += len(vector_ids)
                    self.stats["processed_landmarks"].append(landmark_id)
                else:
                    logger.warning(f"Failed to store vectors for landmark {landmark_id}")
                    all_success = False

            except Exception as e:
                error_msg = f"Error storing vectors for landmark {landmark_id}: {str(e)}"
                logger.error(error_msg)
                self.stats["errors"].append(error_msg)
                all_success = False

        return all_success

    def run(
        self, page_size: int = 10, pages: int = 1, download_limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Run the pipeline.

        Args:
            page_size: Number of landmarks per page
            pages: Number of pages to fetch
            download_limit: Maximum number of PDFs to download

        Returns:
            Dictionary with pipeline statistics
        """
        start_time = time.time()

        # Step 1: Fetch landmarks
        logger.info("STEP 1: Fetching landmarks")
        landmarks = self.get_landmarks(page_size, pages)

        # Step 2: Download PDFs
        logger.info("STEP 2: Downloading PDFs")
        pdf_items = self.download_pdfs(landmarks, download_limit)

        # Step 3: Extract text
        logger.info("STEP 3: Extracting text from PDFs")
        text_items = self.extract_text(pdf_items)

        # Step 4: Chunk text
        logger.info("STEP 4: Chunking text")
        chunked_items = self.chunk_texts(text_items)

        # Step 5: Generate embeddings
        logger.info("STEP 5: Generating embeddings")
        items_with_embeddings = self.generate_embeddings(chunked_items)

        # Step 6: Store in vector database
        logger.info("STEP 6: Storing in vector database")
        store_success = self.store_in_vector_db(items_with_embeddings)

        # Save landmarks data
        landmarks_file = self.data_dir / "landmarks.json"
        with open(landmarks_file, "w") as f:
            json.dump(landmarks, f, indent=2)

        # Calculate statistics
        elapsed_time = time.time() - start_time
        self.stats["elapsed_time"] = f"{elapsed_time:.2f} seconds"
        self.stats["pipeline_success"] = len(self.stats["errors"]) == 0 and store_success

        # Save statistics
        stats_file = self.data_dir / "pipeline_stats.json"
        with open(stats_file, "w") as f:
            json.dump(self.stats, f, indent=2)

        logger.info(f"Pipeline completed in {elapsed_time:.2f} seconds")
        logger.info(f"Landmarks fetched: {self.stats['landmarks_fetched']}")
        logger.info(f"PDFs downloaded: {self.stats['pdfs_downloaded']}")
        logger.info(f"PDFs processed: {self.stats['pdfs_processed']}")
        logger.info(f"Text chunks created: {self.stats['chunks_created']}")
        logger.info(f"Embeddings generated: {self.stats['embeddings_generated']}")
        logger.info(f"Vectors stored: {self.stats['vectors_stored']}")

        if self.stats["errors"]:
            logger.warning(
                f"Pipeline completed with {len(self.stats['errors'])} errors"
            )
        else:
            logger.info("Pipeline completed successfully")

        return self.stats


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(description="NYC Landmarks Pipeline")
    parser.add_argument(
        "--page-size", type=int, default=10, help="Number of landmarks per page"
    )
    parser.add_argument("--pages", type=int, default=1, help="Number of pages to fetch")
    parser.add_argument("--download", action="store_true", help="Download PDFs")
    parser.add_argument("--limit", type=int, help="Limit number of PDFs to download")
    parser.add_argument("--api-key", type=str, help="CoreDataStore API key (optional)")

    args = parser.parse_args()

    # Load API key from environment variable if not provided as argument
    api_key = args.api_key or os.environ.get("COREDATASTORE_API_KEY")

    # Set download limit based on arguments
    download_limit = args.limit if args.download else 0

    # Initialize and run pipeline
    pipeline = LandmarkPipeline(api_key)
    stats = pipeline.run(
        page_size=args.page_size, pages=args.pages, download_limit=download_limit
    )

    # Print summary
    print("\nPipeline Summary:")
    print(f"Landmarks fetched: {stats['landmarks_fetched']}")
    print(f"PDFs downloaded: {stats['pdfs_downloaded']}")
    print(f"PDFs processed: {stats['pdfs_processed']}")
    print(f"Text chunks created: {stats['chunks_created']}")
    print(f"Embeddings generated: {stats['embeddings_generated']}")
    print(f"Vectors stored: {stats['vectors_stored']}")
    print(f"Elapsed time: {stats['elapsed_time']}")

    if stats["errors"]:
        print(f"Errors: {len(stats['errors'])}")
        print("Check the logs for details")
    else:
        print("Status: Success")


if __name__ == "__main__":
    main()

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
  python scripts/ci/process_landmarks.py --pages 2 --download
"""

import argparse
import concurrent.futures
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

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
            chunk_size=settings.CHUNK_SIZE, chunk_overlap=settings.CHUNK_OVERLAP
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
            "processed_landmarks": [],
        }

    def get_landmarks(
        self, start_page: int, end_page: int, page_size: int = 100
    ) -> List[Dict[str, Any]]:
        """Get landmark reports from the API.

        Args:
            start_page: The starting page number to fetch
            end_page: The ending page number to fetch
            page_size: Number of landmarks per page

        Returns:
            List of landmark dictionaries
        """
        all_landmarks: List[Dict[str, Any]] = []
        total_pages_to_fetch = end_page - start_page + 1

        for page in range(start_page, end_page + 1):
            current_page_index = page - start_page + 1
            logger.info(
                f"Fetching page {page} ({current_page_index}/{total_pages_to_fetch}) with size {page_size}"
            )
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

    def _has_pdf(self, landmark: Union[Dict[str, Any], Any]) -> bool:
        """Check if a landmark has a PDF URL.

        Args:
            landmark: The landmark data, either as a dictionary or an object

        Returns:
            True if the landmark has a PDF URL, False otherwise
        """
        # Check if landmark has PDF URL directly
        if isinstance(landmark, dict) and landmark.get("pdfReportUrl"):
            return True
        elif (
            not isinstance(landmark, dict)
            and hasattr(landmark, "pdfReportUrl")
            and landmark.pdfReportUrl
        ):
            return True

        # Check if we can get PDF URL from DB client
        landmark_id = (
            landmark.get("id", "")
            if isinstance(landmark, dict)
            else getattr(landmark, "lpNumber", "")
        )
        return bool(landmark_id and self.db_client.get_landmark_pdf_url(landmark_id))

    def _get_landmark_id(
        self, landmark: Dict[str, Any], default: str = "unknown"
    ) -> str:
        """Extract landmark ID from landmark data.

        Args:
            landmark: The landmark data
            default: Default value if ID cannot be extracted

        Returns:
            The landmark ID
        """
        if isinstance(landmark, dict):
            result = landmark.get("id", "") or landmark.get("lpNumber", default)
            return str(result)
        return str(getattr(landmark, "lpNumber", default))

    def _get_pdf_url(
        self, landmark: Union[Dict[str, Any], Any], landmark_id: str
    ) -> Optional[str]:
        """Get PDF URL for a landmark.

        Args:
            landmark: The landmark data, either as a dictionary or an object
            landmark_id: The landmark ID

        Returns:
            The PDF URL or None if not found
        """
        if isinstance(landmark, dict):
            pdf_url = landmark.get("pdfReportUrl")
        else:
            pdf_url = getattr(landmark, "pdfReportUrl", None)

        if not pdf_url:
            pdf_url = self.db_client.get_landmark_pdf_url(landmark_id)

        return pdf_url

    def _download_pdf_file(self, pdf_url: str, filepath: Path) -> bool:
        """Download a PDF file from URL.

        Args:
            pdf_url: URL of the PDF
            filepath: Path where to save the file

        Returns:
            True if download successful, False otherwise
        """
        response = requests.get(pdf_url, stream=True, timeout=30)
        response.raise_for_status()

        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return True

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
        downloaded: List[Tuple[str, Path, Dict[str, Any]]] = []

        # Filter landmarks that have PDF URLs
        landmarks_with_pdfs = [
            landmark for landmark in landmarks if self._has_pdf(landmark)
        ]

        # Apply limit if specified
        if limit is not None and limit > 0:
            landmarks_with_pdfs = landmarks_with_pdfs[:limit]

        for landmark in tqdm(landmarks_with_pdfs, desc="Downloading PDFs"):
            try:
                # Get landmark ID
                landmark_id = self._get_landmark_id(landmark)

                if not landmark_id:
                    logger.warning(f"Landmark missing ID: {landmark}")
                    continue

                # Get PDF URL
                pdf_url = self._get_pdf_url(landmark, landmark_id)

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
                self._download_pdf_file(pdf_url, filepath)

                downloaded.append((landmark_id, filepath, landmark))
                logger.info(f"Successfully downloaded {filepath}")

                # Add a small delay
                time.sleep(0.5)

            except Exception as e:
                # Get landmark ID safely
                landmark_id = self._get_landmark_id(landmark)

                error_msg = (
                    f"Error downloading PDF for landmark {landmark_id}: {str(e)}"
                )
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
        extracted_texts: List[Tuple[str, str, Dict[str, Any]]] = []

        for landmark_id, pdf_path, landmark_data in tqdm(
            pdf_items, desc="Extracting text from PDFs"
        ):
            try:
                # Extract text from PDF using extract_text_from_bytes
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()
                    text = self.pdf_extractor.extract_text_from_bytes(pdf_bytes)

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
                chunks = self.text_chunker.chunk_text_by_tokens(text)

                # Add metadata to each chunk
                enriched_chunks = []
                for i, chunk in enumerate(chunks):
                    chunk_dict: Dict[str, Any] = {
                        "text": chunk,
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "metadata": {
                            "landmark_id": landmark_id,
                            "chunk_index": i,
                            "total_chunks": len(chunks),
                            "source_type": "pdf",
                            "processing_date": time.strftime("%Y-%m-%d"),
                        },
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

        for landmark_id, chunks, landmark_data in tqdm(
            chunked_items, desc="Generating embeddings"
        ):
            try:
                # Prepare texts for embedding
                texts = [chunk["text"] for chunk in chunks]

                # Generate embeddings in batch
                embeddings = self.embedding_generator.generate_embeddings_batch(texts)

                # Add embeddings to chunks
                chunks_with_embeddings = chunks.copy()
                for i, embedding in enumerate(embeddings):
                    chunks_with_embeddings[i]["embedding"] = embedding

                items_with_embeddings.append(
                    (landmark_id, chunks_with_embeddings, landmark_data)
                )
                logger.info(
                    f"Generated {len(embeddings)} embeddings for landmark {landmark_id}"
                )

                # Update statistics
                self.stats["embeddings_generated"] += len(embeddings)

            except Exception as e:
                error_msg = (
                    f"Error generating embeddings for landmark {landmark_id}: {str(e)}"
                )
                logger.error(error_msg)
                self.stats["errors"].append(error_msg)

        return items_with_embeddings

    def process_landmark_worker(
        self, landmark: Union[Dict[str, Any], Any]
    ) -> Dict[str, Any]:
        """Process a single landmark through all pipeline stages.

        Args:
            landmark: Dictionary containing landmark data

        Returns:
            Dict: Processing results with statistics and status
        """
        result = self._initialize_result(landmark)
        start_time = time.time()

        try:
            # Step 1: Download PDF
            landmark_id = result["landmark_id"]
            if not landmark_id:
                raise ValueError("Landmark missing ID")

            # Get PDF URL and download
            filepath = self._download_pdf(landmark, landmark_id, result)

            # Step 2: Extract and save text
            text = self._extract_and_save_text(filepath, landmark_id, result)

            # Step 3: Chunk text
            enriched_chunks = self._chunk_text(text, landmark_id, result)

            # Step 4: Generate embeddings
            chunks_with_embeddings = self._generate_embeddings(
                enriched_chunks, landmark_id, result
            )

            # Step 5: Store vectors
            self._store_vectors(chunks_with_embeddings, landmark_id, result)

            # Set success status
            result["status"] = "success"

        except Exception as e:
            error_msg = f"Error processing landmark {result['landmark_id']}: {str(e)}"
            result["errors"].append(error_msg)
            logger.error(error_msg)

        # Calculate processing time
        result["stats"]["processing_time"] = time.time() - start_time

        return result

    def _initialize_result(
        self, landmark: Union[Dict[str, Any], Any]
    ) -> Dict[str, Any]:
        """Initialize the result dictionary for landmark processing.

        Args:
            landmark: Dictionary or Pydantic model containing landmark data

        Returns:
            Dict with initialized result structure
        """
        # Get landmark ID - handle both dict and Pydantic models
        if isinstance(landmark, dict):
            landmark_id = landmark.get("id", "") or landmark.get("lpNumber", "")
        else:
            landmark_id = getattr(landmark, "lpNumber", "")

        return {
            "landmark_id": landmark_id,
            "status": "failed",
            "errors": [],
            "stats": {
                "pdf_downloaded": False,
                "text_extracted": False,
                "chunks_created": 0,
                "embeddings_generated": 0,
                "vectors_stored": 0,
                "processing_time": 0,
            },
        }

    def _download_pdf(
        self,
        landmark: Union[Dict[str, Any], Any],
        landmark_id: str,
        result: Dict[str, Any],
    ) -> Path:
        """Download PDF for the landmark.

        Args:
            landmark: Dictionary or Pydantic model containing landmark data
            landmark_id: ID of the landmark
            result: Result dictionary to update

        Returns:
            Path to the downloaded PDF file

        Raises:
            ValueError: If PDF URL is not found or download fails
        """
        # Get PDF URL
        if isinstance(landmark, dict):
            pdf_url = landmark.get("pdfReportUrl")
        else:
            pdf_url = getattr(landmark, "pdfReportUrl", None)

        if not pdf_url:
            pdf_url = self.db_client.get_landmark_pdf_url(landmark_id)

        if not pdf_url:
            raise ValueError(f"No PDF URL found for landmark {landmark_id}")

        # Download PDF
        filename = f"{landmark_id.replace('/', '_')}.pdf"
        filepath = self.pdfs_dir / filename

        if not filepath.exists():
            logger.info(f"Downloading PDF for {landmark_id} from {pdf_url}")
            response = requests.get(pdf_url, stream=True, timeout=30)
            response.raise_for_status()

            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

        result["stats"]["pdf_downloaded"] = True
        return filepath

    def _extract_and_save_text(
        self, filepath: Path, landmark_id: str, result: Dict[str, Any]
    ) -> str:
        """Extract text from PDF and save to file.

        Args:
            filepath: Path to the PDF file
            landmark_id: ID of the landmark
            result: Result dictionary to update

        Returns:
            Extracted text

        Raises:
            ValueError: If no text was extracted
        """
        logger.info(f"Extracting text from PDF for landmark {landmark_id}")
        with open(filepath, "rb") as f:
            pdf_bytes = f.read()
            text = self.pdf_extractor.extract_text_from_bytes(pdf_bytes)

        if not text:
            raise ValueError(f"No text extracted from PDF for landmark {landmark_id}")

        # Save text to file
        text_filename = filepath.stem + ".txt"
        text_filepath = self.text_dir / text_filename
        with open(text_filepath, "w", encoding="utf-8") as f:
            f.write(text)

        result["stats"]["text_extracted"] = True
        return text

    def _chunk_text(
        self, text: str, landmark_id: str, result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Chunk text and create enriched chunks.

        Args:
            text: Text to chunk
            landmark_id: ID of the landmark
            result: Result dictionary to update

        Returns:
            List of enriched chunks
        """
        logger.info(f"Chunking text for landmark {landmark_id}")
        chunks = self.text_chunker.chunk_text_by_tokens(text)
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
                },
            }
            enriched_chunks.append(chunk_dict)

        result["stats"]["chunks_created"] = len(chunks)
        return enriched_chunks

    def _generate_embeddings(
        self,
        enriched_chunks: List[Dict[str, Any]],
        landmark_id: str,
        result: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Generate embeddings for chunks.

        Args:
            enriched_chunks: List of enriched chunks
            landmark_id: ID of the landmark
            result: Result dictionary to update

        Returns:
            List of chunks with embeddings
        """
        logger.info(f"Generating embeddings for landmark {landmark_id}")
        texts = [chunk["text"] for chunk in enriched_chunks]
        embeddings = self.embedding_generator.generate_embeddings_batch(texts)

        chunks_with_embeddings = enriched_chunks.copy()
        for i, embedding in enumerate(embeddings):
            chunks_with_embeddings[i]["embedding"] = embedding

        result["stats"]["embeddings_generated"] = len(embeddings)
        return chunks_with_embeddings

    def _store_vectors(
        self,
        chunks_with_embeddings: List[Dict[str, Any]],
        landmark_id: str,
        result: Dict[str, Any],
    ) -> None:
        """Store vectors in Pinecone.

        Args:
            chunks_with_embeddings: List of chunks with embeddings
            landmark_id: ID of the landmark
            result: Result dictionary to update
        """
        logger.info(f"Storing vectors for landmark {landmark_id} using fixed IDs")
        vector_ids = self.pinecone_db.store_chunks(
            chunks=chunks_with_embeddings,
            id_prefix="",  # No need for id_prefix with fixed IDs
            landmark_id=landmark_id,
            use_fixed_ids=True,  # Explicitly use fixed IDs to prevent duplication
            delete_existing=True,  # Delete any existing vectors for this landmark
        )

        result["stats"]["vectors_stored"] = len(vector_ids)

    def store_in_vector_db(
        self,
        items_with_embeddings: List[Tuple[str, List[Dict[str, Any]], Dict[str, Any]]],
    ) -> bool:
        """Store embeddings in vector database with enhanced metadata.

        Args:
            items_with_embeddings: List of tuples with (landmark_id, chunks_with_embeddings, landmark_data)

        Returns:
            Success status
        """
        all_success = True

        for landmark_id, chunks_with_embeddings, _ in tqdm(
            items_with_embeddings, desc="Storing vectors"
        ):
            try:
                # Store chunks with fixed IDs to prevent duplication
                vector_ids = self.pinecone_db.store_chunks(
                    chunks=chunks_with_embeddings,
                    id_prefix="",  # No need for id_prefix with fixed IDs
                    landmark_id=landmark_id,
                    use_fixed_ids=True,  # Explicitly use fixed IDs to prevent duplication
                    delete_existing=True,  # Delete any existing vectors for this landmark
                )

                if vector_ids:
                    logger.info(
                        f"Stored {len(vector_ids)} vectors for landmark {landmark_id}"
                    )
                    self.stats["vectors_stored"] += len(vector_ids)
                    self.stats["processed_landmarks"].append(landmark_id)
                else:
                    logger.warning(
                        f"Failed to store vectors for landmark {landmark_id}"
                    )
                    all_success = False

            except Exception as e:
                error_msg = (
                    f"Error storing vectors for landmark {landmark_id}: {str(e)}"
                )
                logger.error(error_msg)
                self.stats["errors"].append(error_msg)
                all_success = False

        return all_success

    def run_parallel(
        self,
        start_page: int,
        end_page: int,
        page_size: int = 100,
        download_limit: Optional[int] = None,
        workers: int = 4,
        recreate_index: bool = False,
        drop_index: bool = False,
    ) -> Dict[str, Any]:
        """Run the pipeline with parallel processing.

        Args:
            start_page: The starting page number to fetch
            end_page: The ending page number to fetch
            page_size: Number of landmarks per page
            download_limit: Maximum number of PDFs to download
            workers: Number of parallel worker processes
            recreate_index: Whether to recreate the vector index
            drop_index: Whether to drop the vector index without recreating it

        Returns:
            Dict: Pipeline statistics
        """
        start_time = time.time()

        # Vector DB management
        if recreate_index:
            logger.info("Recreating Pinecone index...")
            if not self.pinecone_db.recreate_index():
                return {"error": "Failed to recreate index"}
        elif drop_index:
            logger.info("Dropping Pinecone index...")
            if not self.pinecone_db.delete_index():
                return {"error": "Failed to drop index"}

        # Step 1: Fetch landmarks
        logger.info(f"Fetching landmarks from page {start_page} to {end_page}...")
        landmarks = self.get_landmarks(start_page, end_page, page_size)

        # Note: download_limit might need reconsideration in batch mode.
        # Applying it here might unevenly distribute work if applied after fetching.
        # For now, we keep it, but it might be better applied per-batch or removed.
        if download_limit and download_limit > 0:
            logger.warning(
                f"Applying download limit of {download_limit} across fetched landmarks."
            )
            landmarks = landmarks[:download_limit]

        if not landmarks:
            return {"error": "No landmarks found"}

        # Step 2: Process landmarks in parallel
        logger.info(f"Processing {len(landmarks)} landmarks with {workers} workers")

        results: List[Dict[str, Any]] = []
        with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
            future_to_landmark = {
                executor.submit(self.process_landmark_worker, landmark): landmark
                for landmark in landmarks
            }

            for future in tqdm(
                concurrent.futures.as_completed(future_to_landmark),
                total=len(future_to_landmark),
                desc="Processing landmarks",
            ):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    landmark = future_to_landmark[future]
                    landmark_id = landmark.get("id", "") or landmark.get(
                        "lpNumber", "unknown"
                    )
                    logger.error(
                        f"Worker exception for landmark {landmark_id}: {str(e)}"
                    )
                    results.append(
                        {
                            "landmark_id": landmark_id,
                            "status": "failed",
                            "errors": [str(e)],
                            "stats": {},
                        }
                    )

        # Step 3: Aggregate statistics
        stats = self._aggregate_results(results)
        stats["elapsed_time"] = f"{time.time() - start_time:.2f} seconds"

        # Step 4: Save statistics
        stats_file = self.data_dir / "pipeline_stats.json"
        with open(stats_file, "w") as f:
            json.dump(stats, f, indent=2)

        return stats

    def _aggregate_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate statistics from parallel processing results.

        Args:
            results: List of processing results

        Returns:
            Dict: Aggregated statistics
        """
        stats: Dict[str, Any] = {
            "landmarks_fetched": len(results),
            "landmarks_processed": 0,
            "pdfs_downloaded": 0,
            "pdfs_processed": 0,
            "chunks_created": 0,
            "embeddings_generated": 0,
            "vectors_stored": 0,
            "errors": [],
            "successful_landmarks": [],
            "failed_landmarks": [],
        }

        for result in results:
            if result["status"] == "success":
                stats["landmarks_processed"] += 1
                stats["successful_landmarks"].append(result["landmark_id"])

                if result["stats"].get("pdf_downloaded"):
                    stats["pdfs_downloaded"] += 1

                if result["stats"].get("text_extracted"):
                    stats["pdfs_processed"] += 1

                stats["chunks_created"] += result["stats"].get("chunks_created", 0)
                stats["embeddings_generated"] += result["stats"].get(
                    "embeddings_generated", 0
                )
                stats["vectors_stored"] += result["stats"].get("vectors_stored", 0)
            else:
                stats["failed_landmarks"].append(result["landmark_id"])
                stats["errors"].extend(result["errors"])

        stats["pipeline_success"] = (
            len(stats["successful_landmarks"]) > 0 and len(stats["errors"]) == 0
        )

        return stats

    def run(
        self,
        start_page: int,
        end_page: int,
        page_size: int = 100,
        download_limit: Optional[int] = None,
        recreate_index: bool = False,
        drop_index: bool = False,
    ) -> Dict[str, Any]:
        """Run the pipeline sequentially for a given page range.

        Args:
            start_page: The starting page number to fetch
            end_page: The ending page number to fetch
            page_size: Number of landmarks per page
            download_limit: Maximum number of PDFs to download
            recreate_index: Whether to recreate the vector index
            drop_index: Whether to drop the vector index without recreating it

        Returns:
            Dictionary with pipeline statistics
        """
        start_time = time.time()

        # Vector DB management
        if recreate_index:
            logger.info("Recreating Pinecone index...")
            if not self.pinecone_db.recreate_index():
                return {"error": "Failed to recreate index"}
        elif drop_index:
            logger.info("Dropping Pinecone index...")
            if not self.pinecone_db.delete_index():
                return {"error": "Failed to drop index"}

        # Step 1: Fetch landmarks
        logger.info(f"STEP 1: Fetching landmarks from page {start_page} to {end_page}")
        landmarks = self.get_landmarks(start_page, end_page, page_size)

        # Step 2: Download PDFs
        logger.info("STEP 2: Downloading PDFs")
        # Apply limit here if needed for sequential mode
        if download_limit and download_limit > 0:
            logger.warning(
                f"Applying download limit of {download_limit} in sequential mode."
            )
            landmarks = landmarks[:download_limit]
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
        self.store_in_vector_db(items_with_embeddings)

        # Calculate elapsed time
        elapsed_time = time.time() - start_time

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


def main() -> None:
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(description="NYC Landmarks Pipeline")
    parser.add_argument(
        "--page-size",
        type=int,
        default=100,
        help="Number of landmarks per API page fetch (default: 100)",
    )
    parser.add_argument(
        "--start-page",
        type=int,
        required=True,
        help="Starting page number to fetch (required)",
    )
    parser.add_argument(
        "--end-page",
        type=int,
        required=True,
        help="Ending page number to fetch (required)",
    )
    # --pages argument removed
    parser.add_argument(
        "--download",
        action="store_true",
        help="Download PDFs (Note: --limit might behave unexpectedly in parallel mode)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of PDFs to download (Use with caution in parallel mode)",
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="CoreDataStore API key (optional, uses env var if not set)",
    )

    # Vector database management options
    parser.add_argument(
        "--recreate-index",
        action="store_true",
        help="Drop and recreate the Pinecone index before processing",
    )
    parser.add_argument(
        "--drop-index",
        action="store_true",
        help="Drop the Pinecone index without recreating it",
    )

    # Parallel processing options
    parser.add_argument(
        "--parallel", action="store_true", help="Use parallel processing mode"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of worker processes for parallel processing",
    )

    args = parser.parse_args()

    # Load API key from environment variable if not provided as argument
    api_key = args.api_key or os.environ.get("COREDATASTORE_API_KEY")

    # Set download limit based on arguments
    download_limit = args.limit if args.download else 0

    # Initialize pipeline
    pipeline = LandmarkPipeline(api_key)

    try:
        # Run in appropriate mode
        if args.parallel:
            if args.start_page > args.end_page:
                raise ValueError("Start page cannot be greater than end page.")
            logger.info(
                f"Using parallel processing mode for pages {args.start_page}-{args.end_page}"
            )
            stats = pipeline.run_parallel(
                start_page=args.start_page,
                end_page=args.end_page,
                page_size=args.page_size,
                download_limit=download_limit,
                workers=args.workers,
                recreate_index=args.recreate_index,
                drop_index=args.drop_index,
            )
        else:
            if args.start_page > args.end_page:
                raise ValueError("Start page cannot be greater than end page.")
            logger.info(
                f"Using sequential processing mode for pages {args.start_page}-{args.end_page}"
            )
            stats = pipeline.run(
                start_page=args.start_page,
                end_page=args.end_page,
                page_size=args.page_size,
                download_limit=download_limit,
                recreate_index=args.recreate_index,
                drop_index=args.drop_index,
            )

        # Print summary if we have stats
        print("\nPipeline Summary:")

        if "landmarks_fetched" in stats:
            print(f"Landmarks fetched: {stats['landmarks_fetched']}")
            print(f"PDFs downloaded: {stats.get('pdfs_downloaded', 0)}")
            print(f"PDFs processed: {stats.get('pdfs_processed', 0)}")
            print(f"Text chunks created: {stats.get('chunks_created', 0)}")
            print(f"Embeddings generated: {stats.get('embeddings_generated', 0)}")
            print(f"Vectors stored: {stats.get('vectors_stored', 0)}")
            print(f"Elapsed time: {stats.get('elapsed_time', 'N/A')}")
        else:
            # Handle the case where the pipeline returned an error dictionary
            if "error" in stats:
                print(f"Pipeline error: {stats['error']}")
            else:
                print("Unknown pipeline result")

        if stats.get("errors") and len(stats["errors"]) > 0:
            print(f"Errors: {len(stats['errors'])}")
            print("Check the logs for details")
        elif "error" not in stats:
            print("Status: Success")

    except Exception as e:
        print("\nPipeline Execution Error:")
        print(f"Error: {str(e)}")
        print("Check the logs for more details.")


if __name__ == "__main__":
    main()

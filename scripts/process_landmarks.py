"""
NYC Landmarks Pipeline Script

This script implements a processing pipeline for NYC landmarks data:
1. Fetches landmark data from the CoreDataStore API
2. Extracts PDF URLs and downloads PDF reports
3. (Placeholder) Processes PDFs to extract text
4. (Placeholder) Generates embeddings from text
5. (Placeholder) Stores embeddings in vector database

Usage:
  python scripts/process_landmarks.py --pages 2 --download
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, cast
from urllib.parse import urljoin

import requests

# Add the project root to the path so we can import nyc_landmarks modules
sys.path.append(str(Path(__file__).resolve().parent.parent))
from nyc_landmarks.utils.logger import get_logger

# Configure logger for this script
logger = get_logger(name="process_landmarks")


class CoreDataStoreClient:
    """CoreDataStore API client for landmark operations."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        """Initialize the CoreDataStore API client."""
        self.base_url = "https://api.coredatastore.com"
        self.api_key = api_key
        self.headers = {}

        # Set up authorization header if API key is provided
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"

        logger.info("Initialized CoreDataStore API client")

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Union[Dict[str, Any], List[Any]]:
        """Make a request to the CoreDataStore API."""
        url = urljoin(self.base_url, endpoint)

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                params=params,
                json=json_data,
                timeout=30,
            )

            # Raise exception for error status codes
            response.raise_for_status()

            # Return JSON response if available
            if response.content:
                # Cast the response to the expected return type
                return cast(Union[Dict[str, Any], List[Any]], response.json())
            return {}

        except requests.exceptions.RequestException as e:
            logger.error(f"API request error: {e}")
            raise Exception(f"Error making API request: {e}")


class LandmarkPipeline:
    """Pipeline for processing NYC landmark data."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the pipeline components."""
        self.api_client = CoreDataStoreClient(api_key)
        self.data_dir = Path("data")
        self.pdfs_dir = self.data_dir / "pdfs"
        self.text_dir = self.data_dir / "text"

        # Ensure directories exist
        self.data_dir.mkdir(exist_ok=True)
        self.pdfs_dir.mkdir(exist_ok=True)
        self.text_dir.mkdir(exist_ok=True)

        # Initialize statistics with proper typing
        self.stats: Dict[str, Any] = {
            "landmarks_fetched": 0,
            "pdfs_downloaded": 0,
            "pdfs_processed": 0,
            "errors": [],  # This is now explicitly a list
        }

    def get_landmarks(
        self, page_size: int = 10, pages: int = 1
    ) -> List[Dict[str, Any]]:
        """Get landmark reports from the API."""
        all_landmarks = []

        for page in range(1, pages + 1):
            logger.info(f"Fetching page {page} of {pages}")
            try:
                # Make the direct API request
                response = self.api_client._make_request(
                    "GET", f"/api/LpcReport/{page_size}/{page}"
                )

                # Extract results
                if response and isinstance(response, dict) and "results" in response:
                    landmarks = response["results"]
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
                self.stats["errors"].append(error_msg)  # Now properly typed
                break

        self.stats["landmarks_fetched"] = len(all_landmarks)
        return all_landmarks

    def download_pdfs(
        self, landmarks: List[Dict[str, Any]], limit: Optional[int] = None
    ) -> List[Tuple[str, Path]]:
        """Download PDFs for landmarks.

        Returns:
            List of tuples with (landmark_id, pdf_path)
        """
        downloaded = []

        # Filter landmarks that have PDF URLs
        landmarks_with_pdfs = [
            landmark
            for landmark in landmarks
            if "pdfReportUrl" in landmark and landmark["pdfReportUrl"]
        ]

        # Apply limit if specified
        if limit is not None:
            landmarks_with_pdfs = landmarks_with_pdfs[:limit]

        for landmark in landmarks_with_pdfs:
            try:
                landmark_id = landmark.get("lpNumber", "")
                pdf_url = landmark["pdfReportUrl"]

                # Generate filename
                filename = f"{landmark_id.replace('/', '_')}.pdf"
                filepath = self.pdfs_dir / filename

                # Skip if already downloaded
                if filepath.exists():
                    logger.info(f"PDF for {landmark_id} already exists at {filepath}")
                    downloaded.append((landmark_id, filepath))
                    continue

                # Download the PDF
                logger.info(f"Downloading PDF for {landmark_id} from {pdf_url}")
                response = requests.get(pdf_url, stream=True, timeout=30)
                response.raise_for_status()

                with open(filepath, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                downloaded.append((landmark_id, filepath))
                logger.info(f"Successfully downloaded {filepath}")

                # Add a small delay
                time.sleep(0.5)

            except Exception as e:
                error_msg = f"Error downloading PDF for landmark {landmark.get('lpNumber', 'unknown')}: {str(e)}"
                logger.error(error_msg)
                self.stats["errors"].append(error_msg)

        self.stats["pdfs_downloaded"] = len(downloaded)
        return downloaded

    def extract_text(self, pdf_paths: List[Tuple[str, Path]]) -> List[Tuple[str, str]]:
        """Extract text from PDFs.

        Note: This is a placeholder function. In a real implementation, this would
        use a PDF text extraction library to process the PDFs.

        Returns:
            List of tuples with (landmark_id, text_content)
        """
        logger.info("Text extraction not yet implemented")
        return [(landmark_id, "") for landmark_id, _ in pdf_paths]

    def generate_embeddings(
        self, texts: List[Tuple[str, str]]
    ) -> List[Tuple[str, List[float]]]:
        """Generate embeddings from text.

        Note: This is a placeholder function. In a real implementation, this would
        use OpenAI or another embedding model to generate embeddings.

        Returns:
            List of tuples with (landmark_id, embedding_vector)
        """
        logger.info("Embedding generation not yet implemented")
        return [(landmark_id, []) for landmark_id, _ in texts]

    def store_in_vector_db(self, embeddings: List[Tuple[str, List[float]]]) -> bool:
        """Store embeddings in vector database.

        Note: This is a placeholder function. In a real implementation, this would
        use Pinecone or another vector database to store the embeddings.

        Returns:
            Success status
        """
        logger.info("Vector database storage not yet implemented")
        return True

    def run(
        self, page_size: int = 10, pages: int = 1, download_limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """Run the pipeline."""
        start_time = time.time()

        # Step 1: Fetch landmarks
        logger.info("STEP 1: Fetching landmarks")
        landmarks = self.get_landmarks(page_size, pages)

        # Step 2: Download PDFs
        logger.info("STEP 2: Downloading PDFs")
        pdf_paths = self.download_pdfs(landmarks, download_limit)

        # Step 3: Extract text (placeholder)
        logger.info("STEP 3: Extracting text (placeholder)")
        texts = self.extract_text(pdf_paths)

        # Step 4: Generate embeddings (placeholder)
        logger.info("STEP 4: Generating embeddings (placeholder)")
        embeddings = self.generate_embeddings(texts)

        # Step 5: Store in vector database (placeholder)
        logger.info("STEP 5: Storing in vector database (placeholder)")
        store_success = self.store_in_vector_db(embeddings)

        # Save landmarks data
        landmarks_file = self.data_dir / "landmarks.json"
        with open(landmarks_file, "w") as f:
            json.dump(landmarks, f, indent=2)

        # Calculate statistics
        elapsed_time = time.time() - start_time
        self.stats["elapsed_time"] = f"{elapsed_time:.2f} seconds"
        self.stats["pipeline_success"] = len(self.stats["errors"]) == 0

        # Save statistics
        stats_file = self.data_dir / "pipeline_stats.json"
        with open(stats_file, "w") as f:
            json.dump(self.stats, f, indent=2)

        logger.info(f"Pipeline completed in {elapsed_time:.2f} seconds")
        logger.info(f"Landmarks fetched: {self.stats['landmarks_fetched']}")
        logger.info(f"PDFs downloaded: {self.stats['pdfs_downloaded']}")

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
    print(f"Elapsed time: {stats['elapsed_time']}")

    if stats["errors"]:
        print(f"Errors: {len(stats['errors'])}")
        print("Check pipeline.log for details")
    else:
        print("Status: Success")


if __name__ == "__main__":
    main()

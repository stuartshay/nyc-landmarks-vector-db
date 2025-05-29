"""
Fetch landmark reports from the NYC Landmarks Vector Database with Wikipedia article counting.

This script provides a unified interface for retrieving landmark data using the
DbClient. It supports full dataset pagination, PDF URL extraction, sample
downloading capabilities, and Wikipedia article counting.

Key Features:
- Total record count retrieval and intelligent pagination
- Complete dataset processing with progress tracking
- PDF URL extraction and optional sample downloading
- Wikipedia article counting for each landmark
- Filtering by borough, object type, neighborhood, and more
- JSON output with timestamps for data analysis
- Robust error handling and comprehensive logging

Usage Examples:

Basic Usage:
    # Fetch all landmark reports with default settings
    python scripts/fetch_landmark_reports.py

    # Get total count and page through first 100 records
    python scripts/fetch_landmark_reports.py --limit 100

    # Show progress for large dataset processing
    python scripts/fetch_landmark_reports.py --verbose

    # Include Wikipedia article counts for each landmark
    python scripts/fetch_landmark_reports.py --include-wikipedia --limit 50

Filtering Options:
    # Filter by borough
    python scripts/fetch_landmark_reports.py --borough Manhattan

    # Filter by object type
    python scripts/fetch_landmark_reports.py --object-type "Individual Landmark"

    # Filter by neighborhood
    python scripts/fetch_landmark_reports.py --neighborhood "Greenwich Village"

    # Combine multiple filters with Wikipedia counting
    python scripts/fetch_landmark_reports.py --borough Brooklyn --object-type "Historic District" --include-wikipedia

    # Search with text query
    python scripts/fetch_landmark_reports.py --search "brownstone"

Advanced Features:
    # Download sample PDFs (first 5)
    python scripts/fetch_landmark_reports.py --download --samples 5

    # Custom page size for processing
    python scripts/fetch_landmark_reports.py --page-size 100

    # Sort results
    python scripts/fetch_landmark_reports.py --sort-column name --sort-order asc

    # Process specific page range
    python scripts/fetch_landmark_reports.py --page 5 --limit 50

    # Include Wikipedia data with Excel export
    python scripts/fetch_landmark_reports.py --include-wikipedia --export-excel --limit 100

    # Include PDF index status for landmark reports
    python scripts/fetch_landmark_reports.py --include-pdf-index --limit 100

    # Combine Wikipedia data and PDF index status
    python scripts/fetch_landmark_reports.py --include-wikipedia --include-pdf-index --limit 50 --export-excel

Excel Export Option:
    # Export results to Excel (XLSX) format
    python scripts/fetch_landmark_reports.py --export-excel

Output Files:
    # Files are saved with timestamps in output/ directory (or as specified by --output-dir)
    output/landmark_reports_20250526_180000.json    # Full landmark data with Wikipedia and/or PDF index status
    output/pdf_urls_20250526_180000.json           # Extracted PDF URLs
    output/fetch_landmark_YYYY_MM_DD_HH_MM.xlsx    # Excel export (if --export-excel is used)

Environment Variables:
    COREDATASTORE_API_KEY: Optional API key for enhanced access

Dependencies:
    - nyc_landmarks.db.db_client: Database client interface
    - nyc_landmarks.models.landmark_models: Pydantic data models
    - nyc_landmarks.utils.logger: Centralized logging

Note: This script replaces direct CoreDataStore API calls with the unified
DbClient interface, providing better error handling, data validation, and
consistency with the rest of the project.
"""

import argparse
import datetime
import json
import os
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

# Add the project root to the path so we can import nyc_landmarks modules
sys.path.append(str(Path(__file__).resolve().parent.parent))

from nyc_landmarks.db.db_client import get_db_client
from nyc_landmarks.models.landmark_models import LpcReportResponse
from nyc_landmarks.utils.exceptions import WikipediaAPIError
from nyc_landmarks.utils.file_utils import ensure_directory_exists
from nyc_landmarks.utils.logger import get_logger

# Configure logger for this script
logger = get_logger(name="fetch_landmark_reports")


@dataclass
class ProcessingMetrics:
    """Track processing metrics and performance."""

    total_records: int = 0
    processed_records: int = 0
    records_with_pdfs: int = 0
    processing_time: float = 0.0
    errors_encountered: List[str] = field(default_factory=list)
    pages_processed: int = 0
    # Wikipedia article metrics
    wikipedia_enabled: bool = False
    landmarks_with_wikipedia: int = 0
    total_wikipedia_articles: int = 0
    wikipedia_api_failures: int = 0
    # PDF index metrics
    pdf_index_enabled: bool = False
    landmarks_in_pdf_index: int = 0
    pdf_index_check_failures: int = 0


@dataclass
class ProcessingResult:
    """Result of landmark processing operation."""

    reports: List[Dict[str, Any]]
    pdf_info: List[Dict[str, str]]
    metrics: ProcessingMetrics
    output_files: Dict[str, str]


class LandmarkReportProcessor:
    """
    Enhanced landmark report processor using DbClient.

    This class provides a high-level interface for fetching, processing,
    and exporting landmark data from the NYC Landmarks database.
    """

    def __init__(self, verbose: bool = False) -> None:
        """Initialize with DbClient and configure logging.

        Args:
            verbose: Enable verbose logging output
        """
        self.db_client = get_db_client()
        self.verbose = verbose

        if self.verbose:
            logger.info("Initialized LandmarkReportProcessor with DbClient")

    def get_total_count(self) -> int:
        """Get total number of landmark records available.

        Returns:
            Total count of landmark records in the database
        """
        try:
            total_count = self.db_client.get_total_record_count()
            logger.info(f"Total landmark records available: {total_count:,}")
            return total_count
        except Exception as e:
            logger.error(f"Error getting total record count: {e}")
            # Return a reasonable default if count retrieval fails
            return 100

    def fetch_all_reports(
        self,
        page_size: int = 50,
        max_records: Optional[int] = None,
        borough: Optional[str] = None,
        object_type: Optional[str] = None,
        neighborhood: Optional[str] = None,
        search_text: Optional[str] = None,
        parent_style_list: Optional[List[str]] = None,
        sort_column: Optional[str] = None,
        sort_order: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch all landmark reports with filtering and pagination.

        Args:
            page_size: Number of records per page
            max_records: Maximum number of records to fetch (None for all)
            borough: Filter by borough name
            object_type: Filter by object type
            neighborhood: Filter by neighborhood
            search_text: Text search query
            parent_style_list: List of architectural styles to filter by
            sort_column: Column to sort results by
            sort_order: Sort direction ('asc' or 'desc')

        Returns:
            List of landmark report dictionaries
        """
        all_reports = []
        page = 1
        total_fetched = 0

        # Get total count for progress tracking
        if max_records is None:
            total_count = self.get_total_count()
            max_records = total_count

        logger.info(
            f"Starting to fetch up to {max_records:,} records with page size {page_size}"
        )

        while total_fetched < max_records:
            try:
                # Calculate remaining records needed
                remaining = max_records - total_fetched
                current_page_size = min(page_size, remaining)

                if self.verbose:
                    logger.info(
                        f"Fetching page {page} (records {total_fetched + 1}-{total_fetched + current_page_size})"
                    )

                # Fetch current page using DbClient
                response: LpcReportResponse = self.db_client.get_lpc_reports(
                    page=page,
                    limit=current_page_size,
                    borough=borough,
                    object_type=object_type,
                    neighborhood=neighborhood,
                    search_text=search_text,
                    parent_style_list=parent_style_list,
                    sort_column=sort_column,
                    sort_order=sort_order,
                )

                # Convert Pydantic models to dictionaries
                page_reports = [model.model_dump() for model in response.results]

                if not page_reports:
                    logger.info(f"No more records found on page {page}")
                    break

                all_reports.extend(page_reports)
                total_fetched += len(page_reports)

                logger.info(
                    f"Fetched {len(page_reports)} records from page {page} (total: {total_fetched:,})"
                )

                # If we got fewer records than requested, we've reached the end
                if len(page_reports) < current_page_size:
                    logger.info("Reached end of available records")
                    break

                page += 1

            except Exception as e:
                logger.error(f"Error fetching page {page}: {e}")
                # Continue with next page on error
                page += 1
                if page > 100:  # Safety limit to prevent infinite loops
                    logger.error("Reached maximum page limit, stopping")
                    break

        logger.info(f"Successfully fetched {len(all_reports):,} landmark reports")
        return all_reports

    def extract_pdf_urls(self, reports: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Extract PDF URLs and basic info from reports.

        Args:
            reports: List of landmark report dictionaries

        Returns:
            List of dictionaries containing PDF information
        """
        pdf_info = []

        for report in reports:
            pdf_url = report.get("pdfReportUrl")
            if pdf_url and pdf_url.strip():
                pdf_info.append(
                    {
                        "id": report.get("lpNumber", ""),
                        "name": report.get("name", ""),
                        "pdf_url": pdf_url,
                        "borough": report.get("borough", ""),
                        "object_type": report.get("objectType", ""),
                    }
                )

        logger.info(f"Extracted {len(pdf_info)} PDF URLs from {len(reports)} reports")
        return pdf_info

    def add_wikipedia_article_counts(
        self, reports: List[Dict[str, Any]], metrics: ProcessingMetrics
    ) -> List[Dict[str, Any]]:
        """Add Wikipedia article counts to landmark reports.

        Args:
            reports: List of landmark report dictionaries
            metrics: Processing metrics to update

        Returns:
            Updated list of landmark reports with Wikipedia article counts
        """
        if not metrics.wikipedia_enabled:
            return reports

        logger.info("Adding Wikipedia article counts to landmark reports...")

        for i, report in enumerate(reports):
            self._process_single_report_wikipedia(report, i, len(reports), metrics)

        self._log_wikipedia_summary(metrics, len(reports))
        return reports

    def _process_single_report_wikipedia(
        self,
        report: Dict[str, Any],
        index: int,
        total_reports: int,
        metrics: ProcessingMetrics,
    ) -> None:
        """Process Wikipedia article count for a single landmark report.

        Args:
            report: Single landmark report dictionary
            index: Current report index (0-based)
            total_reports: Total number of reports being processed
            metrics: Processing metrics to update
        """
        landmark_id = report.get("lpNumber") or report.get("lpcId")

        if not landmark_id:
            logger.warning(
                f"No landmark ID found for report {index + 1}, skipping Wikipedia lookup"
            )
            report["wikipedia_article_count"] = 0
            report["in_wikipedia_index"] = "No"
            return

        try:
            article_count = self._fetch_wikipedia_articles_for_landmark(
                landmark_id, index, total_reports
            )
            report["wikipedia_article_count"] = article_count
            # Add new column to indicate if landmark exists in Wikipedia index
            report["in_wikipedia_index"] = "Yes" if article_count > 0 else "No"

            if article_count > 0:
                metrics.landmarks_with_wikipedia += 1
                metrics.total_wikipedia_articles += article_count

        except Exception as e:
            self._handle_wikipedia_fetch_error(e, landmark_id, metrics)
            report["wikipedia_article_count"] = 0
            report["in_wikipedia_index"] = "No"

    def _fetch_wikipedia_articles_for_landmark(
        self, landmark_id: str, index: int, total_reports: int
    ) -> int:
        """Fetch Wikipedia articles for a specific landmark.

        Args:
            landmark_id: The landmark identifier
            index: Current report index (0-based)
            total_reports: Total number of reports being processed

        Returns:
            Number of Wikipedia articles found
        """
        if self.verbose:
            logger.info(
                f"Fetching Wikipedia articles for landmark {landmark_id} ({index + 1}/{total_reports})"
            )

        wikipedia_articles = self.db_client.get_wikipedia_articles(landmark_id)
        article_count = len(wikipedia_articles)

        if self.verbose and article_count > 0:
            logger.info(
                f"Found {article_count} Wikipedia articles for landmark {landmark_id}"
            )

        return article_count

    def _handle_wikipedia_fetch_error(
        self, error: Exception, landmark_id: str, metrics: ProcessingMetrics
    ) -> None:
        """Handle errors that occur during Wikipedia article fetching.

        Args:
            error: The exception that occurred
            landmark_id: The landmark identifier
            metrics: Processing metrics to update

        Raises:
            WikipediaAPIError: If this is a critical API failure
        """
        error_msg = (
            f"Error fetching Wikipedia articles for landmark {landmark_id}: {error}"
        )
        logger.error(error_msg)
        metrics.errors_encountered.append(error_msg)
        metrics.wikipedia_api_failures += 1

        # If this is a critical API failure (not just missing articles), raise the error
        if isinstance(error, requests.exceptions.ConnectionError):
            raise WikipediaAPIError(
                "Wikipedia API is unreachable", original_error=error
            )

    def _log_wikipedia_summary(
        self, metrics: ProcessingMetrics, total_reports: int
    ) -> None:
        """Log summary of Wikipedia article processing.

        Args:
            metrics: Processing metrics with Wikipedia data
            total_reports: Total number of reports processed
        """
        logger.info(
            f"Completed Wikipedia article counting for {total_reports} landmarks"
        )
        logger.info(
            f"Found Wikipedia articles for {metrics.landmarks_with_wikipedia} landmarks"
        )
        logger.info(f"Total Wikipedia articles: {metrics.total_wikipedia_articles}")

        if metrics.wikipedia_api_failures > 0:
            logger.warning(f"Wikipedia API failures: {metrics.wikipedia_api_failures}")

    def download_sample_pdfs(
        self,
        pdf_info: List[Dict[str, str]],
        output_dir: str = "sample_pdfs",
        limit: int = 5,
    ) -> List[str]:
        """Download a sample of PDFs.

        Args:
            pdf_info: List of PDF information dictionaries
            output_dir: Directory to save downloaded PDFs
            limit: Maximum number of PDFs to download

        Returns:
            List of downloaded file paths
        """
        if not pdf_info:
            logger.warning("No PDF URLs available for download")
            return []

        # Create output directory if it doesn't exist
        ensure_directory_exists(output_dir)

        downloaded_paths = []
        download_count = min(limit, len(pdf_info))

        logger.info(f"Downloading {download_count} sample PDFs to {output_dir}")

        for i, item in enumerate(pdf_info[:download_count]):
            try:
                pdf_url = item["pdf_url"]
                landmark_id = item["id"]

                # Generate safe filename
                safe_id = landmark_id.replace("/", "_").replace("\\", "_")
                filename = f"{safe_id}.pdf"
                filepath = os.path.join(output_dir, filename)

                logger.info(f"Downloading PDF {i + 1}/{download_count}: {landmark_id}")

                # Download the PDF with timeout and error handling
                response = requests.get(pdf_url, stream=True, timeout=60)
                response.raise_for_status()

                with open(filepath, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                downloaded_paths.append(filepath)
                logger.info(f"Successfully downloaded: {filename}")

            except Exception as e:
                logger.error(f"Error downloading PDF for {landmark_id}: {e}")
                continue

        logger.info(f"Successfully downloaded {len(downloaded_paths)} PDFs")
        return downloaded_paths

    def process_with_progress(
        self,
        page_size: int = 50,
        max_records: Optional[int] = None,
        download_samples: bool = False,
        sample_limit: int = 5,
        output_dir: str = "output",
        include_wikipedia: bool = False,
        include_pdf_index: bool = False,
        **filters: Any,
    ) -> ProcessingResult:
        """Process all records with progress tracking and metrics.

        Args:
            page_size: Records per page for pagination
            max_records: Maximum records to process (None for all)
            download_samples: Whether to download sample PDFs
            sample_limit: Number of sample PDFs to download
            output_dir: Directory for output files
            include_wikipedia: Whether to include Wikipedia article counts
            include_pdf_index: Whether to check if PDFs are indexed in vector database
            **filters: Additional filters (borough, object_type, etc.)

        Returns:
            ProcessingResult with reports, metrics, and output files
        """
        start_time = time.time()
        metrics = ProcessingMetrics()
        metrics.wikipedia_enabled = include_wikipedia
        metrics.pdf_index_enabled = include_pdf_index

        try:
            # Get total count
            metrics.total_records = self.get_total_count()

            # Fetch all reports with filters
            logger.info("Starting landmark report processing...")
            reports = self.fetch_all_reports(
                page_size=page_size, max_records=max_records, **filters
            )

            metrics.processed_records = len(reports)

            # Extract PDF information
            pdf_info = self.extract_pdf_urls(reports)
            metrics.records_with_pdfs = len(pdf_info)

            # Add Wikipedia article counts if requested
            if include_wikipedia:
                reports = self.add_wikipedia_article_counts(reports, metrics)
            else:
                # Ensure in_wikipedia_index column is present for Excel export consistency
                reports = self.ensure_wikipedia_index_column(reports)

            # Add PDF index status if requested
            if include_pdf_index:
                reports = self.add_pdf_index_status(reports, metrics)
            else:
                # Ensure in_pdf_index column is present for consistency
                reports = self.ensure_pdf_index_column(reports)

            # Download sample PDFs if requested
            downloaded_paths = []
            if download_samples and pdf_info:
                downloaded_paths = self.download_sample_pdfs(
                    pdf_info,
                    output_dir=os.path.join(output_dir, "sample_pdfs"),
                    limit=sample_limit,
                )

            # Save results to files
            output_files = self._save_results(reports, pdf_info, output_dir, metrics)

            # Calculate final metrics
            metrics.processing_time = time.time() - start_time

            # Log summary
            self._log_processing_summary(metrics, len(downloaded_paths), reports)

            return ProcessingResult(
                reports=reports,
                pdf_info=pdf_info,
                metrics=metrics,
                output_files=output_files,
            )

        except Exception as e:
            metrics.errors_encountered.append(str(e))
            logger.error(f"Error during processing: {e}")
            raise

    def _save_results(
        self,
        reports: List[Dict[str, Any]],
        pdf_info: List[Dict[str, str]],
        output_dir: str,
        metrics: ProcessingMetrics,
    ) -> Dict[str, str]:
        """Save processing results to JSON files.

        Args:
            reports: List of landmark reports
            pdf_info: List of PDF information
            output_dir: Output directory
            metrics: Processing metrics for summary

        Returns:
            Dictionary mapping file types to output paths
        """
        # Create timestamp for unique filenames
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        # Ensure output directory exists
        ensure_directory_exists(output_dir)

        # Define file paths
        landmark_reports_path = Path(output_dir) / f"landmark_reports_{timestamp}.json"
        pdf_urls_path = Path(output_dir) / f"pdf_urls_{timestamp}.json"

        # Create output data with summary
        output_data: Dict[str, Any] = {
            "metadata": {
                "timestamp": timestamp,
                "total_landmarks": len(reports),
                "landmarks_with_pdfs": len(pdf_info),
                "processing_time_seconds": metrics.processing_time,
                "wikipedia_enabled": metrics.wikipedia_enabled,
            },
            "landmarks": reports,
        }

        # Add Wikipedia summary if enabled
        if metrics.wikipedia_enabled:
            output_data["metadata"]["wikipedia_summary"] = {
                "landmarks_with_wikipedia": metrics.landmarks_with_wikipedia,
                "total_wikipedia_articles": metrics.total_wikipedia_articles,
                "wikipedia_api_failures": metrics.wikipedia_api_failures,
                "average_articles_per_landmark": (
                    round(metrics.total_wikipedia_articles / len(reports), 2)
                    if len(reports) > 0
                    else 0
                ),
            }

        # Add PDF index summary if enabled
        if metrics.pdf_index_enabled:
            output_data["metadata"]["pdf_index_summary"] = {
                "landmarks_in_pdf_index": metrics.landmarks_in_pdf_index,
                "pdf_index_check_failures": metrics.pdf_index_check_failures,
                "pdf_index_coverage_percentage": (
                    round((metrics.landmarks_in_pdf_index / len(reports)) * 100, 2)
                    if len(reports) > 0
                    else 0
                ),
            }

        # Save landmark reports with metadata
        with open(landmark_reports_path, "w") as f:
            json.dump(output_data, f, indent=2, default=str)

        # Save PDF URLs
        with open(pdf_urls_path, "w") as f:
            json.dump(pdf_info, f, indent=2, default=str)

        output_files = {
            "landmark_reports": str(landmark_reports_path),
            "pdf_urls": str(pdf_urls_path),
        }

        logger.info("Results saved to:")
        logger.info(f"  Landmark reports: {landmark_reports_path}")
        logger.info(f"  PDF URLs: {pdf_urls_path}")

        return output_files

    def _log_processing_summary(
        self,
        metrics: ProcessingMetrics,
        downloaded_count: int,
        reports: List[Dict[str, Any]],
    ) -> None:
        """Log processing summary with metrics.

        Args:
            metrics: Processing metrics
            downloaded_count: Number of PDFs downloaded
            reports: List of landmark reports for calculating averages
        """
        logger.info("\n" + "=" * 60)
        logger.info("PROCESSING SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total records in database: {metrics.total_records:,}")
        logger.info(f"Records processed: {metrics.processed_records:,}")
        logger.info(f"Records with PDF URLs: {metrics.records_with_pdfs:,}")
        logger.info(f"Sample PDFs downloaded: {downloaded_count}")
        logger.info(f"Processing time: {metrics.processing_time:.2f} seconds")

        # Wikipedia summary
        if metrics.wikipedia_enabled:
            logger.info("\nWikipedia Article Summary:")
            logger.info(
                f"  Landmarks with Wikipedia articles: {metrics.landmarks_with_wikipedia:,}"
            )
            logger.info(
                f"  Total Wikipedia articles found: {metrics.total_wikipedia_articles:,}"
            )
            logger.info(f"  Wikipedia API failures: {metrics.wikipedia_api_failures:,}")
            if len(reports) > 0:
                avg_articles = metrics.total_wikipedia_articles / len(reports)
                logger.info(f"  Average articles per landmark: {avg_articles:.2f}")

        # PDF index summary
        if metrics.pdf_index_enabled:
            logger.info("\nPDF Index Status Summary:")
            logger.info(
                f"  Landmarks with PDFs in vector index: {metrics.landmarks_in_pdf_index:,}"
            )
            logger.info(
                f"  PDF index check failures: {metrics.pdf_index_check_failures:,}"
            )
            if len(reports) > 0:
                coverage_percentage = (
                    metrics.landmarks_in_pdf_index / len(reports)
                ) * 100
                logger.info(f"  PDF index coverage: {coverage_percentage:.2f}%")

        if metrics.errors_encountered:
            logger.warning(f"Errors encountered: {len(metrics.errors_encountered)}")
            for i, error in enumerate(metrics.errors_encountered[:5], 1):
                logger.warning(f"  {i}. {error}")

        logger.info("=" * 60)

    def ensure_wikipedia_index_column(
        self, reports: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Ensure all reports have the in_wikipedia_index column for Excel export.

        Args:
            reports: List of landmark report dictionaries

        Returns:
            Updated list of landmark reports with in_wikipedia_index column
        """
        for report in reports:
            # If the column doesn't exist, set it to "No"
            if "in_wikipedia_index" not in report:
                report["in_wikipedia_index"] = "No"

        return reports

    def check_pdf_in_index(self, landmark_id: str) -> bool:
        """Check if a landmark's PDF is indexed in the vector database.

        Args:
            landmark_id: The landmark identifier

        Returns:
            True if the PDF is found in the vector index, False otherwise
        """
        try:
            from nyc_landmarks.vectordb.pinecone_db import PineconeDB

            # Initialize Pinecone database connection
            pinecone_db = PineconeDB()

            # Query for vectors with this landmark_id and source_type "pdf"
            vectors = pinecone_db.list_vectors(
                limit=1,  # We only need to know if at least one exists
                landmark_id=landmark_id,
                source_type="pdf",
            )

            # Return True if any vectors are found
            return len(vectors) > 0

        except Exception as e:
            logger.warning(f"Error checking PDF index for landmark {landmark_id}: {e}")
            return False

    def add_pdf_index_status(
        self, reports: List[Dict[str, Any]], metrics: ProcessingMetrics
    ) -> List[Dict[str, Any]]:
        """Add PDF index status to landmark reports.

        Args:
            reports: List of landmark report dictionaries
            metrics: Processing metrics to update

        Returns:
            Updated list of landmark reports with PDF index status
        """
        if not metrics.pdf_index_enabled:
            return reports

        logger.info("Checking PDF index status for landmark reports...")

        for i, report in enumerate(reports):
            landmark_id = report.get("lpNumber") or report.get("lpcId")

            if not landmark_id:
                logger.warning(
                    f"No landmark ID found for report {i + 1}, skipping PDF index check"
                )
                report["in_pdf_index"] = "No"
                metrics.pdf_index_check_failures += 1
                continue

            try:
                is_in_index = self.check_pdf_in_index(landmark_id)
                report["in_pdf_index"] = "Yes" if is_in_index else "No"

                if is_in_index:
                    metrics.landmarks_in_pdf_index += 1

                if self.verbose and is_in_index:
                    logger.info(
                        f"Landmark {landmark_id} PDF found in vector index ({i + 1}/{len(reports)})"
                    )

            except Exception as e:
                error_msg = f"Error checking PDF index for landmark {landmark_id}: {e}"
                logger.error(error_msg)
                metrics.errors_encountered.append(error_msg)
                report["in_pdf_index"] = "No"
                metrics.pdf_index_check_failures += 1

        # Log summary
        logger.info(f"Completed PDF index checking for {len(reports)} landmarks")
        logger.info(
            f"Found {metrics.landmarks_in_pdf_index} landmarks with PDFs in vector index"
        )

        if metrics.pdf_index_check_failures > 0:
            logger.warning(
                f"PDF index check failures: {metrics.pdf_index_check_failures}"
            )

        return reports

    def ensure_pdf_index_column(
        self, reports: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Ensure all reports have the in_pdf_index column for consistency.

        Args:
            reports: List of landmark report dictionaries

        Returns:
            Updated list of landmark reports with in_pdf_index column
        """
        for report in reports:
            # If the column doesn't exist, set it to "No"
            if "in_pdf_index" not in report:
                report["in_pdf_index"] = "No"

        return reports


def create_argument_parser() -> argparse.ArgumentParser:
    """Create comprehensive argument parser with all available options.

    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description="Fetch and process NYC landmark reports using DbClient with Wikipedia integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Fetch all reports
  %(prog)s --limit 100 --verbose             # Fetch first 100 with progress
  %(prog)s --borough Manhattan               # Filter by borough
  %(prog)s --search "brownstone"             # Search for text
  %(prog)s --download --samples 10           # Download sample PDFs
  %(prog)s --page 5 --page-size 50           # Fetch specific page
  %(prog)s --include-wikipedia --limit 50    # Include Wikipedia article counts
  %(prog)s --include-pdf-index --limit 25    # Check PDF vector index status
        """,
    )
    parser.add_argument(
        "--export-excel",
        action="store_true",
        help="Export results to Excel (.xlsx) in the output directory",
    )

    # Basic pagination options
    parser.add_argument(
        "--page-size",
        type=int,
        default=50,
        help="Number of records per page (default: 50)",
    )
    parser.add_argument(
        "--limit", type=int, help="Maximum total records to fetch (default: all)"
    )
    parser.add_argument("--page", type=int, help="Fetch specific page number only")

    # Filtering options (matching DbClient.get_lpc_reports parameters)
    parser.add_argument(
        "--borough",
        choices=["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"],
        help="Filter by borough",
    )
    parser.add_argument(
        "--object-type",
        help="Filter by object type (e.g., 'Individual Landmark', 'Historic District')",
    )
    parser.add_argument("--neighborhood", help="Filter by neighborhood name")
    parser.add_argument(
        "--search", help="Search text in landmark names and descriptions"
    )
    parser.add_argument(
        "--styles",
        nargs="+",
        help="Filter by architectural styles (space-separated list)",
    )

    # Sorting options
    parser.add_argument(
        "--sort-column",
        help="Column to sort results by (e.g., 'name', 'dateDesignated')",
    )
    parser.add_argument("--sort-order", choices=["asc", "desc"], help="Sort direction")

    # Wikipedia options
    parser.add_argument(
        "--include-wikipedia",
        action="store_true",
        help="Include Wikipedia article counts for each landmark",
    )

    # PDF index options
    parser.add_argument(
        "--include-pdf-index",
        action="store_true",
        help="Check if landmark PDFs are indexed in the vector database",
    )

    # PDF download options
    parser.add_argument("--download", action="store_true", help="Download sample PDFs")
    parser.add_argument(
        "--samples",
        type=int,
        default=5,
        help="Number of sample PDFs to download (default: 5)",
    )

    # Output options
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Output directory for JSON and Excel files (default: output)",
    )

    # Control options
    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose logging output"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be processed without fetching data",
    )

    return parser


def main() -> None:
    """Main entry point with comprehensive argument parsing and processing."""
    parser = create_argument_parser()
    args = parser.parse_args()

    processor = LandmarkReportProcessor(verbose=args.verbose)

    if args.dry_run:
        _handle_dry_run(processor, args)
        return

    if args.page is not None:
        _handle_page_request(processor, args)
        return

    _handle_full_pipeline(processor, args)


def _handle_dry_run(
    processor: LandmarkReportProcessor, args: argparse.Namespace
) -> None:
    """Handle dry run mode - show what would be processed without fetching data."""
    total_count = processor.get_total_count()
    print(f"DRY RUN: Would process up to {args.limit or total_count:,} records")
    print(f"Page size: {args.page_size}")
    if args.borough:
        print(f"Borough filter: {args.borough}")
    if args.object_type:
        print(f"Object type filter: {args.object_type}")
    if args.search:
        print(f"Search filter: {args.search}")
    if args.download:
        print(f"Would download {args.samples} sample PDFs")
    if args.include_wikipedia:
        print("Would include Wikipedia article counts")


def _handle_page_request(
    processor: LandmarkReportProcessor, args: argparse.Namespace
) -> None:
    """Handle specific page request."""
    try:
        logger.info(f"Fetching specific page {args.page} with {args.page_size} records")
        response = processor.db_client.get_lpc_reports(
            page=args.page,
            limit=args.page_size,
            borough=args.borough,
            object_type=args.object_type,
            neighborhood=args.neighborhood,
            search_text=args.search,
            parent_style_list=args.styles,
            sort_column=args.sort_column,
            sort_order=args.sort_order,
        )

        reports = [model.model_dump() for model in response.results]

        # Add Wikipedia counts if requested
        if args.include_wikipedia:
            metrics = ProcessingMetrics()
            metrics.wikipedia_enabled = True
            reports = processor.add_wikipedia_article_counts(reports, metrics)
        else:
            # Still ensure the wikipedia index column is present for consistency
            reports = processor.ensure_wikipedia_index_column(reports)
            metrics = ProcessingMetrics()
            metrics.wikipedia_enabled = False

        # Add PDF index status if requested
        if args.include_pdf_index:
            if not hasattr(metrics, "pdf_index_enabled"):
                metrics.pdf_index_enabled = True
            else:
                metrics.pdf_index_enabled = True
            reports = processor.add_pdf_index_status(reports, metrics)
        else:
            # Still ensure the pdf index column is present for consistency
            reports = processor.ensure_pdf_index_column(reports)
            if not hasattr(metrics, "pdf_index_enabled"):
                metrics.pdf_index_enabled = False

        pdf_info = processor.extract_pdf_urls(reports)

        # Reuse the existing metrics object for saving
        output_files = processor._save_results(
            reports, pdf_info, args.output_dir, metrics
        )

        print(f"\nPage {args.page} Results:")
        print(f"Records fetched: {len(reports)}")
        print(f"Records with PDFs: {len(pdf_info)}")
        if args.include_wikipedia:
            wikipedia_count = sum(
                1 for r in reports if r.get("wikipedia_article_count", 0) > 0
            )
            total_articles = sum(r.get("wikipedia_article_count", 0) for r in reports)
            print(f"Records with Wikipedia articles: {wikipedia_count}")
            print(f"Total Wikipedia articles: {total_articles}")
        if args.include_pdf_index:
            pdf_index_count = sum(1 for r in reports if r.get("in_pdf_index") == "Yes")
            print(f"Records with PDFs in vector index: {pdf_index_count}")
        print(f"Results saved to: {output_files['landmark_reports']}")

    except Exception as e:
        logger.error(f"Error fetching page {args.page}: {e}")
        sys.exit(1)


def _handle_full_pipeline(
    processor: LandmarkReportProcessor, args: argparse.Namespace
) -> None:
    """Handle full pipeline processing."""
    try:
        result = processor.process_with_progress(
            page_size=args.page_size,
            max_records=args.limit,
            download_samples=args.download,
            sample_limit=args.samples,
            output_dir=args.output_dir,
            include_wikipedia=args.include_wikipedia,
            include_pdf_index=args.include_pdf_index,
            borough=args.borough,
            object_type=args.object_type,
            neighborhood=args.neighborhood,
            search_text=args.search,
            parent_style_list=args.styles,
            sort_column=args.sort_column,
            sort_order=args.sort_order,
        )

        # Excel export option
        if getattr(args, "export_excel", False):
            from pathlib import Path

            from nyc_landmarks.utils.excel_helper import (
                add_filtering_to_all_columns,
                export_dicts_to_excel,
                format_excel_columns,
            )

            # Ensure all reports have the in_wikipedia_index column for Excel export
            result.reports = processor.ensure_wikipedia_index_column(result.reports)
            # Ensure all reports have the in_pdf_index column for Excel export
            result.reports = processor.ensure_pdf_index_column(result.reports)

            # Adjust column widths to accommodate Wikipedia columns
            column_widths = {
                "A": 50,  # name
                "B": 15,  # lpNumber
                "C": 15,  # lpcId
                "D": 20,  # objectType
                "E": 20,  # architect
                "F": 20,  # style
                "G": 35,  # street
                "H": 15,  # borough
                "I": 18,  # dateDesignated
                "J": 15,  # photoStatus
                "K": 15,  # mapStatus
                "L": 20,  # neighborhood
                "M": 10,  # zipCode
                "N": 40,  # photoUrl
                "O": 40,  # pdfReportUrl
                "P": 20,  # wikipedia_article_count
                "Q": 20,  # in_wikipedia_index
                "R": 20,  # in_pdf_index (new column)
            }
            timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M")
            excel_path = Path(args.output_dir) / f"fetch_landmark_{timestamp}.xlsx"
            export_dicts_to_excel(
                data=result.reports,
                output_file_path=str(excel_path),
            )
            format_excel_columns(str(excel_path), column_widths)
            add_filtering_to_all_columns(str(excel_path))
            result.output_files["excel"] = str(excel_path)

        print("\nProcessing Complete!")
        print(f"Total reports processed: {result.metrics.processed_records:,}")
        print(f"Reports with PDF URLs: {result.metrics.records_with_pdfs:,}")

        if result.metrics.wikipedia_enabled:
            print(
                f"Landmarks with Wikipedia articles: {result.metrics.landmarks_with_wikipedia:,}"
            )
            print(
                f"Total Wikipedia articles: {result.metrics.total_wikipedia_articles:,}"
            )
            if result.metrics.wikipedia_api_failures > 0:
                print(
                    f"Wikipedia API failures: {result.metrics.wikipedia_api_failures:,}"
                )

        if result.metrics.pdf_index_enabled:
            print(
                f"Landmarks with PDFs in vector index: {result.metrics.landmarks_in_pdf_index:,}"
            )
            if result.metrics.pdf_index_check_failures > 0:
                print(
                    f"PDF index check failures: {result.metrics.pdf_index_check_failures:,}"
                )

        print(f"Processing time: {result.metrics.processing_time:.2f} seconds")
        print(f"Output files: {list(result.output_files.values())}")

    except Exception as e:
        logger.error(f"Processing failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

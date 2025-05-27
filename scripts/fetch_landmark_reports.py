"""
Fetch landmark reports from the NYC Landmarks Vector Database.

This script provides a unified interface for retrieving landmark data using the
DbClient. It supports full dataset pagination, PDF URL extraction, and sample
downloading capabilities.

Key Features:
- Total record count retrieval and intelligent pagination
- Complete dataset processing with progress tracking
- PDF URL extraction and optional sample downloading
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

Filtering Options:
    # Filter by borough
    python scripts/fetch_landmark_reports.py --borough Manhattan

    # Filter by object type
    python scripts/fetch_landmark_reports.py --object-type "Individual Landmark"

    # Filter by neighborhood
    python scripts/fetch_landmark_reports.py --neighborhood "Greenwich Village"

    # Combine multiple filters
    python scripts/fetch_landmark_reports.py --borough Brooklyn --object-type "Historic District"

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

Output Files:
    # Files are saved with timestamps in logs/ directory
    logs/landmark_reports_20250526_180000.json    # Full landmark data
    logs/pdf_urls_20250526_180000.json           # Extracted PDF URLs

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


@dataclass
class ProcessingResult:
    """Result of landmark processing operation."""

    reports: List[Dict[str, Any]]
    pdf_info: List[Dict[str, str]]
    metrics: ProcessingMetrics
    output_files: Dict[str, str]


# Use the utility function from utils.file_utils


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
        output_dir: str = "logs",
        **filters: Any,
    ) -> ProcessingResult:
        """Process all records with progress tracking and metrics.

        Args:
            page_size: Records per page for pagination
            max_records: Maximum records to process (None for all)
            download_samples: Whether to download sample PDFs
            sample_limit: Number of sample PDFs to download
            output_dir: Directory for output files
            **filters: Additional filters (borough, object_type, etc.)

        Returns:
            ProcessingResult with reports, metrics, and output files
        """
        start_time = time.time()
        metrics = ProcessingMetrics()

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

            # Download sample PDFs if requested
            downloaded_paths = []
            if download_samples and pdf_info:
                downloaded_paths = self.download_sample_pdfs(
                    pdf_info,
                    output_dir=os.path.join(output_dir, "sample_pdfs"),
                    limit=sample_limit,
                )

            # Save results to files
            output_files = self._save_results(reports, pdf_info, output_dir)

            # Calculate final metrics
            metrics.processing_time = time.time() - start_time

            # Log summary
            self._log_processing_summary(metrics, len(downloaded_paths))

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
    ) -> Dict[str, str]:
        """Save processing results to JSON files.

        Args:
            reports: List of landmark reports
            pdf_info: List of PDF information
            output_dir: Output directory

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

        # Save landmark reports
        with open(landmark_reports_path, "w") as f:
            json.dump(reports, f, indent=2, default=str)

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
        self, metrics: ProcessingMetrics, downloaded_count: int
    ) -> None:
        """Log processing summary with metrics.

        Args:
            metrics: Processing metrics
            downloaded_count: Number of PDFs downloaded
        """
        logger.info("\n" + "=" * 60)
        logger.info("PROCESSING SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total records in database: {metrics.total_records:,}")
        logger.info(f"Records processed: {metrics.processed_records:,}")
        logger.info(f"Records with PDF URLs: {metrics.records_with_pdfs:,}")
        logger.info(f"Sample PDFs downloaded: {downloaded_count}")
        logger.info(f"Processing time: {metrics.processing_time:.2f} seconds")

        if metrics.errors_encountered:
            logger.warning(f"Errors encountered: {len(metrics.errors_encountered)}")
            for i, error in enumerate(metrics.errors_encountered[:5], 1):
                logger.warning(f"  {i}. {error}")

        logger.info("=" * 60)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create comprehensive argument parser with all available options.

    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description="Fetch and process NYC landmark reports using DbClient",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Fetch all reports
  %(prog)s --limit 100 --verbose             # Fetch first 100 with progress
  %(prog)s --borough Manhattan               # Filter by borough
  %(prog)s --search "brownstone"             # Search for text
  %(prog)s --download --samples 10           # Download sample PDFs
  %(prog)s --page 5 --page-size 50           # Fetch specific page
        """,
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
        default="logs",
        help="Output directory for JSON files (default: logs)",
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

    # Initialize processor
    processor = LandmarkReportProcessor(verbose=args.verbose)

    # Handle dry run
    if args.dry_run:
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
        return

    # Handle specific page request
    if args.page is not None:
        try:
            logger.info(
                f"Fetching specific page {args.page} with {args.page_size} records"
            )
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
            pdf_info = processor.extract_pdf_urls(reports)

            # Save single page results
            output_files = processor._save_results(reports, pdf_info, args.output_dir)

            print(f"\nPage {args.page} Results:")
            print(f"Records fetched: {len(reports)}")
            print(f"Records with PDFs: {len(pdf_info)}")
            print(f"Results saved to: {output_files['landmark_reports']}")

        except Exception as e:
            logger.error(f"Error fetching page {args.page}: {e}")
            sys.exit(1)
        return

    # Process with full pipeline
    try:
        result = processor.process_with_progress(
            page_size=args.page_size,
            max_records=args.limit,
            download_samples=args.download,
            sample_limit=args.samples,
            output_dir=args.output_dir,
            borough=args.borough,
            object_type=args.object_type,
            neighborhood=args.neighborhood,
            search_text=args.search,
            parent_style_list=args.styles,
            sort_column=args.sort_column,
            sort_order=args.sort_order,
        )

        # Print final summary
        print("\nProcessing Complete!")
        print(f"Total reports processed: {result.metrics.processed_records:,}")
        print(f"Reports with PDF URLs: {result.metrics.records_with_pdfs:,}")
        print(f"Processing time: {result.metrics.processing_time:.2f} seconds")
        print(f"Output files: {list(result.output_files.values())}")

    except Exception as e:
        logger.error(f"Processing failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

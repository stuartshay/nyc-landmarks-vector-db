"""
Script to fetch landmark reports from the CoreDataStore API,
extract PDF URLs, and optionally download sample PDFs.

This is a local test script for the NYC Landmarks Vector Database project.
"""

import argparse
import datetime
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import requests

# Add the project root to the path so we can import nyc_landmarks modules
sys.path.append(str(Path(__file__).resolve().parent.parent))
from nyc_landmarks.utils.logger import get_logger

# Configure logger for this script
logger = get_logger(name="fetch_landmark_reports")


def ensure_directory_exists(directory_path: str) -> None:
    """Ensure that the specified directory exists.

    Args:
        directory_path: Path to the directory to ensure exists.
    """
    Path(directory_path).mkdir(parents=True, exist_ok=True)


class CoreDataStoreClient:
    """Simplified CoreDataStore API client for landmark operations."""

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
                return response.json()
            return {}

        except requests.exceptions.RequestException as e:
            logger.error(f"API request error: {e}")
            raise Exception(f"Error making API request: {e}")


class LandmarkReportFetcher:
    """Class to fetch landmark reports and extract PDF URLs."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize with the CoreDataStore API client."""
        self.api_client = CoreDataStoreClient(api_key)

    def get_lpc_reports(
        self, page_size: int = 10, page: int = 1
    ) -> List[Dict[str, Any]]:
        """Get LPC reports with original response format that includes pdfReportUrl."""
        try:
            # Make the direct API request
            response = self.api_client._make_request(
                "GET", f"/api/LpcReport/{page_size}/{page}"
            )

            # Extract and return the results list
            if response and isinstance(response, dict) and "results" in response:
                return response["results"]
            return []

        except Exception as e:
            logger.error(f"Error fetching LPC reports: {e}")
            return []

    def extract_pdf_urls(self, reports: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Extract PDF URLs and basic info from reports."""
        pdf_info = []

        for report in reports:
            if "pdfReportUrl" in report and report["pdfReportUrl"]:
                pdf_info.append(
                    {
                        "id": report.get("lpNumber", ""),
                        "name": report.get("name", ""),
                        "pdf_url": report["pdfReportUrl"],
                    }
                )

        return pdf_info

    def download_sample_pdf(
        self,
        pdf_info: List[Dict[str, str]],
        output_dir: str = "sample_pdfs",
        limit: int = 1,
    ) -> List[str]:
        """Download a sample of PDFs."""
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        downloaded_paths = []
        for i, item in enumerate(pdf_info):
            if i >= limit:
                break

            try:
                pdf_url = item["pdf_url"]
                landmark_id = item["id"]

                # Generate filename
                filename = f"{landmark_id.replace('/', '_')}.pdf"
                filepath = os.path.join(output_dir, filename)

                # Download the PDF
                logger.info(f"Downloading PDF for {landmark_id} from {pdf_url}")
                response = requests.get(pdf_url, stream=True, timeout=30)
                response.raise_for_status()

                with open(filepath, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                downloaded_paths.append(filepath)
                logger.info(f"Successfully downloaded {filepath}")

            except Exception as e:
                logger.error(f"Error downloading PDF: {e}")

        return downloaded_paths

    def run(
        self,
        page_size: int = 10,
        pages: int = 1,
        download_samples: bool = False,
        sample_limit: int = 1,
    ):
        """Run the fetcher."""
        all_reports = []

        # Fetch the specified number of pages
        for page in range(1, pages + 1):
            logger.info(f"Fetching page {page} of {pages}")
            reports = self.get_lpc_reports(page_size, page)

            if not reports:
                logger.info(f"No reports found on page {page}")
                break

            all_reports.extend(reports)
            logger.info(f"Found {len(reports)} reports on page {page}")

        # Extract PDF URLs
        pdf_info = self.extract_pdf_urls(all_reports)
        logger.info(f"Extracted {len(pdf_info)} PDF URLs")

        # Print a few examples
        for i, item in enumerate(pdf_info[:5]):
            logger.info(
                f"Example {i+1}: {item['id']} - {item['name']} - {item['pdf_url']}"
            )

        # Download sample PDFs if requested
        if download_samples and pdf_info:
            downloaded_paths = self.download_sample_pdf(pdf_info, limit=sample_limit)
            logger.info(f"Downloaded {len(downloaded_paths)} sample PDFs")

        # Create timestamp for unique filenames
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        # Ensure logs directory exists
        logs_dir = Path(__file__).resolve().parent.parent / "logs"
        ensure_directory_exists(logs_dir)

        # Define file paths
        landmark_reports_path = logs_dir / f"landmark_reports_{timestamp}.json"
        pdf_urls_path = logs_dir / f"pdf_urls_{timestamp}.json"

        # Save the results to JSON for inspection
        with open(landmark_reports_path, "w") as f:
            json.dump(all_reports, f, indent=2)

        with open(pdf_urls_path, "w") as f:
            json.dump(pdf_info, f, indent=2)

        logger.info(f"Results saved to {landmark_reports_path} and {pdf_urls_path}")

        return {"total_reports": len(all_reports), "reports_with_pdfs": len(pdf_info)}


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Fetch landmark reports and extract PDF URLs"
    )
    parser.add_argument(
        "--page-size", type=int, default=10, help="Number of reports per page"
    )
    parser.add_argument("--pages", type=int, default=1, help="Number of pages to fetch")
    parser.add_argument("--download", action="store_true", help="Download sample PDFs")
    parser.add_argument(
        "--samples", type=int, default=1, help="Number of sample PDFs to download"
    )
    parser.add_argument("--api-key", type=str, help="CoreDataStore API key (optional)")

    args = parser.parse_args()

    # Load API key from environment variable if not provided as argument
    api_key = args.api_key or os.environ.get("COREDATASTORE_API_KEY")

    fetcher = LandmarkReportFetcher(api_key)
    results = fetcher.run(
        page_size=args.page_size,
        pages=args.pages,
        download_samples=args.download,
        sample_limit=args.samples,
    )

    print("\nSummary:")
    print(f"Total reports fetched: {results['total_reports']}")
    print(f"Reports with PDF URLs: {results['reports_with_pdfs']}")


if __name__ == "__main__":
    main()

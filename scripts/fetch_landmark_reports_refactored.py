"""
Script to fetch landmark reports from the CoreDataStore API,
extract PDF URLs, and optionally download sample PDFs.

This is a local test script for the NYC Landmarks Vector Database project.
It uses Pydantic models for data validation and improved error handling.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, cast
from urllib.parse import urljoin

import requests

# Add the project root to the path so we can import nyc_landmarks modules
sys.path.append(str(Path(__file__).resolve().parent.parent))

from nyc_landmarks.models.landmark_models import (
    ApiError,
    LpcReportModel,
    LpcReportResponse,
    PdfInfo,
    ProcessingResult,
)
from nyc_landmarks.utils.logger import get_logger

# Configure logger for this script
logger = get_logger(name="fetch_landmark_reports")


class CoreDataStoreApiError(Exception):
    """Exception for CoreDataStore API errors."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class CoreDataStoreClient:
    """Improved CoreDataStore API client for landmark operations with Pydantic validation."""

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
        """Make a request to the CoreDataStore API with improved error handling."""
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

            # Handle error responses with more detail
            if response.status_code >= 400:
                error_detail = {}
                try:
                    error_detail = response.json()
                except (ValueError, KeyError):
                    pass

                raise CoreDataStoreApiError(
                    f"API error: {response.status_code} - {response.reason}",
                    status_code=response.status_code,
                    details=error_detail,
                )

            # Return JSON response if available
            if response.content:
                return response.json()
            return {}

        except requests.exceptions.RequestException as e:
            logger.error(f"API request error: {e}")
            raise CoreDataStoreApiError(f"Error making API request: {e}")


class LandmarkReportFetcher:
    """Class to fetch landmark reports and extract PDF URLs using Pydantic models."""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize with the CoreDataStore API client."""
        self.api_client = CoreDataStoreClient(api_key)

    def get_lpc_reports(
        self, page_size: int = 10, page: int = 1
    ) -> List[Dict[str, Any]]:
        """Get LPC reports with Pydantic validation."""
        try:
            # Make the direct API request
            response_data = self.api_client._make_request(
                "GET", f"/api/LpcReport/{page_size}/{page}"
            )

            # Validate the response with Pydantic
            response = LpcReportResponse(**response_data)

            # Return the validated results list
            return [report.dict() for report in response.results]

        except CoreDataStoreApiError as e:
            logger.error(f"CoreDataStore API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching LPC reports: {e}")
            return []

    def extract_pdf_urls(self, reports: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Extract PDF URLs and basic info from reports, with Pydantic validation."""
        pdf_info_list = []

        for report in reports:
            try:
                # Create a validated report model
                lpc_report = LpcReportModel(**report)

                # Only include reports with PDF URLs
                if lpc_report.pdfReportUrl:
                    pdf_info = PdfInfo(
                        id=lpc_report.lpNumber,
                        name=lpc_report.name,
                        pdf_url=lpc_report.pdfReportUrl,
                    )
                    pdf_info_list.append(pdf_info.dict())
            except Exception as e:
                logger.warning(
                    f"Error validating report {report.get('lpNumber', 'unknown')}: {e}"
                )
                continue

        return pdf_info_list

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
                # Validate with Pydantic model
                pdf_item = PdfInfo(**item)

                pdf_url = pdf_item.pdf_url
                landmark_id = pdf_item.id

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
    ) -> ProcessingResult:
        """Run the fetcher with Pydantic validation."""
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

        # Save the results to JSON for inspection
        with open("landmark_reports.json", "w") as f:
            json.dump(all_reports, f, indent=2)

        with open("pdf_urls.json", "w") as f:
            json.dump(pdf_info, f, indent=2)

        logger.info(f"Results saved to landmark_reports.json and pdf_urls.json")

        # Return results as a validated ProcessingResult
        result = ProcessingResult(
            total_reports=len(all_reports), reports_with_pdfs=len(pdf_info)
        )
        return result


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
    result = fetcher.run(
        page_size=args.page_size,
        pages=args.pages,
        download_samples=args.download,
        sample_limit=args.samples,
    )

    print("\nSummary:")
    print(f"Total reports fetched: {result.total_reports}")
    print(f"Reports with PDF URLs: {result.reports_with_pdfs}")


if __name__ == "__main__":
    main()

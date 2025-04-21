#!/usr/bin/env python
"""
Script to fetch all landmark reports from the CoreDataStore API using pagination.

This script demonstrates how to retrieve the complete dataset of NYC landmark reports
by automatically handling pagination. It uses both the original CoreDataStore API
client approach as well as the MCP server approach for comparison.
"""

import argparse
import datetime
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Add the project root to the path so we can import nyc_landmarks modules
sys.path.append(str(Path(__file__).resolve().parent.parent))

from nyc_landmarks.utils.logger import get_logger
from scripts.fetch_landmark_reports import LandmarkReportFetcher, ensure_directory_exists

# Configure logger for this script
logger = get_logger(name="fetch_all_landmark_reports")


def fetch_all_lpc_reports(
    client: Any,
    page_size: int = 50,
    max_pages: Optional[int] = None,
    filters: Optional[Dict[str, Any]] = None,
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Fetch all LPC reports using the MCP client.

    Args:
        client: MCP client instance
        page_size: Number of reports per page
        max_pages: Maximum number of pages to fetch (optional)
        filters: Optional filters to apply

    Returns:
        Tuple of (all_reports, total_count)
    """
    logger.info("Fetching all LPC reports using MCP client")

    # Prepare arguments for the MCP tool
    arguments = {"limit": page_size, "page": 1}

    # Add filters if provided
    if filters:
        arguments.update(filters)

    # Make the first request to get total count
    logger.info(f"Fetching first page with page_size={page_size}")
    response = client.use_mcp_tool(
        server_name="coredatastore-swagger-mcp",
        tool_name="GetLpcReports",
        arguments=arguments,
    )

    if not response or "results" not in response or "total" not in response:
        logger.error("Invalid response from MCP API")
        return [], 0

    total_count = response["total"]
    total_pages = (total_count + page_size - 1) // page_size

    if max_pages:
        total_pages = min(total_pages, max_pages)
        logger.info(f"Limiting to {max_pages} pages")

    logger.info(f"Total reports: {total_count}, Total pages: {total_pages}")

    # Initialize collection with first page results
    all_reports: List[Dict[str, Any]] = []
    if isinstance(response, Dict) and "results" in response:
        all_reports = list(response["results"])

    # Fetch remaining pages
    for page in range(2, total_pages + 1):
        logger.info(f"Fetching page {page} of {total_pages}")
        arguments["page"] = page

        # Make the MCP request
        page_response = client.use_mcp_tool(
            server_name="coredatastore-swagger-mcp",
            tool_name="GetLpcReports",
            arguments=arguments,
        )

        if page_response and "results" in page_response:
            all_reports.extend(page_response["results"])
            logger.info(f"Fetched {len(all_reports)} of {total_count} reports")
        else:
            logger.warning(f"Failed to fetch page {page}")

    return all_reports, total_count


def fetch_with_direct_client(
    api_key: Optional[str] = None,
    page_size: int = 50,
    max_pages: Optional[int] = None,
    output_dir: str = "logs",
) -> Dict[str, Union[str, int, float]]:
    """
    Fetch all landmark reports using the direct API client.

    Args:
        api_key: CoreDataStore API key (optional)
        page_size: Number of reports per page
        max_pages: Maximum number of pages to fetch (for testing)
        output_dir: Directory to store output files

    Returns:
        Dict with result statistics
    """
    logger.info("Fetching all landmark reports using direct client method")

    # Start timing
    start_time = time.time()

    # Create fetcher instance
    fetcher = LandmarkReportFetcher(api_key)

    # Get first page to determine total count
    logger.info(f"Fetching first page with page_size={page_size}")
    response = fetcher.api_client._make_request("GET", f"/api/LpcReport/{page_size}/1")

    if (
        not response
        or not isinstance(response, Dict)
        or "results" not in response
        or "total" not in response
    ):
        logger.error("Invalid response from API")
        return {
            "error": "Invalid API response",
            "reports_fetched": 0,
            "total_reports": 0,
            "reports_with_pdfs": 0,
            "elapsed_time": 0.0,
        }

    total_count = response["total"]
    total_pages = (total_count + page_size - 1) // page_size

    if max_pages:
        total_pages = min(total_pages, max_pages)
        logger.info(f"Limiting to {max_pages} pages")

    logger.info(f"Total reports: {total_count}, Total pages: {total_pages}")

    # Initialize collection
    all_reports: List[Dict[str, Any]] = []
    if (
        isinstance(response, Dict)
        and "results" in response
        and isinstance(response["results"], list)
    ):
        all_reports.extend(response["results"])

    # Fetch remaining pages
    for page in range(2, total_pages + 1):
        logger.info(f"Fetching page {page} of {total_pages}")
        reports = fetcher.get_lpc_reports(page_size=page_size, page=page)
        all_reports.extend(reports)
        logger.info(f"Fetched {len(all_reports)} of {total_count} reports")

    # Calculate time taken
    elapsed_time = time.time() - start_time
    logger.info(f"Fetched {len(all_reports)} reports in {elapsed_time:.2f} seconds")

    # Extract PDF URLs
    pdf_info = fetcher.extract_pdf_urls(all_reports)
    logger.info(f"Extracted {len(pdf_info)} PDF URLs")

    # Create timestamp for unique filenames
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    # Ensure output directory exists
    ensure_directory_exists(output_dir)

    # Define file paths
    all_reports_path = Path(output_dir) / f"all_landmark_reports_{timestamp}.json"
    pdf_urls_path = Path(output_dir) / f"all_pdf_urls_{timestamp}.json"

    # Save the results to JSON
    with open(all_reports_path, "w") as f:
        json.dump(all_reports, f, indent=2)

    with open(pdf_urls_path, "w") as f:
        json.dump(pdf_info, f, indent=2)

    logger.info(f"Results saved to {all_reports_path} and {pdf_urls_path}")

    return {
        "total_reports": total_count,
        "reports_fetched": len(all_reports),
        "reports_with_pdfs": len(pdf_info),
        "elapsed_time": elapsed_time,
    }


def fetch_with_mcp_client(
    page_size: int = 50,
    max_pages: Optional[int] = None,
    filters: Optional[Dict[str, Any]] = None,
    output_dir: str = "logs",
) -> Dict[str, Union[str, int, float]]:
    """
    Fetch all landmark reports using the MCP client.

    Args:
        page_size: Number of reports per page
        max_pages: Maximum number of pages to fetch (for testing)
        filters: Optional filters to apply (Borough, ObjectType, etc.)
        output_dir: Directory to store output files

    Returns:
        Dict with result statistics
    """
    logger.info("Fetching all landmark reports using MCP client method")

    try:
        # Try to import the MCP client
        from claude_dev import use_mcp_tool  # type: ignore

        # Create a simple wrapper class to match our expected interface
        class McpClient:
            def use_mcp_tool(
                self, server_name: str, tool_name: str, arguments: Dict[str, Any]
            ) -> Dict[str, Any]:
                result = use_mcp_tool(
                    server_name=server_name, tool_name=tool_name, arguments=arguments
                )
                if isinstance(result, Dict):
                    return result
                return {}

        # Start timing
        start_time = time.time()

        # Create client and fetch all reports
        client = McpClient()
        all_reports, total_count = fetch_all_lpc_reports(
            client, page_size=page_size, max_pages=max_pages, filters=filters
        )

        # Calculate time taken
        elapsed_time = time.time() - start_time
        logger.info(f"Fetched {len(all_reports)} reports in {elapsed_time:.2f} seconds")

        # Create timestamp for unique filenames
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        # Ensure output directory exists
        ensure_directory_exists(output_dir)

        # Define file path
        all_reports_path = (
            Path(output_dir) / f"all_landmark_reports_mcp_{timestamp}.json"
        )

        # Save the results to JSON
        with open(all_reports_path, "w") as f:
            json.dump(all_reports, f, indent=2)

        logger.info(f"Results saved to {all_reports_path}")

        # Extract PDF URLs
        pdf_info: List[Dict[str, str]] = []
        for report in all_reports:
            if (
                isinstance(report, Dict)
                and "pdfReportUrl" in report
                and report["pdfReportUrl"]
            ):
                # Cast to string to fix the __getitem__ error
                if isinstance(report, Dict) and isinstance(
                    report.get("pdfReportUrl"), str
                ):
                    pdf_url = report.get("pdfReportUrl", "")
                    pdf_info.append(
                        {
                            "id": report.get("lpNumber", ""),
                            "name": report.get("name", ""),
                            "pdf_url": pdf_url,
                        }
                    )

        # Save PDF URLs to JSON
        pdf_urls_path = Path(output_dir) / f"all_pdf_urls_mcp_{timestamp}.json"
        with open(pdf_urls_path, "w") as f:
            json.dump(pdf_info, f, indent=2)

        logger.info(f"Extracted {len(pdf_info)} PDF URLs, saved to {pdf_urls_path}")

        return {
            "total_reports": total_count,
            "reports_fetched": len(all_reports),
            "reports_with_pdfs": len(pdf_info),
            "elapsed_time": elapsed_time,
        }

    except ImportError:
        logger.error("MCP client not available")
        return {
            "error": "MCP client not available",
            "reports_fetched": 0,
            "total_reports": 0,
            "reports_with_pdfs": 0,
            "elapsed_time": 0.0,
        }


def main() -> None:
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Fetch all landmark reports using pagination"
    )
    parser.add_argument(
        "--page-size", type=int, default=50, help="Number of reports per page"
    )
    parser.add_argument(
        "--max-pages", type=int, help="Maximum number of pages to fetch (for testing)"
    )
    parser.add_argument("--api-key", type=str, help="CoreDataStore API key (optional)")
    parser.add_argument(
        "--output-dir", type=str, default="logs", help="Directory to store output files"
    )
    parser.add_argument(
        "--method",
        choices=["direct", "mcp", "both"],
        default="both",
        help="Method to use for fetching (direct API client, MCP client, or both)",
    )
    parser.add_argument(
        "--borough",
        type=str,
        help="Filter by borough (e.g., Manhattan, Brooklyn)",
    )
    parser.add_argument(
        "--object-type",
        type=str,
        help="Filter by object type (e.g., 'Individual Landmark')",
    )

    args = parser.parse_args()

    # Load API key from environment variable if not provided as argument
    api_key = args.api_key or os.environ.get("COREDATASTORE_API_KEY")

    # Prepare filters
    filters = {}
    if args.borough:
        filters["Borough"] = args.borough
    if args.object_type:
        filters["ObjectType"] = args.object_type

    # Run appropriate method(s)
    direct_results = None
    mcp_results = None

    if args.method in ["direct", "both"]:
        direct_results = fetch_with_direct_client(
            api_key=api_key,
            page_size=args.page_size,
            max_pages=args.max_pages,
            output_dir=args.output_dir,
        )

    if args.method in ["mcp", "both"]:
        mcp_results = fetch_with_mcp_client(
            page_size=args.page_size,
            max_pages=args.max_pages,
            filters=filters,
            output_dir=args.output_dir,
        )

    # Print summary
    print("\nSummary:")

    if direct_results:
        print("\nDirect API Client:")
        if "error" in direct_results:
            print(f"  Error: {direct_results['error']}")
        else:
            print(f"  Total reports available: {direct_results['total_reports']}")
            print(f"  Reports fetched: {direct_results['reports_fetched']}")
            print(f"  Reports with PDF URLs: {direct_results['reports_with_pdfs']}")
            print(f"  Time taken: {direct_results['elapsed_time']:.2f} seconds")

    if mcp_results:
        print("\nMCP Client:")
        if "error" in mcp_results:
            print(f"  Error: {mcp_results['error']}")
        else:
            print(f"  Total reports available: {mcp_results['total_reports']}")
            print(f"  Reports fetched: {mcp_results['reports_fetched']}")
            print(f"  Reports with PDF URLs: {mcp_results['reports_with_pdfs']}")
            print(f"  Time taken: {mcp_results['elapsed_time']:.2f} seconds")


if __name__ == "__main__":
    main()

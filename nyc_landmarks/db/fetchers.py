"""
Utility functions for fetching data from CoreDataStore API with pagination support.
"""

from typing import Any, Dict, List, Optional, Tuple, Union

from nyc_landmarks.utils.logger import get_logger

# Configure logger
logger = get_logger(name="fetchers")


def fetch_all_lpc_reports(
    mcp_client,
    page_size: int = 50,
    max_pages: Optional[int] = None,
    filters: Optional[Dict[str, Any]] = None
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Fetch all LPC reports using pagination.

    Args:
        mcp_client: The MCP client object (claude_dev or equivalent)
        page_size: Number of reports to fetch per page
        max_pages: Optional maximum number of pages to fetch (for testing)
        filters: Optional filters to apply to the query (Borough, ObjectType, etc.)

    Returns:
        Tuple containing:
        - List of all landmark reports
        - Total count of reports available
    """
    all_reports = []

    # Initialize arguments
    args = {
        "limit": page_size,
        "page": 1
    }

    # Add any filters
    if filters:
        args.update(filters)

    # Fetch first page to get total count
    try:
        response = mcp_client.use_mcp_tool(
            server_name="coredatastore-swagger-mcp",
            tool_name="GetLpcReports",
            arguments=args
        )

        if not response or "total" not in response:
            logger.error("Failed to fetch first page of reports or missing total count")
            return [], 0

        # Extract results and metadata
        all_reports.extend(response.get("results", []))
        total_count = response.get("total", 0)

        if total_count == 0:
            logger.warning("No reports found")
            return [], 0

        # Calculate total pages
        total_pages = (total_count + page_size - 1) // page_size

        # Apply max_pages limit if specified
        if max_pages is not None:
            total_pages = min(total_pages, max_pages)

        # Fetch remaining pages
        for page in range(2, total_pages + 1):
            logger.info(f"Fetching page {page} of {total_pages}")

            args["page"] = page
            page_response = mcp_client.use_mcp_tool(
                server_name="coredatastore-swagger-mcp",
                tool_name="GetLpcReports",
                arguments=args
            )

            if not page_response or "results" not in page_response:
                logger.error(f"Failed to fetch page {page}")
                continue

            page_results = page_response.get("results", [])
            all_reports.extend(page_results)

            # Log progress
            logger.info(f"Fetched {len(all_reports)} of {total_count} reports ({len(all_reports) / total_count:.1%})")

        return all_reports, total_count

    except Exception as e:
        logger.error(f"Error fetching all LPC reports: {e}")
        return [], 0


def fetch_all_landmarks_for_report(
    mcp_client,
    lpc_number: str,
    page_size: int = 50,
    max_pages: Optional[int] = None
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Fetch all buildings associated with a landmark report.

    Args:
        mcp_client: The MCP client object (claude_dev or equivalent)
        lpc_number: The LPC number for the landmark report
        page_size: Number of records to fetch per page
        max_pages: Optional maximum number of pages to fetch (for testing)

    Returns:
        Tuple containing:
        - List of all buildings for the landmark
        - Total count of buildings available
    """
    all_buildings = []

    # Initialize arguments
    args = {
        "limit": page_size,
        "page": 1,
        "LpcNumber": lpc_number
    }

    # Fetch first page to get total count
    try:
        response = mcp_client.use_mcp_tool(
            server_name="coredatastore-swagger-mcp",
            tool_name="GetLandmarks",
            arguments=args
        )

        if not response or "total" not in response:
            logger.error(f"Failed to fetch buildings for landmark {lpc_number}")
            return [], 0

        # Extract results and metadata
        all_buildings.extend(response.get("results", []))
        total_count = response.get("total", 0)

        if total_count == 0:
            logger.info(f"No buildings found for landmark {lpc_number}")
            return [], 0

        # Calculate total pages
        total_pages = (total_count + page_size - 1) // page_size

        # Apply max_pages limit if specified
        if max_pages is not None:
            total_pages = min(total_pages, max_pages)

        # Fetch remaining pages
        for page in range(2, total_pages + 1):
            logger.info(f"Fetching page {page} of {total_pages} for landmark {lpc_number}")

            args["page"] = page
            page_response = mcp_client.use_mcp_tool(
                server_name="coredatastore-swagger-mcp",
                tool_name="GetLandmarks",
                arguments=args
            )

            if not page_response or "results" not in page_response:
                logger.error(f"Failed to fetch page {page} for landmark {lpc_number}")
                continue

            page_results = page_response.get("results", [])
            all_buildings.extend(page_results)

        return all_buildings, total_count

    except Exception as e:
        logger.error(f"Error fetching buildings for landmark {lpc_number}: {e}")
        return [], 0

"""
Module for fetching data from CoreDataStore using MCP.

This module provides functions to fetch LPC reports and landmark data
from the CoreDataStore API using MCP tools with pagination support.
"""

from typing import Any, Dict, List, Optional, Tuple, Union


def fetch_all_lpc_reports(
    mcp_client: Any,
    page_size: int = 10,
    max_pages: Optional[int] = None,
    filters: Optional[Dict[str, Any]] = None,
    fields_list: Optional[List[str]] = None,
    sort_column: Optional[str] = None,
    sort_order: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Fetch all LPC reports from CoreDataStore API using MCP with pagination.

    Args:
        mcp_client: MCP client object with use_mcp_tool method
        page_size: Number of records per page
        max_pages: Maximum number of pages to fetch (None = fetch all)
        filters: Dictionary of filter parameters to apply
        fields_list: List of fields to include in the response
        sort_column: Column to sort by
        sort_order: Sort direction ("asc" or "desc")

    Returns:
        Tuple of (list of report dictionaries, total count)
    """
    all_reports = []
    total_count = 0
    current_page = 1

    # Prepare base arguments
    args = {
        "limit": page_size,
        "page": current_page,
    }

    # Add optional filters
    if filters:
        args.update(filters)

    # Add optional fields list
    if fields_list:
        args["FieldsList"] = fields_list

    # Add optional sort parameters
    if sort_column:
        args["SortColumn"] = sort_column
    if sort_order:
        args["SortOrder"] = sort_order

    # Make initial request to get total count and first page
    response = mcp_client.use_mcp_tool(
        server_name="coredatastore-swagger-mcp",
        tool_name="GetLpcReports",
        arguments=args
    )

    if not response or "total" not in response or "results" not in response:
        return [], 0

    total_count = response["total"]
    all_reports.extend(response["results"])

    # Calculate total pages
    total_pages = (total_count + page_size - 1) // page_size

    # Limit to max_pages if specified
    if max_pages is not None:
        total_pages = min(total_pages, max_pages)

    # Fetch remaining pages
    for page in range(2, total_pages + 1):
        args["page"] = page
        response = mcp_client.use_mcp_tool(
            server_name="coredatastore-swagger-mcp",
            tool_name="GetLpcReports",
            arguments=args
        )

        if not response or "results" not in response:
            break

        all_reports.extend(response["results"])

    return all_reports, total_count


def fetch_all_landmarks_for_report(
    mcp_client: Any,
    lpc_number: str,
    page_size: int = 10,
    max_pages: Optional[int] = None,
    fields_list: Optional[List[str]] = None,
    sort_column: Optional[str] = None,
    sort_order: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Fetch all buildings/landmarks for a specific LPC report.

    Args:
        mcp_client: MCP client object with use_mcp_tool method
        lpc_number: LPC report number (e.g., "LP-00123")
        page_size: Number of records per page
        max_pages: Maximum number of pages to fetch (None = fetch all)
        fields_list: List of fields to include in the response
        sort_column: Column to sort by
        sort_order: Sort direction ("asc" or "desc")

    Returns:
        Tuple of (list of building dictionaries, total count)
    """
    all_buildings = []
    total_count = 0
    current_page = 1

    # Prepare base arguments
    args = {
        "limit": page_size,
        "page": current_page,
        "LpcNumber": lpc_number
    }

    # Add optional fields list
    if fields_list:
        args["FieldsList"] = fields_list

    # Add optional sort parameters
    if sort_column:
        args["SortColumn"] = sort_column
    if sort_order:
        args["SortOrder"] = sort_order

    # Make initial request to get total count and first page
    response = mcp_client.use_mcp_tool(
        server_name="coredatastore-swagger-mcp",
        tool_name="GetLandmarks",
        arguments=args
    )

    if not response or "total" not in response or "results" not in response:
        return [], 0

    total_count = response["total"]
    all_buildings.extend(response["results"])

    # Calculate total pages
    total_pages = (total_count + page_size - 1) // page_size

    # Limit to max_pages if specified
    if max_pages is not None:
        total_pages = min(total_pages, max_pages)

    # Fetch remaining pages
    for page in range(2, total_pages + 1):
        args["page"] = page
        response = mcp_client.use_mcp_tool(
            server_name="coredatastore-swagger-mcp",
            tool_name="GetLandmarks",
            arguments=args
        )

        if not response or "results" not in response:
            break

        all_buildings.extend(response["results"])

    return all_buildings, total_count

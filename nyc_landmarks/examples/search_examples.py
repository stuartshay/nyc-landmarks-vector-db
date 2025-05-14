"""
Search examples for NYC Landmarks Vector Database.

This module contains example queries that can be used in the API documentation
and for testing purposes.
"""

from typing import Any, Dict


def get_text_query_examples() -> Dict[str, Dict[str, Any]]:
    """
    Get examples for the text query endpoint.

    Returns:
        Dictionary of example queries with their metadata
    """
    return {
        "empire_state_building": {
            "summary": "Empire State Building History (PDF)",
            "description": "Search for information about the Empire State Building's history in PDF documents",
            "value": {
                "query": "What is the history of the Empire State Building?",
                "landmark_id": None,
                "source_type": "pdf",
                "top_k": 5,
            },
        },
        "statue_of_liberty_designation": {
            "summary": "Statue of Liberty Designation (Wikipedia)",
            "description": "Search for information about when the Statue of Liberty was designated as a landmark",
            "value": {
                "query": "When was the Statue of Liberty designated as a landmark?",
                "landmark_id": None,
                "source_type": "wikipedia",
                "top_k": 5,
            },
        },
        "brooklyn_bridge_architecture": {
            "summary": "Brooklyn Bridge Architecture (All Sources)",
            "description": "Search for architectural information about the Brooklyn Bridge from all sources",
            "value": {
                "query": "What is the architectural style of the Brooklyn Bridge?",
                "landmark_id": None,
                "source_type": None,
                "top_k": 10,
            },
        },
        "grand_central_history": {
            "summary": "Grand Central Terminal History",
            "description": "Search for the history and significance of Grand Central Terminal",
            "value": {
                "query": "What is the historical significance of Grand Central Terminal?",
                "landmark_id": None,
                "source_type": "pdf",
                "top_k": 5,
            },
        },
        "central_park_landmarks": {
            "summary": "Central Park Landmarks",
            "description": "Search for information about landmarks in Central Park",
            "value": {
                "query": "What landmarks can be found in Central Park?",
                "landmark_id": None,
                "source_type": "wikipedia",
                "top_k": 8,
            },
        },
        "woolworth_building": {
            "summary": "Woolworth Building Architecture",
            "description": "Search for information about the Woolworth Building's Gothic architecture",
            "value": {
                "query": "What are the Gothic architectural features of the Woolworth Building?",
                "landmark_id": None,
                "source_type": "pdf",
                "top_k": 8,
            },
        },
    }


def get_landmark_filter_examples() -> Dict[str, Dict[str, Any]]:
    """
    Get examples for landmark-specific queries.
    These examples demonstrate filtering by landmark_id.

    Returns:
        Dictionary of example queries with landmark filters
    """
    return {
        "specific_landmark_query": {
            "summary": "Query Specific Landmark",
            "description": "Search for information about a specific landmark using its ID",
            "value": {
                "query": "What are the architectural features?",
                "landmark_id": "LP-00001",  # Example landmark ID
                "source_type": None,
                "top_k": 5,
            },
        }
    }

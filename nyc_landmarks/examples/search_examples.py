"""
Search examples for NYC Landmarks Vector Database.

This module contains example queries that can be used in the API documentation
and for testing purposes. All examples use real NYC landmark data and valid
landmark IDs from the NYC Landmarks Preservation Commission database.
"""

from typing import Any, Dict, List


def get_text_query_examples() -> Dict[str, Dict[str, Any]]:
    """
    Get examples for the text query endpoint using real NYC landmark data.

    Returns:
        Dictionary of example queries with their metadata based on actual landmark IDs
    """
    return {
        "wyckoff_house_history": {
            "summary": "Pieter Claesen Wyckoff House History (Wikipedia)",
            "description": "Search for the history of NYC's oldest structure, the Wyckoff House (LP-00001)",
            "value": {
                "query": "What is the history of the Pieter Claesen Wyckoff House?",
                "landmark_id": None,
                "source_type": "wikipedia",
                "top_k": 5,
            },
        },
        "federal_hall_history": {
            "summary": "Federal Hall National Memorial (PDF)",
            "description": "Search for information about Federal Hall where Washington was inaugurated",
            "value": {
                "query": "What is the historical significance of Federal Hall National Memorial?",
                "landmark_id": None,
                "source_type": "pdf",
                "top_k": 5,
            },
        },
        "brooklyn_bridge_engineering": {
            "summary": "Brooklyn Bridge Engineering (Wikipedia)",
            "description": "Search for engineering and construction details of the Brooklyn Bridge",
            "value": {
                "query": "How was the Brooklyn Bridge engineered and constructed?",
                "landmark_id": None,
                "source_type": "wikipedia",
                "top_k": 6,
            },
        },
        "empire_state_building_architecture": {
            "summary": "Empire State Building Architecture (All Sources)",
            "description": "Search for architectural information about the Empire State Building from all sources",
            "value": {
                "query": "What is the Art Deco architectural style of the Empire State Building?",
                "landmark_id": None,
                "source_type": None,
                "top_k": 8,
            },
        },
        "grand_central_beaux_arts": {
            "summary": "Grand Central Terminal Beaux-Arts Style",
            "description": "Search for Beaux-Arts architectural features of Grand Central Terminal",
            "value": {
                "query": "What are the Beaux-Arts architectural features of Grand Central Terminal?",
                "landmark_id": None,
                "source_type": "pdf",
                "top_k": 6,
            },
        },
        "statue_of_liberty_designation": {
            "summary": "Statue of Liberty National Monument Status",
            "description": "Search for designation history of the Statue of Liberty",
            "value": {
                "query": "When and why was the Statue of Liberty designated as a National Monument?",
                "landmark_id": None,
                "source_type": "wikipedia",
                "top_k": 7,
            },
        },
        "brooklyn_heights_historic_district": {
            "summary": "Brooklyn Heights Historic District",
            "description": "Search for information about Brooklyn Heights Historic District buildings",
            "value": {
                "query": "What buildings are included in the Brooklyn Heights Historic District?",
                "landmark_id": None,
                "source_type": "pdf",
                "top_k": 10,
            },
        },
        "central_park_conservancy": {
            "summary": "Central Park Landmarks and Features",
            "description": "Search for designated landmarks within Central Park",
            "value": {
                "query": "What are the designated landmarks and historic features in Central Park?",
                "landmark_id": None,
                "source_type": "wikipedia",
                "top_k": 8,
            },
        },
    }


def get_landmark_filter_examples() -> Dict[str, Dict[str, Any]]:
    """
    Get examples for landmark-specific queries using real NYC landmark IDs.
    These examples demonstrate filtering by landmark_id with actual LPC numbers.

    Returns:
        Dictionary of example queries with real landmark filters
    """
    return {
        "wyckoff_house_specific": {
            "summary": "Pieter Claesen Wyckoff House (LP-00001)",
            "description": "Search for specific information about NYC's oldest structure using its landmark ID",
            "value": {
                "query": "What are the Dutch Colonial architectural features of this landmark?",
                "landmark_id": "LP-00001",  # Pieter Claesen Wyckoff House - Brooklyn
                "source_type": "pdf",
                "top_k": 5,
            },
        },
        "federal_hall_specific": {
            "summary": "Federal Hall National Memorial (LP-00009)",
            "description": "Search for information about the site of Washington's presidential inauguration",
            "value": {
                "query": "What happened at this landmark during the founding of America?",
                "landmark_id": "LP-00009",  # Federal Hall National Memorial - Manhattan
                "source_type": "wikipedia",
                "top_k": 6,
            },
        },
        "harlem_ymca_specific": {
            "summary": "Harlem YMCA Building (LP-01973)",
            "description": "Search for architectural and historical details of the Harlem YMCA",
            "value": {
                "query": "What is the architectural significance and community role of this landmark?",
                "landmark_id": "LP-01973",  # Harlem YMCA - Manhattan
                "source_type": "pdf",
                "top_k": 7,
            },
        },
        "brooklyn_heights_building": {
            "summary": "Brooklyn Heights Historic District Building",
            "description": "Search for information about a specific building in Brooklyn Heights Historic District",
            "value": {
                "query": "What is the architectural style and historical context of this building?",
                "landmark_id": "LP-00099",  # Brooklyn Heights Historic District
                "source_type": None,  # Search all sources
                "top_k": 8,
            },
        },
        "designation_history_specific": {
            "summary": "Early Landmark Designation History",
            "description": "Search for designation process and criteria for early NYC landmarks",
            "value": {
                "query": "How was this landmark designated and what were the preservation criteria?",
                "landmark_id": "LP-00001",  # Using Wyckoff House as example of early designation
                "source_type": "pdf",
                "top_k": 6,
            },
        },
        "architectural_analysis_specific": {
            "summary": "Federal Hall Architectural Analysis",
            "description": "Search for detailed architectural analysis of Greek Revival elements",
            "value": {
                "query": "What are the specific Greek Revival architectural elements of this landmark?",
                "landmark_id": "LP-00009",  # Federal Hall - good example of Greek Revival
                "source_type": "pdf",
                "top_k": 5,
            },
        },
        "community_impact_specific": {
            "summary": "Harlem YMCA Community Impact",
            "description": "Search for the social and cultural impact of the Harlem YMCA on the community",
            "value": {
                "query": "What was the role of this landmark in the Harlem Renaissance and community development?",
                "landmark_id": "LP-01973",  # Harlem YMCA - significant cultural institution
                "source_type": "wikipedia",
                "top_k": 8,
            },
        },
        "preservation_challenges": {
            "summary": "Historic Preservation Challenges",
            "description": "Search for preservation challenges and restoration efforts for old landmarks",
            "value": {
                "query": "What preservation challenges and restoration work has this landmark faced?",
                "landmark_id": "LP-00001",  # Wyckoff House - oldest structure with preservation challenges
                "source_type": None,  # All sources for comprehensive information
                "top_k": 10,
            },
        },
    }


def get_advanced_query_examples() -> Dict[str, Dict[str, Any]]:
    """
    Get examples of advanced query patterns for API documentation.

    Returns:
        Dictionary of advanced query examples demonstrating complex search patterns
    """
    return {
        "multi_source_comparison": {
            "summary": "Multi-Source Historical Research",
            "description": "Compare information about a landmark across different source types",
            "value": {
                "query": "Compare the historical accounts of the Brooklyn Bridge construction",
                "landmark_id": None,
                "source_type": None,  # Search all sources for comparison
                "top_k": 15,
            },
        },
        "architectural_style_search": {
            "summary": "Architectural Style Pattern Search",
            "description": "Search for landmarks with specific architectural characteristics",
            "value": {
                "query": "Find landmarks with Greek Revival architectural elements and columns",
                "landmark_id": None,
                "source_type": "pdf",
                "top_k": 12,
            },
        },
        "preservation_methodology": {
            "summary": "Historic Preservation Methodology",
            "description": "Research preservation techniques and challenges for historic structures",
            "value": {
                "query": "What preservation methods are used for 17th and 18th century wooden structures?",
                "landmark_id": None,
                "source_type": "pdf",
                "top_k": 10,
            },
        },
        "cultural_significance_research": {
            "summary": "Cultural and Social Impact Research",
            "description": "Explore the cultural significance and community impact of landmarks",
            "value": {
                "query": "How did these landmarks contribute to the Harlem Renaissance and cultural movement?",
                "landmark_id": None,
                "source_type": "wikipedia",
                "top_k": 8,
            },
        },
        "construction_techniques": {
            "summary": "Historical Construction Techniques",
            "description": "Research construction methods and materials used in historic buildings",
            "value": {
                "query": "What construction techniques and materials were used in 19th century Gothic Revival buildings?",
                "landmark_id": None,
                "source_type": "pdf",
                "top_k": 10,
            },
        },
        "urban_development_impact": {
            "summary": "Urban Development and Landmarks",
            "description": "Study the relationship between landmarks and urban development patterns",
            "value": {
                "query": "How did historic landmarks influence neighborhood development and city planning?",
                "landmark_id": None,
                "source_type": None,
                "top_k": 12,
            },
        },
    }


def get_borough_specific_examples() -> Dict[str, Dict[str, Any]]:
    """
    Get examples organized by NYC boroughs for geographic searches.

    Returns:
        Dictionary of borough-specific landmark examples
    """
    return {
        "manhattan_financial_district": {
            "summary": "Manhattan Financial District Landmarks",
            "description": "Historic landmarks in Lower Manhattan's Financial District",
            "value": {
                "query": "What are the historic landmarks in Manhattan's Financial District?",
                "landmark_id": None,
                "source_type": "wikipedia",
                "top_k": 8,
            },
        },
        "brooklyn_historic_districts": {
            "summary": "Brooklyn Historic Districts",
            "description": "Explore historic districts and neighborhoods in Brooklyn",
            "value": {
                "query": "What historic districts and landmark neighborhoods exist in Brooklyn?",
                "landmark_id": None,
                "source_type": "pdf",
                "top_k": 10,
            },
        },
        "manhattan_harlem_culture": {
            "summary": "Harlem Cultural Landmarks",
            "description": "Cultural and historic landmarks in Harlem, Manhattan",
            "value": {
                "query": "What are the significant cultural landmarks in Harlem?",
                "landmark_id": None,
                "source_type": "wikipedia",
                "top_k": 9,
            },
        },
        "queens_diverse_heritage": {
            "summary": "Queens Cultural Heritage Sites",
            "description": "Diverse cultural and historic sites across Queens",
            "value": {
                "query": "What landmarks in Queens represent the borough's diverse cultural heritage?",
                "landmark_id": None,
                "source_type": None,
                "top_k": 8,
            },
        },
        "bronx_historic_sites": {
            "summary": "Bronx Historic Landmarks",
            "description": "Historic landmarks and sites throughout the Bronx",
            "value": {
                "query": "What are the historic landmarks and significant sites in the Bronx?",
                "landmark_id": None,
                "source_type": "pdf",
                "top_k": 7,
            },
        },
        "staten_island_colonial": {
            "summary": "Staten Island Colonial History",
            "description": "Colonial and early American landmarks on Staten Island",
            "value": {
                "query": "What colonial and early American landmarks exist on Staten Island?",
                "landmark_id": None,
                "source_type": "wikipedia",
                "top_k": 6,
            },
        },
    }


def validate_query_example(example: Dict[str, Any]) -> bool:
    """
    Validate that a query example has all required fields.

    Args:
        example: Query example dictionary to validate

    Returns:
        True if example is valid, False otherwise
    """
    required_fields = ["query", "landmark_id", "source_type", "top_k"]

    if "value" not in example:
        return False

    value = example["value"]
    return all(field in value for field in required_fields)


def get_all_examples() -> Dict[str, Dict[str, Dict[str, Any]]]:
    """
    Get all example categories in a single comprehensive dictionary.

    Returns:
        Dictionary containing all example categories
    """
    return {
        "text_queries": get_text_query_examples(),
        "landmark_specific": get_landmark_filter_examples(),
        "advanced_patterns": get_advanced_query_examples(),
        "borough_focused": get_borough_specific_examples(),
    }


def get_example_landmark_ids() -> List[str]:
    """
    Get a list of all landmark IDs used in examples.

    Returns:
        List of landmark ID strings used across all examples
    """
    landmark_ids = set()

    for examples in get_landmark_filter_examples().values():
        landmark_id = examples["value"]["landmark_id"]
        if landmark_id:
            landmark_ids.add(landmark_id)

    return sorted(landmark_ids)


def get_example_queries_by_source_type(source_type: str) -> List[Dict[str, Any]]:
    """
    Filter examples by source type.

    Args:
        source_type: Source type to filter by ("wikipedia", "pdf", or None for all)

    Returns:
        List of examples matching the source type
    """
    matching_examples = []
    all_examples = get_all_examples()

    for category in all_examples.values():
        for example in category.values():
            if example["value"]["source_type"] == source_type:
                matching_examples.append(example)

    return matching_examples

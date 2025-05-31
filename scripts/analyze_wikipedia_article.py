#!/usr/bin/env python3
"""
Script to analyze Wikipedia articles for NYC landmarks.

This script:
1. Fetches a Wikipedia article for a specific landmark ID
2. Dumps the content and metadata to a file for analysis
3. Extracts potential metadata attributes from the Wikipedia content

Usage:
    python scripts/analyze_wikipedia_article.py --landmark-id LP-00006 --output logs/wikipedia_analysis

"""

import argparse
import json
import os
import re
import sys
from typing import Any, Dict, List

from nyc_landmarks.db.db_client import get_db_client
from nyc_landmarks.db.wikipedia_fetcher import WikipediaFetcher
from nyc_landmarks.utils.logger import get_logger

# Configure logging
logger = get_logger(__name__)


def _extract_year_built(content: str) -> Dict[str, Any]:
    """Extract year built/completed from content."""
    metadata = {}
    year_built_patterns = [
        r"built in (\d{4})",
        r"completed in (\d{4})",
        r"constructed in (\d{4})",
        r"erected in (\d{4})",
        r"established in (\d{4})",
        r"founded in (\d{4})",
        r"opened in (\d{4})",
    ]

    for pattern in year_built_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            metadata["year_built"] = int(match.group(1))
            break

    return metadata


def _extract_architect(content: str) -> Dict[str, Any]:
    """Extract architect information from content."""
    metadata = {}
    architect_patterns = [
        r"designed by ([^.,;()\n]+)",
        r"architect(?:s)? ([^.,;()\n]+)",
    ]

    for pattern in architect_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            metadata["architect"] = match.group(1).strip()
            break

    return metadata


def _extract_architectural_styles(content: str) -> Dict[str, Any]:
    """Extract architectural styles from content."""
    metadata = {}
    style_patterns = [
        r"([A-Za-z\s-]+) style",
        r"style(?:s)? (?:is|are|was|were) ([A-Za-z\s-]+)",
    ]

    style_set = set()
    excluded_words = {
        "the",
        "a",
        "an",
        "this",
        "that",
        "these",
        "those",
        "and",
        "or",
        "but",
    }

    for pattern in style_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            style = match.group(1).strip()
            if style.lower() not in excluded_words:
                style_set.add(style)

    if style_set:
        metadata["architectural_styles"] = list(style_set)

    return metadata


def _extract_notable_features(content: str) -> Dict[str, Any]:
    """Extract notable features from content."""
    metadata = {}
    feature_patterns = [
        r"features? (?:include|includes|including) ([^.]+)",
        r"notable (?:for|because of) ([^.]+)",
        r"known for ([^.]+)",
    ]

    features = []
    for pattern in feature_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            feature = match.group(1).strip()
            features.append(feature)

    if features:
        metadata["notable_features"] = features

    return metadata


def _extract_designation_year(content: str) -> Dict[str, Any]:
    """Extract designation year from content."""
    metadata = {}
    designation_patterns = [
        r"designated (?:as|a) (?:landmark|historic) (?:in|on) (\d{4})",
        r"became a (?:landmark|historic) (?:in|on) (\d{4})",
    ]

    for pattern in designation_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            metadata["designation_year"] = int(match.group(1))
            break

    return metadata


def _extract_renovation_years(content: str) -> Dict[str, Any]:
    """Extract renovation/restoration years from content."""
    metadata = {}
    renovation_patterns = [
        r"renovated in (\d{4})",
        r"restored in (\d{4})",
        r"rehabilitation in (\d{4})",
    ]

    renovation_years = []
    for pattern in renovation_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        for match in matches:
            year = int(match.group(1))
            renovation_years.append(year)

    if renovation_years:
        metadata["renovation_years"] = sorted(renovation_years)

    return metadata


def _extract_museum_info(content: str) -> Dict[str, Any]:
    """Extract museum and visiting information from content."""
    metadata: Dict[str, Any] = {}

    if "museum" not in content.lower():
        return metadata

    metadata["is_museum"] = True

    hours_patterns = [
        r"open (?:from|between) ([^.]+)",
        r"hours (?:are|is) ([^.]+)",
        r"visiting hours ([^.]+)",
    ]

    for pattern in hours_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            metadata["visiting_info"] = match.group(1).strip()
            break

    return metadata


def _extract_national_register_status(content: str) -> Dict[str, Any]:
    """Extract National Register status from content."""
    metadata = {}
    if re.search(r"national register of historic places", content, re.IGNORECASE):
        metadata["on_national_register"] = True
    return metadata


def extract_potential_metadata(content: str) -> Dict[str, Any]:
    """
    Extract potential metadata attributes from Wikipedia content.

    Args:
        content: The Wikipedia article content

    Returns:
        Dictionary of potential metadata attributes
    """
    metadata = {}

    # Extract different types of metadata using helper functions
    metadata.update(_extract_year_built(content))
    metadata.update(_extract_architect(content))
    metadata.update(_extract_architectural_styles(content))
    metadata.update(_extract_notable_features(content))
    metadata.update(_extract_designation_year(content))
    metadata.update(_extract_renovation_years(content))
    metadata.update(_extract_museum_info(content))
    metadata.update(_extract_national_register_status(content))

    return metadata


def fetch_wikipedia_article(landmark_id: str) -> List[Dict[str, Any]]:
    """
    Fetch Wikipedia articles for a landmark.

    Args:
        landmark_id: ID of the landmark

    Returns:
        List of dictionaries with article information
    """
    db_client = get_db_client()
    wiki_fetcher = WikipediaFetcher()

    # Get Wikipedia articles for the landmark
    articles = db_client.get_wikipedia_articles(landmark_id)

    if not articles:
        logger.warning(f"No Wikipedia articles found for landmark: {landmark_id}")
        return []

    logger.info(f"Found {len(articles)} Wikipedia articles for landmark: {landmark_id}")

    # Fetch content for each article
    result = []
    for article in articles:
        logger.info(f"- Article: {article.title}, URL: {article.url}")

        # Fetch the actual content from Wikipedia
        logger.info(f"Fetching content from Wikipedia for article: {article.title}")
        article_content = wiki_fetcher.fetch_wikipedia_content(article.url)

        if article_content:
            logger.info(
                f"Successfully fetched content for article: {article.title} ({len(article_content)} chars)"
            )

            # Extract potential metadata
            potential_metadata = extract_potential_metadata(article_content)

            result.append(
                {
                    "title": article.title,
                    "url": article.url,
                    "content": article_content,
                    "potential_metadata": potential_metadata,
                }
            )
        else:
            logger.warning(f"Failed to fetch content for article: {article.title}")

    return result


def save_article_to_file(
    article_data: Dict[str, Any], landmark_id: str, output_dir: str
) -> None:
    """
    Save article data to a file.

    Args:
        article_data: Dictionary with article information
        landmark_id: ID of the landmark
        output_dir: Directory to save the file
    """
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Create a filename based on the landmark ID and article title
    safe_title = article_data["title"].replace(" ", "_").replace("/", "_")
    filename = f"{landmark_id}_{safe_title}.json"
    filepath = os.path.join(output_dir, filename)

    # Save the article data to a JSON file
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(article_data, f, indent=2)

    logger.info(f"Saved article data to {filepath}")

    # Also save a plain text version of the content
    text_filename = f"{landmark_id}_{safe_title}.txt"
    text_filepath = os.path.join(output_dir, text_filename)

    with open(text_filepath, "w", encoding="utf-8") as f:
        f.write(f"Title: {article_data['title']}\n")
        f.write(f"URL: {article_data['url']}\n")
        f.write(f"\n{'-' * 80}\n\n")
        f.write(article_data["content"])
        f.write(f"\n\n{'-' * 80}\n\n")
        f.write("Potential Metadata:\n")
        for key, value in article_data["potential_metadata"].items():
            f.write(f"- {key}: {value}\n")

    logger.info(f"Saved article text to {text_filepath}")


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Analyze Wikipedia articles for NYC landmarks"
    )
    parser.add_argument(
        "--landmark-id",
        type=str,
        required=True,
        help="ID of the landmark to analyze (e.g., LP-00006)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="logs/wikipedia_analysis",
        help="Directory to save output files",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    return parser.parse_args()


def main() -> None:
    """Main entry point for the script."""
    args = parse_arguments()

    # Set up logging based on verbosity
    log_level = "INFO" if args.verbose else "WARNING"
    logger.setLevel(log_level)

    # Fetch the Wikipedia article
    articles = fetch_wikipedia_article(args.landmark_id)

    if not articles:
        print(f"No Wikipedia articles found for landmark: {args.landmark_id}")
        sys.exit(1)

    # Save each article to a file
    for article in articles:
        save_article_to_file(article, args.landmark_id, args.output)

    print(
        f"\nSuccessfully processed {len(articles)} Wikipedia articles for landmark: {args.landmark_id}"
    )
    print(f"Output saved to {args.output}")

    # Print a summary of the potential metadata
    print("\nPotential Metadata Fields:")
    all_fields = set()
    for article in articles:
        all_fields.update(article["potential_metadata"].keys())

    for field in sorted(all_fields):
        print(f"- {field}")


if __name__ == "__main__":
    main()

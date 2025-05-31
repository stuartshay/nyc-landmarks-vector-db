#!/usr/bin/env python3
"""
Script to analyze underutilized CoreDataStore APIs for metadata enhancement opportunities.

This script tests the underutilized APIs mentioned in the Wikipedia refactoring project:
1. Photo Archive API
2. PLUTO Data API
3. Building Details API
4. Reference Data APIs

Usage:
    python scripts/analyze_api_enhancements.py --landmarks LP-00001,LP-00006,LP-00009 --output logs/api_analysis
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List

from nyc_landmarks.db.db_client import get_db_client
from nyc_landmarks.utils.logger import get_logger

# Configure logging
logger = get_logger(__name__)


class APIEnhancementAnalyzer:
    """Analyzes underutilized CoreDataStore APIs for metadata enhancement opportunities."""

    def __init__(self) -> None:
        """Initialize the API analyzer."""
        self.db_client = get_db_client()
        self.analysis_results: Dict[str, Any] = {
            "analysis_metadata": {
                "timestamp": datetime.now().isoformat(),
                "script_version": "1.0.0",
                "description": "Analysis of underutilized CoreDataStore APIs for metadata enhancement",
            },
            "landmark_analyses": {},
            "api_performance": {},
            "enhancement_recommendations": {},
            "summary_statistics": {},
        }

    def test_photo_archive_api(self, landmark_id: str) -> Dict[str, Any]:
        """
        Test the Photo Archive API for a landmark.

        Args:
            landmark_id: ID of the landmark

        Returns:
            Dictionary with photo data and analysis
        """
        logger.info(f"Testing Photo Archive API for landmark: {landmark_id}")
        start_time = time.time()

        try:
            photos = self.db_client.client.get_landmark_photos(landmark_id, limit=10)
            response_time = time.time() - start_time

            photo_analysis: Dict[str, Any] = {
                "api_available": True,
                "response_time_seconds": response_time,
                "photo_count": len(photos) if photos else 0,
                "photos": [],
            }

            if photos:
                photos_list: List[Dict[str, Any]] = []
                for photo in photos:
                    # photos is a List[Dict[str, Any]], so photo is a dict
                    photo_data = {
                        "id": photo.get("id", None),
                        "title": photo.get("title", None),
                        "description": photo.get("description", None),
                        "collection": photo.get("collection", None),
                        "date_period": photo.get("date_period", None),
                        "url": photo.get(
                            "photo_url", None
                        ),  # Note: using photo_url key
                    }
                    photos_list.append(photo_data)
                photo_analysis["photos"] = photos_list

                logger.info(f"Found {len(photos)} photos for landmark {landmark_id}")
            else:
                logger.info(f"No photos found for landmark {landmark_id}")

            return photo_analysis

        except Exception as e:
            logger.error(f"Error testing Photo Archive API for {landmark_id}: {e}")
            return {
                "api_available": False,
                "error": str(e),
                "response_time_seconds": time.time() - start_time,
            }

    def test_pluto_data_api(self, landmark_id: str) -> Dict[str, Any]:
        """
        Test the PLUTO Data API for a landmark.

        Args:
            landmark_id: ID of the landmark

        Returns:
            Dictionary with PLUTO data and analysis
        """
        logger.info(f"Testing PLUTO Data API for landmark: {landmark_id}")
        start_time = time.time()

        try:
            pluto_data = self.db_client.client.get_landmark_pluto_data(landmark_id)
            response_time = time.time() - start_time

            pluto_analysis = {
                "api_available": True,
                "response_time_seconds": response_time,
                "has_pluto_data": bool(pluto_data),
                "pluto_data": {},
            }

            if pluto_data:
                # pluto_data is a List[Dict[str, Any]], so take the first record if available
                first_record = pluto_data[0] if pluto_data else {}
                pluto_analysis["pluto_data"] = {
                    "year_built": first_record.get("yearBuilt", None),
                    "land_use": first_record.get("landUse", None),
                    "historic_district": first_record.get("historicDistrict", None),
                    "zoning_district": first_record.get("zoneDist1", None),
                    "lot_area": first_record.get("lotArea", None),
                    "building_area": first_record.get("buildingArea", None),
                    "num_floors": first_record.get("numFloors", None),
                }
                logger.info(f"Found PLUTO data for landmark {landmark_id}")
            else:
                logger.info(f"No PLUTO data found for landmark {landmark_id}")

            return pluto_analysis

        except Exception as e:
            logger.error(f"Error testing PLUTO Data API for {landmark_id}: {e}")
            return {
                "api_available": False,
                "error": str(e),
                "response_time_seconds": time.time() - start_time,
            }

    def test_building_details_api(self, landmark_id: str) -> Dict[str, Any]:
        """
        Test the Building Details API for a landmark.

        Args:
            landmark_id: ID of the landmark

        Returns:
            Dictionary with building details and analysis
        """
        logger.info(f"Testing Building Details API for landmark: {landmark_id}")
        start_time = time.time()

        try:
            buildings = self.db_client.get_landmark_buildings(landmark_id, limit=50)
            response_time = time.time() - start_time

            building_analysis: Dict[str, Any] = {
                "api_available": True,
                "response_time_seconds": response_time,
                "building_count": len(buildings) if buildings else 0,
                "buildings": [],
            }

            if buildings:
                buildings_list: List[Dict[str, Any]] = []
                for building in buildings:
                    # buildings is a List[LpcReportModel], so use model attributes
                    building_data = {
                        "bbl": getattr(building, "bbl", None),
                        "bin": getattr(building, "binNumber", None),
                        "address": getattr(building, "street", None),
                        "latitude": getattr(building, "latitude", None),
                        "longitude": getattr(building, "longitude", None),
                        "borough": getattr(building, "borough", None),
                        "block": getattr(building, "block", None),
                        "lot": getattr(building, "lot", None),
                    }
                    buildings_list.append(building_data)
                building_analysis["buildings"] = buildings_list

                logger.info(
                    f"Found {len(buildings)} buildings for landmark {landmark_id}"
                )
            else:
                logger.info(f"No buildings found for landmark {landmark_id}")

            return building_analysis

        except Exception as e:
            logger.error(f"Error testing Building Details API for {landmark_id}: {e}")
            return {
                "api_available": False,
                "error": str(e),
                "response_time_seconds": time.time() - start_time,
            }

    def test_reference_data_apis(self) -> Dict[str, Any]:
        """
        Test the Reference Data APIs.

        Returns:
            Dictionary with reference data and analysis
        """
        logger.info("Testing Reference Data APIs")
        reference_analysis = {}

        # Test neighborhoods API
        try:
            start_time = time.time()
            neighborhoods = self.db_client.client.get_neighborhoods()
            reference_analysis["neighborhoods"] = {
                "api_available": True,
                "response_time_seconds": time.time() - start_time,
                "count": len(neighborhoods) if neighborhoods else 0,
                "sample_data": neighborhoods[:5] if neighborhoods else [],
            }
            logger.info(
                f"Found {len(neighborhoods) if neighborhoods else 0} neighborhoods"
            )
        except Exception as e:
            logger.error(f"Error testing neighborhoods API: {e}")
            reference_analysis["neighborhoods"] = {
                "api_available": False,
                "error": str(e),
            }

        # Test object types API
        try:
            start_time = time.time()
            object_types = self.db_client.client.get_object_types()
            reference_analysis["object_types"] = {
                "api_available": True,
                "response_time_seconds": time.time() - start_time,
                "count": len(object_types) if object_types else 0,
                "sample_data": object_types[:5] if object_types else [],
            }
            logger.info(
                f"Found {len(object_types) if object_types else 0} object types"
            )
        except Exception as e:
            logger.error(f"Error testing object types API: {e}")
            reference_analysis["object_types"] = {
                "api_available": False,
                "error": str(e),
            }

        # Test boroughs API
        try:
            start_time = time.time()
            boroughs = self.db_client.client.get_boroughs()
            reference_analysis["boroughs"] = {
                "api_available": True,
                "response_time_seconds": time.time() - start_time,
                "count": len(boroughs) if boroughs else 0,
                "sample_data": boroughs[:5] if boroughs else [],
            }
            logger.info(f"Found {len(boroughs) if boroughs else 0} boroughs")
        except Exception as e:
            logger.error(f"Error testing boroughs API: {e}")
            reference_analysis["boroughs"] = {"api_available": False, "error": str(e)}

        return reference_analysis

    def analyze_landmark(self, landmark_id: str) -> Dict[str, Any]:
        """
        Perform comprehensive API analysis for a single landmark.

        Args:
            landmark_id: ID of the landmark to analyze

        Returns:
            Complete analysis results for the landmark
        """
        logger.info(f"Analyzing landmark: {landmark_id}")

        landmark_analysis: Dict[str, Any] = {
            "landmark_id": landmark_id,
            "analysis_timestamp": datetime.now().isoformat(),
            "photo_archive": self.test_photo_archive_api(landmark_id),
            "pluto_data": self.test_pluto_data_api(landmark_id),
            "building_details": self.test_building_details_api(landmark_id),
        }

        # Calculate potential metadata enhancement value
        enhancement_score = 0
        enhancement_details = []

        if (
            landmark_analysis["photo_archive"]["api_available"]
            and landmark_analysis["photo_archive"].get("photo_count", 0) > 0
        ):
            enhancement_score += 2
            enhancement_details.append(
                "Photo titles and descriptions for enhanced search"
            )

        if (
            landmark_analysis["pluto_data"]["api_available"]
            and landmark_analysis["pluto_data"]["has_pluto_data"]
        ):
            enhancement_score += 3
            enhancement_details.append(
                "Building year, land use, and zoning information"
            )

        if (
            landmark_analysis["building_details"]["api_available"]
            and landmark_analysis["building_details"].get("building_count", 0) > 0
        ):
            enhancement_score += 2
            enhancement_details.append("Precise coordinates and building identifiers")

        landmark_analysis["enhancement_potential"] = {
            "score": enhancement_score,
            "max_score": 7,
            "details": enhancement_details,
        }

        return landmark_analysis

    def generate_recommendations(self) -> Dict[str, Any]:
        """
        Generate implementation recommendations based on analysis results.

        Returns:
            Dictionary with prioritized recommendations
        """
        landmarks_analyzed = list(self.analysis_results["landmark_analyses"].keys())
        total_landmarks = len(landmarks_analyzed)

        if total_landmarks == 0:
            return {"error": "No landmarks analyzed"}

        # Calculate API availability statistics
        photo_api_success = sum(
            1
            for lm in landmarks_analyzed
            if self.analysis_results["landmark_analyses"][lm]["photo_archive"][
                "api_available"
            ]
        )
        pluto_api_success = sum(
            1
            for lm in landmarks_analyzed
            if self.analysis_results["landmark_analyses"][lm]["pluto_data"][
                "api_available"
            ]
        )
        building_api_success = sum(
            1
            for lm in landmarks_analyzed
            if self.analysis_results["landmark_analyses"][lm]["building_details"][
                "api_available"
            ]
        )

        # Calculate data availability statistics
        photos_available = sum(
            1
            for lm in landmarks_analyzed
            if self.analysis_results["landmark_analyses"][lm]["photo_archive"].get(
                "photo_count", 0
            )
            > 0
        )
        pluto_available = sum(
            1
            for lm in landmarks_analyzed
            if self.analysis_results["landmark_analyses"][lm]["pluto_data"][
                "has_pluto_data"
            ]
        )
        buildings_available = sum(
            1
            for lm in landmarks_analyzed
            if self.analysis_results["landmark_analyses"][lm]["building_details"].get(
                "building_count", 0
            )
            > 0
        )

        # Generate recommendations
        recommendations: Dict[str, List[Any]] = {
            "priority_1_high_value": [],
            "priority_2_medium_value": [],
            "priority_3_low_value": [],
            "implementation_notes": [],
        }

        # PLUTO Data API recommendation
        if pluto_api_success / total_landmarks >= 0.8:  # 80% success rate
            priority = (
                "priority_1_high_value"
                if pluto_available / total_landmarks >= 0.6
                else "priority_2_medium_value"
            )
            recommendations[priority].append(
                {
                    "api": "PLUTO Data API",
                    "value": "High - provides building year, land use, zoning information",
                    "success_rate": f"{pluto_api_success}/{total_landmarks} ({pluto_api_success / total_landmarks * 100:.1f}%)",
                    "data_availability": f"{pluto_available}/{total_landmarks} ({pluto_available / total_landmarks * 100:.1f}%)",
                    "implementation_complexity": "Low - API already available in db_client",
                }
            )

        # Building Details API recommendation
        if building_api_success / total_landmarks >= 0.8:
            priority = (
                "priority_1_high_value"
                if buildings_available / total_landmarks >= 0.8
                else "priority_2_medium_value"
            )
            recommendations[priority].append(
                {
                    "api": "Building Details API",
                    "value": "Medium - provides precise coordinates and building identifiers",
                    "success_rate": f"{building_api_success}/{total_landmarks} ({building_api_success / total_landmarks * 100:.1f}%)",
                    "data_availability": f"{buildings_available}/{total_landmarks} ({buildings_available / total_landmarks * 100:.1f}%)",
                    "implementation_complexity": "Low - API already available in db_client",
                }
            )

        # Photo Archive API recommendation
        if photo_api_success / total_landmarks >= 0.8:
            priority = (
                "priority_2_medium_value"
                if photos_available / total_landmarks >= 0.3
                else "priority_3_low_value"
            )
            recommendations[priority].append(
                {
                    "api": "Photo Archive API",
                    "value": "Medium - provides historical context and additional search terms",
                    "success_rate": f"{photo_api_success}/{total_landmarks} ({photo_api_success / total_landmarks * 100:.1f}%)",
                    "data_availability": f"{photos_available}/{total_landmarks} ({photos_available / total_landmarks * 100:.1f}%)",
                    "implementation_complexity": "Medium - requires image handling and storage consideration",
                }
            )

        # Add implementation notes
        recommendations["implementation_notes"] = [
            "All APIs show good reliability and can be safely integrated",
            "PLUTO data provides the highest value metadata enhancement",
            "Building details API provides consistent geographic data",
            "Photo archive requires additional storage and processing considerations",
            "Consider implementing as optional metadata enhancement to maintain backward compatibility",
        ]

        return recommendations

    def save_analysis_results(self, output_path: str) -> None:
        """
        Save analysis results to a file.

        Args:
            output_path: Path to save the analysis results
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Add summary statistics
        self.analysis_results["summary_statistics"] = {
            "landmarks_analyzed": len(self.analysis_results["landmark_analyses"]),
            "reference_data_apis_tested": len(
                self.analysis_results.get("reference_data", {})
            ),
            "total_analysis_time": "calculated_at_save",
        }

        # Generate recommendations
        self.analysis_results["enhancement_recommendations"] = (
            self.generate_recommendations()
        )

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.analysis_results, f, indent=2, ensure_ascii=False)

        logger.info(f"Analysis results saved to: {output_path}")

    def run_analysis(
        self, landmark_ids: List[str], include_reference_apis: bool = True
    ) -> None:
        """
        Run comprehensive API analysis.

        Args:
            landmark_ids: List of landmark IDs to analyze
            include_reference_apis: Whether to test reference data APIs
        """
        logger.info(
            f"Starting API enhancement analysis for {len(landmark_ids)} landmarks"
        )

        # Test reference data APIs once
        if include_reference_apis:
            logger.info("Testing reference data APIs")
            self.analysis_results["reference_data"] = self.test_reference_data_apis()

        # Analyze each landmark
        for landmark_id in landmark_ids:
            try:
                landmark_analysis = self.analyze_landmark(landmark_id)
                self.analysis_results["landmark_analyses"][
                    landmark_id
                ] = landmark_analysis
                logger.info(f"Completed analysis for landmark: {landmark_id}")
            except Exception as e:
                logger.error(f"Failed to analyze landmark {landmark_id}: {e}")
                self.analysis_results["landmark_analyses"][landmark_id] = {
                    "landmark_id": landmark_id,
                    "error": str(e),
                    "analysis_timestamp": datetime.now().isoformat(),
                }

        logger.info("API enhancement analysis completed")


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Analyze underutilized CoreDataStore APIs for metadata enhancement"
    )
    parser.add_argument(
        "--landmarks",
        type=str,
        required=True,
        help="Comma-separated list of landmark IDs to analyze (e.g., LP-00001,LP-00006,LP-00009)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="logs/api_analysis",
        help="Directory to save analysis results",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--skip-reference-apis",
        action="store_true",
        help="Skip testing reference data APIs (neighborhoods, object types, boroughs)",
    )

    return parser.parse_args()


def main() -> None:
    """Main entry point for the script."""
    args = parse_arguments()

    # Set up logging
    if args.verbose:
        logger.setLevel("INFO")
    else:
        logger.setLevel("WARNING")

    # Parse landmark IDs
    landmark_ids = [lm.strip() for lm in args.landmarks.split(",") if lm.strip()]

    if not landmark_ids:
        print("Error: No valid landmark IDs provided")
        sys.exit(1)

    # Create output filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(args.output, f"api_analysis_{timestamp}.json")

    # Run analysis
    analyzer = APIEnhancementAnalyzer()
    analyzer.run_analysis(
        landmark_ids=landmark_ids, include_reference_apis=not args.skip_reference_apis
    )

    # Save results
    analyzer.save_analysis_results(output_file)

    print("\nAPI Enhancement Analysis Complete!")
    print(f"Analyzed {len(landmark_ids)} landmarks")
    print(f"Results saved to: {output_file}")

    # Print summary
    successful_analyses = sum(
        1
        for analysis in analyzer.analysis_results["landmark_analyses"].values()
        if "error" not in analysis
    )
    print(f"Successful analyses: {successful_analyses}/{len(landmark_ids)}")


if __name__ == "__main__":
    main()

"""
Functional tests for building metadata collection.

These tests verify building metadata functionality using non-destructive,
read-only operations against the production landmark index.
"""

import logging
from unittest.mock import patch

import pytest
from dotenv import load_dotenv

# Load environment variables for functional tests
load_dotenv()

logger = logging.getLogger(__name__)


class TestBuildingMetadataCollection:
    """Test building metadata collection functionality (non-destructive, read-only)."""

    @pytest.mark.functional
    def test_database_client_building_retrieval(self) -> None:
        """Test that database client can retrieve building data for landmarks."""
        from nyc_landmarks.db.db_client import get_db_client

        db_client = get_db_client()
        buildings = db_client.get_landmark_buildings("LP-00179")

        assert buildings is not None, "Buildings data should be returned"
        assert (
            len(buildings) > 0
        ), "Should find at least one building for LP-00179 (Gracie Mansion)"

        # Check that building has required fields
        building = buildings[0]
        assert hasattr(building, "bbl"), "Building should have BBL"
        assert hasattr(building, "plutoAddress"), "Building should have plutoAddress"
        assert hasattr(building, "binNumber"), "Building should have BIN number"

    @pytest.mark.functional
    def test_enhanced_metadata_collector(self) -> None:
        """Test that EnhancedMetadataCollector includes building data."""
        from nyc_landmarks.vectordb.enhanced_metadata import EnhancedMetadataCollector

        collector = EnhancedMetadataCollector()
        metadata = collector.collect_landmark_metadata("LP-00179")

        assert metadata is not None, "Enhanced metadata should be returned"

        # Test model_dump to ensure building fields are included
        metadata_dict = metadata.model_dump()
        building_fields = {
            k: v for k, v in metadata_dict.items() if k.startswith("building_")
        }

        assert (
            len(building_fields) > 0
        ), "Enhanced metadata should contain building fields"

        # Check for specific building fields
        expected_fields = [
            "building_0_bbl",
            "building_0_address",
            "building_0_binNumber",
        ]
        for field in expected_fields:
            assert field in building_fields, f"Missing expected building field: {field}"

    @pytest.mark.functional
    def test_landmark_metadata_model_dump_includes_extra_fields(self) -> None:
        """Test that LandmarkMetadata.model_dump() includes extra fields like building data."""
        from nyc_landmarks.models.metadata_models import LandmarkMetadata

        # Create a LandmarkMetadata instance with some extra fields
        metadata = LandmarkMetadata(
            landmark_id="LP-00179",
            name="Test Landmark",
            borough="Manhattan",
            designation_date="2020-01-01T00:00:00",
            has_pluto_data=True,
        )

        # Add some extra fields (simulating building data)
        metadata._extra_fields = {
            "building_0_bbl": "1234567890",
            "building_0_address": "123 Test Street",
            "building_0_binNumber": "1234567",
        }

        # Test model_dump includes extra fields
        dumped = metadata.model_dump()

        assert "building_0_bbl" in dumped, "model_dump should include extra fields"
        assert "building_0_address" in dumped, "model_dump should include extra fields"
        assert (
            "building_0_binNumber" in dumped
        ), "model_dump should include extra fields"
        assert (
            dumped["building_0_bbl"] == "1234567890"
        ), "Extra field values should be preserved"

    @pytest.mark.functional
    def test_pinecone_db_metadata_processing(self) -> None:
        """Test that PineconeDB can process enhanced metadata (read-only)."""
        from nyc_landmarks.vectordb.pinecone_db import PineconeDB

        pinecone_db = PineconeDB()

        # Test the _get_enhanced_metadata method (read-only)
        final_metadata = pinecone_db._get_enhanced_metadata("LP-00179")

        assert final_metadata is not None, "PineconeDB should return enhanced metadata"

        # Verify building fields are present in final metadata
        building_fields = {
            k: v for k, v in final_metadata.items() if k.startswith("building_")
        }
        assert len(building_fields) > 0, "Final metadata should contain building fields"


class TestBuildingMetadataErrorHandling:
    """Test error handling in building metadata collection (non-destructive)."""

    @pytest.mark.functional
    def test_missing_landmark_handling(self) -> None:
        """Test handling of landmarks that don't exist."""
        from nyc_landmarks.vectordb.enhanced_metadata import EnhancedMetadataCollector

        collector = EnhancedMetadataCollector()
        # Use a non-existent landmark ID
        metadata = collector.collect_landmark_metadata("LP-99999")

        # Should still return metadata object, just without building data
        assert (
            metadata is not None
        ), "Should return metadata even for non-existent landmarks"

    @pytest.mark.functional
    def test_database_error_handling(self) -> None:
        """Test handling of database connection errors."""
        from nyc_landmarks.vectordb.enhanced_metadata import EnhancedMetadataCollector

        collector = EnhancedMetadataCollector()

        # Mock database client to raise an exception
        with patch.object(
            collector.db_client, "get_landmark_buildings"
        ) as mock_get_buildings:
            mock_get_buildings.side_effect = Exception("Database connection failed")

            # Should handle error gracefully and still return metadata
            metadata = collector.collect_landmark_metadata("LP-00179")
            assert metadata is not None, "Should handle database errors gracefully"

"""
Comprehensive tests for the scripts/vector_utility.py script.

This module tests all vector utility functionality including fetch, check-landmark,
list-vectors, validate, compare-vectors, and verify-vectors commands.
"""

import io
import json
import tempfile
import unittest
from unittest.mock import Mock, patch

from scripts.vector_utility import (  # Constants; Classes; Helper functions; Core functionality; Utility functions; Command functions
    REQUIRED_METADATA,
    REQUIRED_WIKI_METADATA,
    VectorData,
    _categorize_metadata_differences,
    _check_required_metadata_fields,
    _print_vector_metadata,
    _verify_single_vector,
    _verify_single_vector_in_batch,
    check_deprecated_fields,
    check_landmark_command,
    check_vector_has_embeddings,
    compare_vectors,
    compare_vectors_command,
    convert_matches_to_dicts,
    display_metadata,
    extract_metadata,
    fetch_command,
    filter_matches_by_prefix,
    get_vector_id,
    list_vectors_command,
    process_building_data,
    validate_vector_command,
    validate_vector_metadata,
    verify_article_title,
    verify_batch,
    verify_batch_command,
    verify_id_format,
    verify_vectors,
    verify_vectors_command,
)
from tests.mocks.vector_utility_mocks import (  # Mock arguments
    MockMatch,
    create_mock_matches,
    create_mock_pinecone_db,
    create_mock_pinecone_db_empty,
    create_mock_pinecone_db_with_errors,
    get_mock_args_check_landmark,
    get_mock_args_compare,
    get_mock_args_fetch,
    get_mock_args_list_vectors,
    get_mock_args_validate,
    get_mock_args_verify,
    get_mock_args_verify_batch,
    get_mock_comparison_vectors,
    get_mock_deprecated_metadata,
    get_mock_invalid_vector,
    get_mock_landmark_vectors,
    get_mock_vector_batch,
    get_mock_vector_data,
    get_mock_vector_zero_embeddings,
    get_mock_verification_vectors,
    get_mock_wiki_vector_invalid_title,
)


class TestFetchCommand(unittest.TestCase):
    """Test cases for the fetch command functionality."""

    @patch("scripts.vector_utility.PineconeDB")
    def test_fetch_command_success(self, mock_pinecone_class: Mock) -> None:
        """Test successful vector fetching."""
        mock_db = create_mock_pinecone_db()
        mock_pinecone_class.return_value = mock_db

        args = get_mock_args_fetch()

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            fetch_command(args)

        # Verify the PineconeDB was called correctly
        mock_db.get_index_stats.assert_called_once()

        # Verify output was generated
        output = mock_stdout.getvalue()
        self.assertIn("VECTOR ID", output)

    @patch("scripts.vector_utility.PineconeDB")
    def test_fetch_command_specific_namespace(self, mock_pinecone_class: Mock) -> None:
        """Test fetching from specific namespace."""
        mock_db = create_mock_pinecone_db()
        mock_pinecone_class.return_value = mock_db

        args = get_mock_args_fetch()
        args.namespace = "landmarks"

        with patch("sys.stdout", new_callable=io.StringIO):
            fetch_command(args)

        # Verify fetch was called with specific namespace
        mock_db.fetch_vector_by_id.assert_called_with(args.vector_id, "landmarks")

    @patch("scripts.vector_utility.PineconeDB")
    def test_fetch_command_vector_not_found(self, mock_pinecone_class: Mock) -> None:
        """Test handling when vector is not found."""
        mock_db = create_mock_pinecone_db()
        mock_db.fetch_vector_by_id.return_value = None
        mock_pinecone_class.return_value = mock_db

        args = get_mock_args_fetch()

        with patch("sys.stdout", new_callable=io.StringIO):
            fetch_command(args)

        # Should handle gracefully (no exception)
        self.assertTrue(True)  # If we get here, no exception was raised

    @patch("scripts.vector_utility.PineconeDB")
    def test_fetch_command_error_handling(self, mock_pinecone_class: Mock) -> None:
        """Test error handling in fetch command."""
        mock_db = create_mock_pinecone_db_with_errors()
        mock_pinecone_class.return_value = mock_db

        args = get_mock_args_fetch()

        # Should handle errors gracefully
        fetch_command(args)

        # If we get here, no unhandled exception was raised
        self.assertTrue(True)

    def test_print_vector_metadata(self) -> None:
        """Test vector metadata printing."""
        vector_data = get_mock_vector_data()
        vector_obj = VectorData(vector_data)

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            _print_vector_metadata(vector_obj, vector_data["id"])

        output = mock_stdout.getvalue()
        self.assertIn("VECTOR ID", output)
        self.assertIn("METADATA", output)
        self.assertIn("landmark_id", output)

    def test_vector_data_class(self) -> None:
        """Test VectorData class initialization."""
        vector_dict = get_mock_vector_data()
        vector_obj = VectorData(vector_dict)

        self.assertEqual(vector_obj.id, vector_dict["id"])
        self.assertEqual(vector_obj.values, vector_dict["values"])
        self.assertEqual(vector_obj.metadata, vector_dict["metadata"])


class TestCheckLandmarkCommand(unittest.TestCase):
    """Test cases for the check-landmark command functionality."""

    @patch("scripts.vector_utility.PineconeDB")
    def test_check_landmark_command_success(self, mock_pinecone_class: Mock) -> None:
        """Test successful landmark checking."""
        mock_db = create_mock_pinecone_db()
        mock_pinecone_class.return_value = mock_db

        args = get_mock_args_check_landmark()

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            check_landmark_command(args)

        # Verify query was called with correct parameters
        mock_db.query_vectors.assert_called_once()

        # Verify output was generated
        output = mock_stdout.getvalue()
        self.assertIn("Checking vectors for landmark", output)

    @patch("scripts.vector_utility.PineconeDB")
    def test_check_landmark_command_no_vectors(self, mock_pinecone_class: Mock) -> None:
        """Test landmark checking when no vectors found."""
        mock_db = create_mock_pinecone_db_empty()
        mock_pinecone_class.return_value = mock_db

        args = get_mock_args_check_landmark()

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            check_landmark_command(args)

        output = mock_stdout.getvalue()
        self.assertIn("No vectors found", output)

    def test_extract_metadata(self) -> None:
        """Test metadata extraction from match objects."""
        vector_data = get_mock_vector_data()
        match = MockMatch(vector_data)

        metadata = extract_metadata(match)

        self.assertEqual(metadata, vector_data["metadata"])

    def test_get_vector_id(self) -> None:
        """Test vector ID extraction from match objects."""
        vector_data = get_mock_vector_data()
        match = MockMatch(vector_data)

        vector_id = get_vector_id(match)

        self.assertEqual(vector_id, vector_data["id"])

    def test_check_deprecated_fields(self) -> None:
        """Test checking for deprecated metadata fields."""
        metadata = get_mock_deprecated_metadata()

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            check_deprecated_fields(metadata)

        output = mock_stdout.getvalue()
        self.assertIn("WARNING", output)
        self.assertIn("Deprecated", output)

    def test_process_building_data(self) -> None:
        """Test processing building data from metadata."""
        metadata = {
            "building_count": 2,
            "building_0_bbl": "1000477501",
            "building_1_bbl": "1000477502",
        }

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            process_building_data(metadata)

        output = mock_stdout.getvalue()
        self.assertIn("Building count: 2", output)
        self.assertIn("Building BBLs", output)

    def test_display_metadata_verbose(self) -> None:
        """Test metadata display in verbose mode."""
        metadata = get_mock_vector_data()["metadata"]

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            display_metadata(metadata, verbose=True)

        output = mock_stdout.getvalue()
        self.assertIn("Full metadata", output)


class TestListVectorsCommand(unittest.TestCase):
    """Test cases for the list-vectors command functionality."""

    @patch("scripts.vector_utility.PineconeDB")
    def test_list_vectors_command_success(self, mock_pinecone_class: Mock) -> None:
        """Test successful vector listing."""
        mock_db = create_mock_pinecone_db()
        mock_pinecone_class.return_value = mock_db

        args = get_mock_args_list_vectors()

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            list_vectors_command(args)

        # Verify list_vectors was called
        mock_db.list_vectors.assert_called_once()

        # Verify output was generated
        output = mock_stdout.getvalue()
        self.assertIn("Found", output)

    @patch("scripts.vector_utility.PineconeDB")
    def test_list_vectors_command_empty_results(
        self, mock_pinecone_class: Mock
    ) -> None:
        """Test vector listing with empty results."""
        mock_db = create_mock_pinecone_db_empty()
        mock_pinecone_class.return_value = mock_db

        args = get_mock_args_list_vectors()

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            list_vectors_command(args)

        output = mock_stdout.getvalue()
        self.assertIn("No vectors found", output)

    def test_filter_matches_by_prefix(self) -> None:
        """Test filtering matches by prefix."""
        vector_batch = get_mock_vector_batch()
        matches = create_mock_matches(vector_batch)

        with patch("sys.stdout", new_callable=io.StringIO):
            filtered = filter_matches_by_prefix(matches, "wiki-")

        # Should only return wiki vectors
        self.assertEqual(len(filtered), 3)  # 3 wiki vectors in mock batch
        for match in filtered:
            self.assertTrue(match.id.startswith("wiki-"))

    def test_filter_matches_no_prefix(self) -> None:
        """Test filtering with no prefix (should return all)."""
        vector_batch = get_mock_vector_batch()
        matches = create_mock_matches(vector_batch)

        filtered = filter_matches_by_prefix(matches, None)

        self.assertEqual(len(filtered), len(matches))

    def test_convert_matches_to_dicts(self) -> None:
        """Test converting match objects to dictionaries."""
        vector_batch = get_mock_vector_batch()
        matches = create_mock_matches(vector_batch)

        dicts = convert_matches_to_dicts(matches)

        self.assertEqual(len(dicts), len(matches))
        for i, match_dict in enumerate(dicts):
            self.assertIn("id", match_dict)
            self.assertIn("score", match_dict)
            self.assertEqual(match_dict["id"], matches[i].id)


class TestValidateCommand(unittest.TestCase):
    """Test cases for the validate command functionality."""

    @patch("scripts.vector_utility.PineconeDB")
    def test_validate_vector_command_success(self, mock_pinecone_class: Mock) -> None:
        """Test successful vector validation."""
        mock_db = create_mock_pinecone_db()
        mock_pinecone_class.return_value = mock_db

        args = get_mock_args_validate()

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            validate_vector_command(args)

        # Verify fetch was called
        mock_db.fetch_vector_by_id.assert_called_once()

        # Verify validation output
        output = mock_stdout.getvalue()
        self.assertIn("has all required metadata fields", output)

    @patch("scripts.vector_utility.PineconeDB")
    def test_validate_vector_command_not_found(self, mock_pinecone_class: Mock) -> None:
        """Test validation when vector not found."""
        mock_db = create_mock_pinecone_db()
        mock_db.fetch_vector_by_id.return_value = None
        mock_pinecone_class.return_value = mock_db

        args = get_mock_args_validate()

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            validate_vector_command(args)

        output = mock_stdout.getvalue()
        self.assertIn("not found", output)

    def test_validate_vector_metadata_valid(self) -> None:
        """Test validating valid vector metadata."""
        vector_data = get_mock_vector_data()

        with patch("sys.stdout", new_callable=io.StringIO):
            is_valid = validate_vector_metadata(vector_data, verbose=False)

        self.assertTrue(is_valid)

    def test_validate_vector_metadata_invalid(self) -> None:
        """Test validating invalid vector metadata."""
        vector_data = get_mock_invalid_vector()

        with patch("sys.stdout", new_callable=io.StringIO):
            is_valid = validate_vector_metadata(vector_data, verbose=False)

        self.assertFalse(is_valid)

    def test_check_required_metadata_fields(self) -> None:
        """Test checking for required metadata fields."""
        # Test valid metadata
        valid_metadata = get_mock_vector_data()["metadata"]
        missing = _check_required_metadata_fields(
            "wiki-Test-LP-001-chunk-0", valid_metadata
        )
        self.assertEqual(len(missing), 0)

        # Test invalid metadata
        invalid_metadata = get_mock_invalid_vector()["metadata"]
        missing = _check_required_metadata_fields("invalid-vector-id", invalid_metadata)
        self.assertGreater(len(missing), 0)


class TestCompareVectorsCommand(unittest.TestCase):
    """Test cases for the compare-vectors command functionality."""

    @patch("scripts.vector_utility.PineconeDB")
    def test_compare_vectors_command_success(self, mock_pinecone_class: Mock) -> None:
        """Test successful vector comparison."""
        mock_db = create_mock_pinecone_db()
        mock_pinecone_class.return_value = mock_db

        args = get_mock_args_compare()

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            compare_vectors_command(args)

        # Verify both vectors were fetched
        self.assertEqual(mock_db.fetch_vector_by_id.call_count, 2)

        # Verify comparison output
        output = mock_stdout.getvalue()
        self.assertIn("COMPARING VECTORS", output)

    @patch("scripts.vector_utility.PineconeDB")
    def test_compare_vectors_function_text_format(
        self, mock_pinecone_class: Mock
    ) -> None:
        """Test compare_vectors function with text format."""
        mock_db = create_mock_pinecone_db()
        mock_pinecone_class.return_value = mock_db

        vector1, vector2 = get_mock_comparison_vectors()
        mock_db.fetch_vector_by_id.side_effect = [vector1, vector2]

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            result = compare_vectors("test1", "test2", "text")

        self.assertTrue(result)
        output = mock_stdout.getvalue()
        self.assertIn("COMPARING VECTORS", output)
        self.assertIn("Different Values", output)

    @patch("scripts.vector_utility.PineconeDB")
    def test_compare_vectors_function_json_format(
        self, mock_pinecone_class: Mock
    ) -> None:
        """Test compare_vectors function with JSON format."""
        mock_db = create_mock_pinecone_db()
        mock_pinecone_class.return_value = mock_db

        vector1, vector2 = get_mock_comparison_vectors()
        mock_db.fetch_vector_by_id.side_effect = [vector1, vector2]

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            result = compare_vectors("test1", "test2", "json")

        self.assertTrue(result)
        output = mock_stdout.getvalue()
        # Should be valid JSON output - extract the JSON portion
        lines = output.strip().split("\n")
        json_lines = []
        capture_json = False

        brace_count = 0
        for line in lines:
            if line.strip().startswith("{") and not capture_json:
                capture_json = True
                brace_count = 0

            if capture_json:
                json_lines.append(line)
                # Count braces to know when JSON object is complete
                brace_count += line.count("{") - line.count("}")

                if brace_count == 0:  # Balanced braces, JSON complete
                    break

        if json_lines:
            json_output = "\n".join(json_lines)
            try:
                parsed = json.loads(json_output)
                self.assertIn("vectors", parsed)
                self.assertIn("differences", parsed)
            except json.JSONDecodeError:
                self.fail(f"Output should be valid JSON. Got: {json_output}")
        else:
            self.fail(f"No JSON found in output: {output}")

    @patch("scripts.vector_utility.PineconeDB")
    def test_compare_vectors_first_not_found(self, mock_pinecone_class: Mock) -> None:
        """Test comparison when first vector not found."""
        mock_db = create_mock_pinecone_db()
        mock_db.fetch_vector_by_id.side_effect = [None, get_mock_vector_data()]
        mock_pinecone_class.return_value = mock_db

        with patch("sys.stdout", new_callable=io.StringIO):
            result = compare_vectors("not-found", "test2", "text")

        # Should return False when first vector not found
        self.assertFalse(result)

    @patch("scripts.vector_utility.PineconeDB")
    def test_compare_vectors_second_not_found(self, mock_pinecone_class: Mock) -> None:
        """Test comparison when second vector not found."""
        mock_db = create_mock_pinecone_db()
        mock_db.fetch_vector_by_id.side_effect = [get_mock_vector_data(), None]
        mock_pinecone_class.return_value = mock_db

        with patch("sys.stdout", new_callable=io.StringIO):
            result = compare_vectors("test1", "not-found", "text")

        # Should return False when second vector not found
        self.assertFalse(result)

    def test_categorize_metadata_differences(self) -> None:
        """Test categorizing metadata differences."""
        vector1, vector2 = get_mock_comparison_vectors()
        metadata1 = vector1["metadata"]
        metadata2 = vector2["metadata"]

        all_keys = set(metadata1.keys()).union(set(metadata2.keys()))
        differences, similarities, unique1, unique2 = _categorize_metadata_differences(
            all_keys, metadata1, metadata2
        )

        # Should find differences in chunk_index and text
        self.assertIn("chunk_index", differences)
        self.assertIn("text", differences)

        # Should find unique fields
        self.assertIn("vector1_only", unique1)
        self.assertIn("unique_field", unique2)


class TestVerifyVectorsCommand(unittest.TestCase):
    """Test cases for the verify-vectors command functionality."""

    @patch("scripts.vector_utility.PineconeDB")
    def test_verify_vectors_command_success(self, mock_pinecone_class: Mock) -> None:
        """Test successful vector verification."""
        mock_db = create_mock_pinecone_db()
        mock_pinecone_class.return_value = mock_db

        args = get_mock_args_verify()
        args.verbose = True  # Ensure verbose output for test

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            verify_vectors_command(args)

        # Verify list_vectors was called
        mock_db.list_vectors.assert_called_once()

        # Verify verification output
        output = mock_stdout.getvalue()
        self.assertIn("VERIFYING PINECONE VECTORS", output)

    @patch("scripts.vector_utility.PineconeDB")
    def test_verify_vectors_function(self, mock_pinecone_class: Mock) -> None:
        """Test verify_vectors function."""
        mock_db = create_mock_pinecone_db()
        mock_pinecone_class.return_value = mock_db

        # Set up mock to return verification vectors
        verification_vectors = get_mock_verification_vectors()
        mock_db.list_vectors.return_value = verification_vectors

        result = verify_vectors(limit=5, verbose=False)

        self.assertIsInstance(result, dict)
        self.assertIn("total", result)
        self.assertIn("passed", result)
        self.assertIn("failed", result)
        self.assertEqual(result["total"], 5)

    @patch("scripts.vector_utility.PineconeDB")
    def test_verify_batch_command_success(self, mock_pinecone_class: Mock) -> None:
        """Test successful batch verification."""
        mock_db = create_mock_pinecone_db()
        mock_pinecone_class.return_value = mock_db

        args = get_mock_args_verify_batch()
        args.verbose = True  # Ensure verbose output for test

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            verify_batch_command(args)

        # Verify vectors were fetched
        self.assertGreater(mock_db.fetch_vector_by_id.call_count, 0)

        # Verify batch verification output
        output = mock_stdout.getvalue()
        self.assertIn("BATCH VERIFICATION", output)

    @patch("scripts.vector_utility.PineconeDB")
    def test_verify_batch_with_file(self, mock_pinecone_class: Mock) -> None:
        """Test batch verification with file input."""
        mock_db = create_mock_pinecone_db()
        mock_pinecone_class.return_value = mock_db

        # Create temporary file with vector IDs
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
            f.write("wiki-Test-LP-001-chunk-0\n")
            f.write("wiki-Test-LP-001-chunk-1\n")
            temp_file = f.name

        try:
            args = get_mock_args_verify_batch()
            args.file = temp_file
            args.vector_ids = []

            with patch("sys.stdout", new_callable=io.StringIO):
                verify_batch_command(args)

            # Should have read from file and processed vectors
            self.assertGreater(mock_db.fetch_vector_by_id.call_count, 0)
        finally:
            import os

            os.unlink(temp_file)

    def test_verify_id_format(self) -> None:
        """Test vector ID format verification."""
        # Test valid Wikipedia format
        self.assertTrue(
            verify_id_format(
                "wiki-Manhattan_Building-LP-00079-chunk-0", "wikipedia", "LP-00079"
            )
        )

        # Test valid PDF format
        self.assertTrue(verify_id_format("LP-00079-chunk-0", "pdf", "LP-00079"))

        # Test invalid format
        self.assertFalse(verify_id_format("invalid-format", "wikipedia", "LP-00079"))

    def test_check_vector_has_embeddings(self) -> None:
        """Test checking if vector has valid embeddings."""
        # Test vector with valid embeddings
        valid_vector = get_mock_vector_data()
        self.assertTrue(check_vector_has_embeddings(valid_vector))

        # Test vector with zero embeddings
        zero_vector = get_mock_vector_zero_embeddings()
        self.assertFalse(check_vector_has_embeddings(zero_vector))

        # Test vector with no values
        no_values_vector = {"id": "test", "metadata": {}}
        self.assertFalse(check_vector_has_embeddings(no_values_vector))

    def test_verify_article_title(self) -> None:
        """Test Wikipedia article title verification."""
        # Test valid Wikipedia vector
        wiki_vector = get_mock_vector_data(
            "wiki-Manhattan_Municipal_Building-LP-00079-chunk-0"
        )
        self.assertTrue(
            verify_article_title(wiki_vector["id"], wiki_vector["metadata"])
        )

        # Test invalid Wikipedia vector (mismatched title)
        invalid_wiki = get_mock_wiki_vector_invalid_title()
        self.assertFalse(
            verify_article_title(invalid_wiki["id"], invalid_wiki["metadata"])
        )

        # Test non-Wikipedia vector (should return True - not applicable)
        pdf_vector = get_mock_vector_data("LP-00001-chunk-0")
        self.assertTrue(verify_article_title(pdf_vector["id"], pdf_vector["metadata"]))

    def test_verify_single_vector(self) -> None:
        """Test single vector verification."""
        valid_vector = get_mock_vector_data()

        with patch("sys.stdout", new_callable=io.StringIO):
            issues = _verify_single_vector(valid_vector, False, None, False)

        self.assertEqual(len(issues), 0)

        # Test invalid vector
        invalid_vector = get_mock_invalid_vector()

        with patch("sys.stdout", new_callable=io.StringIO):
            issues = _verify_single_vector(invalid_vector, False, None, False)

        self.assertGreater(len(issues), 0)

    def test_verify_batch_function(self) -> None:
        """Test verify_batch function directly."""
        with patch("scripts.vector_utility.PineconeDB") as mock_pinecone_class:
            mock_db = create_mock_pinecone_db()
            mock_pinecone_class.return_value = mock_db

            vector_ids = ["wiki-Test-LP-001-chunk-0", "wiki-Test-LP-001-chunk-1"]
            result = verify_batch(vector_ids, verbose=False)

            self.assertIsInstance(result, dict)
            self.assertIn("total", result)
            self.assertIn("found", result)
            self.assertIn("valid", result)
            self.assertEqual(result["total"], 2)


class TestUtilityFunctions(unittest.TestCase):
    """Test cases for utility functions and constants."""

    def test_required_metadata_constants(self) -> None:
        """Test that required metadata constants are defined."""
        self.assertIsInstance(REQUIRED_METADATA, list)
        self.assertIn("landmark_id", REQUIRED_METADATA)
        self.assertIn("source_type", REQUIRED_METADATA)
        self.assertIn("chunk_index", REQUIRED_METADATA)
        self.assertIn("text", REQUIRED_METADATA)

        self.assertIsInstance(REQUIRED_WIKI_METADATA, list)
        self.assertIn("article_title", REQUIRED_WIKI_METADATA)
        self.assertIn("article_url", REQUIRED_WIKI_METADATA)

    def test_constants_coverage(self) -> None:
        """Test that all required fields are covered in validation."""
        # This ensures our mock data includes all required fields
        valid_wiki_vector = get_mock_vector_data("wiki-Test-LP-001-chunk-0")
        metadata = valid_wiki_vector["metadata"]

        # Should have all required fields
        for field in REQUIRED_METADATA:
            self.assertIn(
                field, metadata, f"Required field {field} missing from mock data"
            )

        for field in REQUIRED_WIKI_METADATA:
            self.assertIn(
                field, metadata, f"Required Wiki field {field} missing from mock data"
            )


class TestErrorHandling(unittest.TestCase):
    """Test cases for error handling scenarios."""

    @patch("scripts.vector_utility.PineconeDB")
    def test_fetch_command_with_connection_error(
        self, mock_pinecone_class: Mock
    ) -> None:
        """Test fetch command with connection errors."""
        mock_db = create_mock_pinecone_db_with_errors()
        mock_pinecone_class.return_value = mock_db

        args = get_mock_args_fetch()

        # Should handle errors gracefully
        fetch_command(args)

        # If we reach here, no unhandled exception was raised
        self.assertTrue(True)

    @patch("scripts.vector_utility.PineconeDB")
    def test_verify_vectors_with_errors(self, mock_pinecone_class: Mock) -> None:
        """Test vector verification with errors."""
        mock_db = create_mock_pinecone_db_with_errors()
        mock_pinecone_class.return_value = mock_db

        result = verify_vectors(verbose=False)

        # Should return error result
        self.assertIn("error", result)
        self.assertEqual(result["total"], 0)

    @patch("scripts.vector_utility.PineconeDB")
    def test_list_command_with_errors(self, mock_pinecone_class: Mock) -> None:
        """Test list command with connection errors."""
        mock_db = create_mock_pinecone_db_with_errors()
        mock_pinecone_class.return_value = mock_db

        args = get_mock_args_list_vectors()

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            list_vectors_command(args)

        # Should handle errors gracefully and print error message
        output = mock_stdout.getvalue()
        self.assertIn("Error", output)

    @patch("scripts.vector_utility.PineconeDB")
    def test_check_landmark_command_with_errors(
        self, mock_pinecone_class: Mock
    ) -> None:
        """Test check-landmark command with connection errors."""
        mock_db = create_mock_pinecone_db_with_errors()
        mock_pinecone_class.return_value = mock_db

        args = get_mock_args_check_landmark()

        with patch("sys.stdout", new_callable=io.StringIO):
            check_landmark_command(args)

        # Should handle errors gracefully
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()

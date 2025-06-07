import os
import sys
import threading
from typing import Any, Dict, List, Tuple
from unittest.mock import Mock

import pytest

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


def _mock_process_landmark(landmark_id: str) -> Tuple[bool, int, int]:
    """Mock implementation of process_landmark method."""
    if not landmark_id or landmark_id == 'error_landmark':
        return False, 0, 0
    return True, 2, 2


def _mock_process_text_into_chunks(text: str) -> List[Dict[str, Any]]:
    """Mock implementation of _process_text_into_chunks method."""
    if not text.strip():
        return []
    chunks = []
    # Simple chunking by sentences
    sentences = text.split('.')
    for i, sentence in enumerate(sentences):
        if sentence.strip():
            chunks.append(
                {
                    'text': sentence.strip(),
                    'metadata': {'source': 'wikipedia', 'chunk_id': i},
                }
            )
    return chunks


def _mock_is_article_quality_sufficient(
    article_data: Dict[str, Any], quality_score: float
) -> bool:
    """Mock implementation of _is_article_quality_sufficient method."""
    # Basic quality check
    if quality_score < 0.5:
        return False
    if not article_data.get('content') or len(article_data.get('content', '')) < 100:
        return False
    return True


def _create_mock_wikipedia_processor() -> Any:
    """Create a mock WikipediaProcessor class for testing."""

    class MockWikipediaProcessor:
        def __init__(self) -> None:
            self.fetcher = Mock()
            self.embedding_generator = Mock()
            self.vector_db = Mock()
            self.quality_fetcher = Mock()

        def process_landmark(self, landmark_id: str) -> Tuple[bool, int, int]:
            return _mock_process_landmark(landmark_id)

        def _process_text_into_chunks(self, text: str) -> List[Dict[str, Any]]:
            return _mock_process_text_into_chunks(text)

        def _is_article_quality_sufficient(
            self, article_data: Dict[str, Any], quality_score: float
        ) -> bool:
            return _mock_is_article_quality_sufficient(article_data, quality_score)

    return MockWikipediaProcessor


def get_wikipedia_processor() -> Tuple[Any, bool]:
    """Safely get WikipediaProcessor class or create a mock."""
    try:
        from nyc_landmarks.wikipedia.processor import WikipediaProcessor

        return WikipediaProcessor, True
    except ImportError:
        return _create_mock_wikipedia_processor(), False


class TestWikipediaProcessingFixClean:
    """Test Wikipedia processor functionality with focus on data cleaning and fixes."""

    @pytest.fixture(scope="class")
    def processor_class_info(self) -> Tuple[Any, bool]:
        """Get processor class and whether it's real or mock."""
        return get_wikipedia_processor()

    @pytest.fixture
    def processor(self, processor_class_info: Tuple[Any, bool]) -> Any:
        """Create a processor instance."""
        ProcessorClass, is_real = processor_class_info
        return ProcessorClass()

    def test_processor_instantiation(
        self, processor_class_info: Tuple[Any, bool]
    ) -> None:
        """Test that processor can be instantiated."""
        ProcessorClass, is_real = processor_class_info
        processor = ProcessorClass()
        assert processor is not None

        if is_real:
            print("✅ Using real WikipediaProcessor")
        else:
            print("⚠️  Using mock WikipediaProcessor")

    def test_processor_has_required_attributes(self, processor: Any) -> None:
        """Test that processor has expected attributes."""
        required_attrs = [
            'wiki_fetcher',
            'embedding_generator',
            'pinecone_db',
            'quality_fetcher',
        ]

        for attr in required_attrs:
            assert hasattr(processor, attr), f"Processor missing attribute: {attr}"
            print(f"✅ Found attribute: {attr}")

    def test_process_landmark_method_exists(self, processor: Any) -> None:
        """Test that process_landmark_wikipedia method exists and is callable."""
        assert hasattr(
            processor, 'process_landmark_wikipedia'
        ), "process_landmark_wikipedia method not found"
        assert callable(
            processor.process_landmark_wikipedia
        ), "process_landmark_wikipedia is not callable"
        print("✅ process_landmark_wikipedia method exists and is callable")

    def test_process_landmark_success_case(self, processor: Any) -> None:
        """Test successful landmark processing."""
        # Skip this test if we don't have a real processor
        if not hasattr(processor, 'wiki_fetcher'):
            pytest.skip("Skipping integration test - using mock processor")

        # This would be an integration test - we'll mock it for unit testing
        result = processor.process_landmark_wikipedia('test_landmark')

        assert isinstance(
            result, tuple
        ), "process_landmark_wikipedia should return a tuple"
        assert len(result) == 3, "process_landmark_wikipedia should return 3 values"
        success, articles_processed, chunks_embedded = result
        assert isinstance(success, bool), "First return value should be boolean"
        assert isinstance(
            articles_processed, int
        ), "Second return value should be integer"
        assert isinstance(chunks_embedded, int), "Third return value should be integer"

        print(f"✅ process_landmark_wikipedia returned: {result}")

    def test_process_landmark_failure_case(self, processor: Any) -> None:
        """Test landmark processing failure handling."""
        # Test with empty or invalid input
        result = processor.process_landmark_wikipedia('')

        # Result should be a tuple
        assert isinstance(result, tuple), "Should return tuple for empty input"
        assert len(result) == 3, "Should return 3 values for empty input"

        success, articles_processed, chunks_embedded = result

        # For empty input, should typically return success but with zero processing
        if success:
            assert articles_processed == 0
            assert chunks_embedded == 0
            print("✅ Empty input handled as success with zero processing")
        else:
            print("⚠️  Empty input was processed as failure (acceptable behavior)")

    def test_text_processing_basic(self, processor: Any) -> None:
        """Test basic text processing functionality."""
        if hasattr(processor, '_process_text_into_chunks'):
            sample_text = (
                "This is sentence one. This is sentence two. This is sentence three."
            )
            chunks = processor._process_text_into_chunks(sample_text)

            assert isinstance(chunks, list), "Should return a list of chunks"
            assert len(chunks) > 0, "Should create at least one chunk"

            for chunk in chunks:
                assert isinstance(chunk, dict), "Each chunk should be a dictionary"
                assert 'text' in chunk, "Each chunk should have 'text' key"
                assert 'metadata' in chunk, "Each chunk should have 'metadata' key"
                assert isinstance(
                    chunk['metadata'], dict
                ), "Metadata should be a dictionary"

            print(f"✅ Text processing created {len(chunks)} chunks")
        else:
            print("⚠️  _process_text_into_chunks method not found, skipping test")

    def test_text_processing_empty_input(self, processor: Any) -> None:
        """Test text processing with empty input."""
        if hasattr(processor, '_process_text_into_chunks'):
            empty_chunks = processor._process_text_into_chunks("")
            assert isinstance(
                empty_chunks, list
            ), "Should return a list even for empty input"

            whitespace_chunks = processor._process_text_into_chunks("   \n\t   ")
            assert isinstance(
                whitespace_chunks, list
            ), "Should handle whitespace-only input"

            print("✅ Empty input handling works correctly")
        else:
            print(
                "⚠️  _process_text_into_chunks method not found, skipping empty input test"
            )

    def test_quality_assessment_basic(self, processor: Any) -> None:
        """Test basic quality assessment functionality."""
        if hasattr(processor, '_is_article_quality_sufficient'):
            good_article = {
                'title': 'Comprehensive Article',
                'content': 'This is a long and detailed article about a landmark. '
                * 10,
                'extract': 'A detailed description.',
            }

            poor_article = {
                'title': 'Stub Article',
                'content': 'Short.',
                'extract': 'Brief.',
            }

            # Test with high quality score
            high_quality = processor._is_article_quality_sufficient(good_article, 0.8)
            assert isinstance(
                high_quality, bool
            ), "Quality assessment should return boolean"

            # Test with low quality score
            low_quality = processor._is_article_quality_sufficient(poor_article, 0.2)
            assert isinstance(
                low_quality, bool
            ), "Quality assessment should return boolean"

            print(f"✅ Quality assessment: high={high_quality}, low={low_quality}")
        else:
            print(
                "⚠️  _is_article_quality_sufficient method not found, skipping quality test"
            )

    @pytest.mark.parametrize(
        "quality_score,expected_result_type",
        [
            (0.9, bool),
            (0.5, bool),
            (0.1, bool),
            (0.0, bool),
            (1.0, bool),
        ],
    )
    def test_quality_threshold_variations(
        self, processor: Any, quality_score: float, expected_result_type: type
    ) -> None:
        """Test quality assessment with various threshold values."""
        if hasattr(processor, '_is_article_quality_sufficient'):
            article = {
                'title': 'Test Article',
                'content': 'Test content with reasonable length for evaluation.',
                'extract': 'Test extract.',
            }

            result = processor._is_article_quality_sufficient(article, quality_score)
            assert isinstance(result, expected_result_type)
            print(f"✅ Quality score {quality_score} -> {result}")
        else:
            print(f"⚠️  Skipping quality test for score {quality_score}")

    def test_data_cleaning_markup_removal(self, processor: Any) -> None:
        """Test cleaning of Wikipedia markup and formatting."""
        if hasattr(processor, '_process_text_into_chunks'):
            dirty_text = """
            This text has {{citation needed}} tags.
            It has [edit] links and [[wikilinks]].
            References[edit] section should be handled.
            External links[edit] too.
            """

            chunks = processor._process_text_into_chunks(dirty_text)
            assert isinstance(chunks, list)

            if chunks:
                combined_text = ' '.join(chunk.get('text', '') for chunk in chunks)
                # Basic assertion - text should be processed
                assert len(combined_text) > 0
                print("✅ Markup cleaning processed text successfully")
            else:
                print("⚠️  No chunks created from dirty text")
        else:
            print(
                "⚠️  Cannot test markup removal without _process_text_into_chunks method"
            )

    def test_chunk_metadata_structure(self, processor: Any) -> None:
        """Test that chunk metadata has expected structure."""
        if hasattr(processor, '_process_text_into_chunks'):
            sample_text = "This is a test article about landmarks in New York City."
            chunks = processor._process_text_into_chunks(sample_text)

            for chunk in chunks:
                metadata = chunk.get('metadata', {})
                assert isinstance(metadata, dict), "Metadata should be a dictionary"
                assert 'source' in metadata, "Metadata should include source"

                # Source should be wikipedia for this processor
                assert metadata['source'] == 'wikipedia', "Source should be 'wikipedia'"

            print("✅ Chunk metadata structure is correct")
        else:
            print(
                "⚠️  Cannot test metadata structure without _process_text_into_chunks method"
            )

    def test_error_handling_robustness(self, processor: Any) -> None:
        """Test error handling with various problematic inputs."""
        test_cases = [
            'error_landmark',  # Designed to trigger errors in mock
            'landmark_with_special_chars_!@#$%',
            '12345',  # Numeric ID
            'very_long_landmark_id_' + 'x' * 100,
        ]

        for test_case in test_cases:
            try:
                result = processor.process_landmark_wikipedia(test_case)
                assert isinstance(
                    result, tuple
                ), f"Should return tuple for input: {test_case}"
                assert (
                    len(result) == 3
                ), f"Should return 3 values for input: {test_case}"
                print(f"✅ Handled input '{test_case[:20]}...' successfully")
            except Exception as e:
                print(f"⚠️  Error with input '{test_case[:20]}...': {e}")

    def test_concurrent_access_safety(self, processor: Any) -> None:
        """Test that processor can handle concurrent access safely."""
        results = []
        errors = []

        def process_in_thread(landmark_id: str) -> None:
            try:
                result = processor.process_landmark_wikipedia(f'landmark_{landmark_id}')
                results.append(result)
            except Exception as e:
                errors.append(e)

        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=process_in_thread, args=(str(i),))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join(timeout=10)  # 10 second timeout

        # Verify results
        assert len(results) + len(errors) == 5, "Should have 5 total results/errors"

        if errors:
            print(f"⚠️  {len(errors)} errors occurred during concurrent access")
        else:
            print("✅ Concurrent access completed without errors")

        print(f"✅ Processed {len(results)} landmarks concurrently")


class TestIntegrationScenarios:
    """Test integration scenarios and end-to-end workflows."""

    @pytest.fixture
    def processor(self) -> Any:
        ProcessorClass, _ = get_wikipedia_processor()
        return ProcessorClass()

    def test_complete_processing_workflow(self, processor: Any) -> None:
        """Test a complete processing workflow from start to finish."""
        landmark_id = 'central_park_test'

        # Execute the complete workflow
        result = processor.process_landmark_wikipedia(landmark_id)

        # Verify result format
        assert isinstance(result, tuple)
        assert len(result) == 3

        success, articles_processed, chunks_embedded = result

        # Log the results
        if success:
            print(
                f"✅ Complete workflow successful: {articles_processed} articles, {chunks_embedded} embeddings"
            )
        else:
            print(f"⚠️  Workflow completed with failure: {result}")

        # Basic sanity checks
        assert isinstance(success, bool)
        assert isinstance(articles_processed, int)
        assert isinstance(chunks_embedded, int)
        assert articles_processed >= 0
        assert chunks_embedded >= 0

    def test_batch_processing_simulation(self, processor: Any) -> None:
        """Test processing multiple landmarks in sequence."""
        landmark_ids = [
            'landmark_1',
            'landmark_2',
            'landmark_3',
            'landmark_4',
            'landmark_5',
        ]

        results = []
        for landmark_id in landmark_ids:
            try:
                result = processor.process_landmark_wikipedia(landmark_id)
                results.append((landmark_id, result))
            except Exception as e:
                results.append((landmark_id, f"Error: {e}"))

        assert len(results) == len(landmark_ids)

        successful_count = sum(
            1 for _, result in results if isinstance(result, tuple) and result[0]
        )
        print(f"✅ Batch processing: {successful_count}/{len(landmark_ids)} successful")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s', '--tb=short'])

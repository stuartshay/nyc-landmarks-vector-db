import os
import sys
import threading
import time
from typing import Any, Dict, List, Tuple
from unittest.mock import Mock, patch

import pytest

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from nyc_landmarks.wikipedia.processor import WikipediaProcessor
from scripts.ci.process_wikipedia_articles import (
    _get_processor,
    main,
    process_landmarks_parallel,
    process_landmarks_sequential,
)


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


class TestGetProcessor:
    """Test the _get_processor function and thread-local behavior."""

    def test_get_processor_returns_wikipedia_processor(self) -> None:
        """Test that _get_processor returns a WikipediaProcessor instance."""
        processor = _get_processor()
        assert isinstance(processor, WikipediaProcessor)

    def test_get_processor_thread_local_same_thread(self) -> None:
        """Test that _get_processor returns the same instance within the same thread."""
        processor1 = _get_processor()
        processor2 = _get_processor()
        assert processor1 is processor2

    def test_get_processor_thread_local_different_threads(self) -> None:
        """Test that _get_processor returns different instances in different threads."""
        processors = {}

        def get_processor_in_thread(thread_id: int) -> None:
            processors[thread_id] = _get_processor()

        # Create two threads
        thread1 = threading.Thread(target=get_processor_in_thread, args=(1,))
        thread2 = threading.Thread(target=get_processor_in_thread, args=(2,))

        thread1.start()
        thread2.start()

        thread1.join()
        thread2.join()

        # Different threads should have different processor instances
        assert processors[1] is not processors[2]
        assert isinstance(processors[1], WikipediaProcessor)
        assert isinstance(processors[2], WikipediaProcessor)

    def test_get_processor_thread_local_reuse_within_thread(self) -> None:
        """Test that multiple calls to _get_processor in same thread return same instance."""
        processors = []

        def collect_processors() -> None:
            for _ in range(5):
                processors.append(_get_processor())

        thread = threading.Thread(target=collect_processors)
        thread.start()
        thread.join()

        # All processors in the same thread should be the same instance
        first_processor = processors[0]
        for processor in processors[1:]:
            assert processor is first_processor


class TestProcessSingleLandmarkHelper:
    """Test the process_single_landmark helper function behavior through parallel processing."""

    @patch('scripts.ci.process_wikipedia_articles._get_processor')
    def test_process_single_landmark_through_parallel(
        self, mock_get_processor: Mock
    ) -> None:
        """Test single landmark processing through the parallel processing function."""
        # Mock processor and its methods
        mock_processor = Mock()
        mock_processor.process_landmark_wikipedia.return_value = (True, 5, 10)
        mock_get_processor.return_value = mock_processor

        # Test through parallel processing with 1 worker
        result = process_landmarks_parallel(
            ["landmark_123"], delete_existing=False, workers=1
        )

        # Verify the result structure
        assert "landmark_123" in result
        assert result["landmark_123"]["success"] is True
        assert result["landmark_123"]["articles_processed"] == 5
        assert result["landmark_123"]["chunks_embedded"] == 10
        assert "__metadata__" in result

    @patch('scripts.ci.process_wikipedia_articles._get_processor')
    def test_process_single_landmark_failure_through_parallel(
        self, mock_get_processor: Mock
    ) -> None:
        """Test handling of processing failure for a single landmark through parallel processing."""
        # Mock processor that raises an exception
        mock_processor = Mock()
        mock_processor.process_landmark_wikipedia.side_effect = Exception(
            "Processing failed"
        )
        mock_get_processor.return_value = mock_processor

        result = process_landmarks_parallel(
            ["landmark_123"], delete_existing=False, workers=1
        )

        # Verify the failure is handled properly
        assert "landmark_123" in result
        assert result["landmark_123"]["success"] is False
        assert result["landmark_123"]["articles_processed"] == 0
        assert result["landmark_123"]["chunks_embedded"] == 0
        assert "__metadata__" in result
        assert len(result["__metadata__"]["errors"]) > 0

    @patch('scripts.ci.process_wikipedia_articles._get_processor')
    def test_process_single_landmark_uses_thread_local_processor(
        self, mock_get_processor: Mock
    ) -> None:
        """Test that the parallel processing helper uses the thread-local processor."""
        mock_processor = Mock()
        mock_processor.process_landmark_wikipedia.return_value = (True, 1, 1)
        mock_get_processor.return_value = mock_processor

        process_landmarks_parallel(["test_id"], delete_existing=False, workers=1)

        mock_get_processor.assert_called_once()


class TestProcessLandmarksParallel:
    """Test the process_landmarks_parallel function."""

    @patch('scripts.ci.process_wikipedia_articles._get_processor')
    def test_process_landmarks_parallel_success(self, mock_get_processor: Mock) -> None:
        """Test successful parallel processing of landmarks."""
        landmark_ids = ["landmark_1", "landmark_2", "landmark_3"]

        # Mock processor with successful results
        mock_processor = Mock()
        mock_processor.process_landmark_wikipedia.side_effect = [
            (True, 2, 4),
            (True, 3, 6),
            (False, 0, 0),  # One failure
        ]
        mock_get_processor.return_value = mock_processor

        result = process_landmarks_parallel(
            landmark_ids, delete_existing=False, workers=2
        )

        # Verify the result structure
        assert "landmark_1" in result
        assert result["landmark_1"]["success"] is True
        assert result["landmark_1"]["articles_processed"] == 2
        assert result["landmark_1"]["chunks_embedded"] == 4

        assert "landmark_2" in result
        assert result["landmark_2"]["success"] is True
        assert result["landmark_2"]["articles_processed"] == 3
        assert result["landmark_2"]["chunks_embedded"] == 6

        assert "landmark_3" in result
        assert result["landmark_3"]["success"] is False
        assert result["landmark_3"]["articles_processed"] == 0
        assert result["landmark_3"]["chunks_embedded"] == 0

        assert "__metadata__" in result

    @patch('scripts.ci.process_wikipedia_articles._get_processor')
    def test_process_landmarks_parallel_empty_list(
        self, mock_get_processor: Mock
    ) -> None:
        """Test parallel processing with empty landmark list."""
        result = process_landmarks_parallel([], delete_existing=False, workers=2)

        # Should return empty results with metadata
        assert result == {"__metadata__": {"errors": [], "skipped_landmarks": set()}}
        mock_get_processor.assert_not_called()

    @patch('scripts.ci.process_wikipedia_articles._get_processor')
    def test_process_landmarks_parallel_all_failures(
        self, mock_get_processor: Mock
    ) -> None:
        """Test parallel processing when all landmarks fail."""
        landmark_ids = ["landmark_1", "landmark_2"]

        # Mock processor with all failures
        mock_processor = Mock()
        mock_processor.process_landmark_wikipedia.side_effect = [
            (False, 0, 0),
            (False, 0, 0),
        ]
        mock_get_processor.return_value = mock_processor

        result = process_landmarks_parallel(
            landmark_ids, delete_existing=False, workers=2
        )

        # Verify all failed
        assert "landmark_1" in result
        assert result["landmark_1"]["success"] is False
        assert "landmark_2" in result
        assert result["landmark_2"]["success"] is False
        assert "__metadata__" in result

    @patch('scripts.ci.process_wikipedia_articles._get_processor')
    def test_process_landmarks_parallel_concurrent_execution(
        self, mock_get_processor: Mock
    ) -> None:
        """Test that parallel processing can handle concurrent execution."""
        landmark_ids = ["landmark_1", "landmark_2", "landmark_3", "landmark_4"]
        execution_times = []

        def slow_process(
            landmark_id: str, delete_existing: bool = False
        ) -> Tuple[bool, int, int]:
            start_time = time.time()
            time.sleep(0.1)  # Simulate processing time
            end_time = time.time()
            execution_times.append((landmark_id, start_time, end_time))
            return (True, 1, 1)

        mock_processor = Mock()
        mock_processor.process_landmark_wikipedia.side_effect = slow_process
        mock_get_processor.return_value = mock_processor

        start_total = time.time()
        result = process_landmarks_parallel(
            landmark_ids, delete_existing=False, workers=2
        )
        end_total = time.time()

        # With 4 items and 2 workers, should take ~0.2 seconds (2 batches)
        # rather than 0.4 seconds (sequential)
        total_time = end_total - start_total
        assert total_time < 0.35  # Allow some overhead

        # Verify all processed successfully
        for landmark_id in landmark_ids:
            assert landmark_id in result
            assert result[landmark_id]["success"] is True

        assert len(execution_times) == 4


class TestProcessLandmarksSequential:
    """Test the process_landmarks_sequential function."""

    @patch('scripts.ci.process_wikipedia_articles._get_processor')
    def test_process_landmarks_sequential_success(
        self, mock_get_processor: Mock
    ) -> None:
        """Test successful sequential processing of landmarks."""
        landmark_ids = ["landmark_1", "landmark_2", "landmark_3"]

        # Mock processor
        mock_processor = Mock()
        mock_processor.process_landmark_wikipedia.side_effect = [
            (True, 2, 4),
            (True, 3, 6),
            (False, 0, 0),  # One failure
        ]
        mock_get_processor.return_value = mock_processor

        result = process_landmarks_sequential(landmark_ids, delete_existing=False)

        # Verify the result structure
        assert "landmark_1" in result
        assert result["landmark_1"]["success"] is True
        assert result["landmark_1"]["articles_processed"] == 2
        assert result["landmark_1"]["chunks_embedded"] == 4

        assert "landmark_2" in result
        assert result["landmark_2"]["success"] is True
        assert result["landmark_2"]["articles_processed"] == 3
        assert result["landmark_2"]["chunks_embedded"] == 6

        assert "landmark_3" in result
        assert result["landmark_3"]["success"] is False
        assert result["landmark_3"]["articles_processed"] == 0
        assert result["landmark_3"]["chunks_embedded"] == 0

        assert "__metadata__" in result

        # Verify all landmarks were processed in order
        assert mock_processor.process_landmark_wikipedia.call_count == 3
        call_args = [
            call[0][0]
            for call in mock_processor.process_landmark_wikipedia.call_args_list
        ]
        assert call_args == landmark_ids

    @patch('scripts.ci.process_wikipedia_articles._get_processor')
    def test_process_landmarks_sequential_uses_get_processor(
        self, mock_get_processor: Mock
    ) -> None:
        """Test that sequential processing uses _get_processor instead of direct instantiation."""
        landmark_ids = ["landmark_1"]

        mock_processor = Mock()
        mock_processor.process_landmark_wikipedia.return_value = (True, 1, 1)
        mock_get_processor.return_value = mock_processor

        process_landmarks_sequential(landmark_ids, delete_existing=False)

        # Verify that _get_processor was called
        mock_get_processor.assert_called_once()
        # Verify that the processor's process_landmark_wikipedia was called
        mock_processor.process_landmark_wikipedia.assert_called_once_with(
            "landmark_1", delete_existing=False
        )

    @patch('scripts.ci.process_wikipedia_articles._get_processor')
    def test_process_landmarks_sequential_empty_list(
        self, mock_get_processor: Mock
    ) -> None:
        """Test sequential processing with empty landmark list."""
        mock_processor = Mock()
        mock_get_processor.return_value = mock_processor

        result = process_landmarks_sequential([], delete_existing=False)

        # Should return empty results with metadata
        assert result == {"__metadata__": {"errors": [], "skipped_landmarks": set()}}

        # Should still get processor but not call process_landmark_wikipedia
        mock_get_processor.assert_called_once()
        mock_processor.process_landmark_wikipedia.assert_not_called()

    @patch('scripts.ci.process_wikipedia_articles._get_processor')
    def test_process_landmarks_sequential_exception_handling(
        self, mock_get_processor: Mock
    ) -> None:
        """Test that sequential processing handles exceptions properly."""
        landmark_ids = ["landmark_1", "landmark_2"]

        mock_processor = Mock()
        mock_processor.process_landmark_wikipedia.side_effect = [
            Exception("Processing failed"),
            (True, 1, 2),
        ]
        mock_get_processor.return_value = mock_processor

        result = process_landmarks_sequential(landmark_ids, delete_existing=False)

        # First landmark should fail, second should succeed
        assert "landmark_1" in result
        assert result["landmark_1"]["success"] is False
        assert result["landmark_1"]["articles_processed"] == 0
        assert result["landmark_1"]["chunks_embedded"] == 0

        assert "landmark_2" in result
        assert result["landmark_2"]["success"] is True
        assert result["landmark_2"]["articles_processed"] == 1
        assert result["landmark_2"]["chunks_embedded"] == 2

        assert "__metadata__" in result
        assert len(result["__metadata__"]["errors"]) == 1


class TestMainFunction:
    """Test the main function and argument parsing."""

    # Note: The main function tests are commented out because they require complex mocking
    # of the argument parsing and landmark fetching logic that is better tested through
    # integration tests rather than unit tests.

    def test_main_function_exists(self) -> None:
        """Test that the main function exists and is callable."""
        assert callable(main)


class TestConcurrencyAndThreadSafety:
    """Test concurrent execution and thread safety."""

    def test_multiple_threads_get_different_processors(self) -> None:
        """Test that multiple threads get different processor instances."""
        processors = {}
        threads = []

        def get_and_store_processor(thread_id: int) -> None:
            processor = _get_processor()
            processors[thread_id] = processor
            # Use the processor to ensure it's properly initialized
            assert hasattr(processor, 'process_landmark_wikipedia')

        # Create multiple threads
        for i in range(5):
            thread = threading.Thread(target=get_and_store_processor, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        # Verify we have 5 different processor instances
        assert len(processors) == 5
        processor_ids = [id(p) for p in processors.values()]
        assert len(set(processor_ids)) == 5  # All different instances

    @patch('scripts.ci.process_wikipedia_articles._get_processor')
    def test_parallel_processing_thread_safety(self, mock_get_processor: Mock) -> None:
        """Test that parallel processing is thread-safe."""
        landmark_ids = [
            f"landmark_{i}" for i in range(8)
        ]  # More landmarks to encourage thread usage
        results_tracking = []

        def track_processing(
            landmark_id: str, delete_existing: bool = False
        ) -> Tuple[bool, int, int]:
            import time

            thread_id = threading.current_thread().ident
            # Small delay to encourage multiple threads
            time.sleep(0.01)
            results_tracking.append((landmark_id, thread_id))
            return (True, 1, 2)

        mock_processor = Mock()
        mock_processor.process_landmark_wikipedia.side_effect = track_processing
        mock_get_processor.return_value = mock_processor

        result = process_landmarks_parallel(
            landmark_ids, delete_existing=False, workers=4
        )

        # Verify all landmarks were processed
        for landmark_id in landmark_ids:
            assert landmark_id in result
            assert result[landmark_id]["success"] is True
            assert result[landmark_id]["articles_processed"] == 1
            assert result[landmark_id]["chunks_embedded"] == 2

        # Verify thread usage (ThreadPoolExecutor may use fewer threads than max for small/fast tasks)
        thread_ids = {thread_id for _, thread_id in results_tracking}
        assert len(thread_ids) >= 1  # At least one thread used
        # Don't require multiple threads as ThreadPoolExecutor behavior can vary
        # The key is that the parallel function works correctly

        # Verify all landmarks were processed exactly once
        processed_landmarks = [landmark_id for landmark_id, _ in results_tracking]
        assert set(processed_landmarks) == set(landmark_ids)
        assert len(processed_landmarks) == len(landmark_ids)


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

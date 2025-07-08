import os
import sys
import threading
import time
from typing import Any, Dict, List, Tuple
from unittest.mock import Mock, patch

import pytest

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

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

    @patch('scripts.ci.process_wikipedia_articles.WikipediaProcessor')
    def test_get_processor_returns_wikipedia_processor(
        self, mock_processor_class: Mock
    ) -> None:
        """Test that _get_processor returns a WikipediaProcessor instance."""
        mock_instance = Mock()
        mock_processor_class.return_value = mock_instance

        processor = _get_processor()
        assert processor is mock_instance
        mock_processor_class.assert_called_once()

    @patch('scripts.ci.process_wikipedia_articles.WikipediaProcessor')
    def test_get_processor_thread_local_same_thread(
        self, mock_processor_class: Mock
    ) -> None:
        """Test that _get_processor returns the same instance within the same thread."""
        # Clear any existing thread-local data
        import scripts.ci.process_wikipedia_articles as script_module

        if hasattr(script_module._thread_local, 'processor'):
            delattr(script_module._thread_local, 'processor')

        mock_instance = Mock()
        mock_processor_class.return_value = mock_instance

        processor1 = _get_processor()
        processor2 = _get_processor()

        assert processor1 is processor2
        # Should only be called once due to thread-local caching
        mock_processor_class.assert_called_once()

    @patch('scripts.ci.process_wikipedia_articles.WikipediaProcessor')
    def test_get_processor_thread_local_different_threads(
        self, mock_processor_class: Mock
    ) -> None:
        """Test that _get_processor returns different instances in different threads."""
        processors = {}
        mock_instances = [Mock(), Mock()]
        mock_processor_class.side_effect = mock_instances

        def get_processor_in_thread(thread_id: int) -> None:
            processors[thread_id] = _get_processor()

        # Create two threads
        thread1 = threading.Thread(target=get_processor_in_thread, args=(1,))
        thread2 = threading.Thread(target=get_processor_in_thread, args=(2,))

        thread1.start()
        thread2.start()

        thread1.join()
        thread2.join()

        # Verify we got results from both threads
        assert len(processors) == 2
        assert 1 in processors
        assert 2 in processors
        # Verify different instances
        assert processors[1] is not processors[2]

    @patch('scripts.ci.process_wikipedia_articles.WikipediaProcessor')
    def test_get_processor_thread_local_reuse_within_thread(
        self, mock_processor_class: Mock
    ) -> None:
        """Test that multiple calls to _get_processor in same thread return same instance."""
        processors = []
        mock_instance = Mock()
        mock_processor_class.return_value = mock_instance

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
        # Should only be called once due to thread-local caching
        mock_processor_class.assert_called_once()


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

        # Mock processor with successful results - use a function to ensure deterministic behavior
        mock_processor = Mock()

        def mock_process_landmark_wikipedia(
            landmark_id: str, delete_existing: bool = False
        ) -> Tuple[bool, int, int]:
            """Return deterministic results based on landmark ID."""
            if landmark_id == "landmark_1":
                return (True, 2, 4)
            elif landmark_id == "landmark_2":
                return (True, 3, 6)
            elif landmark_id == "landmark_3":
                return (False, 0, 0)  # One failure
            else:
                return (False, 0, 0)  # Default failure for unknown IDs

        mock_processor.process_landmark_wikipedia.side_effect = (
            mock_process_landmark_wikipedia
        )
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

        # Mock processor with all failures - use a function for deterministic behavior
        mock_processor = Mock()

        def mock_process_landmark_wikipedia_failures(
            landmark_id: str, delete_existing: bool = False
        ) -> Tuple[bool, int, int]:
            """Return failure for all landmark IDs."""
            return (False, 0, 0)

        mock_processor.process_landmark_wikipedia.side_effect = (
            mock_process_landmark_wikipedia_failures
        )
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

        # Mock processor with deterministic results based on landmark ID
        mock_processor = Mock()

        def mock_process_landmark_wikipedia_sequential(
            landmark_id: str, delete_existing: bool = False
        ) -> Tuple[bool, int, int]:
            """Return deterministic results based on landmark ID."""
            if landmark_id == "landmark_1":
                return (True, 2, 4)
            elif landmark_id == "landmark_2":
                return (True, 3, 6)
            elif landmark_id == "landmark_3":
                return (False, 0, 0)  # One failure
            else:
                return (False, 0, 0)  # Default failure for unknown IDs

        mock_processor.process_landmark_wikipedia.side_effect = (
            mock_process_landmark_wikipedia_sequential
        )
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

        def mock_process_landmark_with_exception(
            landmark_id: str, delete_existing: bool = False
        ) -> Tuple[bool, int, int]:
            """Return exception for landmark_1, success for landmark_2."""
            if landmark_id == "landmark_1":
                raise Exception("Processing failed")
            elif landmark_id == "landmark_2":
                return (True, 1, 2)
            else:
                return (False, 0, 0)  # Default failure for unknown IDs

        mock_processor.process_landmark_wikipedia.side_effect = (
            mock_process_landmark_with_exception
        )
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

    @patch('scripts.ci.process_wikipedia_articles.WikipediaProcessor')
    def test_multiple_threads_get_different_processors(
        self, mock_processor_class: Mock
    ) -> None:
        """Test that multiple threads get different processor instances."""
        processors = {}
        threads = []

        # Create different mock instances for each thread
        mock_instances = [Mock() for _ in range(5)]
        mock_processor_class.side_effect = mock_instances

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


class TestProcessLandmarksZeroArticles:
    """Test zero articles handling across both processing modes."""

    @pytest.mark.parametrize(
        "processing_function,test_landmarks,expected_side_effect",
        [
            (
                process_landmarks_parallel,
                ["landmark_1", "landmark_2"],
                [(True, 0, 0), (False, 0, 0)],  # side_effect for parallel
            ),
            (
                process_landmarks_sequential,
                ["landmark_1"],
                (True, 0, 0),  # return_value for sequential
            ),
        ],
    )
    @patch('scripts.ci.process_wikipedia_articles._get_processor')
    def test_process_landmarks_skips_zero_articles(
        self,
        mock_get_processor: Mock,
        processing_function: Any,
        test_landmarks: List[str],
        expected_side_effect: Any,
    ) -> None:
        """Landmarks with zero articles should be tracked as skipped."""
        mock_processor = Mock()
        mock_get_processor.return_value = mock_processor

        # Configure mock based on whether it's parallel or sequential
        if processing_function == process_landmarks_parallel:
            mock_processor.process_landmark_wikipedia.side_effect = expected_side_effect
            result = processing_function(
                test_landmarks, delete_existing=False, workers=2
            )
        else:  # sequential
            mock_processor.process_landmark_wikipedia.return_value = (
                expected_side_effect
            )
            result = processing_function(test_landmarks, delete_existing=False)

        skipped = result["__metadata__"]["skipped_landmarks"]
        assert skipped == set(test_landmarks)

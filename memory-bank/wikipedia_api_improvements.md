# Wikipedia API Improvements

## Project Overview

**Objective**: Improve the performance, reliability, and efficiency of API calls within the Wikipedia processing components of the NYC Landmarks Vector Database.

**Date Started**: 2025-06-05

## Analysis of Current Implementation

### Identified Issues

1. **HTTP Request Inefficiencies**:

   - No connection pooling or session reuse
   - Basic timeout configuration with single value for all timeouts
   - Limited HTTP client configuration options
   - Inefficient sequential processing of requests

1. **Lack of Caching**:

   - No caching mechanism for Wikipedia content or API responses
   - Redundant fetching of the same content across different runs
   - No TTL-based invalidation strategy for cached content

1. **Simplistic Rate Limiting**:

   - Fixed delay regardless of response times or API requirements
   - No adaptive rate limiting based on response headers
   - Lacks sophisticated backoff strategies for high traffic scenarios

1. **Basic Error Handling**:

   - Limited retry logic for specific exception types
   - No circuit breaker pattern to prevent cascading failures
   - Insufficient logging for debugging purposes
   - No differentiation between transient and permanent failures

1. **Content Extraction Limitations**:

   - BeautifulSoup parsing could be more robust
   - No fallback mechanisms for different page structures
   - HTML scraping instead of direct API integration
   - Limited error recovery for parsing failures

1. **Metadata Collection Inefficiencies**:

   - Collecting metadata separately for each article
   - No reuse of metadata across related articles for the same landmark
   - Limited bulk processing capabilities

1. **API Response Processing**:

   - Immediate processing of entire responses
   - Memory-intensive operations for large articles
   - No streaming or generator-based processing

## Implementation Plan

### Phase 1: Quick Wins

These improvements provide immediate benefits with minimal risk:

1. **Implement Connection Pooling**

   - Replace individual `requests.get()` calls with a persistent `requests.Session()`
   - Configure session with appropriate headers, timeouts, and retry parameters
   - Implement keep-alive for connection reuse
   - Sample code:
     ```python
     class WikipediaFetcher:
         def __init__(self) -> None:
             # Create a persistent session
             self.session = requests.Session()
             self.session.headers.update(
                 {
                     "User-Agent": "NYCLandmarksVectorDB/1.0 (https://github.com/username/nyc-landmarks-vector-db; email@example.com) Python-Requests/2.31.0"
                 }
             )
             # Configure connection pooling
             adapter = requests.adapters.HTTPAdapter(
                 pool_connections=10, pool_maxsize=20, max_retries=3
             )
             self.session.mount("http://", adapter)
             self.session.mount("https://", adapter)
     ```

1. **Enhanced Timeout Handling**

   - Replace single timeout with separate connect, read, and total timeouts
   - Configure timeouts based on expected operation times
   - Sample code:
     ```python
     def fetch_wikipedia_content(self, url: str) -> Tuple[Optional[str], Optional[str]]:
         try:
             response = self.session.get(
                 url,
                 timeout=(3.05, 27),  # (connect_timeout, read_timeout)
             )
             # Process response...
     ```

1. **Implement Metadata Caching**

   - Add in-memory cache for landmark metadata to avoid redundant collection
   - Implement landmark-level caching with timestamp-based expiration
   - Sample code:
     ```python
     class EnhancedMetadataCollector:
         def __init__(self) -> None:
             self._metadata_cache: Dict[str, Tuple[datetime.datetime, Any]] = {}
             self._cache_ttl = datetime.timedelta(hours=24)

         def collect_landmark_metadata(self, landmark_id: str) -> Optional[Any]:
             # Check cache first
             if landmark_id in self._metadata_cache:
                 timestamp, data = self._metadata_cache[landmark_id]
                 if datetime.datetime.now() - timestamp < self._cache_ttl:
                     logger.info(f"Using cached metadata for landmark {landmark_id}")
                     return data

             # Collect metadata as before if not in cache
             metadata = self._collect_metadata_implementation(landmark_id)

             # Store in cache
             if metadata:
                 self._metadata_cache[landmark_id] = (datetime.datetime.now(), metadata)

             return metadata
     ```

1. **Enhanced Error Handling and Logging**

   - Improve error categorization (network, parsing, API errors)
   - Add more detailed logging for debugging
   - Implement structured logging for better error analysis
   - Sample code:
     ```python
     def _fetch_and_parse_html(self, url: str) -> BeautifulSoup:
         try:
             logger.info(f"Fetching Wikipedia content from: {url}")
             response = self.session.get(url, timeout=(3.05, 27))
             response.raise_for_status()

             logger.debug(f"HTTP response status: {response.status_code}")
             logger.debug(f"Response headers: {dict(response.headers)}")
             logger.debug(f"Response preview: {response.text[:500]}...")

             return BeautifulSoup(response.text, "html.parser")
         except requests.exceptions.ConnectionError as e:
             logger.error(f"Connection error fetching {url}: {e}", exc_info=True)
             raise
         except requests.exceptions.Timeout as e:
             logger.error(f"Timeout error fetching {url}: {e}", exc_info=True)
             raise
         except requests.exceptions.HTTPError as e:
             logger.error(
                 f"HTTP error ({response.status_code}) fetching {url}: {e}", exc_info=True
             )
             raise
         except Exception as e:
             logger.error(f"Unexpected error fetching {url}: {e}", exc_info=True)
             raise
     ```

### Phase 2: Performance Optimization

More substantial improvements that require deeper changes:

1. **Implement Async Content Fetching**

   - Use `asyncio` and `aiohttp` for concurrent HTTP requests
   - Batch Wikipedia article fetches where possible
   - Maintain compatibility with existing synchronous code

1. **Add Comprehensive Response Caching**

   - Cache Wikipedia content responses with TTL
   - Cache article quality assessments
   - Implement disk-based cache for larger responses
   - Add cache invalidation based on revision IDs

1. **Improve Rate Limiting**

   - Implement adaptive rate limiting based on response headers
   - Use token bucket algorithm for more sophisticated rate control
   - Add backoff strategies for 429 responses

### Phase 3: Robustness Improvements

Advanced improvements that require significant changes:

1. **Enhance Content Extraction**

   - Add fallback parsers for different Wikipedia page structures
   - Consider using Wikipedia's API directly instead of scraping HTML
   - Implement better handling of edge cases (tables, images, references)

1. **Implement Circuit Breaker Pattern**

   - Add circuit breaker for Wikipedia API calls
   - Define different retry strategies for different types of failures
   - Implement graceful degradation when services are unavailable

1. **Optimize Memory Usage**

   - Implement streaming parsers for large Wikipedia responses
   - Use generators for processing large articles
   - Optimize memory usage during processing

## Testing Strategy

1. **Unit Tests**

   - Test connection pooling behavior
   - Test timeout handling with mock responses
   - Test caching implementation
   - Test error handling scenarios

1. **Integration Tests**

   - Test end-to-end Wikipedia fetching with real articles
   - Validate improvement in request efficiency
   - Test error recovery in realistic scenarios

1. **Performance Tests**

   - Measure response times before and after changes
   - Evaluate memory usage
   - Test under high concurrency

## Success Metrics

1. **Performance Improvements**

   - 30%+ reduction in average Wikipedia article fetch time
   - 50%+ improvement in concurrent article processing
   - Reduced memory usage during processing

1. **Reliability Improvements**

   - Reduced error rates during Wikipedia processing
   - Better recovery from transient failures
   - Improved error logging and diagnostics

1. **Code Quality Improvements**

   - More maintainable API integration code
   - Better separation of concerns
   - Improved testability

## References

- [Requests Session Objects](https://requests.readthedocs.io/en/latest/user/advanced/#session-objects)
- [Async HTTP Requests with aiohttp](https://docs.aiohttp.org/en/stable/)
- [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
- [Token Bucket Algorithm](https://en.wikipedia.org/wiki/Token_bucket)
- [Wikipedia API Documentation](https://www.mediawiki.org/wiki/API:Main_page)

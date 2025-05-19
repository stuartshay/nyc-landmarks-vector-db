# Active Context

## Current Focus

- Enhanced `process_wikipedia_articles.py` script with pagination and full processing capabilities
- Implemented `--all` option to process the entire database of landmarks
- Fixed issues with processing certain landmarks in `process_all_landmarks.py` script
- Implemented a more robust attribute access mechanism using a `safe_get_attribute()`
  helper function
- Resolved type checking errors and improved code reliability
- Refactored complex functions in the landmark processing pipeline to reduce complexity

## Recent Changes

- **Feature Enhancement**: Added `--page-size` parameter to `process_wikipedia_articles.py` to control the number of landmarks fetched per API request. This feature:
  - Makes the page size configurable (default: 100)
  - Allows optimizing API requests based on server load and network conditions
  - Provides better control over processing batches
  - Can be used to tune performance based on available resources
  - Supports parameter combinations like `--all --page-size 50` to process all landmarks with smaller batches
  - Can be combined with `--limit` as in `--all --page-size 50 --limit 5` to process a limited number of landmarks

- **Argument Validation**: Implemented mutual exclusivity between `--all` and `--page` parameters:
  - Used argparse's mutually exclusive group feature
  - Added clear error message when both parameters are used together
  - Enhanced help text to indicate incompatible arguments
  - Ensured proper validation to enforce supported usage patterns

- **Feature Enhancement**: Added `--all` parameter to `process_wikipedia_articles.py` to process the entire database. This feature:
  - Uses the `get_total_record_count()` method from `DbClient` to determine the total number of landmarks
  - Allows processing all available landmarks in a single run
  - Can be combined with `--limit` to process only a subset of the total records

- **Feature Enhancement**: Added `--page` parameter to `process_wikipedia_articles.py` to allow starting the landmark fetch from a specific page number. This enables:
  - Resuming failed processing runs from a specific page
  - Distributing processing workload across multiple runs
  - Processing specific subsets of landmarks by page number
  - Better control over which landmarks are processed

- **Code Fix**: Fixed Pyright error in `check_landmark_processing.py` by correctly
  formatting the file-level setting directive on its own line. The error "Pyright
  comments used to control file-level settings must appear on their own line" was
  resolved by ensuring the `# pyright: reportMissingImports=false` directive appears on
  its own line without other comments.

- **Bug Fix**: Fixed the "'LpcReportDetailResponse' object has no attribute 'get'" error
  in the landmark processing pipeline by implementing a safe attribute accessor that
  works with both dictionary-style objects and Pydantic models

- Created a reusable `safe_get_attribute()` function that abstracts away the differences
  between dictionary-style access and attribute access

- Fixed type annotation issues to properly handle both dictionary responses and Pydantic
  model objects

- Added enhanced error logging for problematic landmark IDs (LP-00048, LP-00112,
  LP-00012)

- Refactored complex functions into smaller, focused helper functions to reduce
  cognitive complexity:
  - Added `extract_landmark_id()` to cleanly handle ID extraction from different object
    types
  - Added `fetch_landmarks_page()` to centralize API request logic and error handling
  - Added `get_landmark_pdf_url()` to extract PDF URLs consistently
  - Added `create_chunk_metadata()` to standardize metadata generation
  - Added `generate_and_validate_embedding()` to handle embedding generation and
    validation

- Successfully processed previously failing landmarks with the updated code

## Active Decisions

- Added a new `--all` option to process all available landmarks in the database
- Integrated with the `DbClient.get_total_record_count()` method to determine the total number of landmarks
- Made `process_all` an optional parameter with a default value of `False` to maintain backward compatibility
- Ensured that `--all` respects the `--limit` option if provided (using the smaller of the two values)
- Added pagination support to `process_wikipedia_articles.py` to give more control over landmark processing
- Made `start_page` an optional parameter with a default value of 1 to maintain backward compatibility
- Updated functions to properly handle the new parameter throughout the processing pipeline
- Used a unified attribute access approach with the `safe_get_attribute()` function
  instead of maintaining separate code paths for different object types
- Improved type annotations to ensure proper static type checking
- Added better logging for debugging problematic landmark processing
- Enhanced robustness by handling both dictionary and object attribute access patterns
  consistently
- Adopted a modular approach to break down complex functions into smaller, more focused
  units with clear responsibilities

## Next Steps

- Implement better error handling for oversized Wikipedia articles (like The Ansonia - LP-00285) that exceed token limits
- Add automatic chunk size adjustment for large Wikipedia articles to prevent 400 errors
- Enhance the Wikipedia article fetcher to automatically split very large articles into smaller chunks
- Add additional filtering options to target specific types of landmarks or specific geographical areas
- Create a resumption capability to continue processing from where a previous run left off
- Implement smart retry logic for failed landmarks, with backoff strategies
- Continue monitoring landmark processing to ensure no new errors occur
- Consider applying similar robust attribute access patterns in other parts of the codebase
- Update test cases to verify both dictionary and object attribute access works as expected
- Consider adding additional error handling and recovery mechanisms to make processing even more robust
- Apply similar refactoring techniques to other complex functions in the codebase to improve maintainability
- Add additional validation for other command-line arguments to prevent conflicts

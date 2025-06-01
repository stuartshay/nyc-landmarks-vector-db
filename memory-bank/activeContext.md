# Active Context

## Current Focus

The current focus is on the Wikipedia Processing Script Refactoring & Metadata Enhancement Project. This involves refactoring the large `scripts/ci/process_wikipedia_articles.py` script (757 lines) into modular components while conducting comprehensive analysis of Wikipedia articles for metadata enhancement opportunities.

## Recent Changes

- **Added Wikipedia revision ID tracking**: Enhanced the Wikipedia fetcher and processor to track article revision IDs, providing better versioning and citation support for all Wikipedia content. This revision ID is now consistently propagated through the entire pipeline from fetching to storage in the vector database.
- **Fixed return type in `WikipediaFetcher.fetch_wikipedia_content`**: Updated the method to consistently return a tuple of (content, rev_id) for better error handling and type consistency.
- **Enhanced metadata in Wikipedia chunks**: Included revision IDs in chunk metadata to enable precise article version tracking for citations and updates.
- **Successfully implemented `nyc_landmarks/wikipedia/processor.py`**: Created the `WikipediaProcessor` class as planned in Phase 1 of the refactoring project, extracting core Wikipedia processing functionality from the main script.
- **Created Wikipedia package structure**: Established `nyc_landmarks/wikipedia/` directory with proper module organization.
- **Developed custom Wikipedia analysis script**: Implemented `scripts/analyze_wikipedia_article.py` to analyze individual Wikipedia articles and extract potential metadata attributes.
- **Added landmarks processing module**: Created `nyc_landmarks/landmarks/landmarks_processing.py` to support the refactoring effort.
- **Enhanced results reporting**: Added `nyc_landmarks/utils/results_reporter.py` for better statistics and reporting capabilities.
- **Created API Enhancement Analysis Script**: Added `scripts/analyze_api_enhancements.py` to test underutilized CoreDataStore APIs for Phase 2 of the Wikipedia refactoring project.
- **Fixed Package Version Synchronization Workflow**: Implemented `scripts/ci/sync_versions.sh` and updated GitHub Actions workflow to automatically sync package versions between requirements.txt and setup.py for Dependabot PRs.

## Next Steps

### Phase 1 Completion (Refactoring)

1. Complete extraction of utilities to `nyc_landmarks/wikipedia/utils.py`
1. Finalize results reporting module improvements
1. Streamline the main `scripts/ci/process_wikipedia_articles.py` script to target ~200 lines
1. Verify all functionality is preserved after refactoring

### Phase 2 Implementation (API Analysis)

1. Execute Wikipedia processing command with 25 landmarks to test refactored components
1. Test underutilized CoreDataStore APIs (photos, PLUTO data, building details)
1. Analyze metadata enhancement opportunities from API data
1. Generate comprehensive analysis dump file

### Phase 3 (Metadata Enhancement)

1. Integrate highest-value API enhancements
1. Implement improved metadata extraction patterns for Wikipedia content
1. Create enhanced metadata schema
1. Performance optimization

## Active Decisions and Considerations

### Refactoring Architecture

- Maintaining backward compatibility while improving modularity
- Ensuring no breaking changes to existing interfaces
- Preserving all existing functionality during the transition

### Metadata Enhancement Strategy

- Focus on non-intrusive enhancements that don't break current functionality
- Implement optional enhanced metadata collection that can be enabled/disabled
- Prioritize API integrations based on data quality and processing performance impact

### Testing and Validation

- Need to thoroughly test refactored components against original script behavior
- Validate that Wikipedia processing performance is maintained or improved
- Ensure proper error handling and logging throughout the refactored modules

## Current Challenges

- Balancing code modularity with maintaining existing functionality
- Managing the complexity of multiple API integrations while keeping performance optimal
- Ensuring comprehensive testing coverage for the refactored components
- Coordinating the phased approach to avoid disrupting existing workflows

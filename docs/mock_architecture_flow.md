# Mock Architecture Flow Documentation

## Overview

This document illustrates the mock architecture used in the NYC Landmarks Vector DB project to replace external dependencies during testing.

## Mock Flow Architecture

```mermaid
graph TD
    A[Integration Test] --> B{Use Mock?}
    B -->|Yes| C[create_mock_db_client()]
    B -->|No| D[Real db_client]

    C --> E[Mock DB Client]
    D --> F[Real CoreDataStore API]

    E --> G[Mock Wikipedia Articles]
    E --> H[Mock Landmark Details]
    E --> I[Mock Buildings Data]
    E --> J[Mock Metadata]

    F --> K[External API Calls]
    F --> L[Network Dependencies]
    F --> M[Timeout Risks]

    G --> N[Predictable Test Data]
    H --> N
    I --> N
    J --> N

    K --> O[Variable Results]
    L --> P[Test Instability]
    M --> P

    N --> Q[Fast, Reliable Tests]
    O --> R[Slow, Flaky Tests]
    P --> R

    style C fill:#90EE90
    style E fill:#90EE90
    style G fill:#90EE90
    style H fill:#90EE90
    style I fill:#90EE90
    style J fill:#90EE90
    style N fill:#90EE90
    style Q fill:#90EE90

    style D fill:#FFB6C1
    style F fill:#FFB6C1
    style K fill:#FFB6C1
    style L fill:#FFB6C1
    style M fill:#FFB6C1
    style O fill:#FFB6C1
    style P fill:#FFB6C1
    style R fill:#FFB6C1
```

## Mock Types and Use Cases

```mermaid
graph LR
    A[Mock Types] --> B[Standard Mock]
    A --> C[Error Mock]
    A --> D[Empty Response Mock]

    B --> B1[create_mock_db_client()]
    B --> B2[Normal Test Scenarios]
    B --> B3[Happy Path Testing]

    C --> C1[create_mock_db_client_with_errors()]
    C --> C2[Connection Errors]
    C --> C3[Timeout Scenarios]
    C --> C4[Invalid Data]

    D --> D1[create_mock_db_client_empty_responses()]
    D --> D2[No Data Found]
    D --> D3[Edge Cases]
    D --> D4[Boundary Testing]

    style B fill:#87CEEB
    style C fill:#FFA07A
    style D fill:#DDA0DD
```

## Wikipedia Integration Test Flow with Mocks

```mermaid
sequenceDiagram
    participant Test as Integration Test
    participant Mock as Mock DB Client
    participant Fetcher as Wikipedia Fetcher
    participant Embedder as Embedding Generator
    participant Pinecone as Pinecone DB

    Test->>Mock: get_wikipedia_articles("LP-00001")
    Mock-->>Test: [WikipediaArticleModel objects]

    Test->>Fetcher: process_wikipedia_article(article)
    Fetcher-->>Test: WikipediaContentModel with chunks

    Test->>Embedder: process_chunks(chunks)
    Embedder-->>Test: chunks_with_embeddings

    Test->>Pinecone: store_chunks(chunks, prefix, landmark_id)
    Pinecone-->>Test: vector_ids

    Test->>Pinecone: query_vectors(embedding, filters)
    Pinecone-->>Test: matching_vectors

    Test->>Test: Assert results match expectations
    Test->>Pinecone: cleanup_test_vectors(vector_ids)

    Note over Test,Pinecone: Mock eliminates external API dependency
    Note over Test,Pinecone: Predictable data ensures consistent results
```

## Mock Data Structure

```mermaid
classDiagram
    class MockDBClient {
        +get_wikipedia_articles(landmark_id) List~WikipediaArticleModel~
        +get_landmark_details(landmark_id) Optional~Any~
        +get_buildings_from_landmark_detail(landmark_id) List~LandmarkDetail~
        +get_landmark_metadata(landmark_id) Optional~LandmarkMetadata~
    }

    class WikipediaArticleModel {
        +id: Optional~int~
        +lpNumber: str
        +url: str
        +title: str
        +content: Optional~str~
        +recordType: str
    }

    class LandmarkDetail {
        +landmark_id: str
        +name: str
        +address: str
        +borough: str
    }

    class LandmarkMetadata {
        +landmark_id: str
        +name: str
        +architect: str
        +style: str
        +neighborhood: str
        +buildings: List~Dict~
    }

    MockDBClient --> WikipediaArticleModel
    MockDBClient --> LandmarkDetail
    MockDBClient --> LandmarkMetadata
```

## Benefits of Mock Architecture

```mermaid
mindmap
    root((Mock Benefits))
        Speed
            No Network Calls
            No API Delays
            Instant Response
        Reliability
            Predictable Data
            No External Failures
            Consistent Results
        Testing
            Error Simulation
            Edge Case Testing
            Boundary Conditions
        Development
            Offline Testing
            No API Keys Needed
            Independent Development
        Maintenance
            Easier Debugging
            Clear Test Intent
            Reduced Complexity
```

## Current Mock Implementation Status

```mermaid
graph TD
    A[Mock Implementation] --> B[✅ Mock Functions Created]
    A --> C[❌ Import Issues to Fix]
    A --> D[✅ Multiple Mock Types]
    A --> E[✅ Pytest Integration Ready]

    B --> B1[create_mock_db_client]
    B --> B2[create_mock_db_client_with_errors]
    B --> B3[create_mock_db_client_empty_responses]

    C --> C1[WikipediaArticleModel Import]
    C --> C2[Field Name Corrections]
    C --> C3[Module Path Issues]

    D --> D1[Standard Mock]
    D --> D2[Error Scenarios]
    D --> D3[Empty Responses]

    E --> E1[Fixture Functions]
    E --> E2[Direct Usage]
    E --> E3[Parameterized Tests]

    style B fill:#90EE90
    style D fill:#90EE90
    style E fill:#90EE90
    style C fill:#FFB6C1
```

## Next Steps for Mock Implementation

1. **Fix Import Issues**: Resolve WikipediaArticleModel import path
1. **Validate Field Names**: Ensure mock data matches actual model requirements
1. **Test Mock Integration**: Run tests with mocks to verify functionality
1. **Expand Mock Coverage**: Add more landmark IDs and scenarios
1. **Document Usage**: Create examples for different mock types

## Usage Examples

### Standard Mock Usage

```python
from tests.mocks import create_mock_db_client


def test_wikipedia_processing():
    mock_client = create_mock_db_client()
    articles = mock_client.get_wikipedia_articles("LP-00001")
    assert len(articles) > 0
```

### Error Testing

```python
from tests.mocks import create_mock_db_client_with_errors


def test_api_error_handling():
    mock_client = create_mock_db_client_with_errors()
    with pytest.raises(ConnectionError):
        mock_client.get_wikipedia_articles("LP-00001")
```

### Empty Response Testing

```python
from tests.mocks import create_mock_db_client_empty_responses


def test_no_data_scenario():
    mock_client = create_mock_db_client_empty_responses()
    articles = mock_client.get_wikipedia_articles("LP-99999")
    assert len(articles) == 0
```

# API Query Search Sequence Diagram

## Mermaid Sequence Diagram

This diagram shows the complete flow of logging for a POST request to `/api/query/search` with correlation ID propagation.

```mermaid
sequenceDiagram
    participant Client
    participant RequestContext as Request Context
    participant ReqBodyMW as Request Body Middleware
    participant PerfMW as Performance Middleware
    participant QueryAPI as Query API Endpoint
    participant Validation as Validation Logger
    participant EmbedGen as Embedding Generator
    participant VectorDB as Vector Database (Pinecone)
    participant Logger as Logging System

    Note over Client, Logger: POST /api/query/search Request Flow

    Client->>RequestContext: POST /api/query/search
    Note right of Client: Headers: X-Request-ID or auto-generated UUID

    RequestContext->>RequestContext: Setup request tracking
    RequestContext->>Logger: Log: Request context initialized

    RequestContext->>ReqBodyMW: Process request
    ReqBodyMW->>ReqBodyMW: Extract correlation_id from headers
    ReqBodyMW->>ReqBodyMW: Read & sanitize request body
    ReqBodyMW->>Logger: Log: POST request body logged
    Note right of Logger: correlation_id: abc-123<br/>endpoint: /api/query/search<br/>request_body: {...}

    ReqBodyMW->>PerfMW: Continue to performance middleware
    PerfMW->>PerfMW: Record start_time
    PerfMW->>PerfMW: Extract correlation_id
    PerfMW->>PerfMW: Categorize endpoint as "query"

    PerfMW->>QueryAPI: Route to search_text()
    QueryAPI->>QueryAPI: Extract client info (IP, User-Agent)

    QueryAPI->>Validation: validate_text_query()
    Validation->>Logger: Log: Validation check (query)
    Note right of Logger: correlation_id: abc-123<br/>validation_type: text_query

    QueryAPI->>Validation: validate_landmark_id()
    Validation->>Logger: Log: Validation check (landmark_id)

    QueryAPI->>Validation: validate_top_k()
    Validation->>Logger: Log: Validation check (top_k)

    QueryAPI->>Validation: validate_source_type()
    Validation->>Logger: Log: Validation check (source_type)

    QueryAPI->>Validation: log_validation_success()
    Validation->>Logger: Log: Valid API request processed
    Note right of Logger: correlation_id: abc-123<br/>validation_status: success<br/>request_data: {...}

    QueryAPI->>QueryAPI: Extract correlation_id = get_correlation_id(request)

    QueryAPI->>Logger: Log: Embedding generation start
    Note right of Logger: correlation_id: abc-123<br/>operation: embedding_generation<br/>query_text: "What is the history..."

    QueryAPI->>EmbedGen: generate_embedding(query.query)
    EmbedGen->>EmbedGen: Call OpenAI API
    EmbedGen->>QueryAPI: Return embedding vector

    QueryAPI->>Logger: Log: Embedding generation complete
    Note right of Logger: correlation_id: abc-123<br/>operation: embedding_generation_complete<br/>embedding_dimensions: 1536

    QueryAPI->>QueryAPI: Build filter_dict (source_type: "wikipedia")

    QueryAPI->>VectorDB: query_vectors(embedding, top_k=5, filter_dict, correlation_id)
    VectorDB->>Logger: Log: Vector query operation start
    Note right of Logger: correlation_id: abc-123<br/>operation: vector_query_start<br/>top_k: 5<br/>source_type: wikipedia

    VectorDB->>VectorDB: Execute Pinecone similarity search
    VectorDB->>VectorDB: Apply filters & return results

    VectorDB->>Logger: Log: Vector query operation complete
    Note right of Logger: correlation_id: abc-123<br/>operation: vector_query_complete<br/>results_count: 5

    VectorDB->>QueryAPI: Return search results

    QueryAPI->>QueryAPI: Process results & build response
    QueryAPI->>PerfMW: Return SearchResponse

    PerfMW->>PerfMW: Calculate duration_ms = (end_time - start_time) * 1000
    PerfMW->>Logger: Log: API request performance
    Note right of Logger: correlation_id: abc-123<br/>endpoint: POST /api/query/search<br/>duration_ms: 1250.5<br/>status_code: 200

    PerfMW->>Client: HTTP 200 + SearchResponse JSON

    Note over Client, Logger: All logs contain the same correlation_id for aggregation
```

## Log Aggregation Flow

```mermaid
graph TD
    A[Incoming Request] --> B{Has Correlation ID Header?}
    B -->|Yes| C[Extract from Header]
    B -->|No| D[Generate UUID4]
    C --> E[correlation_id = header_value]
    D --> E

    E --> F[Request Body Middleware]
    F --> G[Performance Middleware]
    G --> H[API Endpoint]
    H --> I[Validation Logger]
    H --> J[Embedding Generator]
    H --> K[Vector Database]

    F --> L[Log Entry 1]
    I --> M[Log Entry 2]
    I --> N[Log Entry 3]
    J --> O[Log Entry 4]
    J --> P[Log Entry 5]
    K --> Q[Log Entry 6]
    K --> R[Log Entry 7]
    G --> S[Log Entry 8]

    L --> T[All logs contain same correlation_id]
    M --> T
    N --> T
    O --> T
    P --> T
    Q --> T
    R --> T
    S --> T

    T --> U[Log Aggregation Query]
    U --> V[grep correlation_id logs/*.log]
    U --> W[jq '.correlation_id == "abc-123"' logs/*.json]
```

## Component Interaction Overview

```mermaid
graph LR
    subgraph "Middleware Layer"
        A[Request Context] --> B[Request Body Logging]
        B --> C[Performance Monitoring]
    end

    subgraph "API Layer"
        C --> D[Query Endpoint]
        D --> E[Input Validation]
    end

    subgraph "Business Logic"
        E --> F[Embedding Generation]
        F --> G[Vector Database Query]
    end

    subgraph "Logging System"
        H[Structured Logs]
        I[Correlation ID Tracking]
        J[Performance Metrics]
    end

    A -.-> H
    B -.-> H
    C -.-> H
    D -.-> H
    E -.-> H
    F -.-> H
    G -.-> H

    A -.-> I
    B -.-> I
    C -.-> I
    D -.-> I
    E -.-> I
    F -.-> I
    G -.-> I

    C -.-> J
    F -.-> J
    G -.-> J
```

## Correlation ID Lifecycle

```mermaid
stateDiagram-v2
    [*] --> HeaderCheck: Request Received
    HeaderCheck --> ExtractHeader: X-Request-ID found
    HeaderCheck --> ExtractHeader: X-Correlation-ID found
    HeaderCheck --> ExtractHeader: Request-ID found
    HeaderCheck --> ExtractHeader: Correlation-ID found
    HeaderCheck --> GenerateUUID: No correlation header

    ExtractHeader --> PropagateID: correlation_id = header_value
    GenerateUUID --> PropagateID: correlation_id = uuid4()

    PropagateID --> ReqBodyLog: Log request body
    PropagateID --> ValidationLog: Log validation
    PropagateID --> EmbeddingLog: Log embedding ops
    PropagateID --> VectorLog: Log vector ops
    PropagateID --> PerfLog: Log performance

    ReqBodyLog --> LogAggregation
    ValidationLog --> LogAggregation
    EmbeddingLog --> LogAggregation
    VectorLog --> LogAggregation
    PerfLog --> LogAggregation

    LogAggregation --> [*]: Request Complete
```

## Key Logging Points Summary

| Step | Component       | Log Message                        | Correlation ID |
| ---- | --------------- | ---------------------------------- | -------------- |
| 1    | Request Body MW | "POST request body logged"         | ✅             |
| 2    | Validation      | "Valid API request processed"      | ✅             |
| 3    | Query API       | "Generating embedding for query"   | ✅             |
| 4    | Query API       | "Embedding generation completed"   | ✅             |
| 5    | Vector DB       | "Starting vector query operation"  | ✅             |
| 6    | Vector DB       | "Vector query operation completed" | ✅             |
| 7    | Performance MW  | "API request completed"            | ✅             |

All log entries contain the same correlation ID, enabling complete request tracing and log aggregation.

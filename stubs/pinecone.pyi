"""Type stubs for Pinecone SDK"""

from typing import Any, Dict, List, Optional, TypedDict, Union

class NamespaceStats(TypedDict):
    """TypedDict for namespace statistics."""

    vector_count: int

class ServerlessSpec:
    """Specification for serverless Pinecone index."""

    def __init__(self, cloud: str, region: str) -> None: ...

class IndexStats:
    """Statistics about a Pinecone index."""

    dimension: int
    index_fullness: float
    total_vector_count: int
    namespaces: Dict[str, NamespaceStats]

class Match:
    """Match object returned from a query."""

    id: str
    score: float
    metadata: Optional[Dict[str, Any]]
    values: Optional[List[float]]

class QueryResponse:
    """Response from a query."""

    matches: List[Match]

class Index:
    """Pinecone index client."""

    def __init__(self, name: str) -> None: ...
    def describe_index_stats(self) -> IndexStats: ...
    def upsert(
        self, vectors: List[Dict[str, Any]], namespace: Optional[str] = None
    ) -> Dict[str, Any]: ...
    def delete(
        self,
        ids: Optional[List[str]] = None,
        filter: Optional[Dict[str, Any]] = None,
        namespace: Optional[str] = None,
        delete_all: Optional[bool] = None,
    ) -> Dict[str, Any]: ...
    def query(
        self,
        vector: List[float],
        top_k: int,
        include_metadata: bool = False,
        include_values: bool = False,
        namespace: Optional[str] = None,
        filter: Optional[Dict[str, Any]] = None,
    ) -> QueryResponse: ...

class IndexDefinition:
    """Definition of a Pinecone index."""

    name: str

class Pinecone:
    """Pinecone client."""

    def __init__(self, api_key: str) -> None: ...
    def list_indexes(self) -> List[IndexDefinition]: ...
    def Index(self, name: str) -> Index: ...
    def create_index(
        self,
        name: str,
        dimension: int,
        metric: str,
        spec: Optional[Union[ServerlessSpec, Any]] = None,
        **kwargs: Any,
    ) -> None: ...
    def delete_index(self, name: str) -> None: ...

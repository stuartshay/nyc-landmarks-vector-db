# Analysis: Code that can be moved/replaced from vector_utility.py to pinecone_db.py

## Summary
After analyzing both `scripts/vector_utility.py` and `nyc_landmarks/vectordb/pinecone_db.py`, I found several areas where code duplication exists and where functionality in the script could be replaced with calls to the PineconeDB class methods.

## Key Findings

### 1. Fetch Vector Functionality - REPLACEABLE ✅
**Current code in vector_utility.py:**
```python
def fetch_vector(vector_id: str, pretty_print: bool = False, namespace: Optional[str] = None):
    # Uses direct Pinecone SDK calls
    result = cast(TypeAny, index).fetch(
        ids=[vector_id],
        namespace=pinecone_db.namespace if pinecone_db.namespace else None,
    )
```

**Available in PineconeDB:**
```python
def fetch_vector_by_id(self, vector_id: str, namespace: Optional[str] = None) -> Optional[Dict[str, Any]]:
    # Already implements fetch functionality with query approach
```

**Recommendation:** Replace the entire `fetch_vector()` function in vector_utility.py with a call to `PineconeDB.fetch_vector_by_id()`.

### 2. Query Vectors by Landmark - REPLACEABLE ✅
**Current code in vector_utility.py:**
```python
def query_landmark_vectors(pinecone_db: PineconeDB, landmark_id: str, namespace: Optional[str] = None):
    # Direct index query
    query_response = pinecone_db.index.query(
        vector=[0.0] * dimension,
        filter={"landmark_id": landmark_id},
        top_k=100,
        include_metadata=True,
        namespace=pinecone_db.namespace if pinecone_db.namespace else None,
    )
```

**Available in PineconeDB:**
```python
def query_vectors_by_landmark(self, landmark_id: str, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
    # Same functionality already implemented
```

**Recommendation:** Replace `query_landmark_vectors()` with calls to `PineconeDB.query_vectors_by_landmark()`.

### 3. List Vectors with Filtering - REPLACEABLE ✅
**Current code in vector_utility.py:**
```python
def query_pinecone_index(pinecone_db: PineconeDB, limit: int, namespace: Optional[str] = None, prefix: Optional[str] = None):
    # Complex querying logic with prefix filtering
```

**Available in PineconeDB:**
```python
def list_vectors_with_filter(self, prefix: Optional[str] = None, limit: int = 10, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
    # Same functionality with prefix filtering
```

**Recommendation:** Replace the complex `query_pinecone_index()` and related filtering logic with `PineconeDB.list_vectors_with_filter()`.

### 4. Vector Validation - PARTIALLY REPLACEABLE ⚠️
**Current code in vector_utility.py:**
```python
def validate_vector_metadata(vector_data: Dict[str, Any], verbose: bool = False) -> bool:
    # Validation logic for metadata fields
```

**Available in PineconeDB:**
```python
def validate_vector_metadata(self, vector_id: str, namespace: Optional[str] = None) -> Tuple[bool, List[str]]:
    # More comprehensive validation with detailed error reporting
```

**Recommendation:** The PineconeDB version is more comprehensive. Replace the script version but adapt the return format to maintain backward compatibility.

### 5. Constants and Patterns - SHOULD BE CENTRALIZED 📝
**Current duplication:**
- `REQUIRED_METADATA` constants exist in both files
- `REQUIRED_WIKI_METADATA` constants exist in both files
- `PDF_ID_PATTERN` and `WIKI_ID_PATTERN` regex patterns exist in both files

**Recommendation:** Move these constants to a shared module or keep them in PineconeDB and import from there.

## Specific Refactoring Recommendations

### Phase 1: Replace Core Functionality
1. **Replace fetch_vector()**: Use `PineconeDB.fetch_vector_by_id()`
2. **Replace query_landmark_vectors()**: Use `PineconeDB.query_vectors_by_landmark()`
3. **Replace list_vectors()**: Use `PineconeDB.list_vectors_with_filter()`

### Phase 2: Improve Validation
1. **Replace validate_vector_metadata()**: Use `PineconeDB.validate_vector_metadata()` but adapt output format
2. **Centralize constants**: Move validation constants to PineconeDB or shared module

### Phase 3: Simplify Setup
1. **Consolidate setup_pinecone_client()**: This can be simplified since PineconeDB handles initialization

## Code that CANNOT be easily replaced
1. **Command-line argument parsing**: Script-specific CLI handling
2. **Pretty printing functions**: Display formatting logic specific to the utility
3. **Batch processing logic**: Some of the batch verification logic is script-specific
4. **Main() function and CLI setup**: Script entry point and argument handling

## Benefits of Refactoring
1. **Reduced code duplication**: Eliminate ~300 lines of duplicate functionality
2. **Consistent behavior**: Single source of truth for vector operations
3. **Better error handling**: PineconeDB methods have more robust error handling
4. **Easier maintenance**: Changes to vector operations only need to be made in one place
5. **Type safety**: PineconeDB methods have better type annotations

## Estimated Impact
- **Lines of code reduction**: ~300-400 lines
- **Maintainability improvement**: High
- **Risk level**: Low (functions are well-encapsulated)
- **Testing required**: Medium (verify CLI behavior matches)

# NYC Landmarks Vector Database - Research Items

This document tracks technology, tools, and approaches that require deeper investigation
before implementation decisions are made.

## Pinecone Assistant MCP Server

### Overview

- GitHub: https://github.com/pinecone-io/assistant-mcp
- Provides an MCP server implementation for retrieving information from Pinecone
  Assistant
- Supports multiple results retrieval with configurable result count
- Docker-based deployment with environment variable configuration

### Requirements

- Pinecone API key (already in use in our project)
- Pinecone Assistant API host - obtained after creating an Assistant in Pinecone Console
- Docker for deployment

### Potential Benefits

- Enhanced retrieval capabilities beyond raw vector search
- Simplified query interface for complex search operations
- Future-proofing as Pinecone evolves their offerings

### Open Questions

- How does Pinecone Assistant differ from the core Pinecone vector database we're
  currently using?
- What would be required to migrate our current vector data to work with Pinecone
  Assistant?
- Does Pinecone Assistant support all the metadata filtering capabilities we currently
  leverage?
- Would integration require significant refactoring of our query API?
- What are the pricing implications of using Pinecone Assistant vs. core Pinecone?

### Next Steps

- Set up a test project to evaluate functionality with a subset of our data
- Determine API compatibility with our current query patterns
- Develop a proof-of-concept integration to assess effort and benefits

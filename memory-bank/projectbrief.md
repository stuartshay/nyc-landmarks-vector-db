# NYC Landmarks Vector Database - Project Brief

## Project Overview

This project aims to create a vector database of New York City landmarks by extracting
text from PDF reports associated with each landmark, converting that text into vector
embeddings, and storing those embeddings in a vector database (Pinecone). This will
enable semantic search and the creation of a chatbot that can answer questions about NYC
landmarks.

## Core Requirements

1. Extract text from PDF reports stored in Azure Blob Storage
1. Process and chunk the text for optimal embedding
1. Generate embeddings using OpenAI's embedding models
1. Store embeddings in Pinecone vector database
1. Create API endpoints for vector search and chat functionality
1. Enable conversation memory for the chatbot
1. Support filtering by landmark ID
1. Integrate with CoreDataStore API exclusively as the data source
1. Integrate Wikipedia articles associated with landmarks into the vector database
1. Enable combined search across both PDF reports and Wikipedia content

## Key Goals

- Create a system that can answer detailed questions about NYC landmarks
- Enable semantic search across the landmark documentation and associated Wikipedia
  articles
- Build a foundation for a conversational AI about NYC landmarks
- Create a scalable, maintainable architecture for the system
- Implement secure credential management using Google Cloud Secret Store
- Set up CI/CD pipeline using GitHub Actions
- Integrate multiple data sources (PDF reports and Wikipedia) to enhance information
  quality
- Provide proper source attribution in search results and chat responses

## Success Criteria

- Successfully extract and process text from PDF reports
- Generate high-quality embeddings for all landmark documents
- Fetch, process, and store Wikipedia article content for landmarks
- Store embeddings in Pinecone with appropriate metadata for source attribution
- Create functional API endpoints for querying the vector database
- Enable chatbot functionality with conversation memory
- Implement secure credential management
- Document the system thoroughly
- Provide clear source attribution to distinguish PDF content from Wikipedia content

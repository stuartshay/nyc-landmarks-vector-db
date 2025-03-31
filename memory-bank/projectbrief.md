# NYC Landmarks Vector Database - Project Brief

## Project Overview
This project aims to create a vector database of New York City landmarks by extracting text from PDF reports associated with each landmark, converting that text into vector embeddings, and storing those embeddings in a vector database (Pinecone). This will enable semantic search and the creation of a chatbot that can answer questions about NYC landmarks.

## Core Requirements
1. Extract text from PDF reports stored in Azure Blob Storage
2. Process and chunk the text for optimal embedding
3. Generate embeddings using OpenAI's embedding models
4. Store embeddings in Pinecone vector database
5. Create API endpoints for vector search and chat functionality
6. Enable conversation memory for the chatbot
7. Support filtering by landmark ID
8. Integrate with existing Postgres database and REST API

## Key Goals
- Create a system that can answer detailed questions about NYC landmarks
- Enable semantic search across the landmark documentation
- Build a foundation for a conversational AI about NYC landmarks
- Create a scalable, maintainable architecture for the system
- Implement secure credential management using Google Cloud Secret Store
- Set up CI/CD pipeline using GitHub Actions

## Success Criteria
- Successfully extract and process text from PDF reports
- Generate high-quality embeddings for all landmark documents
- Store embeddings in Pinecone with appropriate metadata
- Create functional API endpoints for querying the vector database
- Enable chatbot functionality with conversation memory
- Implement secure credential management
- Document the system thoroughly

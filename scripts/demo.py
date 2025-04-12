#!/usr/bin/env python
"""
Demonstration script for NYC Landmarks Vector Database.

This script demonstrates the end-to-end process of:
1. Extracting text from a landmark PDF
2. Chunking the text
3. Generating embeddings
4. Storing embeddings in Pinecone
5. Performing a vector search
6. Using the chatbot functionality
"""

import argparse
import logging
import os
import sys
import time
from pprint import pprint
from typing import Any, Dict, List, Optional

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nyc_landmarks.chat.conversation import Conversation
from nyc_landmarks.config.settings import settings
from nyc_landmarks.db.db_client import DbClient
from nyc_landmarks.embeddings.generator import EmbeddingGenerator
from nyc_landmarks.pdf.extractor import PDFExtractor
from nyc_landmarks.pdf.text_chunker import TextChunker
from nyc_landmarks.vectordb.pinecone_db import PineconeDB

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL.value,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def demo_pdf_extraction(landmark_id: str) -> Dict[str, Any]:
    """Demonstrate PDF extraction.

    Args:
        landmark_id: ID of the landmark to process

    Returns:
        Dictionary with extraction results
    """
    print("\n=== PDF EXTRACTION DEMO ===\n")

    pdf_extractor = PDFExtractor()
    result = pdf_extractor.process_landmark_pdf(landmark_id)

    if result.get("success"):
        text = result.get("text", "")
        print(f"Successfully extracted text from PDF for landmark {landmark_id}")
        print(f"Text length: {len(text)} characters")
        print(f"First 500 characters:\n{text[:500]}...\n")
    else:
        error = result.get("error", "Unknown error")
        print(f"Failed to extract text from PDF for landmark {landmark_id}: {error}")

    return result


def demo_text_chunking(text: str, landmark_id: str) -> List[Dict[str, Any]]:
    """Demonstrate text chunking.

    Args:
        text: Text to chunk
        landmark_id: ID of the landmark

    Returns:
        List of chunk dictionaries
    """
    print("\n=== TEXT CHUNKING DEMO ===\n")

    text_chunker = TextChunker()
    db_client = DbClient()

    # Get landmark metadata
    landmark = db_client.get_landmark_by_id(landmark_id)
    landmark_metadata = {
        "landmark_id": landmark_id,
        "name": landmark.get("name", "") if landmark else "",
        "location": landmark.get("location", "") if landmark else "",
        "borough": landmark.get("borough", "") if landmark else "",
        "type": landmark.get("type", "") if landmark else "",
        "designation_date": (
            str(landmark.get("designation_date", "")) if landmark else ""
        ),
    }

    # Chunk text
    chunks = text_chunker.process_landmark_text(
        text=text,
        landmark_id=landmark_id,
        additional_metadata=landmark_metadata,
    )

    print(f"Generated {len(chunks)} chunks from text")

    if chunks:
        first_chunk = chunks[0]
        print(f"\nSample chunk:")
        print(f"Text: {first_chunk['text'][:200]}...")
        print(f"Metadata: {first_chunk['metadata']}")
        print(f"Token count: {first_chunk['metadata']['token_count']}")

    return chunks


def demo_embedding_generation(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Demonstrate embedding generation.

    Args:
        chunks: List of text chunks

    Returns:
        List of chunks with embeddings
    """
    print("\n=== EMBEDDING GENERATION DEMO ===\n")

    embedding_generator = EmbeddingGenerator()

    # Process first chunk only for demo purposes
    print("Processing first chunk for demo purposes...")
    demo_chunks = [chunks[0]]
    processed_chunks = embedding_generator.process_chunks(demo_chunks)

    print(f"Generated embeddings for {len(processed_chunks)} chunks")

    if processed_chunks:
        first_chunk = processed_chunks[0]
        print(f"\nSample embedding:")
        print(f"Embedding dimensions: {len(first_chunk['embedding'])}")
        print(f"First 5 embedding values: {first_chunk['embedding'][:5]}")

    return processed_chunks


def demo_vector_storage(
    chunks_with_embeddings: List[Dict[str, Any]], landmark_id: str
) -> List[str]:
    """Demonstrate vector storage in Pinecone.

    Args:
        chunks_with_embeddings: List of chunks with embeddings
        landmark_id: ID of the landmark

    Returns:
        List of stored vector IDs
    """
    print("\n=== VECTOR STORAGE DEMO ===\n")

    vector_db = PineconeDB()

    # Delete existing vectors for this landmark
    print(f"Deleting existing vectors for landmark {landmark_id}...")
    vector_db.delete_by_metadata({"landmark_id": landmark_id})

    # Store vectors
    print("Storing vectors in Pinecone...")
    vector_ids = vector_db.store_chunks(
        chunks_with_embeddings, id_prefix=f"{landmark_id}-demo-"
    )

    print(f"Stored {len(vector_ids)} vectors in Pinecone")

    if vector_ids:
        print(f"Sample vector ID: {vector_ids[0]}")

    # Get index stats
    stats = vector_db.get_index_stats()
    print(f"\nIndex stats: {stats}")

    return vector_ids


def demo_vector_search(
    query: str, landmark_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Demonstrate vector search.

    Args:
        query: Search query
        landmark_id: Optional landmark ID filter

    Returns:
        List of search results
    """
    print("\n=== VECTOR SEARCH DEMO ===\n")

    embedding_generator = EmbeddingGenerator()
    vector_db = PineconeDB()
    db_client = DbClient()

    print(f"Searching for: {query}")

    # Generate query embedding
    query_embedding = embedding_generator.generate_embedding(query)

    # Prepare filter if landmark_id is provided
    filter_dict = None
    if landmark_id:
        filter_dict = {"landmark_id": landmark_id}
        print(f"Filtering by landmark_id: {landmark_id}")

    # Perform vector search
    matches = vector_db.query_vectors(query_embedding, top_k=3, filter_dict=filter_dict)

    print(f"Found {len(matches)} matches")

    # Process matches
    results = []
    for i, match in enumerate(matches):
        text = match.metadata.get("text", "")
        match_landmark_id = match.metadata.get("landmark_id", "")
        score = match.score

        # Get landmark name from PostgreSQL if available
        landmark_name = None
        landmark = postgres_db.get_landmark_by_id(match_landmark_id)
        if landmark:
            landmark_name = landmark.get("name")

        # Create result
        result = {
            "text": text[:200] + "..." if len(text) > 200 else text,
            "score": score,
            "landmark_id": match_landmark_id,
            "landmark_name": landmark_name,
        }

        results.append(result)

        print(f"\nMatch {i+1}:")
        print(f"Score: {score}")
        print(f"Landmark: {landmark_name} (ID: {match_landmark_id})")
        print(f"Text: {text[:200]}...")

    return results


def demo_chat(query: str, landmark_id: Optional[str] = None) -> Dict[str, Any]:
    """Demonstrate chat functionality.

    Args:
        query: User query
        landmark_id: Optional landmark ID filter

    Returns:
        Dictionary with chat response
    """
    print("\n=== CHAT DEMO ===\n")

    # This is a simplified version of the chat endpoint logic
    embedding_generator = EmbeddingGenerator()
    vector_db = PineconeDB()
    postgres_db = PostgresDB()

    # Create conversation
    conversation = Conversation()

    # Add system message
    system_message = (
        "You are a knowledgeable assistant that specializes in New York City landmarks. "
        "Your responses should be informative, accurate, and based on the information "
        "provided in the landmark reports and database."
    )
    conversation.add_message("system", system_message)

    # Add user query
    conversation.add_message("user", query)

    print(f"User query: {query}")

    # Get relevant context from vector database
    context_text = ""
    sources = []

    # Generate embedding for the query
    query_embedding = embedding_generator.generate_embedding(query)

    # Prepare filter if landmark_id is provided
    filter_dict = None
    if landmark_id:
        filter_dict = {"landmark_id": landmark_id}
        print(f"Filtering by landmark_id: {landmark_id}")

    # Query the vector database
    matches = vector_db.query_vectors(query_embedding, top_k=3, filter_dict=filter_dict)

    # Process matches to create context
    for i, match in enumerate(matches):
        text = match.metadata.get("text", "")
        match_landmark_id = match.metadata.get("landmark_id", "")
        score = match.score

        # Only use matches with a reasonable similarity score
        if score < 0.7:
            continue

        # Add to context text
        context_text += f"\nContext {i+1}:\n{text}\n"

        # Get landmark name from PostgreSQL if available
        landmark_name = None
        landmark = postgres_db.get_landmark_by_id(match_landmark_id)
        if landmark:
            landmark_name = landmark.get("name")

        # Add to sources
        source = {
            "text": text[:200] + "..." if len(text) > 200 else text,
            "landmark_id": match_landmark_id,
            "landmark_name": landmark_name,
            "score": score,
        }
        sources.append(source)

    print(f"\nFound {len(sources)} relevant context sources")

    # In a real implementation, we would use OpenAI API to generate a response
    # For demo purposes, we'll just create a mock response
    mock_response = (
        f"This is a mock response to the query: {query}\n\n"
        f"In a real implementation, I would use the OpenAI API to generate a response "
        f"based on the {len(sources)} relevant context sources found in the vector database."
    )

    if sources:
        mock_response += f"\n\nHere's an excerpt from the most relevant source:\n\n"
        mock_response += sources[0]["text"]

    # Add assistant response to conversation
    conversation.add_message("assistant", mock_response)

    print(f"\nMock assistant response: {mock_response}")

    # Create and return response
    response = {
        "conversation_id": conversation.conversation_id,
        "response": mock_response,
        "sources": sources,
    }

    return response


def main():
    """Main entry point for the demo script."""
    parser = argparse.ArgumentParser(
        description="Demonstrate NYC Landmarks Vector Database functionality"
    )

    # Add command-line arguments
    parser.add_argument(
        "--landmark-id",
        default="LPC-123",  # Replace with a valid landmark ID in your database
        help="ID of the landmark to process",
    )

    parser.add_argument(
        "--query",
        default="Tell me about the architectural style of this landmark",
        help="Search query or chat question",
    )

    # Parse arguments
    args = parser.parse_args()

    # Run demonstration
    try:
        print("\n=== NYC LANDMARKS VECTOR DATABASE DEMONSTRATION ===\n")
        print(f"Using landmark ID: {args.landmark_id}")
        print(f"Using query: {args.query}")

        # Step 1: Extract text from PDF
        pdf_result = demo_pdf_extraction(args.landmark_id)

        if not pdf_result.get("success"):
            print("PDF extraction failed, cannot continue with demonstration")
            return

        # Step 2: Chunk text
        text = pdf_result.get("text", "")
        chunks = demo_text_chunking(text, args.landmark_id)

        if not chunks:
            print("Text chunking failed, cannot continue with demonstration")
            return

        # Step 3: Generate embeddings
        chunks_with_embeddings = demo_embedding_generation(chunks)

        if not chunks_with_embeddings:
            print("Embedding generation failed, cannot continue with demonstration")
            return

        # Step 4: Store vectors in Pinecone
        vector_ids = demo_vector_storage(chunks_with_embeddings, args.landmark_id)

        if not vector_ids:
            print("Vector storage failed, cannot continue with demonstration")
            return

        # Step 5: Perform vector search
        results = demo_vector_search(args.query, args.landmark_id)

        # Step 6: Demonstrate chat
        chat_response = demo_chat(args.query, args.landmark_id)

        print("\n=== DEMONSTRATION COMPLETE ===\n")

    except Exception as e:
        print(f"Error during demonstration: {e}")


if __name__ == "__main__":
    main()

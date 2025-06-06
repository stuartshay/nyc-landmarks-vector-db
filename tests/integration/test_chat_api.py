"""
Unit tests for Chat API functionality.

This module tests the chat API endpoints, response generation, and conversation management.
"""

from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from openai.types.chat import ChatCompletionMessage
from openai.types.chat.chat_completion import Choice

from nyc_landmarks.chat.conversation import Conversation
from nyc_landmarks.main import app


@pytest.fixture
def test_client() -> TestClient:
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def mock_conversation() -> Conversation:
    """Create a mock conversation for testing."""
    conversation = Conversation(conversation_id="test-id")
    conversation.add_message("system", "System message")
    conversation.add_message("user", "User message")
    conversation.add_message("assistant", "Assistant response")
    return conversation


@pytest.fixture
def mock_pinecone_match() -> Any:
    """Create a mock pinecone match result."""

    class MockMatch:
        def __init__(self, id: str, score: float, metadata: dict) -> None:
            self.id = id
            self.score = score
            self.metadata = metadata

    return MockMatch(
        id="LP-00001-chunk-0",
        score=0.89,
        metadata={
            "landmark_id": "LP-00001",
            "text": "This is sample text about a landmark in NYC.",
            "chunk_index": 0,
            "source": "landmark_report",
        },
    )


class MockChatCompletion:
    """Mock for OpenAI ChatCompletion."""

    def __init__(self, content: str = "This is a test response") -> None:
        self.choices = [
            Choice(
                index=0,
                message=ChatCompletionMessage(role="assistant", content=content),
                finish_reason="stop",
            )
        ]


class TestChatAPI:
    """Test cases for the Chat API."""

    @pytest.mark.integration
    @patch("nyc_landmarks.api.chat.conversation_store")
    @patch("nyc_landmarks.api.chat.openai.chat.completions.create")
    @patch("nyc_landmarks.api.chat.PineconeDB")
    @patch("nyc_landmarks.api.chat.EmbeddingGenerator")
    @patch("nyc_landmarks.api.chat.DbClient")
    def test_chat_message_new_conversation(
        self,
        mock_db_client: Any,
        mock_embedding_generator: Any,
        mock_pinecone_db: Any,
        mock_openai_create: Any,
        mock_conv_store: Any,
        test_client: TestClient,
        mock_conversation: Conversation,
    ) -> None:
        """Test chat_message endpoint with a new conversation."""
        # Setup mocks
        mock_conv_store.get_conversation.return_value = None
        mock_conv_store.create_conversation.return_value = mock_conversation

        mock_embedding_generator.return_value.generate_embedding.return_value = [
            0.1
        ] * 1536
        mock_pinecone_db.return_value.query_vectors.return_value = []
        mock_openai_create.return_value = MockChatCompletion("Test response")

        # Test
        response = test_client.post(
            "/api/chat/message",
            json={"message": "Hello, what can you tell me about NYC landmarks?"},
        )

        # Assert
        assert response.status_code == 200
        assert "conversation_id" in response.json()
        assert response.json()["response"] == "Test response"
        assert mock_conv_store.create_conversation.called
        assert mock_embedding_generator.return_value.generate_embedding.called
        assert mock_pinecone_db.return_value.query_vectors.called
        assert mock_openai_create.called

    @pytest.mark.integration
    @patch("nyc_landmarks.api.chat.conversation_store")
    @patch("nyc_landmarks.api.chat.openai.chat.completions.create")
    @patch("nyc_landmarks.api.chat.PineconeDB")
    @patch("nyc_landmarks.api.chat.EmbeddingGenerator")
    @patch("nyc_landmarks.api.chat.DbClient")
    def test_chat_message_existing_conversation(
        self,
        mock_db_client: Any,
        mock_embedding_generator: Any,
        mock_pinecone_db: Any,
        mock_openai_create: Any,
        mock_conv_store: Any,
        test_client: TestClient,
        mock_conversation: Conversation,
    ) -> None:
        """Test chat_message endpoint with an existing conversation."""
        # Setup mocks
        mock_conv_store.get_conversation.return_value = mock_conversation

        mock_embedding_generator.return_value.generate_embedding.return_value = [
            0.1
        ] * 1536
        mock_pinecone_db.return_value.query_vectors.return_value = []
        mock_openai_create.return_value = MockChatCompletion("Follow-up response")

        # Test
        response = test_client.post(
            "/api/chat/message",
            json={
                "message": "Tell me more about that landmark.",
                "conversation_id": "test-id",
            },
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["conversation_id"] == "test-id"
        assert response.json()["response"] == "Follow-up response"
        assert not mock_conv_store.create_conversation.called
        assert mock_conv_store.get_conversation.called
        assert mock_embedding_generator.return_value.generate_embedding.called
        assert mock_pinecone_db.return_value.query_vectors.called
        assert mock_openai_create.called

    @pytest.mark.integration
    @patch("nyc_landmarks.api.chat.conversation_store")
    @patch("nyc_landmarks.api.chat.openai.chat.completions.create")
    @patch("nyc_landmarks.api.chat.PineconeDB")
    @patch("nyc_landmarks.api.chat.EmbeddingGenerator")
    @patch("nyc_landmarks.api.chat.DbClient")
    def test_chat_message_with_landmark_filter(
        self,
        mock_db_client: Any,
        mock_embedding_generator: Any,
        mock_pinecone_db: Any,
        mock_openai_create: Any,
        mock_conv_store: Any,
        test_client: TestClient,
        mock_conversation: Conversation,
        mock_pinecone_match: Any,
    ) -> None:
        """Test chat_message endpoint with landmark filtering."""
        # Setup mocks
        mock_conv_store.get_conversation.return_value = None
        mock_conv_store.create_conversation.return_value = mock_conversation

        mock_embedding_generator.return_value.generate_embedding.return_value = [
            0.1
        ] * 1536
        mock_pinecone_db.return_value.query_vectors.return_value = [mock_pinecone_match]

        # Mock the landmark data from db client
        mock_db_client.return_value.get_landmark_by_id.return_value = {
            "name": "Test Landmark"
        }

        mock_openai_create.return_value = MockChatCompletion(
            "This is information about Test Landmark."
        )

        # Use FastAPI dependency overrides to inject the mock db_client
        from nyc_landmarks.api.chat import get_db_client
        from nyc_landmarks.main import app as fastapi_app

        fastapi_app.dependency_overrides[get_db_client] = (
            lambda: mock_db_client.return_value
        )

        try:
            # Test
            response = test_client.post(
                "/api/chat/message",
                json={
                    "message": "Tell me about this landmark.",
                    "landmark_id": "LP-00001",
                },
            )

            # Assert
            assert response.status_code == 200
            assert "conversation_id" in response.json()
            assert (
                response.json()["response"]
                == "This is information about Test Landmark."
            )
            assert response.json()["landmark_id"] == "LP-00001"
            assert len(response.json()["sources"]) == 1
            assert response.json()["sources"][0]["landmark_id"] == "LP-00001"
            # Check if filter_dict was included in the query_vectors call
            call_kwargs = mock_pinecone_db.return_value.query_vectors.call_args[1]
            assert call_kwargs.get("filter_dict") == {"landmark_id": "LP-00001"}

            # The get_landmark_by_id should be called because the mock_pinecone_match
            # has landmark_id "LP-00001" in its metadata, which triggers _get_landmark_name
            mock_db_client.return_value.get_landmark_by_id.assert_called_with(
                "LP-00001"
            )
        finally:
            fastapi_app.dependency_overrides = {}

    @patch("nyc_landmarks.api.chat.conversation_store")
    def test_get_conversation_history(
        self,
        mock_conv_store: Any,
        test_client: TestClient,
        mock_conversation: Conversation,
    ) -> None:
        """Test get_conversation_history endpoint."""
        # Setup mocks
        mock_conv_store.get_conversation.return_value = mock_conversation

        # Test
        response = test_client.get("/api/chat/conversations/test-id")

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert "messages" in response_data
        assert len(response_data["messages"]) == 2  # Excludes system message
        assert response_data["messages"][0]["role"] == "user"
        assert response_data["messages"][1]["role"] == "assistant"

    @patch("nyc_landmarks.api.chat.conversation_store")
    def test_get_conversation_history_not_found(
        self, mock_conv_store: Any, test_client: TestClient
    ) -> None:
        """Test get_conversation_history with non-existent conversation."""
        # Setup mocks
        mock_conv_store.get_conversation.return_value = None

        # Test
        response = test_client.get("/api/chat/conversations/nonexistent-id")

        # Assert
        assert response.status_code == 404
        assert "Conversation not found" in response.json()["detail"]

    @patch("nyc_landmarks.api.chat.conversation_store")
    def test_delete_conversation(
        self, mock_conv_store: Any, test_client: TestClient
    ) -> None:
        """Test delete_conversation endpoint."""
        # Setup mocks
        mock_conv_store.delete_conversation.return_value = True

        # Test
        response = test_client.delete("/api/chat/conversations/test-id")

        # Assert
        assert response.status_code == 200
        assert response.json()["success"] is True
        mock_conv_store.delete_conversation.assert_called_with("test-id")

    @patch("nyc_landmarks.api.chat.conversation_store")
    def test_delete_conversation_not_found(
        self, mock_conv_store: Any, test_client: TestClient
    ) -> None:
        """Test delete_conversation with non-existent conversation."""
        # Setup mocks
        mock_conv_store.delete_conversation.return_value = False

        # Test
        response = test_client.delete("/api/chat/conversations/nonexistent-id")

        # Assert
        assert response.status_code == 404
        assert "Conversation not found" in response.json()["detail"]

    @pytest.mark.integration
    @patch("nyc_landmarks.api.chat.openai.chat.completions.create")
    @patch("nyc_landmarks.api.chat.conversation_store")
    @patch("nyc_landmarks.api.chat.EmbeddingGenerator")
    @patch("nyc_landmarks.api.chat.PineconeDB")
    @patch("nyc_landmarks.api.chat.DbClient")
    def test_openai_error_handling(
        self,
        mock_db_client: Any,
        mock_pinecone_db: Any,
        mock_embedding_generator: Any,
        mock_conv_store: Any,
        mock_openai_create: Any,
        test_client: TestClient,
        mock_conversation: Conversation,
    ) -> None:
        """Test error handling for OpenAI API errors."""
        # Setup mocks
        mock_conv_store.get_conversation.return_value = None
        mock_conv_store.create_conversation.return_value = mock_conversation

        # Setup embedding generator mock to return valid embeddings
        mock_embedding_generator.return_value.generate_embedding.return_value = [
            0.1
        ] * 1536

        # Setup Pinecone mock to return empty results
        mock_pinecone_db.return_value.query_vectors.return_value = []

        # Setup OpenAI error
        mock_openai_create.side_effect = Exception("OpenAI API error")

        # Test
        response = test_client.post(
            "/api/chat/message",
            json={"message": "Hello, what can you tell me about NYC landmarks?"},
        )

        # Assert
        assert response.status_code == 500
        assert "OpenAI API error" in response.json()["detail"]

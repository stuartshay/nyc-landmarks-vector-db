"""
Pydantic models for Wikipedia article data used in NYC Landmarks Vector Database.

This module contains data models for Wikipedia articles associated with landmarks,
including their metadata, quality assessments, and processing information.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class WikipediaQualityModel(BaseModel):
    """
    Model representing a Wikipedia article quality assessment.

    This model captures the quality assessment of a Wikipedia article,
    including the quality prediction and probability scores for each
    quality level (FA, GA, B, C, Start, Stub).
    """

    model_config = ConfigDict(from_attributes=True)

    prediction: str = Field(
        ..., description="Quality prediction (FA, GA, B, C, Start, Stub)"
    )
    probabilities: Dict[str, float] = Field(
        ..., description="Probability for each quality level"
    )
    rev_id: str = Field(..., description="Wikipedia revision ID")

    def get_quality_description(self) -> str:
        """Return a human-readable description of the quality level."""
        descriptions = {
            "FA": "Featured Article - Wikipedia's highest quality designation",
            "GA": "Good Article - High quality article that meets the Good Article criteria",
            "B": "B-Class - Mostly complete with no major issues",
            "C": "C-Class - Substantial article with room for improvement",
            "Start": "Start-Class - Basic information but significant expansion needed",
            "Stub": "Stub-Class - Very basic information, significant expansion needed",
        }

        return descriptions.get(
            self.prediction, f"Unknown quality level: {self.prediction}"
        )


class WikipediaArticleModel(BaseModel):
    """
    Model representing a Wikipedia article associated with a landmark.

    This model captures the essential fields of a Wikipedia article including
    its ID, URL, title, associated landmark ID, and revision ID.
    """

    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = Field(
        None, description="Unique identifier for the article record"
    )
    lpNumber: str = Field(
        ..., description="Landmark Preservation Commission identifier"
    )
    url: str = Field(..., description="URL to the Wikipedia article")
    title: str = Field(..., description="Title of the Wikipedia article")
    content: Optional[str] = Field(
        None, description="Full content of the Wikipedia article"
    )
    recordType: str = Field("Wikipedia", description="Type of record")
    rev_id: Optional[str] = Field(
        None, description="Wikipedia revision ID for version tracking"
    )

    @field_validator("url", mode="after")  # pyright: ignore[misc] # type: ignore
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate that URL is properly formatted."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must be a valid HTTP or HTTPS URL")
        return v


class WikipediaContentModel(BaseModel):
    """
    Model representing the content of a Wikipedia article.

    This model stores both the raw content of the article and
    its processed chunks ready for embedding.
    """

    model_config = ConfigDict(from_attributes=True)

    lpNumber: str = Field(
        ..., description="Landmark Preservation Commission identifier"
    )
    url: str = Field(..., description="URL to the Wikipedia article")
    title: str = Field(..., description="Title of the Wikipedia article")
    content: str = Field(..., description="Raw content of the Wikipedia article")
    chunks: Optional[List[Dict[str, Any]]] = Field(
        None, description="Processed text chunks for embedding"
    )
    rev_id: Optional[str] = Field(
        None, description="Wikipedia revision ID for version tracking"
    )
    quality: Optional[WikipediaQualityModel] = Field(
        None, description="Quality assessment of the article"
    )

    @field_validator("url", mode="after")  # pyright: ignore[misc] # type: ignore
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate that URL is properly formatted."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must be a valid HTTP or HTTPS URL")
        return v


class WikipediaProcessingResult(BaseModel):
    """
    Model representing the result of processing Wikipedia articles.

    This model captures summary statistics from processing Wikipedia articles,
    such as the total number of articles processed and how many were successfully embedded.
    """

    model_config = ConfigDict(from_attributes=True)

    total_landmarks: int = Field(..., description="Total number of landmarks checked")
    landmarks_with_wikipedia: int = Field(
        ..., description="Number of landmarks with Wikipedia articles"
    )
    total_articles: int = Field(
        ..., description="Total number of Wikipedia articles found"
    )
    articles_processed: int = Field(
        ..., description="Number of articles successfully processed"
    )
    articles_with_errors: int = Field(
        ..., description="Number of articles with processing errors"
    )
    total_chunks: int = Field(..., description="Total number of text chunks generated")
    chunks_embedded: int = Field(
        ..., description="Number of chunks successfully embedded"
    )

    def __str__(self) -> str:
        """Return a string representation of the processing result."""
        return (
            f"Total landmarks: {self.total_landmarks}, "
            f"Landmarks with Wikipedia: {self.landmarks_with_wikipedia}, "
            f"Total articles: {self.total_articles}, "
            f"Articles processed: {self.articles_processed}, "
            f"Articles with errors: {self.articles_with_errors}, "
            f"Total chunks: {self.total_chunks}, "
            f"Chunks embedded: {self.chunks_embedded}"
        )

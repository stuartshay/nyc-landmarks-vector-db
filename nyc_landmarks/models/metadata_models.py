"""
Metadata Models for NYC Landmarks Vector Database

This module contains Pydantic models for handling metadata related to landmarks
and Wikipedia articles. These models ensure consistent data validation and
structure across the application.

Models:
- LandmarkMetadata: Represents metadata for landmarks, including identification,
  location, architectural details, and additional data.
- WikipediaMetadata: Represents metadata for Wikipedia articles, including
title, URL, and processing date.

These models are designed to be flexible and support dictionary-like access
and mutation to maintain compatibility with existing code.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr


class SourceType(str, Enum):
    WIKIPEDIA = "Wikipedia"
    PDF = "Pdf"


class RootMetadataModel(BaseModel):
    """
    Root metadata model for all metadata types.

    This model serves as a base for other metadata models, providing common fields.
    """

    _processing_date: str = PrivateAttr(
        default_factory=lambda: datetime.utcnow().isoformat()
    )
    source_type: SourceType = Field(..., description="Source type of the metadata")

    @property
    def processing_date(self) -> str:
        return self._processing_date


class LandmarkMetadata(BaseModel):
    """
    Model representing landmark metadata used for vector database storage.

    This model standardizes the metadata structure used with vector embeddings,
    ensuring consistent field names and types across the application.

    The model supports dictionary-like access and mutation to maintain
    compatibility with existing code that expects a dictionary.
    """

    model_config = ConfigDict(from_attributes=True, extra="allow")

    # Core landmark identification fields
    landmark_id: str = Field(
        ..., description="Landmark Preservation Commission identifier"
    )
    name: str = Field(..., description="Name of the landmark")

    # Location and classification fields
    location: Optional[str] = Field(
        None, description="Street address or location of the landmark"
    )
    borough: Optional[str] = Field(
        None, description="Borough where the landmark is located"
    )
    type: Optional[str] = Field(
        None, description="Type of landmark (e.g., Individual Landmark)"
    )
    designation_date: Optional[str] = Field(
        None, description="Date when the landmark was designated"
    )

    # Architectural information
    architect: Optional[str] = Field(None, description="Architect of the landmark")
    style: Optional[str] = Field(
        None, description="Architectural style of the landmark"
    )
    neighborhood: Optional[str] = Field(
        None, description="Neighborhood of the landmark"
    )

    # Additional data that may be present
    has_pluto_data: Optional[bool] = Field(
        None, description="Indicates if PLUTO data is available"
    )
    year_built: Optional[str] = Field(None, description="Year the structure was built")
    land_use: Optional[str] = Field(None, description="Land use category")
    historic_district: Optional[str] = Field(None, description="Historic district name")
    zoning_district: Optional[str] = Field(None, description="Primary zoning district")

    # Extra fields dictionary to store additional fields
    _extra_fields: Dict[str, Any] = PrivateAttr(default_factory=dict)

    def __init__(self, **data: Any):
        # Extract fields that are defined in the model
        model_fields = {k: v for k, v in data.items() if k in self.__annotations__}
        # Store extra fields that are not defined in the model
        extra_fields = {k: v for k, v in data.items() if k not in self.__annotations__}

        # Initialize with model fields
        super().__init__(**model_fields)
        # Store extra fields
        self._extra_fields = extra_fields

    # Dictionary-like access methods
    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-like access with metadata['key']."""
        if key in self.__annotations__:
            return getattr(self, key)
        return self._extra_fields.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        """Allow dictionary-like assignment with metadata['key'] = value."""
        if key in self.__annotations__:
            setattr(self, key, value)
        else:
            self._extra_fields[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value with a default, like a dictionary."""
        try:
            value = self[key]
            return default if value is None else value
        except (KeyError, AttributeError):
            return default

    def update(self, data: Dict[str, Any]) -> None:
        """Update values like a dictionary."""
        for key, value in data.items():
            self[key] = value

    def __contains__(self, key: str) -> bool:
        """Support 'in' operator to check if a key exists."""
        return key in self.__annotations__ or key in self._extra_fields

    def keys(self) -> List[str]:
        """Return all keys including model fields and extra fields."""
        return list(self.__annotations__.keys()) + list(self._extra_fields.keys())

    def items(self) -> List[tuple[str, Any]]:
        """Return all items as (key, value) pairs."""
        model_items = [
            (k, getattr(self, k))
            for k in self.__annotations__
            if getattr(self, k) is not None
        ]
        return model_items + list(self._extra_fields.items())

    def dict(self, **kwargs: Any) -> Dict[str, Any]:
        """Return a dictionary of all fields including extras."""
        result: Dict[str, Any] = super().model_dump(**kwargs)
        result.update(self._extra_fields)
        return result


class WikipediaMetadata(RootMetadataModel):
    """
    Model representing metadata for Wikipedia articles.

    This model captures key information about a Wikipedia article,
    such as its title and URL.
    """

    title: str = Field(..., description="Title of the Wikipedia article")
    url: str = Field(..., description="URL of the Wikipedia article")


class PdrReportMetadata(RootMetadataModel):
    """
    Model representing metadata for PDR reports.

    This model captures key information about a PDR report,
    such as its PDF report URL.
    """

    pdfReportUrl: str = Field(..., description="URL of the PDF report")

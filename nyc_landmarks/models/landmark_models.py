"""
Pydantic models for NYC Landmarks Vector Database.

This module contains data models for various aspects of the NYC Landmarks
system, particularly focused on landmark reports and their metadata.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


class LpcReportModel(BaseModel):
    """
    Model representing a Landmark Preservation Commission (LPC) report.

    This model captures the essential fields of an LPC report including
    its unique identifier, name, and URL to the PDF report.
    """

    model_config = ConfigDict(from_attributes=True)

    lpNumber: str = Field(
        ..., description="Landmark Preservation Commission identifier"
    )
    name: str = Field(..., description="Name of the landmark")
    pdfReportUrl: Optional[str] = Field(None, description="URL to the PDF report")
    borough: Optional[str] = Field(
        None, description="Borough where the landmark is located"
    )
    objectType: Optional[str] = Field(None, description="Type of landmark object")
    street: Optional[str] = Field(None, description="Street address of the landmark")
    dateDesignated: Optional[Union[str, datetime]] = Field(
        None, description="Date when the landmark was designated"
    )
    architect: Optional[str] = Field(None, description="Architect of the landmark")
    style: Optional[str] = Field(
        None, description="Architectural style of the landmark"
    )
    neighborhood: Optional[str] = Field(
        None, description="Neighborhood of the landmark"
    )
    photoUrl: Optional[str] = Field(None, description="URL to a photo of the landmark")

    @field_validator("pdfReportUrl", "photoUrl")
    @classmethod
    def validate_url(cls, v):
        """Validate that URLs are properly formatted if they exist."""
        if v is not None and not v.startswith(("http://", "https://")):
            raise ValueError("URL must be a valid HTTP or HTTPS URL")
        return v


class LpcReportResponse(BaseModel):
    """
    Model representing the response from the LPC Report API.

    This model includes pagination information and a list of LPC reports.
    """

    model_config = ConfigDict(from_attributes=True)

    results: List[LpcReportModel] = Field(..., description="List of LPC reports")
    totalCount: int = Field(..., description="Total number of records available")
    pageCount: int = Field(..., description="Number of pages available")


class PdfInfo(BaseModel):
    """
    Model representing extracted information about a landmark PDF.

    This model contains the essential information needed to identify and
    access a PDF document for a specific landmark.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Landmark identifier")
    name: str = Field(..., description="Name of the landmark")
    pdf_url: str = Field(..., description="URL to the PDF report")

    @field_validator("pdf_url")
    @classmethod
    def validate_pdf_url(cls, v):
        """Validate that the PDF URL is properly formatted."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("PDF URL must be a valid HTTP or HTTPS URL")
        return v


class ProcessingResult(BaseModel):
    """
    Model representing the result of a landmark report processing operation.

    This model captures summary statistics from processing landmark reports,
    such as the total number of reports processed and how many had PDF URLs.
    """

    model_config = ConfigDict(from_attributes=True)

    total_reports: int = Field(..., description="Total number of reports fetched")
    reports_with_pdfs: int = Field(..., description="Number of reports with PDF URLs")

    def __str__(self) -> str:
        """Return a string representation of the processing result."""
        return f"Total reports: {self.total_reports}, Reports with PDFs: {self.reports_with_pdfs}"


class ApiError(BaseModel):
    """
    Model representing an API error response.

    This model helps standardize error handling from the CoreDataStore API.
    """

    model_config = ConfigDict(from_attributes=True)

    status_code: int = Field(..., description="HTTP status code")
    message: str = Field(..., description="Error message")
    detail: Optional[Dict[str, Any]] = Field(
        None, description="Additional error details"
    )

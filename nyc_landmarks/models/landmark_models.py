"""
Pydantic models for NYC Landmarks Vector Database.

This module contains data models for various aspects of the NYC Landmarks
system, particularly focused on landmark reports and their metadata.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl, validator


class LpcReportModel(BaseModel):
    """
    Model representing a Landmark Preservation Commission (LPC) report.

    This model captures the essential fields of an LPC report including
    its unique identifier, name, and URL to the PDF report.
    """

    lpNumber: str = Field(
        ..., description="Landmark Preservation Commission identifier"
    )
    name: str = Field(..., description="Name of the landmark")
    pdfReportUrl: Optional[str] = Field(None, description="URL to the PDF report")
    borough: Optional[str] = Field(
        None, description="Borough where the landmark is located"
    )
    objectType: Optional[str] = Field(None, description="Type of landmark object")

    @validator("pdfReportUrl")
    def validate_pdf_url(cls, v):
        """Validate that the PDF URL is properly formatted if it exists."""
        if v is not None and not v.startswith(("http://", "https://")):
            raise ValueError("PDF URL must be a valid HTTP or HTTPS URL")
        return v


class LpcReportResponse(BaseModel):
    """
    Model representing the response from the LPC Report API.

    This model includes pagination information and a list of LPC reports.
    """

    results: List[LpcReportModel] = Field(..., description="List of LPC reports")
    totalCount: int = Field(..., description="Total number of records available")
    pageCount: int = Field(..., description="Number of pages available")


class PdfInfo(BaseModel):
    """
    Model representing extracted information about a landmark PDF.

    This model contains the essential information needed to identify and
    access a PDF document for a specific landmark.
    """

    id: str = Field(..., description="Landmark identifier")
    name: str = Field(..., description="Name of the landmark")
    pdf_url: str = Field(..., description="URL to the PDF report")

    @validator("pdf_url")
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

    status_code: int = Field(..., description="HTTP status code")
    message: str = Field(..., description="Error message")
    detail: Optional[Dict[str, Any]] = Field(
        None, description="Additional error details"
    )

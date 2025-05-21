"""
Pydantic models for landmark-related data structures.

These models provide type-safe structures for the landmark information
and ensure consistent data validation and access patterns.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, field_validator


class LpcReportModel(BaseModel):
    """
    Model representing a Landmark Preservation Commission (LPC) report.

    This model captures the essential fields of an LPC report including
    its unique identifier, name, and URL to the PDF report.
    """

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description="Name of the landmark")
    lpcId: Optional[str] = Field(None, description="LPC internal identifier")
    lpNumber: str = Field(
        ..., description="Landmark Preservation Commission identifier"
    )
    objectType: Optional[str] = Field(None, description="Type of landmark object")
    architect: Optional[str] = Field(None, description="Architect of the landmark")
    style: Optional[str] = Field(
        None, description="Architectural style of the landmark"
    )
    street: Optional[str] = Field(None, description="Street address of the landmark")
    borough: Optional[str] = Field(
        None, description="Borough where the landmark is located"
    )
    dateDesignated: Optional[Union[str, datetime]] = Field(
        None, description="Date when the landmark was designated"
    )
    photoStatus: Optional[bool] = Field(
        None, description="Indicates if photo is available"
    )
    mapStatus: Optional[bool] = Field(None, description="Indicates if map is available")
    neighborhood: Optional[str] = Field(
        None, description="Neighborhood of the landmark"
    )
    zipCode: Optional[str] = Field(None, description="ZIP code of the landmark")
    photoUrl: Optional[str] = Field(None, description="URL to a photo of the landmark")
    pdfReportUrl: Optional[str] = Field(None, description="URL to the PDF report")

    @field_validator("pdfReportUrl", "photoUrl", mode="after")  # type: ignore[misc]
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate that URLs are properly formatted if they exist."""
        if v is not None and not v.startswith(("http://", "https://")):
            raise ValueError("URL must be a valid HTTP or HTTPS URL")
        return v


class LpcReportResponse(BaseModel):
    """
    Model representing the response from the LPC Report API.

    This model includes pagination information and a list of LPC reports.
    """

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    total: int = Field(..., description="Total number of records available")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Number of records per page")
    from_: int = Field(..., alias="from", description="Starting record number")
    to: int = Field(..., description="Ending record number")
    results: List[LpcReportModel] = Field(..., description="List of LPC reports")

    @property
    def totalCount(self) -> int:
        return self.total

    @property
    def pageCount(self) -> int:
        return self.page


class MapPoint(BaseModel):
    """Model representing a geographic point with latitude and longitude."""

    model_config = ConfigDict(from_attributes=True)

    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")


class MapMarker(BaseModel):
    """Model representing a marker on a map."""

    model_config = ConfigDict(from_attributes=True)

    point: MapPoint = Field(..., description="Geographic point of the marker")


class MapData(BaseModel):
    """Model representing map data for a landmark."""

    model_config = ConfigDict(from_attributes=True)

    zoom: int = Field(..., description="Zoom level for the map")
    mapType: str = Field(..., description="Type of map (e.g., 'Hybrid')")
    centerPoint: MapPoint = Field(..., description="Center point of the map")
    markers: List[MapMarker] = Field(..., description="Markers on the map")


class LandmarkDetail(BaseModel):
    """Model representing detailed information about a landmark building."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description="Name of the landmark")
    lpNumber: str = Field(
        ..., description="Landmark Preservation Commission identifier"
    )
    bbl: Optional[str] = Field(None, description="Borough-Block-Lot identifier")
    binNumber: Optional[int] = Field(None, description="Building Identification Number")
    boroughId: Optional[str] = Field(None, description="Borough identifier code")
    objectType: Optional[str] = Field(None, description="Type of landmark object")
    block: Optional[int] = Field(None, description="Block number")
    lot: Optional[int] = Field(None, description="Lot number")
    plutoAddress: Optional[str] = Field(None, description="PLUTO database address")
    designatedAddress: Optional[str] = Field(
        None, description="Official designated address"
    )
    number: Optional[str] = Field(None, description="Building number")
    street: Optional[str] = Field(None, description="Street name")
    city: Optional[str] = Field(None, description="City name")
    designatedDate: Optional[Union[str, datetime]] = Field(
        None, description="Designation date"
    )
    calendaredDate: Optional[Union[str, datetime]] = Field(
        None, description="Date calendared for consideration"
    )
    publicHearingDate: Optional[str] = Field(None, description="Public hearing date")
    historicDistrict: Optional[str] = Field(
        None, description="Historic district information"
    )
    otherHearingDate: Optional[str] = Field(None, description="Other hearing date")
    isCurrent: Optional[bool] = Field(None, description="If the data is current")
    status: Optional[str] = Field(None, description="Designation status")
    lastAction: Optional[str] = Field(None, description="Last action taken")
    priorStatus: Optional[str] = Field(None, description="Prior status")
    recordType: Optional[str] = Field(None, description="Type of record")
    isBuilding: Optional[bool] = Field(
        None, description="If the landmark is a building"
    )
    isVacantLot: Optional[bool] = Field(
        None, description="If the landmark is a vacant lot"
    )
    isSecondaryBuilding: Optional[bool] = Field(
        None, description="If it's a secondary building"
    )
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")


class LpcReportDetailResponse(BaseModel):
    """
    Model representing the detailed response from the LPC Report API for a single landmark.

    This model includes comprehensive information about a landmark, including its map data
    and associated buildings or structures.
    """

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description="Name of the landmark")
    lpcId: Optional[str] = Field(None, description="LPC internal identifier")
    lpNumber: str = Field(
        ..., description="Landmark Preservation Commission identifier"
    )
    objectType: Optional[str] = Field(None, description="Type of landmark object")
    architect: Optional[str] = Field(None, description="Architect of the landmark")
    style: Optional[str] = Field(
        None, description="Architectural style of the landmark"
    )
    street: Optional[str] = Field(None, description="Street address of the landmark")
    city: Optional[str] = Field(None, description="City name")
    state: Optional[str] = Field(None, description="State abbreviation")
    zipCode: Optional[str] = Field(None, description="ZIP code of the landmark")
    borough: Optional[str] = Field(
        None, description="Borough where the landmark is located"
    )
    dateDesignated: Optional[Union[str, datetime]] = Field(
        None, description="Date when the landmark was designated"
    )
    photoStatus: Optional[bool] = Field(
        None, description="Indicates if photo is available"
    )
    photoCollectionStatus: Optional[bool] = Field(
        None, description="Indicates if photo collection is available"
    )
    photoArchiveStatus: Optional[bool] = Field(
        None, description="Indicates if photo archive is available"
    )
    mapStatus: Optional[bool] = Field(None, description="Indicates if map is available")
    pdfStatus: Optional[bool] = Field(
        None, description="Indicates if PDF report is available"
    )
    neighborhood: Optional[str] = Field(
        None, description="Neighborhood of the landmark"
    )
    photoUrl: Optional[str] = Field(None, description="URL to a photo of the landmark")
    pdfReportUrl: Optional[str] = Field(None, description="URL to the PDF report")
    bbl: Optional[Union[int, str]] = Field(
        None, description="Borough-Block-Lot identifier (can be int, str, or None)"
    )
    bin: Optional[int] = Field(None, description="Building Identification Number")
    objectId: Optional[int] = Field(None, description="Object identifier")
    shapeArea: Optional[float] = Field(None, description="Area of the landmark's shape")
    shapeLength: Optional[float] = Field(
        None, description="Length of the landmark's shape"
    )
    shapeLookupKey: Optional[str] = Field(None, description="Shape lookup key")
    map: Optional[MapData] = Field(None, description="Map data for the landmark")
    landmarks: Optional[List[LandmarkDetail]] = Field(
        None, description="Associated landmark buildings"
    )

    @field_validator("pdfReportUrl", "photoUrl", mode="after")  # type: ignore[misc]
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate that URLs are properly formatted if they exist."""
        if v is not None and not v.startswith(("http://", "https://")):
            raise ValueError("URL must be a valid HTTP or HTTPS URL")
        return v

    # No helper methods needed, we'll use the fields directly


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

    @field_validator("pdf_url", mode="after")  # type: ignore[misc]
    @classmethod
    def validate_pdf_url(cls, v: str) -> str:
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


class PlutoDataModel(BaseModel):
    """
    Model representing PLUTO (Primary Land Use Tax Lot Output) data for a landmark.

    This model captures key property information from the NYC Department of City Planning's
    PLUTO database, which provides extensive land use and geographic data.
    """

    model_config = ConfigDict(from_attributes=True)

    yearBuilt: Optional[str] = Field(None, description="Year the structure was built")
    landUse: Optional[str] = Field(None, description="Land use category")
    historicDistrict: Optional[str] = Field(None, description="Historic district name")
    zoneDist1: Optional[str] = Field(None, description="Primary zoning district")


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

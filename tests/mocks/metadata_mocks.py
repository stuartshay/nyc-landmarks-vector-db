"""
Mock data for metadata tests.

This module provides consistent mock metadata data that can be used
across different test files.
"""

from nyc_landmarks.models.metadata_models import (
    PdrReportMetadata,
    RootMetadataModel,
    SourceType,
    WikipediaMetadata,
)


def get_mock_root_metadata(source_type: SourceType) -> RootMetadataModel:
    """
    Get mock RootMetadataModel for testing.

    Args:
        source_type: The source type of the metadata (e.g., Wikipedia or Pdf).

    Returns:
        A RootMetadataModel instance with mock data.
    """
    return RootMetadataModel(source_type=source_type)


def get_mock_wikipedia_metadata() -> WikipediaMetadata:
    """
    Get mock Wikipedia metadata for testing.

    Returns:
        A WikipediaMetadata instance containing mock metadata.
    """
    return WikipediaMetadata(
        title="Irad Hawley House",
        url="https://en.wikipedia.org/wiki/Irad_Hawley_House",
        source_type=SourceType.WIKIPEDIA,
    )


def get_mock_pdr_report_metadata() -> PdrReportMetadata:
    """
    Get mock PdrReportMetadata for testing.

    Returns:
        A PdrReportMetadata instance containing mock metadata.
    """
    return PdrReportMetadata(
        pdfReportUrl="https://example.com/reports/sample_report.pdf",
        source_type=SourceType.PDF,
    )

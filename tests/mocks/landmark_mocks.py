"""
Mock data for landmark tests.

This module provides consistent mock landmark data that can be used
across different test files.
"""

from typing import Any, Dict, List

from nyc_landmarks.models.landmark_models import (
    LandmarkDetail,
    LpcReportDetailResponse,
)


def get_mock_landmark_details() -> LpcReportDetailResponse:
    """
    Get mock landmark details for testing.

    Returns:
        An LpcReportDetailResponse object containing mock landmark details data.
    """
    return LpcReportDetailResponse(
        name="Irad Hawley House",
        lpNumber="LP-00009",
        lpcId="0009",
        objectType="Individual Landmark",
        architect="Unknown",
        style="Italianate",
        street="47 Fifth Avenue",
        borough="Manhattan",
        dateDesignated="1969-09-09T00:00:00",
        photoStatus=True,
        photoCollectionStatus=True,
        photoArchiveStatus=True,
        mapStatus=True,
        pdfStatus=True,
        plutoStatus=True,
        neighborhood="Greenwich Village",
        photoUrl="https://cdn.informationcart.com/images/0009.jpg",
        pdfReportUrl="https://cdn.informationcart.com/pdf/0009.pdf",
        bbl=1005690004,
        city="New York",
        state="NY",
        zipCode="10003",
        bin=None,
        objectId=None,
        shapeArea=None,
        shapeLength=None,
        shapeLookupKey=None,
        map=None,
        landmarks=None,
    )


def get_mock_buildings_from_landmark_detail() -> list[LandmarkDetail]:
    """
    Get mock buildings list for landmark detail testing.

    Returns:
        A list of LandmarkDetail objects representing buildings associated with a landmark.
    """
    return [
        LandmarkDetail(
            lpNumber="LP-00001A",
            name="Building 1",
            designatedAddress="123 Main St",
            boroughId="1",
            objectType="Individual Landmark",
            designatedDate="2020-01-01",
            historicDistrict="Test District",
            street="123 Main St",
            bbl="1000010001",
            binNumber=1000001,
            block=1000,
            lot=1,
            plutoAddress="123 Main St New York NY",
            number="123",
            city="New York",
            calendaredDate="2019-01-01",
            publicHearingDate="2019-02-01",
            otherHearingDate="2019-03-01",
            isCurrent=True,
            status="Designated",
            lastAction="Designated",
            priorStatus="Calendared",
            recordType="Individual Landmark",
            isBuilding=True,
            isVacantLot=False,
            isSecondaryBuilding=False,
            latitude=40.7128,
            longitude=-74.0060,
        ),
        LandmarkDetail(
            lpNumber="LP-00001B",
            name="Building 2",
            designatedAddress="456 Side St",
            boroughId="1",
            objectType="Individual Landmark",
            designatedDate="2020-01-02",
            historicDistrict="Test District",
            street="456 Side St",
            bbl="1000020001",
            binNumber=1000002,
            block=1000,
            lot=2,
            plutoAddress="456 Side St New York NY",
            number="456",
            city="New York",
            calendaredDate="2019-01-02",
            publicHearingDate="2019-02-02",
            otherHearingDate="2019-03-02",
            isCurrent=True,
            status="Designated",
            lastAction="Designated",
            priorStatus="Calendared",
            recordType="Individual Landmark",
            isBuilding=True,
            isVacantLot=False,
            isSecondaryBuilding=False,
            latitude=40.7129,
            longitude=-74.0061,
        ),
    ]


def get_mock_building_model() -> Dict[str, Any]:
    """
    Get a mock building model with attribute-style access for testing.

    This is primarily used for testing attribute access patterns in
    EnhancedMetadataCollector's test_building_data_pydantic_model test.

    Returns:
        A dictionary with mock building data that can be used to create a Mock object
        with attribute-style access.
    """
    return {
        "name": "Salmagundi Club",
        "bbl": "1005690004",
        "binNumber": 1009274,
        "boroughId": "MN",
        "objectType": "Individual Landmark",
        "block": 569,
        "lot": 4,
        "latitude": 40.7342490239599,
        "longitude": -73.9944453559693,
        "designatedAddress": "47 5 AVENUE",
    }


def get_mock_landmarks_for_test_fetch_buildings() -> List[LandmarkDetail]:
    """
    Get mock landmark buildings for the test_fetch_buildings_from_landmark_detail test.

    This function extracts the building data used in test_fetch_buildings_from_landmark_detail
    to a separate mock function for reuse.

    Returns:
        List of LandmarkDetail objects for building data
    """
    return get_mock_buildings_from_landmark_detail()

"""
PDF text extraction module for NYC Landmarks Vector Database.

This module handles retrieving PDFs from CoreDataStore API URLs and
extracting text content from those PDFs.
"""

import io
import logging
from typing import Any, Dict, List, Optional, Tuple

import pypdf
import requests

from nyc_landmarks.config.settings import settings
from nyc_landmarks.db.coredatastore_api import CoreDataStoreAPI

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.LOG_LEVEL.value)


class PDFExtractor:
    """PDF text extraction from CoreDataStore API URLs."""

    def __init__(self) -> None:
        """Initialize the PDF extractor."""
        self.api_client = CoreDataStoreAPI()
        logger.info("Initialized PDF extractor with CoreDataStore API client")

    def download_pdf_from_url(self, url: str) -> Optional[bytes]:
        """Download a PDF from a URL.

        Args:
            url: URL of the PDF to download

        Returns:
            PDF content as bytes, or None if the download failed
        """
        try:
            # Download the PDF from the URL
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            logger.info(f"Downloaded PDF from URL: {url}")
            return response.content
        except Exception as e:
            logger.error(f"Error downloading PDF from URL {url}: {e}")
            return None

    def extract_text_from_bytes(self, pdf_bytes: bytes) -> Optional[str]:
        """Extract text from PDF bytes.

        Args:
            pdf_bytes: PDF content as bytes

        Returns:
            Extracted text, or None if extraction failed
        """
        try:
            # Create a file-like object from the bytes
            pdf_file = io.BytesIO(pdf_bytes)

            # Extract text using PyPDF
            extracted_text = []

            with pypdf.PdfReader(pdf_file) as pdf:
                for page_num in range(len(pdf.pages)):
                    # Extract text from the page
                    page = pdf.pages[page_num]
                    page_text = page.extract_text()

                    # Add page text to the extracted text list
                    if page_text:
                        extracted_text.append(page_text)

            # Combine all page texts into a single string
            full_text = "\n\n".join(extracted_text)

            logger.info(f"Extracted {len(extracted_text)} pages of text")
            return full_text
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return None

    def extract_text_from_url(self, url: str) -> Optional[str]:
        """Extract text from a PDF at the given URL.

        Args:
            url: URL of the PDF to extract text from

        Returns:
            Extracted text, or None if extraction failed
        """
        # Download the PDF from the URL
        pdf_bytes = self.download_pdf_from_url(url)
        if not pdf_bytes:
            return None

        # Extract text from the PDF
        return self.extract_text_from_bytes(pdf_bytes)

    def process_landmark_pdf(
        self, landmark_id: str, pdf_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a PDF for a specific landmark.

        Args:
            landmark_id: ID of the landmark
            pdf_url: URL of the PDF (if None, will get from API)

        Returns:
            Dictionary containing extracted text and metadata
        """
        result = {
            "landmark_id": landmark_id,
            "success": False,
        }

        try:
            # Get PDF URL from API if not provided
            if not pdf_url:
                pdf_url = self.api_client.get_landmark_pdf_url(landmark_id)

            if not pdf_url:
                error = "No PDF URL found for landmark"
                logger.error(f"{error}: {landmark_id}")
                result["error"] = error
                return result

            # Extract text from the PDF
            text = self.extract_text_from_url(pdf_url)

            if not text:
                error = "Failed to extract text from PDF"
                logger.error(f"{error}: {landmark_id}")
                result["error"] = error
                return result

            # Add text and metadata to result
            result["text"] = text
            result["page_count"] = text.count("\n\n") + 1  # Approximate count
            result["pdf_url"] = pdf_url
            result["success"] = True

            return result

        except Exception as e:
            error = str(e)
            logger.error(f"Error processing landmark PDF {landmark_id}: {error}")
            result["error"] = error
            return result

"""
PDF text extraction module for NYC Landmarks Vector Database.

This module handles retrieving PDFs from Azure Blob Storage and
extracting text content from those PDFs.
"""

import io
import logging
from typing import Any, Dict, List, Optional, Tuple

import pypdf
from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob import BlobClient, BlobServiceClient, ContainerClient

from nyc_landmarks.config.settings import settings

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.LOG_LEVEL.value)


class PDFExtractor:
    """PDF text extraction from Azure Blob Storage."""

    def __init__(self):
        """Initialize the PDF extractor with Azure Blob Storage credentials."""
        self.connection_string = settings.AZURE_STORAGE_CONNECTION_STRING
        self.container_name = settings.AZURE_STORAGE_CONTAINER_NAME
        self.blob_service_client = None
        self.container_client = None

        # Initialize Azure Blob Storage client if connection string is provided
        if self.connection_string and self.container_name:
            try:
                self.blob_service_client = BlobServiceClient.from_connection_string(
                    self.connection_string
                )
                self.container_client = self.blob_service_client.get_container_client(
                    self.container_name
                )
                logger.info(
                    f"Connected to Azure Blob Storage container: {self.container_name}"
                )
            except Exception as e:
                logger.error(f"Error connecting to Azure Blob Storage: {e}")
                raise

    def list_pdfs(self) -> List[str]:
        """List all PDFs in the Azure Blob Storage container.

        Returns:
            List of PDF blob names
        """
        if not self.container_client:
            logger.error("Azure Blob Storage not configured")
            return []

        try:
            # List all blobs in the container and filter for PDFs
            all_blobs = self.container_client.list_blobs()
            pdf_blobs = [
                blob.name for blob in all_blobs if blob.name.lower().endswith(".pdf")
            ]

            logger.info(f"Found {len(pdf_blobs)} PDFs in container")
            return pdf_blobs
        except Exception as e:
            logger.error(f"Error listing PDFs: {e}")
            return []

    def get_pdf_blob(self, blob_name: str) -> Optional[bytes]:
        """Download a PDF blob from Azure Blob Storage.

        Args:
            blob_name: Name of the PDF blob to download

        Returns:
            PDF content as bytes, or None if the blob couldn't be downloaded
        """
        if not self.container_client:
            logger.error("Azure Blob Storage not configured")
            return None

        try:
            # Get a blob client for the specified blob
            blob_client = self.container_client.get_blob_client(blob_name)

            # Download the blob
            download_stream = blob_client.download_blob()
            blob_content = download_stream.readall()

            logger.info(f"Downloaded PDF blob: {blob_name}")
            return blob_content
        except ResourceNotFoundError:
            logger.error(f"PDF blob not found: {blob_name}")
            return None
        except Exception as e:
            logger.error(f"Error downloading PDF blob {blob_name}: {e}")
            return None

    def extract_text_from_blob(self, blob_name: str) -> Optional[str]:
        """Extract text from a PDF blob in Azure Blob Storage.

        Args:
            blob_name: Name of the PDF blob to extract text from

        Returns:
            Extracted text, or None if extraction failed
        """
        # Download the PDF blob
        pdf_bytes = self.get_pdf_blob(blob_name)
        if not pdf_bytes:
            return None

        # Extract text from the PDF
        return self.extract_text_from_bytes(pdf_bytes)

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

            # Extract text using PyPDF2
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

    def extract_text_with_metadata(self, blob_name: str) -> Dict[str, Any]:
        """Extract text and metadata from a PDF blob.

        Args:
            blob_name: Name of the PDF blob to extract from

        Returns:
            Dictionary containing extracted text and metadata
        """
        text = self.extract_text_from_blob(blob_name)

        # We could extract more metadata here, like landmark ID from filename
        # For now, just include the blob name and success status
        result = {
            "blob_name": blob_name,
            "success": text is not None,
        }

        if text:
            result["text"] = text
            result["page_count"] = text.count("\n\n") + 1  # Approximate count

        return result

    def process_landmark_pdf(
        self, landmark_id: str, blob_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a PDF for a specific landmark.

        Args:
            landmark_id: ID of the landmark
            blob_name: Name of the PDF blob (if None, will attempt to find based on landmark_id)

        Returns:
            Dictionary containing extracted text and metadata
        """
        # If blob_name is not provided, try to find it based on landmark_id
        if not blob_name:
            # List all PDFs and find one that matches the landmark_id
            all_pdfs = self.list_pdfs()
            matching_pdfs = [pdf for pdf in all_pdfs if landmark_id in pdf]

            if not matching_pdfs:
                logger.error(f"No PDF found for landmark ID: {landmark_id}")
                return {
                    "landmark_id": landmark_id,
                    "success": False,
                    "error": "No matching PDF found",
                }

            # Use the first matching PDF
            blob_name = matching_pdfs[0]

        # Extract text from the PDF
        result = self.extract_text_with_metadata(blob_name)

        # Add landmark_id to the result
        result["landmark_id"] = landmark_id

        return result

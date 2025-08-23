"""
Text extraction service for processing uploaded documents.
"""

import logging
from io import BytesIO
from typing import Any, Dict, Optional, Tuple

# Try to import document processing libraries with fallbacks
try:
    import fitz  # PyMuPDF for PDF processing

    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    logging.warning("PyMuPDF not available, PDF extraction disabled")

try:
    from docx import Document as DocxDocument

    PYTHON_DOCX_AVAILABLE = True
except ImportError:
    PYTHON_DOCX_AVAILABLE = False
    logging.warning("python-docx not available, DOCX extraction disabled")

from app.core.database import db
from app.models.enums import FileStatus
from app.utils.file_utils import estimate_page_count

logger = logging.getLogger(__name__)


class ExtractionService:
    """Handles text extraction from various document formats."""

    def __init__(self):
        self.max_text_length = 10_000_000  # 10MB text limit

    async def extract_text_from_file(self, file_id: str) -> Dict[str, Any]:
        """
        Extract text from a processing file.

        Args:
            file_id: Processing file ID

        Returns:
            Dict with extraction results and metadata
        """
        logger.info(f"Starting text extraction for file {file_id}")

        try:
            # Get file record
            file_result = (
                await db.supabase.table("processing_files").select("*").eq("id", file_id).execute()
            )
            if not file_result.data:
                raise ValueError(f"File {file_id} not found")

            file_record = file_result.data[0]
            storage_path = file_record["stored_path"]
            mime_type = file_record["mime_type"]

            # Update status to extracting
            await self._update_file_status(file_id, FileStatus.EXTRACTING_TEXT)

            # Download file content
            content = await self._download_file_content(storage_path)

            # Extract text based on MIME type
            extraction_result = await self._extract_text_by_type(content, mime_type)

            if extraction_result["success"]:
                # Save extracted text
                await self._save_extracted_text(file_id, extraction_result)
                await self._update_file_status(file_id, FileStatus.ANALYZING_METADATA)

                logger.info(f"Successfully extracted text from file {file_id}")
                return {
                    "success": True,
                    "file_id": file_id,
                    "text_length": len(extraction_result["text"]),
                    "page_count": extraction_result["page_count"],
                }
            else:
                await self._update_file_status(
                    file_id, FileStatus.EXTRACTION_FAILED, error_message=extraction_result["error"]
                )
                return {"success": False, "file_id": file_id, "error": extraction_result["error"]}

        except Exception as e:
            logger.error(f"Text extraction failed for file {file_id}: {e}")
            await self._update_file_status(
                file_id, FileStatus.EXTRACTION_FAILED, error_message=str(e)
            )
            return {"success": False, "file_id": file_id, "error": str(e)}

    async def _extract_text_by_type(self, content: bytes, mime_type: str) -> Dict[str, Any]:
        """Extract text based on file MIME type."""
        try:
            if mime_type == "application/pdf":
                return await self._extract_from_pdf(content)
            elif (
                mime_type
                == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ):
                return await self._extract_from_docx(content)
            elif mime_type in ["text/plain", "text/markdown"]:
                return await self._extract_from_text(content)
            else:
                return {
                    "success": False,
                    "error": f"Unsupported MIME type for extraction: {mime_type}",
                }
        except Exception as e:
            logger.error(f"Text extraction error for MIME type {mime_type}: {e}")
            return {"success": False, "error": f"Extraction failed: {str(e)}"}

    async def _extract_from_pdf(self, content: bytes) -> Dict[str, Any]:
        """Extract text from PDF using PyMuPDF."""
        if not PYMUPDF_AVAILABLE:
            return {
                "success": False,
                "error": "PDF extraction not available - PyMuPDF not installed",
            }

        try:
            doc = fitz.open(stream=content, filetype="pdf")

            text_content = []
            page_count = len(doc)

            for page_num in range(page_count):
                page = doc.load_page(page_num)
                page_text = page.get_text()
                text_content.append(page_text)

            doc.close()

            full_text = "\n\n".join(text_content)

            # Check text length limits
            if len(full_text) > self.max_text_length:
                return {
                    "success": False,
                    "error": f"Extracted text too large: {len(full_text)} chars (max: {self.max_text_length})",
                }

            return {
                "success": True,
                "text": full_text,
                "page_count": page_count,
                "word_count": len(full_text.split()),
                "char_count": len(full_text),
            }

        except Exception as e:
            return {"success": False, "error": f"PDF extraction failed: {str(e)}"}

    async def _extract_from_docx(self, content: bytes) -> Dict[str, Any]:
        """Extract text from DOCX using python-docx."""
        if not PYTHON_DOCX_AVAILABLE:
            return {
                "success": False,
                "error": "DOCX extraction not available - python-docx not installed",
            }

        try:
            doc = DocxDocument(BytesIO(content))

            text_content = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text)

            full_text = "\n\n".join(text_content)

            # Check text length limits
            if len(full_text) > self.max_text_length:
                return {
                    "success": False,
                    "error": f"Extracted text too large: {len(full_text)} chars (max: {self.max_text_length})",
                }

            page_count = estimate_page_count(full_text)

            return {
                "success": True,
                "text": full_text,
                "page_count": page_count,
                "word_count": len(full_text.split()),
                "char_count": len(full_text),
            }

        except Exception as e:
            return {"success": False, "error": f"DOCX extraction failed: {str(e)}"}

    async def _extract_from_text(self, content: bytes) -> Dict[str, Any]:
        """Extract text from plain text files."""
        try:
            # Try UTF-8 first, fallback to latin-1
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                text = content.decode("latin-1")

            # Check text length limits
            if len(text) > self.max_text_length:
                return {
                    "success": False,
                    "error": f"Text file too large: {len(text)} chars (max: {self.max_text_length})",
                }

            page_count = estimate_page_count(text)

            return {
                "success": True,
                "text": text,
                "page_count": page_count,
                "word_count": len(text.split()),
                "char_count": len(text),
            }

        except Exception as e:
            return {"success": False, "error": f"Text extraction failed: {str(e)}"}

    async def _download_file_content(self, storage_path: str) -> bytes:
        """Download file content from Supabase storage."""
        try:
            content = db.supabase.storage.from_("documents").download(storage_path)
            return content
        except Exception as e:
            logger.error(f"Failed to download file {storage_path}: {e}")
            raise

    async def _save_extracted_text(self, file_id: str, extraction_result: Dict[str, Any]):
        """Save extracted text and metadata to database."""
        try:
            update_data = {
                "extracted_text": extraction_result["text"],
                "page_count": extraction_result["page_count"],
                "word_count": extraction_result["word_count"],
                "char_count": extraction_result["char_count"],
            }

            await db.supabase.table("processing_files").update(update_data).eq(
                "id", file_id
            ).execute()

        except Exception as e:
            logger.error(f"Failed to save extracted text for file {file_id}: {e}")
            raise

    async def _update_file_status(self, file_id: str, status: FileStatus, **kwargs):
        """Update file processing status."""
        try:
            from datetime import datetime

            update_data = {
                "status": status.value,
                "updated_at": datetime.utcnow().isoformat(),
                **kwargs,
            }

            await db.supabase.table("processing_files").update(update_data).eq(
                "id", file_id
            ).execute()

        except Exception as e:
            logger.error(f"Failed to update file {file_id} status: {e}")
            raise

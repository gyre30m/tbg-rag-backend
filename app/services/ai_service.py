"""
AI service for metadata extraction and document analysis.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import openai
from anthropic import Anthropic

from app.core.config import settings
from app.core.database import db
from app.models.enums import DocumentCategory, DocumentType, FileStatus

logger = logging.getLogger(__name__)


class AIService:
    """Handles AI-powered metadata extraction and document analysis."""

    def __init__(self):
        self.openai_client = (
            openai.AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
        )
        self.anthropic_client = (
            Anthropic(api_key=settings.anthropic_api_key) if settings.anthropic_api_key else None
        )

        if not self.openai_client and not self.anthropic_client:
            logger.warning("No AI API keys configured - metadata extraction will be limited")

    async def extract_metadata(self, file_id: str) -> Dict[str, Any]:
        """
        Extract metadata from a processing file using AI.

        Args:
            file_id: Processing file ID

        Returns:
            Dict with extraction results
        """
        logger.info(f"Starting AI metadata extraction for file {file_id}")

        try:
            # Get file record with extracted text
            file_result = (
                await db.supabase.table("processing_files").select("*").eq("id", file_id).execute()
            )
            if not file_result.data:
                raise ValueError(f"File {file_id} not found")

            file_record = file_result.data[0]

            if not file_record.get("extracted_text"):
                raise ValueError(f"No extracted text found for file {file_id}")

            # Update status to extracting metadata
            await self._update_file_status(file_id, FileStatus.EXTRACTING_METADATA)

            # Extract metadata using AI
            metadata_result = await self._extract_metadata_with_ai(
                file_record["extracted_text"], file_record["original_filename"]
            )

            if metadata_result["success"]:
                # Save metadata to database
                await self._save_metadata(file_id, metadata_result["metadata"])
                await self._update_file_status(file_id, FileStatus.METADATA_EXTRACTED)

                logger.info(f"Successfully extracted metadata from file {file_id}")
                return {
                    "success": True,
                    "file_id": file_id,
                    "metadata": metadata_result["metadata"],
                }
            else:
                await self._update_file_status(
                    file_id, FileStatus.AI_FAILED, error_message=metadata_result["error"]
                )
                return {"success": False, "file_id": file_id, "error": metadata_result["error"]}

        except Exception as e:
            logger.error(f"AI metadata extraction failed for file {file_id}: {e}")
            await self._update_file_status(file_id, FileStatus.AI_FAILED, error_message=str(e))
            return {"success": False, "file_id": file_id, "error": str(e)}

    async def _extract_metadata_with_ai(self, text: str, filename: str) -> Dict[str, Any]:
        """Extract metadata using AI models."""
        try:
            # Truncate text if too long (keep first part for metadata extraction)
            max_chars = 50000  # Reasonable limit for AI processing
            if len(text) > max_chars:
                text = text[:max_chars] + "...[truncated]"

            prompt = self._create_metadata_extraction_prompt(text, filename)

            # Try Anthropic first if available, fallback to OpenAI
            if self.anthropic_client:
                result = await self._extract_with_anthropic(prompt)
            elif self.openai_client:
                result = await self._extract_with_openai(prompt)
            else:
                return {"success": False, "error": "No AI API keys configured"}

            return result

        except Exception as e:
            logger.error(f"AI metadata extraction error: {e}")
            return {"success": False, "error": f"AI extraction failed: {str(e)}"}

    def _create_metadata_extraction_prompt(self, text: str, filename: str) -> str:
        """Create prompt for metadata extraction."""
        doc_types = [e.value for e in DocumentType]
        doc_categories = [e.value for e in DocumentCategory]

        return f"""
Analyze this document and extract metadata in JSON format.

Document filename: {filename}
Document text: {text}

Extract the following metadata:

1. title: Clear, descriptive title (if not obvious from text, derive from content)
2. authors: List of author names (empty list if none found)
3. publication_date: ISO date if found (YYYY-MM-DD format, null if not found)
4. doc_type: One of {doc_types}
   - book: Books, textbooks, reference materials
   - article: Academic papers, journal articles, research papers
   - statute: Laws, regulations, statutes
   - case_law: Court cases, legal precedents
   - expert_report: Expert witness reports, professional analyses
   - other: Any other document type
5. doc_category: One of {doc_categories}
   - PI: Personal Injury related
   - WD: Wrongful Death related
   - EM: Employment related
   - BV: Business Valuation related
   - Other: Other categories
6. description: Brief 2-3 sentence summary of document content
7. keywords: List of relevant keywords/tags (5-10 keywords)
8. bluebook_citation: If this is a legal document (case_law or statute), provide proper Bluebook citation format. Otherwise null.
9. confidence_scores: Object with confidence (0-1) for each field:
   - title_confidence
   - authors_confidence
   - date_confidence
   - type_confidence
   - category_confidence

Return ONLY valid JSON with no additional text or formatting:

{{
  "title": "string",
  "authors": ["string"],
  "publication_date": "YYYY-MM-DD or null",
  "doc_type": "string",
  "doc_category": "string",
  "description": "string",
  "keywords": ["string"],
  "bluebook_citation": "string or null",
  "confidence_scores": {{
    "title_confidence": 0.0,
    "authors_confidence": 0.0,
    "date_confidence": 0.0,
    "type_confidence": 0.0,
    "category_confidence": 0.0
  }}
}}
"""

    async def _extract_with_anthropic(self, prompt: str) -> Dict[str, Any]:
        """Extract metadata using Anthropic Claude."""
        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=2000,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}],
            )

            content = response.content[0].text.strip()

            # Parse JSON response
            metadata = json.loads(content)

            # Validate extracted metadata
            validated_metadata = self._validate_metadata(metadata)

            return {"success": True, "metadata": validated_metadata}

        except json.JSONDecodeError as e:
            logger.error(f"Anthropic returned invalid JSON: {e}")
            return {"success": False, "error": "AI returned invalid JSON response"}
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return {"success": False, "error": f"Anthropic API failed: {str(e)}"}

    async def _extract_with_openai(self, prompt: str) -> Dict[str, Any]:
        """Extract metadata using OpenAI GPT."""
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.1,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content.strip()

            # Parse JSON response
            metadata = json.loads(content)

            # Validate extracted metadata
            validated_metadata = self._validate_metadata(metadata)

            return {"success": True, "metadata": validated_metadata}

        except json.JSONDecodeError as e:
            logger.error(f"OpenAI returned invalid JSON: {e}")
            return {"success": False, "error": "AI returned invalid JSON response"}
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return {"success": False, "error": f"OpenAI API failed: {str(e)}"}

    def _validate_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean extracted metadata."""
        # Ensure required fields exist with defaults
        validated = {
            "title": metadata.get("title", "Unknown Title"),
            "authors": metadata.get("authors", []),
            "publication_date": metadata.get("publication_date"),
            "doc_type": metadata.get("doc_type", "other"),
            "doc_category": metadata.get("doc_category", "Other"),
            "description": metadata.get("description", ""),
            "keywords": metadata.get("keywords", []),
            "bluebook_citation": metadata.get("bluebook_citation"),
            "confidence_scores": metadata.get("confidence_scores", {}),
        }

        # Validate doc_type
        valid_doc_types = [e.value for e in DocumentType]
        if validated["doc_type"] not in valid_doc_types:
            validated["doc_type"] = "other"

        # Validate doc_category
        valid_doc_categories = [e.value for e in DocumentCategory]
        if validated["doc_category"] not in valid_doc_categories:
            validated["doc_category"] = "Other"

        # Ensure authors and keywords are lists
        if not isinstance(validated["authors"], list):
            validated["authors"] = []
        if not isinstance(validated["keywords"], list):
            validated["keywords"] = []

        # Validate publication_date format
        if validated["publication_date"]:
            try:
                datetime.fromisoformat(validated["publication_date"])
            except (ValueError, TypeError):
                validated["publication_date"] = None

        return validated

    async def _save_metadata(self, file_id: str, metadata: Dict[str, Any]):
        """Save extracted metadata to database."""
        try:
            update_data = {
                "ai_title": metadata["title"],
                "ai_authors": metadata["authors"],
                "ai_publication_date": metadata["publication_date"],
                "ai_doc_type": metadata["doc_type"],
                "ai_doc_category": metadata["doc_category"],
                "ai_description": metadata["description"],
                "ai_keywords": metadata["keywords"],
                "ai_bluebook_citation": metadata["bluebook_citation"],
                "ai_confidence_scores": metadata["confidence_scores"],
            }

            await db.supabase.table("processing_files").update(update_data).eq(
                "id", file_id
            ).execute()

        except Exception as e:
            logger.error(f"Failed to save metadata for file {file_id}: {e}")
            raise

    async def _update_file_status(self, file_id: str, status: FileStatus, **kwargs):
        """Update file processing status."""
        try:
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

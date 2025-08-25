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
        self.openai_client = None
        self.anthropic_client = None

        # Initialize OpenAI client if API key is available
        if settings.openai_api_key and settings.openai_api_key.strip():
            try:
                self.openai_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
                logger.info("OpenAI AI service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.openai_client = None

        # Initialize Anthropic client if API key is available
        if settings.anthropic_api_key and settings.anthropic_api_key.strip():
            try:
                self.anthropic_client = Anthropic(api_key=settings.anthropic_api_key)
                logger.info("Anthropic AI service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {e}")
                self.anthropic_client = None

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
            client = await db.get_supabase_client()
            file_result = await (
                client.table("processing_files").select("*").eq("id", file_id).execute()
            )
            if not file_result.data:
                raise ValueError(f"File {file_id} not found")

            file_record = file_result.data[0]

            if not file_record.get("extracted_text"):
                raise ValueError(f"No extracted text found for file {file_id}")

            # Update status to extracting metadata
            await self._update_file_status(file_id, FileStatus.ANALYZING_METADATA)

            # Extract metadata using AI
            metadata_result = await self._extract_metadata_with_ai(
                file_record["extracted_text"], file_record["original_filename"]
            )

            if metadata_result["success"]:
                # Save metadata to database
                await self._save_metadata(file_id, metadata_result["metadata"])
                await self._update_file_status(file_id, FileStatus.GENERATING_EMBEDDINGS)

                logger.info(f"Successfully extracted metadata from file {file_id}")
                return {
                    "success": True,
                    "file_id": file_id,
                    "metadata": metadata_result["metadata"],
                }
            else:
                await self._update_file_status(
                    file_id, FileStatus.ANALYSIS_FAILED, error_message=metadata_result["error"]
                )
                return {"success": False, "file_id": file_id, "error": metadata_result["error"]}

        except Exception as e:
            logger.error(f"AI metadata extraction failed for file {file_id}: {e}")
            await self._update_file_status(
                file_id, FileStatus.ANALYSIS_FAILED, error_message=str(e)
            )
            return {"success": False, "file_id": file_id, "error": str(e)}

    async def _extract_metadata_with_ai(self, text: str, filename: str) -> Dict[str, Any]:
        """Extract metadata using AI models combined with pattern extraction."""
        try:
            # Truncate text if too long (keep first part for metadata extraction)
            max_chars = 50000  # Reasonable limit for AI processing
            if len(text) > max_chars:
                text = text[:max_chars] + "...[truncated]"

            # Extract pattern-based metadata first
            pattern_metadata = self._extract_pattern_metadata(text)

            prompt = self._create_metadata_extraction_prompt(text, filename)

            # Try Anthropic first if available, fallback to OpenAI, then to basic extraction
            if self.anthropic_client:
                ai_result = await self._extract_with_anthropic(prompt)
            elif self.openai_client:
                ai_result = await self._extract_with_openai(prompt)
            else:
                logger.warning("No AI services available, using basic metadata extraction")
                ai_result = self._extract_basic_metadata(text, filename)

            if not ai_result["success"]:
                return ai_result

            # Combine AI results with pattern extraction
            metadata = ai_result["metadata"]

            # Use filename as fallback title if AI didn't extract a good one
            if not metadata.get("title") or metadata["title"] in ["Unknown Title", filename]:
                metadata["title"] = self._extract_title_from_filename(filename)

            # Add pattern-extracted financial data to metadata
            if pattern_metadata.get("dollar_amounts"):
                metadata["identified_amounts"] = pattern_metadata["dollar_amounts"]
            if pattern_metadata.get("potential_discount_rates"):
                metadata["identified_rates"] = pattern_metadata["potential_discount_rates"]
            if pattern_metadata.get("case_names"):
                metadata["case_citations"] = pattern_metadata["case_names"]
            if pattern_metadata.get("court"):
                # Only add if AI didn't extract it
                if not metadata.get("court"):
                    metadata["court"] = pattern_metadata["court"]

            # Enhance keywords with pattern-extracted terms
            ai_keywords = metadata.get("keywords", [])
            if pattern_metadata.get("case_names"):
                # Add case parties as keywords
                for case in pattern_metadata["case_names"][:2]:  # Limit to prevent spam
                    parties = case.replace(" v. ", " ").split()
                    ai_keywords.extend([p for p in parties if len(p) > 2])

            # Remove duplicates and limit keywords
            metadata["keywords"] = list(dict.fromkeys(ai_keywords))[:10]

            result = {"success": True, "metadata": metadata}

            return result

        except Exception as e:
            logger.error(f"AI metadata extraction error: {e}")
            return {"success": False, "error": f"AI extraction failed: {str(e)}"}

    def _detect_estate_case(self, text: str, filename: str) -> bool:
        """Detect if this is likely a wrongful death case based on estate patterns."""
        import re

        combined_text = f"{filename} {text[:2000]}".lower()

        # Look for estate patterns that indicate wrongful death
        estate_patterns = [
            r"\bestate\s+of\s+[a-z]+",
            r"\bestate\s+v\.",
            r"[a-z]+\s+estate\s+v\.",
            r"\bestate\b.*\bv\b",
            r"\bv\b.*\bestate\b",
        ]

        for pattern in estate_patterns:
            if re.search(pattern, combined_text):
                return True

        return False

    def _extract_pattern_metadata(self, text: str) -> Dict[str, Any]:
        """Extract metadata using regex patterns for forensic economics data."""
        import re

        metadata: Dict[str, Any] = {}

        # Extract dollar amounts
        dollar_pattern = r"\$[\d,]+(?:\.\d{2})?(?:\s*(?:million|billion|thousand|M|B|K))?"
        dollar_matches = re.findall(dollar_pattern, text, re.IGNORECASE)
        if dollar_matches:
            metadata["dollar_amounts"] = list(set(dollar_matches[:10]))

        # Extract percentages (potential discount rates)
        percent_pattern = r"(\d+(?:\.\d+)?)\s*%"
        percent_matches = re.findall(percent_pattern, text)
        if percent_matches:
            rates = [float(p) for p in percent_matches if 0 < float(p) < 30]
            if rates:
                metadata["potential_discount_rates"] = list(set(rates[:5]))

        # Extract case citations (e.g., "Smith v. Jones")
        case_pattern = (
            r"([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s+v\.\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)"
        )
        case_matches = re.findall(case_pattern, text[:3000])
        if case_matches:
            metadata["case_names"] = [f"{p} v. {d}" for p, d in case_matches[:3]]

        # Extract dates
        date_patterns = [
            r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}",
            r"\d{1,2}/\d{1,2}/\d{4}",
            r"\d{4}-\d{2}-\d{2}",
        ]

        for pattern in date_patterns:
            matches = re.findall(pattern, text[:3000], re.IGNORECASE)
            if matches:
                metadata["extracted_dates"] = matches[:5]
                break

        # Extract court names
        court_patterns = [
            r"(?:United States |U\.S\. )?(?:District |Circuit |Supreme )?Court[^,\.]{0,30}",
            r"(?:Superior|Municipal|County) Court[^,\.]{0,30}",
            r"\d+(?:st|nd|rd|th) (?:Circuit|District)[^,\.]{0,30}",
        ]

        for pattern in court_patterns:
            court_match = re.search(pattern, text[:3000], re.IGNORECASE)
            if court_match:
                metadata["court"] = court_match.group().strip()
                break

        return metadata

    def _extract_title_from_filename(self, filename: str) -> str:
        """Clean up filename to use as fallback title."""
        import re

        # Remove extension
        title = re.sub(r"\.[^.]+$", "", filename)
        # Replace underscores and hyphens with spaces
        title = re.sub(r"[_-]", " ", title)
        # Remove extra whitespace
        title = " ".join(title.split())
        # Title case
        title = title.title()
        return title

    def _create_metadata_extraction_prompt(self, text: str, filename: str) -> str:
        """Create prompt for metadata extraction."""
        # Truncate text to reasonable length for AI processing
        text_sample = text[:6000] if len(text) > 6000 else text

        # Detect estate case for wrongful death context
        is_estate_case = self._detect_estate_case(text_sample, filename)
        estate_context = ""
        if is_estate_case:
            estate_context = "\n\nIMPORTANT: This appears to involve an 'Estate of' plaintiff, which typically indicates a Wrongful Death case. Please classify doc_category as 'WD' unless there is clear evidence otherwise."

        doc_types = [e.value for e in DocumentType]
        doc_categories = [e.value for e in DocumentCategory]

        return f"""
You are a forensic economics expert analyzing legal documents. Extract comprehensive metadata from this document with high accuracy.

Document filename: {filename}
Document text (first 6000 characters): {text_sample}

Extract the following information:

1. title: Clear, descriptive document title (not just filename - analyze content for proper title)
2. authors: List of document authors, parties, experts, or key persons mentioned
3. publication_date: Document date in YYYY-MM-DD format (null if not clearly found)
4. doc_type: One of {doc_types}
   - book: Books, textbooks, reference materials, manuals
   - article: Academic papers, journal articles, research papers
   - statute: Laws, regulations, statutes, codes
   - case_law: Court cases, legal precedents, opinions, rulings
   - expert_report: Expert witness reports, professional analyses
   - other: Any other document type
5. doc_category: REQUIRED - One of {doc_categories}
   - Personal Injury: Physical injuries, accidents, medical malpractice, product liability
   - Wrongful Death: Death cases, estate plaintiffs, survival actions, loss of life
   - Employment: Wrongful termination, discrimination, workplace harassment, labor disputes
   - Business Valuation: Company valuations, business disputes, economic analysis, M&A
   - Other: Contract disputes, property issues, other legal matters
6. description: Brief 2-3 sentence summary focusing on key findings or purpose
7. keywords: List of 5-10 relevant legal/economic keywords and key topics
8. bluebook_citation: For legal documents, provide proper Bluebook citation format (null for non-legal docs)
9. confidence_scores: Your confidence (0.0 to 1.0) for each extracted field{estate_context}

DOCUMENT CATEGORY GUIDANCE:
- Look for case names like "Estate of [Name]" or "[Name] Estate" which indicate Wrongful Death (WD)
- Personal injury involves living persons with physical injuries
- Employment cases involve workplace issues, termination, discrimination
- Business valuation involves company values, economic analysis, financial disputes

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
                "ai_bluebook_citation": metadata.get("case_citations")
                or metadata["bluebook_citation"],
                "ai_confidence_scores": metadata["confidence_scores"],
                # Add pattern-extracted fields
                "ai_court": metadata.get("court"),
                "ai_identified_amounts": metadata.get("identified_amounts"),
                "ai_identified_rates": metadata.get("identified_rates"),
            }

            client = await db.get_supabase_client()
            await client.table("processing_files").update(update_data).eq("id", file_id).execute()

        except Exception as e:
            logger.error(f"Failed to save metadata for file {file_id}: {e}")
            raise

    def _extract_basic_metadata(self, text: str, filename: str) -> Dict[str, Any]:
        """Extract basic metadata without AI services."""
        import os

        # Generate basic metadata from filename and text analysis
        title = filename
        if title.endswith((".pdf", ".docx", ".txt", ".md")):
            title = os.path.splitext(title)[0]
        title = title.replace("_", " ").replace("-", " ").title()

        # Simple heuristics for doc type based on filename
        doc_type = "other"
        filename_lower = filename.lower()
        if any(word in filename_lower for word in ["statute", "law", "code", "regulation"]):
            doc_type = "statute"
        elif any(word in filename_lower for word in ["case", "court", "decision", "ruling"]):
            doc_type = "case_law"
        elif any(word in filename_lower for word in ["article", "paper", "journal"]):
            doc_type = "article"
        elif any(word in filename_lower for word in ["book", "textbook", "manual"]):
            doc_type = "book"

        # Basic summary from first 500 characters
        summary = text[:500].strip()
        if len(text) > 500:
            summary += "..."

        metadata = {
            "title": title,
            "authors": [],
            "publication_date": None,
            "doc_type": doc_type,
            "doc_category": "Other",
            "description": summary,
            "keywords": [],
            "bluebook_citation": None,
            "confidence_scores": {"overall": 0.5},  # Low confidence for basic extraction
            "extraction_method": "basic_heuristics",
        }

        logger.info(f"Generated basic metadata: {title} ({doc_type})")
        return {"success": True, "metadata": metadata}

    async def _update_file_status(self, file_id: str, status: FileStatus, **kwargs):
        """Update file processing status."""
        try:
            update_data = {
                "status": status.value,
                "updated_at": datetime.utcnow().isoformat(),
                **kwargs,
            }

            client = await db.get_supabase_client()
            await client.table("processing_files").update(update_data).eq("id", file_id).execute()

        except Exception as e:
            logger.error(f"Failed to update file {file_id} status: {e}")
            raise

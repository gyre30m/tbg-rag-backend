"""
Pydantic models for document-related data structures.
These models define the API request/response schemas.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import DocumentCategory, DocumentType


class DocumentBase(BaseModel):
    """Base document model with common fields."""

    title: str = Field(..., description="Document title")
    doc_type: DocumentType = Field(..., description="Type of document")
    doc_category: DocumentCategory = Field(..., description="Document category/practice area")
    authors: Optional[List[str]] = Field(default=None, description="Document authors")
    citation: Optional[str] = Field(default=None, description="Bluebook citation")
    summary: Optional[str] = Field(default=None, description="Document summary")
    tags: Optional[List[str]] = Field(default=None, description="Document tags/keywords")


class DocumentMetadata(DocumentBase):
    """Extended document metadata for case law and other specific types."""

    # Legal Information (for case_law)
    case_name: Optional[str] = Field(default=None, description="Case name (e.g., Smith v. Jones)")
    case_number: Optional[str] = Field(default=None, description="Court docket number")
    court: Optional[str] = Field(default=None, description="Court name")
    jurisdiction: Optional[str] = Field(default=None, description="Legal jurisdiction")
    practice_area: Optional[str] = Field(default=None, description="Area of law")
    date: Optional[datetime] = Field(default=None, description="Document date")

    # Expert Report Specific (for expert_report)
    methodologies: Optional[List[str]] = Field(
        default=None, description="Calculation methodologies used"
    )
    damage_amounts: Optional[List[float]] = Field(
        default=None, description="Dollar amounts calculated"
    )
    discount_rates: Optional[List[float]] = Field(
        default=None, description="Discount rates applied"
    )
    subject_ages: Optional[List[int]] = Field(
        default=None, description="Ages of subjects in analysis"
    )
    education_levels: Optional[List[str]] = Field(
        default=None, description="Education levels considered"
    )

    # AI Analysis
    confidence_score: Optional[float] = Field(
        default=None, ge=0, le=1, description="AI confidence in metadata extraction"
    )


class DocumentCreate(DocumentMetadata):
    """Model for creating new documents."""

    filename: str = Field(..., description="Generated filename")
    original_filename: str = Field(..., description="Original uploaded filename")
    content_hash: str = Field(..., description="Content hash for deduplication")
    file_size: int = Field(..., ge=0, description="File size in bytes")
    mime_type: str = Field(..., description="MIME type")
    storage_path: str = Field(..., description="Storage path in Supabase")
    page_count: Optional[int] = Field(default=None, ge=0, description="Number of pages")
    word_count: Optional[int] = Field(default=None, ge=0, description="Word count")


class DocumentUpdate(BaseModel):
    """Model for updating document metadata during review."""

    title: Optional[str] = None
    doc_type: Optional[DocumentType] = None
    doc_category: Optional[DocumentCategory] = None
    authors: Optional[List[str]] = None
    citation: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[List[str]] = None
    case_name: Optional[str] = None
    case_number: Optional[str] = None
    court: Optional[str] = None
    jurisdiction: Optional[str] = None
    practice_area: Optional[str] = None
    date: Optional[datetime] = None


class DocumentResponse(DocumentMetadata):
    """Full document response model."""

    id: UUID
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    storage_path: str
    page_count: Optional[int]
    word_count: Optional[int]
    content_hash: str
    is_reviewed: bool
    uploaded_by: UUID
    created_at: datetime
    updated_at: Optional[datetime]
    reviewed_by: Optional[UUID]
    reviewed_at: Optional[datetime]

    class Config:
        from_attributes = True


class DocumentLibraryItem(BaseModel):
    """Simplified document model for library listings."""

    id: UUID
    title: str
    doc_type: DocumentType
    doc_category: DocumentCategory
    authors: Optional[List[str]]
    citation: Optional[str]
    created_at: datetime
    file_size: int
    page_count: Optional[int]
    word_count: Optional[int]


class DocumentStats(BaseModel):
    """Document statistics for library dashboard."""

    total_documents: int
    books_textbooks: int
    articles_publications: int
    statutes_codes: int
    case_law: int
    expert_reports: int
    other_documents: int


class DocumentSearchQuery(BaseModel):
    """Search query parameters for document library."""

    search: Optional[str] = Field(default=None, description="Text search query")
    doc_type: Optional[DocumentType] = Field(default=None, description="Filter by document type")
    doc_category: Optional[DocumentCategory] = Field(default=None, description="Filter by category")
    page: int = Field(default=1, ge=1, description="Page number")
    limit: int = Field(default=50, ge=1, le=100, description="Items per page")


class DocumentSearchResponse(BaseModel):
    """Document search results."""

    documents: List[DocumentLibraryItem]
    page: int
    limit: int
    total: int
    has_more: bool


class DocumentSearchRequest(BaseModel):
    """Model for vector similarity search requests."""

    query: str = Field(..., description="Search query text")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of results")
    similarity_threshold: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Minimum similarity score"
    )
    doc_categories: Optional[List[str]] = Field(
        default=None, description="Optional document categories to filter by"
    )


class DocumentSearchResult(BaseModel):
    """Model for individual similarity search result."""

    content: str
    chunk_index: int
    filename: str
    title: Optional[str]
    doc_type: Optional[str]
    doc_category: Optional[str]
    similarity_score: float


class VectorSearchResponse(BaseModel):
    """Model for vector similarity search response."""

    query: str
    results: List[DocumentSearchResult]
    total_results: int

"""
Enums for document processing status and types.
These match the status definitions from our workflow documentation.
"""

from enum import Enum


class FileStatus(str, Enum):
    """File processing status enum - matches database constraint exactly."""

    # Upload Phase
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    UPLOAD_FAILED = "upload_failed"

    # Processing Phase
    QUEUED = "queued"
    EXTRACTING_TEXT = "extracting_text"
    EXTRACTION_FAILED = "extraction_failed"
    ANALYZING_METADATA = "analyzing_metadata"
    ANALYSIS_FAILED = "analysis_failed"
    GENERATING_EMBEDDINGS = "generating_embeddings"
    EMBEDDING_FAILED = "embedding_failed"
    PROCESSING_COMPLETE = "processing_complete"

    # Review Phase
    REVIEW_PENDING = "review_pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"

    # Special States
    DUPLICATE = "duplicate"
    CANCELLED = "cancelled"
    RETRY_PENDING = "retry_pending"


class BatchStatus(str, Enum):
    """Batch processing status enum - matches database constraint exactly."""

    CREATED = "created"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    PROCESSING_COMPLETE = "processing_complete"
    REVIEW_READY = "review_ready"
    UNDER_REVIEW = "under_review"
    REVIEW_COMPLETE = "review_complete"
    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially_completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DocumentType(str, Enum):
    """Document type enum."""

    BOOK = "book"
    ARTICLE = "article"
    STATUTE = "statute"
    CASE_LAW = "case_law"
    EXPERT_REPORT = "expert_report"
    OTHER = "other"


class DocumentCategory(str, Enum):
    """Document category enum."""

    PERSONAL_INJURY = "PI"
    WRONGFUL_DEATH = "WD"
    EMPLOYMENT = "EM"
    BUSINESS_VALUATION = "BV"
    OTHER = "Other"


class DocumentStatus(str, Enum):
    """Document status enum - matches database constraint exactly."""

    PROCESSING = "processing"  # Document is being processed
    REVIEW_PENDING = "review_pending"  # Ready for human review
    ACTIVE = "active"  # Approved and in library
    DELETED = "deleted"  # Soft deleted
    ARCHIVED = "archived"  # Archived for long-term storage


class LogLevel(str, Enum):
    """Log level enum for processing logs."""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"

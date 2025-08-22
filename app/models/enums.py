"""
Enums for document processing status and types.
These match the status definitions from our workflow documentation.
"""

from enum import Enum


class FileStatus(str, Enum):
    """File processing status enum."""

    # Upload Phase
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    UPLOAD_FAILED = "upload_failed"

    # Processing Phase
    QUEUED = "queued"
    EXTRACTING = "extracting"
    EXTRACTION_FAILED = "extraction_failed"
    ANALYZING = "analyzing"
    ANALYSIS_FAILED = "analysis_failed"
    EMBEDDING = "embedding"
    EMBEDDING_FAILED = "embedding_failed"

    # Review Phase
    REVIEW_PENDING = "review_pending"
    REVIEW_IN_PROGRESS = "review_in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"

    # Special Cases
    DUPLICATE = "duplicate"
    CANCELLED = "cancelled"
    RETRY_PENDING = "retry_pending"


class BatchStatus(str, Enum):
    """Batch processing status enum (calculated from file statuses)."""

    CREATED = "created"
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    EXTRACTING = "extracting"
    ANALYZING = "analyzing"
    EMBEDDING = "embedding"
    REVIEW_READY = "review_ready"
    PARTIALLY_APPROVED = "partially_approved"
    COMPLETED = "completed"
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


class LogLevel(str, Enum):
    """Log level enum for processing logs."""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"

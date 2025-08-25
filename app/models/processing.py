"""
Pydantic models for document processing and job management.
These models handle the upload, processing, and review workflow.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator

from app.models.enums import BatchStatus, FileStatus, LogLevel


class ProcessingJobBase(BaseModel):
    """Base processing job model."""

    total_files: int = Field(..., ge=0, description="Total number of files in batch")
    processed_files: int = Field(default=0, ge=0, description="Number of files processed")
    completed_files: int = Field(default=0, ge=0, description="Number of files completed")
    failed_files: int = Field(default=0, ge=0, description="Number of files failed")


class ProcessingJobCreate(ProcessingJobBase):
    """Model for creating new processing jobs."""

    webhook_url: Optional[str] = Field(default=None, description="Webhook URL for status updates")
    webhook_secret: Optional[str] = Field(
        default=None, description="Webhook secret for verification"
    )


class ProcessingJobResponse(ProcessingJobBase):
    """Full processing job response."""

    id: UUID
    status: BatchStatus
    error_message: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    last_webhook_at: Optional[datetime]

    class Config:
        from_attributes = True


class ProcessingFileBase(BaseModel):
    """Base processing file model."""

    original_filename: str = Field(..., description="Original uploaded filename")
    file_size: int = Field(..., ge=0, description="File size in bytes")
    mime_type: str = Field(..., description="MIME type")


class ProcessingFileCreate(ProcessingFileBase):
    """Model for creating processing file records."""

    batch_id: UUID = Field(..., description="Parent processing job ID")
    stored_path: str = Field(..., description="Storage path in Supabase")
    content_hash: Optional[str] = Field(default=None, description="Content hash")


class ProcessingFileUpdate(BaseModel):
    """Model for updating processing file status."""

    status: Optional[FileStatus] = None
    document_id: Optional[UUID] = None
    extracted_text: Optional[str] = None
    word_count: Optional[int] = None
    page_count: Optional[int] = None
    content_hash: Optional[str] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    retry_count: Optional[int] = None
    last_retry_at: Optional[datetime] = None


class ProcessingFileResponse(ProcessingFileBase):
    """Full processing file response."""

    id: UUID
    batch_id: UUID
    document_id: Optional[UUID]
    stored_path: str
    status: FileStatus
    content_hash: Optional[str]
    word_count: Optional[int]
    page_count: Optional[int]
    error_message: Optional[str]
    error_details: Optional[Dict[str, Any]]
    retry_count: int
    last_retry_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class UploadFileInfo(BaseModel):
    """Information about uploaded file."""

    filename: str
    size: int
    content_type: str

    @validator("content_type")
    def validate_content_type(cls, v):
        """Validate that content type is supported."""
        supported_types = [
            "application/pdf",
            "text/plain",
            "text/markdown",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ]
        if v not in supported_types:
            raise ValueError(f"Unsupported file type: {v}")
        return v

    @validator("size")
    def validate_file_size(cls, v):
        """Validate file size is within limits."""
        max_size = 52428800  # 50MB
        if v > max_size:
            raise ValueError(f"File too large: {v} bytes (max: {max_size})")
        return v


class FailedFileInfo(BaseModel):
    """Information about a failed file upload."""

    filename: str
    error: str
    is_duplicate: Optional[bool] = False
    existing_document_id: Optional[UUID] = None
    existing_processing_file_id: Optional[UUID] = None


class UploadResponse(BaseModel):
    """Response from file upload endpoint."""

    job_id: UUID
    uploaded_files: List[UUID]
    failed_files: List[FailedFileInfo]
    total_files: int
    success_count: int
    error_count: int


class ReviewQueueItem(BaseModel):
    """Item in the review queue."""

    id: UUID
    document_id: UUID
    title: str
    original_filename: str
    doc_type: str
    doc_category: str
    confidence_score: Optional[float]
    processing_status: FileStatus
    file_size: int
    uploaded_at: datetime
    batch_id: UUID
    preview_text: Optional[str] = Field(description="First 500 chars of extracted text")


class ReviewQueueResponse(BaseModel):
    """Review queue listing response."""

    queue: List[ReviewQueueItem]
    total_pending: int
    total_in_progress: int


class ProcessingLog(BaseModel):
    """Processing log entry."""

    job_id: UUID
    job_status: BatchStatus
    created_at: datetime
    total_files: int
    completed_files: int
    failed_files: int
    log_message: str
    log_level: LogLevel


class ProcessingLogsResponse(BaseModel):
    """Processing logs response."""

    logs: List[ProcessingLog]
    total_logs: int


class BatchStatusSummary(BaseModel):
    """Summary of batch processing status."""

    job: ProcessingJobResponse
    batch_status: BatchStatus
    files: List[ProcessingFileResponse]
    status_counts: Dict[str, int]
    progress_percent: float


class WebhookEvent(BaseModel):
    """Webhook event payload."""

    type: str = Field(..., description="Event type")
    data: Dict[str, Any] = Field(..., description="Event data")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

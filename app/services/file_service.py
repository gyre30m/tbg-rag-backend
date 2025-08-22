"""
File service for handling document uploads and storage operations.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Tuple
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import settings
from app.core.database import db
from app.models.enums import FileStatus
from app.models.processing import ProcessingFileCreate, UploadResponse
from app.services.processing_service import ProcessingService
from app.utils.file_utils import FileValidator, calculate_content_hash, generate_safe_filename

logger = logging.getLogger(__name__)


class FileService:
    """Handles file upload, validation, and storage operations."""

    def __init__(self):
        self.validator = FileValidator()
        self.processing_service = ProcessingService()

    async def upload_files(self, files: List[UploadFile], user_id: str) -> UploadResponse:
        """
        Upload multiple files and create processing job.

        Args:
            files: List of uploaded files
            user_id: ID of the user uploading files

        Returns:
            UploadResponse with job details and results
        """
        logger.info(f"Starting upload of {len(files)} files for user {user_id}")

        # Validate batch size
        if len(files) > settings.max_files_per_batch:
            raise ValueError(f"Too many files: {len(files)} (max: {settings.max_files_per_batch})")

        # Create processing job
        job_data = {
            "total_files": len(files),
            "processed_files": 0,
            "completed_files": 0,
            "failed_files": 0,
            "status": "created",
            "created_at": datetime.utcnow().isoformat(),
        }

        job_result = await db.supabase.table("processing_jobs").insert(job_data).execute()
        job_id = job_result.data[0]["id"]

        uploaded_files = []
        failed_files = []

        # Process each file
        for file in files:
            try:
                file_result = await self._process_single_file(file, job_id, user_id)

                if file_result["success"]:
                    uploaded_files.append(file_result["file_id"])
                else:
                    failed_files.append({"filename": file.filename, "error": file_result["error"]})

            except Exception as e:
                logger.error(f"Failed to process file {file.filename}: {e}")
                failed_files.append({"filename": file.filename, "error": str(e)})

        # Update job with results
        await db.supabase.table("processing_jobs").update(
            {
                "status": "uploaded" if uploaded_files else "failed",
                "processed_files": len(uploaded_files),
                "failed_files": len(failed_files),
            }
        ).eq("id", job_id).execute()

        # Start background processing for successful uploads
        if uploaded_files:
            await self._start_background_processing(uploaded_files)

        return UploadResponse(
            job_id=job_id,
            uploaded_files=uploaded_files,
            failed_files=failed_files,
            total_files=len(files),
            success_count=len(uploaded_files),
            error_count=len(failed_files),
        )

    async def _process_single_file(
        self, file: UploadFile, job_id: str, user_id: str
    ) -> Dict[str, Any]:
        """
        Process a single uploaded file.

        Args:
            file: Uploaded file
            job_id: Processing job ID
            user_id: User ID

        Returns:
            Dict with success status and file_id or error
        """
        try:
            # Read file content
            content = await file.read()
            await file.seek(0)  # Reset file pointer

            # Validate file
            validation_result = self.validator.validate_file(file.filename, content)
            if not validation_result.is_valid:
                return {"success": False, "error": "; ".join(validation_result.errors)}

            # Calculate content hash for deduplication
            content_hash = calculate_content_hash(content)

            # Check for existing document with same hash
            existing = (
                await db.supabase.table("documents")
                .select("id")
                .eq("content_hash", content_hash)
                .execute()
            )
            if existing.data:
                return {"success": False, "error": "Duplicate document already exists"}

            # Generate unique storage path
            file_id = str(uuid4())
            safe_filename = generate_safe_filename(file.filename, file_id)
            storage_path = f"uploads/{safe_filename}"

            # Upload to Supabase Storage
            upload_result = db.supabase.storage.from_("documents").upload(
                storage_path, content, {"content-type": file.content_type}
            )

            if hasattr(upload_result, "error") and upload_result.error:
                logger.error(f"Storage upload failed: {upload_result.error}")
                return {"success": False, "error": "Storage upload failed"}

            # Create processing file record
            file_data = {
                "batch_id": job_id,
                "original_filename": file.filename,
                "stored_path": storage_path,
                "file_size": len(content),
                "mime_type": file.content_type,
                "content_hash": content_hash,
                "status": FileStatus.UPLOADED.value,
                "retry_count": 0,
                "created_at": datetime.utcnow().isoformat(),
            }

            file_result = await db.supabase.table("processing_files").insert(file_data).execute()
            file_record_id = file_result.data[0]["id"]

            logger.info(f"Successfully uploaded file {file.filename} with ID {file_record_id}")

            return {"success": True, "file_id": file_record_id, "storage_path": storage_path}

        except Exception as e:
            logger.error(f"Error processing file {file.filename}: {e}")
            return {"success": False, "error": f"Processing error: {str(e)}"}

    async def _start_background_processing(self, file_ids: List[str]):
        """
        Start background processing for uploaded files.

        Args:
            file_ids: List of processing file IDs to process
        """
        logger.info(f"Starting background processing for {len(file_ids)} files")

        # Queue each file for text extraction
        for file_id in file_ids:
            try:
                await self.processing_service.queue_text_extraction(file_id)
            except Exception as e:
                logger.error(f"Failed to queue file {file_id} for processing: {e}")

                # Mark file as failed
                await db.supabase.table("processing_files").update(
                    {
                        "status": FileStatus.EXTRACTION_FAILED.value,
                        "error_message": f"Failed to queue for processing: {str(e)}",
                    }
                ).eq("id", file_id).execute()

    async def get_file_content(self, storage_path: str) -> bytes:
        """
        Retrieve file content from storage.

        Args:
            storage_path: Path to file in storage

        Returns:
            File content as bytes
        """
        try:
            download_result = db.supabase.storage.from_("documents").download(storage_path)
            return download_result
        except Exception as e:
            logger.error(f"Failed to download file {storage_path}: {e}")
            raise

    async def delete_file(self, storage_path: str) -> bool:
        """
        Delete file from storage.

        Args:
            storage_path: Path to file in storage

        Returns:
            True if successful, False otherwise
        """
        try:
            delete_result = db.supabase.storage.from_("documents").remove([storage_path])
            return True
        except Exception as e:
            logger.error(f"Failed to delete file {storage_path}: {e}")
            return False

    async def update_file_status(self, file_id: str, status: FileStatus, **kwargs) -> bool:
        """
        Update file processing status.

        Args:
            file_id: Processing file ID
            status: New status
            **kwargs: Additional fields to update

        Returns:
            True if successful, False otherwise
        """
        try:
            update_data = {
                "status": status.value,
                "updated_at": datetime.utcnow().isoformat(),
                **kwargs,
            }

            await db.supabase.table("processing_files").update(update_data).eq(
                "id", file_id
            ).execute()

            logger.debug(f"Updated file {file_id} status to {status.value}")
            return True

        except Exception as e:
            logger.error(f"Failed to update file {file_id} status: {e}")
            return False

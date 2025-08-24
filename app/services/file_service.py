"""
File service for handling document uploads and storage operations.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import settings
from app.core.database import db
from app.models.enums import BatchStatus, DocumentStatus, FileStatus
from app.models.processing import UploadResponse
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
        start_time = time.time()
        logger.info(f"🔄 UPLOAD START: {len(files)} files for user {user_id}")

        # Validate batch size
        if len(files) == 0:
            raise ValueError("No files provided")
        if len(files) > settings.max_files_per_batch:
            raise ValueError(f"Too many files: {len(files)} (max: {settings.max_files_per_batch})")

        # Create processing job
        job_data = {
            "total_files": len(files),
            "processed_files": 0,
            "completed_files": 0,
            "failed_files": 0,
            "status": BatchStatus.CREATED.value,  # Use enum value
            "created_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"📝 Creating processing job for {len(files)} files")
        client = await db.get_supabase_client()
        job_result = await client.table("processing_jobs").insert(job_data).execute()
        job_id = job_result.data[0]["id"]
        logger.info(f"✅ Processing job created: {job_id}")

        uploaded_files = []
        failed_files = []

        # Process each file
        for i, file in enumerate(files, 1):
            file_start = time.time()
            logger.info(f"📄 Processing file {i}/{len(files)}: {file.filename} ({file.size} bytes)")
            try:
                file_result = await self._process_single_file(file, job_id, user_id)
                file_duration = time.time() - file_start

                if file_result["success"]:
                    uploaded_files.append(file_result["file_id"])
                    logger.info(
                        f"✅ File processed successfully: {file.filename} in {file_duration:.2f}s"
                    )
                else:
                    failure_info = {"filename": file.filename, "error": file_result["error"]}
                    if file_result.get("is_duplicate"):
                        failure_info["is_duplicate"] = True
                        failure_info["existing_document_id"] = file_result.get(
                            "existing_document_id"
                        )
                    failed_files.append(failure_info)
                    logger.error(
                        f"❌ File processing failed: {file.filename} - {file_result['error']} ({file_duration:.2f}s)"
                    )

            except Exception as e:
                file_duration = time.time() - file_start
                logger.error(
                    f"❌ Exception processing file {file.filename}: {e} ({file_duration:.2f}s)"
                )
                failed_files.append({"filename": file.filename, "error": str(e)})

        # Update job with results
        client = await db.get_supabase_client()
        await client.table("processing_jobs").update(
            {
                "status": BatchStatus.PROCESSING.value
                if uploaded_files
                else BatchStatus.FAILED.value,
                "processed_files": len(uploaded_files) + len(failed_files),
                "failed_files": len(failed_files),
            }
        ).eq("id", job_id).execute()

        # Start background processing for successful uploads
        if uploaded_files:
            asyncio.create_task(self._start_background_processing(uploaded_files))

        return UploadResponse(
            job_id=job_id,
            uploaded_files=uploaded_files,
            failed_files=failed_files,
            total_files=len(files),
            success_count=len(uploaded_files),
            error_count=len(failed_files),
        )

        total_duration = time.time() - start_time
        logger.info(
            f"🎯 UPLOAD COMPLETE: {len(uploaded_files)} successful, {len(failed_files)} failed in {total_duration:.2f}s"
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
            client = await db.get_supabase_client()

            # Check 1: Documents that are fully processed and in the library
            existing_documents = (
                await client.table("documents")
                .select("id, title")
                .eq("content_hash", content_hash)
                .eq("is_deleted", False)  # Only check non-deleted documents
                .execute()
            )

            # Check 2: Processing files that are currently being processed successfully
            # Exclude failed states: failed, extraction_failed, duplicate, cancelled
            existing_processing = (
                await client.table("processing_files")
                .select("id, original_filename, status")
                .eq("content_hash", content_hash)
                .not_.in_("status", ["failed", "extraction_failed", "duplicate", "cancelled"])
                .execute()
            )

            if existing_documents.data:
                document = existing_documents.data[0]
                return {
                    "success": False,
                    "error": f"Document already exists in library: {document.get('title', 'Untitled')}",
                    "is_duplicate": True,
                    "existing_document_id": document["id"],
                }

            if existing_processing.data:
                processing_file = existing_processing.data[0]
                return {
                    "success": False,
                    "error": f"Document is already being processed: {processing_file.get('original_filename', 'Unknown')} (Status: {processing_file.get('status', 'unknown')})",
                    "is_duplicate": True,
                    "existing_processing_file_id": processing_file["id"],
                }

            # Generate unique storage path
            file_id = str(uuid4())
            safe_filename = generate_safe_filename(file.filename, file_id)
            storage_path = f"uploads/{safe_filename}"

            # Upload to Supabase Storage
            client = await db.get_supabase_client()
            upload_result = await client.storage.from_("documents").upload(
                storage_path, content, {"content-type": file.content_type}
            )

            if hasattr(upload_result, "error") and upload_result.error:
                logger.error(f"Storage upload failed: {upload_result.error}")
                return {"success": False, "error": "Storage upload failed"}

            # Create document record immediately with basic information
            document_data = {
                "title": file.filename,  # Use filename as initial title
                "filename": safe_filename,
                "original_filename": file.filename,
                "doc_type": "other",  # Default type, will be updated by AI
                "doc_category": "Other",  # Default category, will be updated by AI
                "content_hash": content_hash,
                "file_size": len(content),
                "mime_type": file.content_type,
                "storage_path": storage_path,
                "is_reviewed": False,  # Not yet reviewed
                "is_deleted": False,
                "is_archived": False,
                "uploaded_by": user_id,
                "created_at": datetime.utcnow().isoformat(),
            }

            document_result = await client.table("documents").insert(document_data).execute()
            document_id = document_result.data[0]["id"]

            # Create processing file record linked to the document
            file_data = {
                "batch_id": job_id,
                "document_id": document_id,  # Link to the document immediately
                "original_filename": file.filename,
                "stored_path": storage_path,
                "file_size": len(content),
                "mime_type": file.content_type,
                "content_hash": content_hash,
                "status": FileStatus.UPLOADED.value,
                "retry_count": 0,
                "created_at": datetime.utcnow().isoformat(),
            }

            file_result = await client.table("processing_files").insert(file_data).execute()
            file_record_id = file_result.data[0]["id"]

            logger.info(
                f"Successfully uploaded file {file.filename} with processing ID {file_record_id} and document ID {document_id}"
            )

            return {
                "success": True,
                "file_id": file_record_id,
                "document_id": document_id,
                "storage_path": storage_path,
            }

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
                client = await db.get_supabase_client()
                await client.table("processing_files").update(
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
            client = await db.get_supabase_client()
            download_result = await client.storage.from_("documents").download(storage_path)
            return bytes(download_result)
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
            client = await db.get_supabase_client()
            await client.storage.from_("documents").remove([storage_path])
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

            client = await db.get_supabase_client()
            await client.table("processing_files").update(update_data).eq("id", file_id).execute()

            logger.debug(f"Updated file {file_id} status to {status.value}")
            return True

        except Exception as e:
            logger.error(f"Failed to update file {file_id} status: {e}")
            return False

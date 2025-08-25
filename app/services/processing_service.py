"""
Processing orchestration service for managing document processing workflows.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.database import db
from app.core.logging_utils import processing_logger
from app.models.enums import BatchStatus, DocumentStatus, FileStatus
from app.services.ai_service import AIService
from app.services.langchain_processor import langchain_processor

logger = logging.getLogger(__name__)


class ProcessingService:
    """Orchestrates the document processing pipeline."""

    def __init__(self):
        self.ai_service = AIService()
        # LangChain handles extraction, chunking, and embeddings
        self.max_concurrent_files = 5  # Limit concurrent processing

    async def queue_text_extraction(self, file_id: str) -> bool:
        """
        Queue a file for text extraction processing.

        Args:
            file_id: Processing file ID

        Returns:
            True if successfully queued
        """
        try:
            logger.info(f"🚀 QUEUE: Starting text extraction for file {file_id}")

            # Update file status to queued
            await self._update_file_status(file_id, FileStatus.QUEUED)
            await self._update_document_processing_status(file_id, "extracting_text")

            # Start background processing (fire and forget)
            logger.info(f"🔄 QUEUE: Creating async task for file {file_id}")
            asyncio.create_task(self._process_file_pipeline(file_id))
            logger.info(f"✅ QUEUE: File {file_id} queued successfully")

            return True

        except Exception as e:
            logger.error(f"❌ QUEUE: Failed to queue file {file_id}: {e}")
            return False

    async def process_batch(self, batch_id: str) -> Dict[str, Any]:
        """
        Process all files in a batch through the complete pipeline.

        Args:
            batch_id: Processing job/batch ID

        Returns:
            Dict with processing results
        """
        logger.info(f"Starting batch processing for batch {batch_id}")

        try:
            # Get all files in the batch
            client = await db.get_supabase_client()
            files_result = await (
                client.table("processing_files")
                .select("id, status")
                .eq("batch_id", batch_id)
                .execute()
            )

            if not files_result.data:
                return {"success": False, "batch_id": batch_id, "error": "No files found in batch"}

            file_ids = [
                f["id"] for f in files_result.data if f["status"] == FileStatus.UPLOADED.value
            ]

            if not file_ids:
                return {
                    "success": False,
                    "batch_id": batch_id,
                    "error": "No files ready for processing",
                }

            # Update batch status to processing
            await self._update_batch_status(batch_id, BatchStatus.PROCESSING)

            # Process files with concurrency control
            semaphore = asyncio.Semaphore(self.max_concurrent_files)
            tasks = [self._process_file_with_semaphore(semaphore, file_id) for file_id in file_ids]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Analyze results
            successful = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
            failed = len(results) - successful

            # Update batch with final status
            final_status = BatchStatus.PROCESSING_COMPLETE if failed == 0 else BatchStatus.FAILED
            await self._update_batch_status(
                batch_id, final_status, processed_files=successful, failed_files=failed
            )

            logger.info(
                f"Batch {batch_id} processing complete: {successful} success, {failed} failed"
            )

            return {
                "success": True,
                "batch_id": batch_id,
                "total_files": len(file_ids),
                "successful_files": successful,
                "failed_files": failed,
                "status": final_status.value,
            }

        except Exception as e:
            logger.error(f"Batch processing failed for batch {batch_id}: {e}")
            await self._update_batch_status(batch_id, BatchStatus.FAILED, error_message=str(e))
            return {"success": False, "batch_id": batch_id, "error": str(e)}

    async def _process_file_with_semaphore(
        self, semaphore: asyncio.Semaphore, file_id: str
    ) -> Dict[str, Any]:
        """Process a single file with concurrency control."""
        async with semaphore:
            return await self._process_file_pipeline(file_id)

    async def _process_file_pipeline(self, file_id: str) -> Dict[str, Any]:
        """
        Process a single file through the complete pipeline.

        Args:
            file_id: Processing file ID

        Returns:
            Dict with processing results
        """
        start_time = time.time()
        processing_logger.log_step("langchain_pipeline_start", file_id=file_id)

        try:
            # Get file path for LangChain processing
            client = await db.get_supabase_client()
            file_result = (
                await client.table("processing_files").select("*").eq("id", file_id).execute()
            )

            if not file_result.data:
                raise ValueError(f"File {file_id} not found")

            file_record = file_result.data[0]
            file_path = file_record.get("stored_path")

            if not file_path:
                raise ValueError(f"File path not found for file {file_id}")

            # Use LangChain processor for extraction, chunking, and embeddings
            # Note: LangChain processor handles status updates internally
            try:
                langchain_result = await langchain_processor.process_pdf_file(file_id, file_path)
            except Exception as e:
                logger.error(f"LangChain processing failed for file {file_id}: {e}")
                # Fallback to avoid breaking deployment
                langchain_result = {"success": False, "error": f"Processing failed: {str(e)}"}

            if not langchain_result["success"]:
                return langchain_result

            # Step 2: AI Metadata Extraction (still using our custom AI service)
            step_start = time.time()
            processing_logger.log_step("ai_metadata_start", file_id=file_id)
            await self._update_document_processing_status(file_id, "analyzing_metadata")
            metadata_result = await self.ai_service.extract_metadata(file_id)
            step_duration = time.time() - step_start

            if not metadata_result["success"]:
                processing_logger.log_error(
                    "ai_metadata_failed",
                    Exception(metadata_result.get("error", "Unknown error")),
                    file_id=file_id,
                    duration_seconds=step_duration,
                )
                return dict(metadata_result)
            processing_logger.log_step(
                "ai_metadata_complete", file_id=file_id, duration_seconds=step_duration
            )

            # Step 3: Update document record with text metrics
            # (AI service already saved metadata directly to documents)
            logger.info(f"📄 STEP 3: Updating document record with text metrics for file {file_id}")

            # Merge text metrics from langchain with AI metadata
            combined_metadata = metadata_result.get("metadata", {})
            combined_metadata.update(
                {
                    "preview_text": langchain_result.get("preview_text"),
                    "page_count": langchain_result.get("page_count"),
                    "word_count": langchain_result.get("word_count"),
                    "char_count": langchain_result.get("char_count"),
                    "chunk_count": langchain_result.get("chunk_count"),
                }
            )

            document_id = await self._update_document_with_text_metrics(file_id, combined_metadata)

            # Mark file as ready for review
            logger.info(f"📋 Marking file {file_id} as ready for review")
            await self._update_file_status(
                file_id, FileStatus.REVIEW_PENDING, document_id=document_id
            )
            await self._update_document_processing_status(file_id, "ready_for_review")

            # Clean up processing_files to save storage
            # Remove large fields that are no longer needed
            logger.info(f"🧹 Cleaning up processing_files record {file_id}")
            await self._cleanup_processing_file(file_id)

            # Check if batch is complete after this file finishes
            client = await db.get_supabase_client()
            file_result = (
                await client.table("processing_files")
                .select("batch_id")
                .eq("id", file_id)
                .execute()
            )
            if file_result.data:
                await self._check_batch_completion(file_result.data[0]["batch_id"])

            total_duration = time.time() - start_time
            logger.info(
                f"🎯 PIPELINE COMPLETE: File {file_id} processed successfully in {total_duration:.2f}s"
            )

            return {
                "success": True,
                "file_id": file_id,
                "text_length": langchain_result.get("text_length", 0),
                "page_count": 0,  # LangChain doesn't track page count in this simple version
                "chunk_count": langchain_result.get("chunk_count", 0),
                "metadata": metadata_result.get("metadata", {}),
                "status": FileStatus.REVIEW_PENDING.value,
            }

        except Exception as e:
            total_duration = time.time() - start_time
            logger.error(
                f"💥 PIPELINE FAILED: File {file_id} failed after {total_duration:.2f}s: {e}"
            )

            # Instead of marking as failed, delete the document (cascades to chunks, etc.)
            await self._delete_failed_document(file_id, error_message=str(e))

            # Still update processing file status for tracking
            await self._update_file_status(
                file_id, FileStatus.EXTRACTION_FAILED, error_message=str(e)
            )

            # Check if batch is complete after this file fails
            try:
                client = await db.get_supabase_client()
                file_result = (
                    await client.table("processing_files")
                    .select("batch_id")
                    .eq("id", file_id)
                    .execute()
                )
                if file_result.data:
                    await self._check_batch_completion(file_result.data[0]["batch_id"])
            except Exception as batch_check_error:
                logger.error(f"Failed to check batch completion: {batch_check_error}")

            return {"success": False, "file_id": file_id, "error": str(e)}

    async def _update_document_with_text_metrics(
        self, file_id: str, ai_metadata: Dict[str, Any]
    ) -> str:
        """
        Update document with text metrics from langchain processing.
        Note: AI metadata is now saved directly to documents by AI service.

        Args:
            file_id: Processing file ID
            ai_metadata: Extracted AI metadata

        Returns:
            Document ID
        """
        try:
            # Get processing file record and its document
            client = await db.get_supabase_client()
            file_result = (
                await client.table("processing_files")
                .select("document_id")
                .eq("id", file_id)
                .execute()
            )

            if not file_result.data:
                raise ValueError(f"Processing file {file_id} not found")

            document_id = file_result.data[0].get("document_id")

            if not document_id:
                raise ValueError(f"No document linked to processing file {file_id}")

            # Only update text metrics from langchain processor
            # AI metadata is saved directly by AI service now
            document_update_data = {
                # Text metadata from extraction
                "preview_text": ai_metadata.get("preview_text"),
                "page_count": ai_metadata.get("page_count"),
                "word_count": ai_metadata.get("word_count"),
                "char_count": ai_metadata.get("char_count"),
                "chunk_count": ai_metadata.get("chunk_count"),
                "updated_at": datetime.utcnow().isoformat(),
            }

            # Remove None values to avoid overwriting existing data
            document_update_data = {k: v for k, v in document_update_data.items() if v is not None}

            # Update the existing document record
            document_result = (
                await client.table("documents")
                .update(document_update_data)
                .eq("id", document_id)
                .execute()
            )

            if not document_result.data:
                raise ValueError(f"Failed to update document {document_id}")

            # Update document chunks to reference the document (in case they weren't linked before)
            await client.table("document_chunks").update({"document_id": document_id}).eq(
                "processing_file_id", file_id
            ).execute()

            logger.info(
                f"✅ Document {document_id} updated with AI metadata for file {file_id} and ready for review"
            )
            return str(document_id)

        except Exception as e:
            logger.error(f"❌ Failed to update document with metadata for file {file_id}: {e}")
            raise

    async def approve_file_for_library(
        self, file_id: str, reviewer_id: str, review_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Approve a processed file for inclusion in the document library.

        Args:
            file_id: Processing file ID
            reviewer_id: ID of the reviewing user
            review_notes: Optional review notes

        Returns:
            Dict with approval results
        """
        logger.info(f"Approving file {file_id} for library by reviewer {reviewer_id}")

        try:
            # Get processing file record
            client = await db.get_supabase_client()
            file_result = await (
                client.table("processing_files").select("*").eq("id", file_id).execute()
            )
            if not file_result.data:
                raise ValueError(f"File {file_id} not found")

            file_record = file_result.data[0]
            document_id = file_record.get("document_id")

            if not document_id:
                raise ValueError(f"No document linked to processing file {file_id}")

            if file_record["status"] != FileStatus.REVIEW_PENDING.value:
                raise ValueError(
                    f"File {file_id} is not ready for review (status: {file_record['status']})"
                )

            # Update existing document to mark as approved and active
            document_update_data = {
                # Document approved - mark as reviewed and active in library
                "is_reviewed": True,
                "reviewed_by": reviewer_id,
                "reviewed_at": datetime.utcnow().isoformat(),
                "review_notes": review_notes,
                "updated_at": datetime.utcnow().isoformat(),
            }

            # Update the document record
            document_result = (
                await client.table("documents")
                .update(document_update_data)
                .eq("id", document_id)
                .execute()
            )

            if not document_result.data:
                raise ValueError(f"Failed to update document {document_id}")

            # Update processing file status
            await self._update_file_status(
                file_id,
                FileStatus.APPROVED,
                reviewed_by=reviewer_id,
                reviewed_at=datetime.utcnow().isoformat(),
                review_notes=review_notes,
            )

            logger.info(f"File {file_id} approved and document {document_id} moved to library")

            return {
                "success": True,
                "file_id": file_id,
                "document_id": document_id,
                "status": FileStatus.APPROVED.value,
            }

        except Exception as e:
            logger.error(f"Failed to approve file {file_id}: {e}")
            return {"success": False, "file_id": file_id, "error": str(e)}

    async def reject_file(
        self, file_id: str, reviewer_id: str, rejection_reason: str
    ) -> Dict[str, Any]:
        """
        Reject a processed file from inclusion in the document library.

        Args:
            file_id: Processing file ID
            reviewer_id: ID of the reviewing user
            rejection_reason: Reason for rejection

        Returns:
            Dict with rejection results
        """
        logger.info(f"Rejecting file {file_id} by reviewer {reviewer_id}")

        try:
            # Update processing file status
            await self._update_file_status(
                file_id,
                FileStatus.REJECTED,
                reviewed_by=reviewer_id,
                reviewed_at=datetime.utcnow().isoformat(),
                review_notes=rejection_reason,
            )

            logger.info(f"File {file_id} rejected: {rejection_reason}")

            return {
                "success": True,
                "file_id": file_id,
                "status": FileStatus.REJECTED.value,
                "reason": rejection_reason,
            }

        except Exception as e:
            logger.error(f"Failed to reject file {file_id}: {e}")
            return {"success": False, "file_id": file_id, "error": str(e)}

    async def get_processing_status(self, batch_id: str) -> Dict[str, Any]:
        """
        Get detailed processing status for a batch.

        Args:
            batch_id: Processing job/batch ID

        Returns:
            Dict with batch and file statuses
        """
        try:
            # Get batch info
            client = await db.get_supabase_client()
            batch_result = await (
                client.table("processing_jobs").select("*").eq("id", batch_id).execute()
            )
            if not batch_result.data:
                raise ValueError(f"Batch {batch_id} not found")

            batch_info = batch_result.data[0]

            # Get file statuses
            files_result = await (
                client.table("processing_files")
                .select("id, original_filename, status, error_message, created_at, updated_at")
                .eq("batch_id", batch_id)
                .execute()
            )

            files_by_status: Dict[str, List[Dict[str, Any]]] = {}
            for file_record in files_result.data:
                status = file_record["status"]
                if status not in files_by_status:
                    files_by_status[status] = []
                files_by_status[status].append(file_record)

            return {
                "success": True,
                "batch_id": batch_id,
                "batch_info": batch_info,
                "files_by_status": files_by_status,
                "total_files": len(files_result.data),
            }

        except Exception as e:
            logger.error(f"Failed to get processing status for batch {batch_id}: {e}")
            return {"success": False, "batch_id": batch_id, "error": str(e)}

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

    async def _update_document_processing_status(
        self, file_id: str, processing_status: str, **kwargs
    ):
        """Update document processing status based on processing file ID."""
        try:
            client = await db.get_supabase_client()

            # Get document_id from processing file
            file_result = (
                await client.table("processing_files")
                .select("document_id")
                .eq("id", file_id)
                .limit(1)
                .execute()
            )
            if not file_result.data:
                raise ValueError(f"Processing file {file_id} not found")

            document_id = file_result.data[0]["document_id"]
            if not document_id:
                raise ValueError(f"No document linked to processing file {file_id}")

            # Update document with processing status
            update_data = {
                "processing_status": processing_status,
                "updated_at": datetime.utcnow().isoformat(),
                **kwargs,
            }
            await client.table("documents").update(update_data).eq("id", document_id).execute()
            logger.info(f"Updated document {document_id} processing_status to {processing_status}")

        except Exception as e:
            logger.error(f"Failed to update document processing status for file {file_id}: {e}")
            raise

    async def _delete_failed_document(self, file_id: str, error_message: str = None):
        """Delete document and associated data when processing fails."""
        try:
            client = await db.get_supabase_client()

            # Get document_id from processing file
            file_result = (
                await client.table("processing_files")
                .select("document_id")
                .eq("id", file_id)
                .limit(1)
                .execute()
            )
            if not file_result.data:
                logger.warning(
                    f"Processing file {file_id} not found when trying to delete document"
                )
                return

            document_id = file_result.data[0]["document_id"]
            if not document_id:
                logger.warning(f"No document linked to processing file {file_id}")
                return

            # Delete document - this will cascade to document_chunks, document_access, etc.
            await client.table("documents").delete().eq("id", document_id).execute()
            logger.info(f"Deleted failed document {document_id} and cascaded cleanup")

        except Exception as e:
            logger.error(f"Failed to delete document for failed file {file_id}: {e}")
            # Don't re-raise - processing failure cleanup shouldn't fail the batch

    async def _cleanup_processing_file(self, file_id: str):
        """Clean up processing_files record after successful processing to save storage."""
        try:
            client = await db.get_supabase_client()

            # Clear large fields that are no longer needed
            # Keep audit fields like batch_id, status, timestamps
            cleanup_data = {
                "extracted_text": None,  # This is the largest field
                "preview_text": None,  # Now stored in documents
                "page_count": None,  # Now stored in documents
                "word_count": None,  # Now stored in documents
                "char_count": None,  # Now stored in documents
                "chunk_count": None,  # Now stored in documents
                "updated_at": datetime.utcnow().isoformat(),
            }

            await client.table("processing_files").update(cleanup_data).eq("id", file_id).execute()
            logger.info(f"Cleaned up processing_files record {file_id} to save storage")

        except Exception as e:
            logger.warning(f"Failed to cleanup processing_files {file_id}: {e}")
            # Don't fail the processing if cleanup fails

    async def _update_batch_status(self, batch_id: str, status: BatchStatus, **kwargs):
        """Update batch processing status."""
        try:
            update_data = {
                "status": status.value,
                "updated_at": datetime.utcnow().isoformat(),
                **kwargs,
            }

            client = await db.get_supabase_client()
            await client.table("processing_jobs").update(update_data).eq("id", batch_id).execute()

        except Exception as e:
            logger.error(f"Failed to update batch {batch_id} status: {e}")
            raise

    async def _check_batch_completion(self, batch_id: str):
        """Check if all files in a batch are complete and update batch status."""
        try:
            client = await db.get_supabase_client()

            # Get all files for this batch
            files_result = (
                await client.table("processing_files")
                .select("status")
                .eq("batch_id", batch_id)
                .execute()
            )

            if not files_result.data:
                logger.warning(f"No files found for batch {batch_id}")
                return

            # Count files by status
            status_counts: Dict[str, int] = {}
            for file_data in files_result.data:
                status = file_data["status"]
                status_counts[status] = status_counts.get(status, 0) + 1

            total_files = len(files_result.data)
            completed_files = status_counts.get("review_pending", 0) + status_counts.get(
                "approved", 0
            )
            failed_files = (
                status_counts.get("extraction_failed", 0)
                + status_counts.get("analysis_failed", 0)
                + status_counts.get("embedding_failed", 0)
            )

            # Check if all files are in final states
            processing_files = total_files - completed_files - failed_files

            logger.info(
                f"Batch {batch_id}: {total_files} total, {completed_files} completed, {failed_files} failed, {processing_files} still processing"
            )

            if processing_files == 0:  # All files are in final states
                from app.models.enums import BatchStatus

                if failed_files == 0:
                    final_status = BatchStatus.PROCESSING_COMPLETE
                elif completed_files > 0:
                    final_status = BatchStatus.PARTIALLY_COMPLETED
                else:
                    final_status = BatchStatus.FAILED

                # Update batch status
                await client.table("processing_jobs").update(
                    {
                        "status": final_status.value,
                        "completed_files": completed_files,
                        "failed_files": failed_files,
                        "updated_at": datetime.utcnow().isoformat(),
                    }
                ).eq("id", batch_id).execute()

                logger.info(
                    f"✅ BATCH COMPLETE: Updated batch {batch_id} status to {final_status.value}"
                )

        except Exception as e:
            logger.error(f"Failed to check batch completion for {batch_id}: {e}")

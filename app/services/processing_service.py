"""
Processing orchestration service for managing document processing workflows.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.database import db
from app.models.enums import BatchStatus, DocumentStatus, FileStatus
from app.services.ai_service import AIService
from app.services.embedding_service import EmbeddingService
from app.services.extraction_service import ExtractionService

logger = logging.getLogger(__name__)


class ProcessingService:
    """Orchestrates the document processing pipeline."""

    def __init__(self):
        self.extraction_service = ExtractionService()
        self.ai_service = AIService()
        self.embedding_service = EmbeddingService()
        self.max_concurrent_files = 5  # Limit concurrent processing

    def queue_text_extraction(self, file_id: str) -> bool:
        """
        Queue a file for text extraction processing.

        Args:
            file_id: Processing file ID

        Returns:
            True if successfully queued
        """
        try:
            logger.info(f"Queuing file {file_id} for text extraction")

            # Update file status to queued
            self._update_file_status(file_id, FileStatus.QUEUED)

            # Start background processing (fire and forget)
            asyncio.create_task(self._process_file_pipeline(file_id))

            return True

        except Exception as e:
            logger.error(f"Failed to queue file {file_id}: {e}")
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
            files_result = (
                db.supabase.table("processing_files")
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
            self._update_batch_status(batch_id, BatchStatus.PROCESSING)

            # Process files with concurrency control
            semaphore = asyncio.Semaphore(self.max_concurrent_files)
            tasks = [self._process_file_with_semaphore(semaphore, file_id) for file_id in file_ids]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Analyze results
            successful = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
            failed = len(results) - successful

            # Update batch with final status
            final_status = BatchStatus.PROCESSING_COMPLETE if failed == 0 else BatchStatus.FAILED
            self._update_batch_status(
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
            self._update_batch_status(batch_id, BatchStatus.FAILED, error_message=str(e))
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
        logger.info(f"Starting pipeline processing for file {file_id}")

        try:
            # Step 1: Text Extraction
            extraction_result = await self.extraction_service.extract_text_from_file(file_id)
            if not extraction_result["success"]:
                logger.error(
                    f"Text extraction failed for file {file_id}: {extraction_result['error']}"
                )
                return dict(extraction_result)

            # Step 2: AI Metadata Extraction
            metadata_result = await self.ai_service.extract_metadata(file_id)
            if not metadata_result["success"]:
                logger.error(
                    f"Metadata extraction failed for file {file_id}: {metadata_result['error']}"
                )
                return dict(metadata_result)

            # Step 3: Embedding Generation
            embedding_result = await self.embedding_service.generate_embeddings(file_id)
            if not embedding_result["success"]:
                logger.error(
                    f"Embedding generation failed for file {file_id}: {embedding_result['error']}"
                )
                return dict(embedding_result)

            # Mark file as ready for review
            self._update_file_status(file_id, FileStatus.REVIEW_PENDING)

            logger.info(f"Pipeline processing completed successfully for file {file_id}")

            return {
                "success": True,
                "file_id": file_id,
                "text_length": extraction_result.get("text_length", 0),
                "page_count": extraction_result.get("page_count", 0),
                "chunk_count": embedding_result.get("chunk_count", 0),
                "metadata": metadata_result.get("metadata", {}),
                "status": FileStatus.REVIEW_PENDING.value,
            }

        except Exception as e:
            logger.error(f"Pipeline processing failed for file {file_id}: {e}")
            self._update_file_status(file_id, FileStatus.EXTRACTION_FAILED, error_message=str(e))
            return {"success": False, "file_id": file_id, "error": str(e)}

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
            file_result = (
                db.supabase.table("processing_files").select("*").eq("id", file_id).execute()
            )
            if not file_result.data:
                raise ValueError(f"File {file_id} not found")

            file_record = file_result.data[0]

            if file_record["status"] != FileStatus.REVIEW_PENDING.value:
                raise ValueError(
                    f"File {file_id} is not ready for review (status: {file_record['status']})"
                )

            # Create document record in the main documents table
            document_data = {
                "title": file_record.get("ai_title", file_record["original_filename"]),
                "authors": file_record.get("ai_authors", []),
                "publication_date": file_record.get("ai_publication_date"),
                "doc_type": file_record.get("ai_doc_type", "other"),
                "doc_category": file_record.get("ai_doc_category", "Other"),
                "description": file_record.get("ai_description", ""),
                "keywords": file_record.get("ai_keywords", []),
                "bluebook_citation": file_record.get("ai_bluebook_citation"),
                "content_hash": file_record["content_hash"],
                "stored_path": file_record["stored_path"],
                "file_size": file_record["file_size"],
                "mime_type": file_record["mime_type"],
                "page_count": file_record.get("page_count", 1),
                "word_count": file_record.get("word_count", 0),
                "char_count": file_record.get("char_count", 0),
                "chunk_count": file_record.get("chunk_count", 0),
                "status": DocumentStatus.ACTIVE.value,
                "reviewed_by": reviewer_id,
                "reviewed_at": datetime.utcnow().isoformat(),
                "review_notes": review_notes,
                "created_at": datetime.utcnow().isoformat(),
            }

            # Insert document record
            document_result = db.supabase.table("documents").insert(document_data).execute()
            document_id = document_result.data[0]["id"]

            # Update processing file status
            self._update_file_status(
                file_id,
                FileStatus.APPROVED,
                document_id=document_id,
                reviewed_by=reviewer_id,
                reviewed_at=datetime.utcnow().isoformat(),
                review_notes=review_notes,
            )

            # Update document chunks to reference the new document
            db.supabase.table("document_chunks").update({"document_id": document_id}).eq(
                "processing_file_id", file_id
            ).execute()

            logger.info(f"File {file_id} approved and added to library as document {document_id}")

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
            self._update_file_status(
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
            batch_result = (
                db.supabase.table("processing_jobs").select("*").eq("id", batch_id).execute()
            )
            if not batch_result.data:
                raise ValueError(f"Batch {batch_id} not found")

            batch_info = batch_result.data[0]

            # Get file statuses
            files_result = (
                db.supabase.table("processing_files")
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

    def _update_file_status(self, file_id: str, status: FileStatus, **kwargs):
        """Update file processing status."""
        try:
            update_data = {
                "status": status.value,
                "updated_at": datetime.utcnow().isoformat(),
                **kwargs,
            }

            db.supabase.table("processing_files").update(update_data).eq("id", file_id).execute()

        except Exception as e:
            logger.error(f"Failed to update file {file_id} status: {e}")
            raise

    def _update_batch_status(self, batch_id: str, status: BatchStatus, **kwargs):
        """Update batch processing status."""
        try:
            update_data = {
                "status": status.value,
                "updated_at": datetime.utcnow().isoformat(),
                **kwargs,
            }

            db.supabase.table("processing_jobs").update(update_data).eq("id", batch_id).execute()

        except Exception as e:
            logger.error(f"Failed to update batch {batch_id} status: {e}")
            raise

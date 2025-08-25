"""
Simplified queue API - documents only approach.
This replaces the complex processing_files + documents logic with a clean documents-only queue.
"""

import logging
from typing import Any, Dict

from app.core.database import db

logger = logging.getLogger(__name__)


async def get_review_queue_simple(current_user: Dict[str, Any]):
    """
    Get review queue - simplified approach using only documents table.
    Documents track their own processing_status, so no need for complex processing_files logic.
    """
    try:
        client = await db.get_supabase_client()

        # Get all documents that are not yet reviewed and not deleted
        # This includes documents in all processing stages via processing_status
        documents_result = await (
            client.table("documents")
            .select("*")
            .eq("is_reviewed", False)
            .eq("is_deleted", False)
            .order("created_at", desc=True)
            .execute()
        )

        queue_items = []
        total_processing = 0
        total_pending = 0
        total_in_progress = 0
        # No total_failed needed since failed documents are deleted

        # Process each document and create queue items with processing badges
        for doc in documents_result.data or []:
            processing_status = doc.get("processing_status", "uploaded")

            # Map processing status for display and counting
            if processing_status in [
                "uploaded",
                "extracting_text",
                "analyzing_metadata",
                "generating_embeddings",
            ]:
                total_processing += 1
            elif processing_status == "ready_for_review":
                total_pending += 1
            elif processing_status == "under_review":
                total_in_progress += 1
            # No failed counting since failed documents are deleted

            # Get batch info from linked processing file for display
            batch_id = None
            try:
                processing_file_result = await (
                    client.table("processing_files")
                    .select("batch_id")
                    .eq("document_id", doc["id"])
                    .limit(1)
                    .execute()
                )
                if processing_file_result.data:
                    batch_id = processing_file_result.data[0]["batch_id"]
            except Exception as e:
                logger.warning(f"Could not get batch_id for document {doc['id']}: {e}")

            # Create simplified queue item - all documents, with processing badges
            queue_item = {
                "id": doc["id"],  # Always use document ID
                "type": "document",  # Always document type
                "title": doc.get("title") or doc["original_filename"],
                "original_filename": doc["original_filename"],
                "doc_type": doc.get("doc_type"),
                "doc_category": doc.get("doc_category"),
                "confidence_score": doc.get("confidence_score"),
                "processing_status": processing_status,  # Used for badges
                "uploaded_at": doc["created_at"],
                "file_size": doc["file_size"],
                "batch_id": batch_id,
                # Full metadata available
                "preview_text": doc.get("preview_text"),
                "summary": doc.get("summary"),
                "case_name": doc.get("case_name"),
                "case_number": doc.get("case_number"),
                "court": doc.get("court"),
                "jurisdiction": doc.get("jurisdiction"),
                "practice_area": doc.get("practice_area"),
                "date": doc.get("date"),
                "authors": doc.get("authors"),
                "keywords": doc.get("keywords"),
                "tags": doc.get("tags"),
                # Text metrics
                "page_count": doc.get("page_count"),
                "word_count": doc.get("word_count"),
                "char_count": doc.get("char_count"),
                "chunk_count": doc.get("chunk_count"),
            }
            queue_items.append(queue_item)

        return {
            "queue": queue_items,
            "total_processing": total_processing,
            "total_pending": total_pending,
            "total_in_progress": total_in_progress,
            "total_failed": 0,  # Failed documents are deleted, not tracked
            "total_documents": len(queue_items),
        }

    except Exception as e:
        logger.error(f"Review queue failed: {e}")
        raise

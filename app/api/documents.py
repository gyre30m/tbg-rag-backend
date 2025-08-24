"""
Documents API endpoints for file upload and document management.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import verify_jwt_token
from app.models.documents import (
    DocumentSearchRequest,
    DocumentSearchResult,
    DocumentUpdate,
    VectorSearchResponse,
)
from app.models.enums import DocumentStatus, FileStatus
from app.models.processing import UploadResponse
from app.services.embedding_service import EmbeddingService
from app.services.file_service import FileService
from app.services.processing_service import ProcessingService

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

# Initialize services
file_service = FileService()
processing_service = ProcessingService()
embedding_service = EmbeddingService()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """Extract and verify user from JWT token."""
    try:
        user_data = await verify_jwt_token(credentials.credentials)
        return user_data
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@router.post("/upload", response_model=UploadResponse, tags=["Documents"])
async def upload_documents(
    files: List[UploadFile] = File(..., description="Documents to upload"),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Upload multiple documents for processing.

    - **files**: List of document files (PDF, DOCX, TXT, MD)
    - Returns upload job information and file processing status
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    user_id = current_user.get("sub")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid user token")

    try:
        result = await file_service.upload_files(files, user_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail="Upload failed")


@router.get("/processing-status/{batch_id}", tags=["Documents"])
async def get_processing_status(
    batch_id: str, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get detailed processing status for a batch of uploaded documents.

    - **batch_id**: Processing job ID returned from upload
    - Returns batch status and individual file processing progress
    """
    try:
        result = await processing_service.get_processing_status(batch_id)
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail="Status check failed")


@router.post("/{document_id}/approve", tags=["Documents"])
async def approve_file_for_library(
    document_id: str,
    review_notes: Optional[str] = Form(None, description="Optional review notes"),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Approve a processed file for inclusion in the document library.

    - **document_id**: Processing file ID
    - **review_notes**: Optional notes from the reviewer
    - Moves the document from processing to the main library
    """
    user_id = current_user.get("sub")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid user token")

    try:
        result = await processing_service.approve_file_for_library(
            document_id, user_id, review_notes
        )
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except Exception as e:
        logger.error(f"Approval failed: {e}")
        raise HTTPException(status_code=500, detail="Approval failed")


@router.post("/reject/{file_id}", tags=["Documents"])
async def reject_file(
    file_id: str,
    rejection_reason: str = Form(..., description="Reason for rejection"),
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Reject a processed file from inclusion in the document library.

    - **file_id**: Processing file ID
    - **rejection_reason**: Required reason for rejection
    - Marks the document as rejected and removes it from the processing queue
    """
    user_id = current_user.get("sub")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid user token")

    try:
        result = await processing_service.reject_file(file_id, user_id, rejection_reason)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except Exception as e:
        logger.error(f"Rejection failed: {e}")
        raise HTTPException(status_code=500, detail="Rejection failed")


@router.post("/search", response_model=VectorSearchResponse, tags=["Documents"])
async def search_documents(
    search_request: DocumentSearchRequest, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Search documents using vector similarity search.

    - **query**: Search query text
    - **limit**: Maximum number of results (default: 10)
    - **similarity_threshold**: Minimum similarity score 0-1 (default: 0.7)
    - **doc_categories**: Optional list of document categories to filter by
    - Returns similar document chunks with metadata
    """
    try:
        similar_chunks = await embedding_service.search_similar_chunks(
            query_text=search_request.query,
            limit=search_request.limit,
            similarity_threshold=search_request.similarity_threshold,
            doc_categories=search_request.doc_categories,
        )

        # Convert dictionary results to DocumentSearchResult objects
        results = [
            DocumentSearchResult(
                content=chunk.get("text_content", ""),
                chunk_index=chunk.get("chunk_index", 0),
                filename=chunk.get("filename", ""),
                title=chunk.get("title"),
                doc_type=chunk.get("doc_type"),
                doc_category=chunk.get("doc_category"),
                similarity_score=chunk.get("similarity_score", 0.0),
            )
            for chunk in similar_chunks
        ]

        return VectorSearchResponse(
            query=search_request.query, results=results, total_results=len(results)
        )
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail="Search failed")


@router.post("/clear-failed", tags=["Documents"])
async def clear_failed_documents(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Clear failed and duplicate files from the processing queue.

    - Removes processing_files with status: failed, extraction_failed, duplicate
    - Returns count of cleared files
    """
    try:
        from app.core.database import db

        client = await db.get_supabase_client()

        # Delete processing files with failed or duplicate status
        result = await (
            client.table("processing_files")
            .delete()
            .in_("status", ["failed", "extraction_failed", "duplicate"])
            .execute()
        )

        cleared_count = len(result.data) if result.data else 0

        logger.info(
            f"Cleared {cleared_count} failed/duplicate files for user {current_user.get('sub')}"
        )

        return {"success": True, "cleared_count": cleared_count}
    except Exception as e:
        logger.error(f"Failed to clear failed/duplicate files: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear queue")


@router.get("/library", tags=["Documents"])
async def list_library_documents(
    limit: int = 50,
    offset: int = 0,
    doc_type: Optional[str] = None,
    doc_category: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    List documents in the main library.

    - **limit**: Maximum number of documents to return (default: 50)
    - **offset**: Number of documents to skip (default: 0)
    - **doc_type**: Optional filter by document type
    - **doc_category**: Optional filter by document category
    - Returns paginated list of library documents
    """
    try:
        from app.core.database import db

        # Build query
        client = await db.get_supabase_client()
        query = (
            client.table("documents")
            .select(
                "id, title, authors, publication_date, doc_type, doc_category, "
                "description, keywords, page_count, word_count, created_at, reviewed_by"
            )
            .eq("is_reviewed", True)
            .eq("is_deleted", False)
        )

        # Apply filters
        if doc_type:
            query = query.eq("doc_type", doc_type)
        if doc_category:
            query = query.eq("doc_category", doc_category)

        # Apply pagination and ordering
        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

        result = await query.execute()

        return {
            "documents": result.data,
            "total": len(result.data),
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        logger.error(f"Library listing failed: {e}")
        raise HTTPException(status_code=500, detail="Library listing failed")


@router.get("/queue", tags=["Documents"])
async def get_review_queue(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get documents pending review with full metadata.

    Returns ALL documents that need human review - those with is_reviewed = false,
    including documents that are still being processed. Documents appear in the queue
    immediately after upload and show their current processing status.
    """
    try:
        from app.core.database import db

        client = await db.get_supabase_client()

        # Get all processing files that are not in terminal states
        # This shows files from upload through processing pipeline
        # Include failed and duplicate files so users can see them in the queue
        processing_files_result = await (
            client.table("processing_files")
            .select("*")
            .not_.in_("status", ["approved", "rejected", "cancelled"])
            .order("created_at", desc=True)
            .execute()
        )

        # Get documents ready for review (processing complete, not yet reviewed)
        documents_ready_for_review = await (
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
        total_failed = 0

        # First, add all processing files (files in pipeline)
        for processing_file in processing_files_result.data or []:
            # Skip if this file has a document that's ready for review
            # (it will be shown in document section instead)
            if processing_file["document_id"]:
                # Check if the associated document is ready for review
                doc_ready = any(
                    doc["id"] == processing_file["document_id"]
                    for doc in (documents_ready_for_review.data or [])
                    if processing_file.get("status") == "review_pending"
                )
                if doc_ready:
                    continue  # Skip this processing file, show as document instead

            # Create queue item for processing file
            processing_status = processing_file["status"]

            # Map processing status for display
            if processing_status in [
                "uploaded",
                "queued",
                "extracting_text",
                "analyzing_metadata",
                "generating_embeddings",
                "processing_complete",
            ]:
                display_status = "processing"
                total_processing += 1
            elif processing_status == "under_review":
                display_status = "under_review"
                total_in_progress += 1
            elif processing_status in ["extraction_failed", "failed"]:
                display_status = "failed"
                total_failed += 1
            elif processing_status == "duplicate":
                display_status = "duplicate"
                total_failed += 1  # Count duplicates as failed for UI purposes
            else:
                display_status = processing_status
                total_processing += 1

            queue_item = {
                "id": processing_file["id"],  # Use processing file ID while in pipeline
                "type": "processing_file",  # Distinguish from documents
                "title": processing_file["original_filename"],  # Show filename as title
                "original_filename": processing_file["original_filename"],
                "doc_type": None,  # Not available until processed
                "doc_category": None,  # Not available until processed
                "confidence_score": None,  # Not available until processed
                "processing_status": display_status,
                "raw_processing_status": processing_status,
                "uploaded_at": processing_file["created_at"],
                "file_size": processing_file["file_size"],
                "batch_id": processing_file["batch_id"],
                # No metadata available yet
                "summary": None,
                "case_name": None,
                "case_number": None,
                "court": None,
                "jurisdiction": None,
                "practice_area": None,
                "date": None,
                "authors": None,
            }
            queue_items.append(queue_item)

        # Second, add documents ready for review (replace processing file entries)
        for doc in documents_ready_for_review.data or []:
            # Get the associated processing file for additional info
            processing_files_for_doc = await (
                client.table("processing_files")
                .select("id, batch_id, status, created_at, file_size")
                .eq("document_id", doc["id"])
                .limit(1)
                .execute()
            )

            processing_file = (
                processing_files_for_doc.data[0] if processing_files_for_doc.data else None
            )

            # Only show if processing is complete and ready for review
            if processing_file and processing_file["status"] == "review_pending":
                display_status = "review_pending"
                total_pending += 1

                queue_item = {
                    "id": doc["id"],  # Use document ID when ready for review
                    "type": "document",  # Distinguish from processing files
                    "title": doc["title"],
                    "original_filename": doc["original_filename"],
                    "doc_type": doc["doc_type"],
                    "doc_category": doc["doc_category"],
                    "confidence_score": doc["confidence_score"],
                    "processing_status": display_status,
                    "raw_processing_status": processing_file["status"],
                    "uploaded_at": doc["created_at"],
                    "file_size": doc["file_size"],
                    "batch_id": processing_file["batch_id"],
                    # Full metadata available for review
                    "summary": doc.get("summary"),
                    "case_name": doc.get("case_name"),
                    "case_number": doc.get("case_number"),
                    "court": doc.get("court"),
                    "jurisdiction": doc.get("jurisdiction"),
                    "practice_area": doc.get("practice_area"),
                    "date": doc.get("date"),
                    "authors": doc.get("authors"),
                }
                queue_items.append(queue_item)

        return {
            "queue": queue_items,
            "total_processing": total_processing,
            "total_pending": total_pending,
            "total_in_progress": total_in_progress,
            "total_failed": total_failed,
            "total_documents": len(queue_items),
        }

    except Exception as e:
        logger.error(f"Review queue failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get review queue")


@router.put("/{document_id}/metadata", tags=["Documents"])
async def update_document_metadata(
    document_id: str,
    metadata: DocumentUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Update document metadata during review.

    Allows reviewers to edit AI-extracted metadata before approving documents.
    Sets review status to 'review_in_progress' and tracks review session.
    """
    try:
        from datetime import datetime

        from app.core.database import db

        user_id = current_user.get("sub")
        if not user_id:
            raise HTTPException(status_code=400, detail="Invalid user token")

        # Build update data from provided fields
        update_data = {}
        if metadata.title is not None:
            update_data["title"] = metadata.title
        if metadata.doc_type is not None:
            update_data["doc_type"] = metadata.doc_type.value
        if metadata.doc_category is not None:
            update_data["doc_category"] = metadata.doc_category.value
        if metadata.authors is not None:
            update_data["authors"] = ", ".join(metadata.authors) if metadata.authors else None
        if metadata.citation is not None:
            update_data["citation"] = metadata.citation
        if metadata.summary is not None:
            update_data["summary"] = metadata.summary
        if metadata.case_name is not None:
            update_data["case_name"] = metadata.case_name
        if metadata.case_number is not None:
            update_data["case_number"] = metadata.case_number
        if metadata.court is not None:
            update_data["court"] = metadata.court
        if metadata.jurisdiction is not None:
            update_data["jurisdiction"] = metadata.jurisdiction
        if metadata.practice_area is not None:
            update_data["practice_area"] = metadata.practice_area
        if metadata.date is not None:
            update_data["date"] = metadata.date.isoformat()

        # Add review tracking fields
        update_data["updated_at"] = datetime.utcnow().isoformat()

        # Check if document exists
        client = await db.get_supabase_client()
        doc_check = await (
            client.table("documents").select("id, is_reviewed").eq("id", document_id).execute()
        )

        if not doc_check.data:
            raise HTTPException(status_code=404, detail="Document not found")

        document = doc_check.data[0]
        if document.get("is_reviewed"):
            raise HTTPException(
                status_code=400, detail="Cannot edit metadata of already reviewed document"
            )

        # Update document metadata
        result = await client.table("documents").update(update_data).eq("id", document_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Document not found")

        # Update processing file status to track review session
        processing_update = {
            "status": FileStatus.UNDER_REVIEW.value,
            "reviewed_by": user_id,
            "review_started_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        await client.table("processing_files").update(processing_update).eq(
            "document_id", document_id
        ).execute()

        # Return updated document
        updated_doc = result.data[0]

        return {
            "success": True,
            "message": "Document metadata updated successfully",
            "document": updated_doc,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Metadata update failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to update document metadata")


@router.get("/stats", tags=["Documents"])
async def get_document_stats(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get document statistics for library dashboard.

    Returns counts of documents by type for the statistics cards.
    Only includes reviewed documents in the main library.
    """
    try:
        from app.core.database import db

        # Query document counts by type using the new RPC function
        client = await db.get_supabase_client()
        result = await client.rpc("get_document_stats").execute()

        # Initialize all document types to 0
        stats = {
            "total_documents": 0,
            "books_textbooks": 0,
            "articles_publications": 0,
            "statutes_codes": 0,
            "case_law": 0,
            "expert_reports": 0,
            "other_documents": 0,
        }

        # Map database results to response format
        if result.data:
            for row in result.data:
                doc_type = row.get("doc_type")
                count = row.get("count", 0)

                if doc_type == "book":
                    stats["books_textbooks"] = count
                elif doc_type == "article":
                    stats["articles_publications"] = count
                elif doc_type == "statute":
                    stats["statutes_codes"] = count
                elif doc_type == "case_law":
                    stats["case_law"] = count
                elif doc_type == "expert_report":
                    stats["expert_reports"] = count
                elif doc_type == "other":
                    stats["other_documents"] = count

        # Calculate total
        stats["total_documents"] = sum(
            [
                stats["books_textbooks"],
                stats["articles_publications"],
                stats["statutes_codes"],
                stats["case_law"],
                stats["expert_reports"],
                stats["other_documents"],
            ]
        )

        return stats

    except Exception as e:
        logger.error(f"Document stats failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get document statistics")


@router.get("/library/{document_id}", tags=["Documents"])
async def get_document_details(
    document_id: str, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get detailed information about a specific document.

    - **document_id**: Document ID
    - Returns complete document metadata and processing information
    """
    try:
        from app.core.database import db

        # Get document details
        client = await db.get_supabase_client()
        doc_result = await client.table("documents").select("*").eq("id", document_id).execute()
        if not doc_result.data:
            raise HTTPException(status_code=404, detail="Document not found")

        document = doc_result.data[0]

        # Get document chunks count
        chunks_result = await (
            client.table("document_chunks")
            .select("id", count="exact")
            .eq("document_id", document_id)
            .execute()
        )

        document["chunk_count"] = chunks_result.count or 0

        return document
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document details failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get document details")


@router.delete("/library/{document_id}", tags=["Documents"])
async def delete_document(
    document_id: str, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete a document from the library (soft delete).

    - **document_id**: Document ID
    - Marks the document as deleted rather than physically removing it
    """
    try:
        from datetime import datetime

        from app.core.database import db

        user_id = current_user.get("sub")

        # Update document status to deleted
        client = await db.get_supabase_client()
        result = await (
            client.table("documents")
            .update(
                {
                    "is_deleted": True,
                    "deleted_by": user_id,
                    "deleted_at": datetime.utcnow().isoformat(),
                }
            )
            .eq("id", document_id)
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Document not found")

        return {"success": True, "message": "Document deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document deletion failed: {e}")
        raise HTTPException(status_code=500, detail="Document deletion failed")

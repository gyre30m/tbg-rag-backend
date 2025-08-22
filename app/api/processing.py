"""
Processing API endpoints for managing document processing workflows.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.database import db
from app.core.security import verify_jwt_token
from app.services.processing_service import ProcessingService

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

# Initialize services
processing_service = ProcessingService()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """Extract and verify user from JWT token."""
    try:
        user_data = verify_jwt_token(credentials.credentials)
        return user_data
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@router.post("/batch/{batch_id}/process", tags=["Processing"])
async def process_batch(batch_id: str, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Manually trigger processing for an entire batch.

    - **batch_id**: Processing job/batch ID
    - Processes all files in the batch through the complete pipeline
    - Returns processing results and status
    """
    try:
        result = await processing_service.process_batch(batch_id)
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        raise HTTPException(status_code=500, detail="Batch processing failed")


@router.get("/batches", tags=["Processing"])
async def list_processing_batches(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    List processing batches/jobs.

    - **limit**: Maximum number of batches to return (default: 50)
    - **offset**: Number of batches to skip (default: 0)
    - **status**: Optional filter by batch status
    - Returns paginated list of processing batches
    """
    try:
        # Build query
        query = db.supabase.table("processing_jobs").select(
            "id, total_files, processed_files, completed_files, failed_files, "
            "status, created_at, updated_at"
        )

        # Apply status filter
        if status:
            query = query.eq("status", status)

        # Apply pagination and ordering
        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

        result = await query.execute()

        return {"batches": result.data, "total": len(result.data), "limit": limit, "offset": offset}
    except Exception as e:
        logger.error(f"Batch listing failed: {e}")
        raise HTTPException(status_code=500, detail="Batch listing failed")


@router.get("/files/pending-review", tags=["Processing"])
async def list_files_pending_review(
    limit: int = 50, offset: int = 0, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    List files that are ready for human review.

    - **limit**: Maximum number of files to return (default: 50)
    - **offset**: Number of files to skip (default: 0)
    - Returns files with status 'ready_for_review'
    """
    try:
        result = (
            await db.supabase.table("processing_files")
            .select(
                "id, batch_id, original_filename, ai_title, ai_doc_type, ai_doc_category, "
                "ai_description, page_count, word_count, created_at, updated_at"
            )
            .eq("status", "ready_for_review")
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )

        return {"files": result.data, "total": len(result.data), "limit": limit, "offset": offset}
    except Exception as e:
        logger.error(f"Pending review listing failed: {e}")
        raise HTTPException(status_code=500, detail="Pending review listing failed")


@router.get("/files/{file_id}", tags=["Processing"])
async def get_processing_file_details(
    file_id: str, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get detailed information about a processing file.

    - **file_id**: Processing file ID
    - Returns complete file processing information including extracted metadata
    """
    try:
        # Get processing file details
        result = await db.supabase.table("processing_files").select("*").eq("id", file_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Processing file not found")

        file_data = result.data[0]

        # Get chunk count if embeddings were generated
        if file_data["status"] in [
            "embeddings_generated",
            "ready_for_review",
            "approved_for_library",
        ]:
            chunks_result = (
                await db.supabase.table("document_chunks")
                .select("id", count="exact")
                .eq("processing_file_id", file_id)
                .execute()
            )
            file_data["actual_chunk_count"] = chunks_result.count or 0

        return file_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Processing file details failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get processing file details")


@router.get("/files/{file_id}/text", tags=["Processing"])
async def get_extracted_text(
    file_id: str, max_length: int = 10000, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get extracted text from a processing file.

    - **file_id**: Processing file ID
    - **max_length**: Maximum text length to return (default: 10000)
    - Returns extracted text content (truncated if necessary)
    """
    try:
        result = (
            await db.supabase.table("processing_files")
            .select("extracted_text, status")
            .eq("id", file_id)
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Processing file not found")

        file_data = result.data[0]

        if not file_data.get("extracted_text"):
            raise HTTPException(status_code=400, detail="No extracted text available")

        text = file_data["extracted_text"]
        if len(text) > max_length:
            text = text[:max_length] + "...[truncated]"

        return {
            "file_id": file_id,
            "text": text,
            "text_length": len(file_data["extracted_text"]),
            "truncated": len(file_data["extracted_text"]) > max_length,
            "status": file_data["status"],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Text retrieval failed")


@router.get("/files/{file_id}/chunks", tags=["Processing"])
async def get_file_chunks(
    file_id: str,
    limit: int = 20,
    offset: int = 0,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Get text chunks for a processing file.

    - **file_id**: Processing file ID
    - **limit**: Maximum number of chunks to return (default: 20)
    - **offset**: Number of chunks to skip (default: 0)
    - Returns paginated list of text chunks with embeddings metadata
    """
    try:
        result = (
            await db.supabase.table("document_chunks")
            .select("id, chunk_index, text_content, token_count, created_at")
            .eq("processing_file_id", file_id)
            .order("chunk_index")
            .range(offset, offset + limit - 1)
            .execute()
        )

        return {
            "file_id": file_id,
            "chunks": result.data,
            "total": len(result.data),
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        logger.error(f"Chunks retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Chunks retrieval failed")


@router.post("/files/{file_id}/retry", tags=["Processing"])
async def retry_file_processing(
    file_id: str, current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Retry processing for a failed file.

    - **file_id**: Processing file ID
    - Resets the file status and retries the processing pipeline
    """
    try:
        # Get current file status
        result = (
            await db.supabase.table("processing_files")
            .select("status, retry_count")
            .eq("id", file_id)
            .execute()
        )
        if not result.data:
            raise HTTPException(status_code=404, detail="Processing file not found")

        file_data = result.data[0]
        current_status = file_data["status"]
        retry_count = file_data.get("retry_count", 0)

        # Check if retry is allowed
        if current_status not in [
            "extraction_failed",
            "ai_failed",
            "embedding_failed",
            "processing_failed",
        ]:
            raise HTTPException(
                status_code=400, detail=f"Cannot retry file with status: {current_status}"
            )

        if retry_count >= 3:
            raise HTTPException(status_code=400, detail="Maximum retry attempts exceeded")

        # Reset file status and increment retry count
        from datetime import datetime

        from app.models.enums import FileStatus

        await db.supabase.table("processing_files").update(
            {
                "status": FileStatus.UPLOADED.value,
                "retry_count": retry_count + 1,
                "error_message": None,
                "updated_at": datetime.utcnow().isoformat(),
            }
        ).eq("id", file_id).execute()

        # Queue for processing
        success = await processing_service.queue_text_extraction(file_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to queue file for retry")

        return {
            "success": True,
            "file_id": file_id,
            "retry_count": retry_count + 1,
            "message": "File queued for retry processing",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Retry processing failed: {e}")
        raise HTTPException(status_code=500, detail="Retry processing failed")


@router.get("/stats", tags=["Processing"])
async def get_processing_stats(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get processing statistics and system health.

    - Returns counts of files by status, batch statistics, and performance metrics
    """
    try:
        # Get file status counts
        file_stats_result = await db.supabase.rpc("get_file_status_counts").execute()
        file_stats = file_stats_result.data if file_stats_result.data else []

        # Get batch status counts
        batch_stats_result = await db.supabase.rpc("get_batch_status_counts").execute()
        batch_stats = batch_stats_result.data if batch_stats_result.data else []

        # Get recent activity (last 24 hours)
        from datetime import datetime, timedelta

        yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat()

        recent_files_result = (
            await db.supabase.table("processing_files")
            .select("id", count="exact")
            .gte("created_at", yesterday)
            .execute()
        )

        recent_batches_result = (
            await db.supabase.table("processing_jobs")
            .select("id", count="exact")
            .gte("created_at", yesterday)
            .execute()
        )

        return {
            "file_status_counts": {item["status"]: item["count"] for item in file_stats},
            "batch_status_counts": {item["status"]: item["count"] for item in batch_stats},
            "recent_activity": {
                "files_last_24h": recent_files_result.count or 0,
                "batches_last_24h": recent_batches_result.count or 0,
            },
            "generated_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Stats retrieval failed")

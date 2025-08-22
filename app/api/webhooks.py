"""
Webhooks API endpoints for processing notifications and external integrations.
"""

import hashlib
import hmac
import json
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException, Request

from app.core.config import settings
from app.services.processing_service import ProcessingService

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize services
processing_service = ProcessingService()


def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify webhook signature for security."""
    if not secret:
        logger.warning("No webhook secret configured - skipping signature verification")
        return True

    try:
        expected_signature = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()

        # Handle different signature formats
        if signature.startswith("sha256="):
            signature = signature[7:]

        return hmac.compare_digest(expected_signature, signature)
    except Exception as e:
        logger.error(f"Signature verification failed: {e}")
        return False


@router.post("/processing/status", tags=["Webhooks"])
async def processing_status_webhook(
    request: Request,
    x_signature: Optional[str] = Header(None, alias="X-Signature"),
    x_webhook_secret: Optional[str] = Header(None, alias="X-Webhook-Secret"),
):
    """
    Webhook endpoint for processing status updates.

    - Receives notifications about file processing completion
    - Verifies webhook signatures for security
    - Updates processing status and triggers next steps
    """
    try:
        # Get request body
        body = await request.body()

        # Verify signature if secret is configured
        webhook_secret = x_webhook_secret or settings.webhook_secret
        if webhook_secret and x_signature:
            if not verify_webhook_signature(body, x_signature, webhook_secret):
                raise HTTPException(status_code=401, detail="Invalid webhook signature")

        # Parse webhook payload
        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON payload")

        # Validate required fields
        event_type = payload.get("event_type")
        if not event_type:
            raise HTTPException(status_code=400, detail="Missing event_type field")

        # Handle different event types
        if event_type == "file_processing_completed":
            return await handle_file_processing_completed(payload)
        elif event_type == "batch_processing_completed":
            return await handle_batch_processing_completed(payload)
        elif event_type == "processing_error":
            return await handle_processing_error(payload)
        else:
            logger.warning(f"Unknown event type: {event_type}")
            return {"status": "ignored", "reason": "unknown_event_type"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")


async def handle_file_processing_completed(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Handle file processing completion webhook."""
    file_id = payload.get("file_id")
    if not file_id:
        raise HTTPException(status_code=400, detail="Missing file_id field")

    processing_status = payload.get("status")
    if not processing_status:
        raise HTTPException(status_code=400, detail="Missing status field")

    logger.info(f"Processing completed for file {file_id} with status {processing_status}")

    try:
        # Update file status based on webhook payload
        from datetime import datetime

        from app.core.database import db
        from app.models.enums import FileStatus

        # Map webhook status to internal status
        status_mapping = {
            "success": FileStatus.READY_FOR_REVIEW,
            "failed": FileStatus.PROCESSING_FAILED,
            "text_extracted": FileStatus.TEXT_EXTRACTED,
            "metadata_extracted": FileStatus.METADATA_EXTRACTED,
            "embeddings_generated": FileStatus.EMBEDDINGS_GENERATED,
        }

        new_status = status_mapping.get(processing_status)
        if not new_status:
            logger.warning(f"Unknown processing status: {processing_status}")
            return {"status": "ignored", "reason": "unknown_status"}

        # Update file record
        update_data = {"status": new_status.value, "updated_at": datetime.utcnow().isoformat()}

        # Add error message if failed
        if processing_status == "failed" and payload.get("error_message"):
            update_data["error_message"] = payload["error_message"]

        # Add processing metrics if available
        if payload.get("metrics"):
            metrics = payload["metrics"]
            if "processing_time" in metrics:
                update_data["processing_time"] = metrics["processing_time"]
            if "text_length" in metrics:
                update_data["char_count"] = metrics["text_length"]

        await db.supabase.table("processing_files").update(update_data).eq("id", file_id).execute()

        logger.info(f"Updated file {file_id} status to {new_status.value}")

        return {"status": "processed", "file_id": file_id, "new_status": new_status.value}

    except Exception as e:
        logger.error(f"Failed to handle file processing completion: {e}")
        raise HTTPException(status_code=500, detail="Failed to update file status")


async def handle_batch_processing_completed(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Handle batch processing completion webhook."""
    batch_id = payload.get("batch_id")
    if not batch_id:
        raise HTTPException(status_code=400, detail="Missing batch_id field")

    logger.info(f"Batch processing completed for batch {batch_id}")

    try:
        # Get batch processing results
        result = await processing_service.get_processing_status(batch_id)
        if not result["success"]:
            raise HTTPException(status_code=404, detail="Batch not found")

        # Update batch with completion metrics
        from datetime import datetime

        from app.core.database import db

        batch_info = result["batch_info"]
        files_by_status = result["files_by_status"]

        # Calculate final statistics
        completed_files = len(files_by_status.get("ready_for_review", []))
        completed_files += len(files_by_status.get("approved_for_library", []))
        failed_files = len(files_by_status.get("processing_failed", []))
        failed_files += len(files_by_status.get("extraction_failed", []))
        failed_files += len(files_by_status.get("ai_failed", []))
        failed_files += len(files_by_status.get("embedding_failed", []))

        # Determine final batch status
        from app.models.enums import BatchStatus

        if failed_files == 0:
            final_status = BatchStatus.COMPLETED
        elif completed_files > 0:
            final_status = BatchStatus.PARTIALLY_FAILED
        else:
            final_status = BatchStatus.FAILED

        # Update batch record
        await db.supabase.table("processing_jobs").update(
            {
                "status": final_status.value,
                "completed_files": completed_files,
                "failed_files": failed_files,
                "updated_at": datetime.utcnow().isoformat(),
            }
        ).eq("id", batch_id).execute()

        logger.info(f"Updated batch {batch_id} status to {final_status.value}")

        return {
            "status": "processed",
            "batch_id": batch_id,
            "final_status": final_status.value,
            "completed_files": completed_files,
            "failed_files": failed_files,
        }

    except Exception as e:
        logger.error(f"Failed to handle batch processing completion: {e}")
        raise HTTPException(status_code=500, detail="Failed to update batch status")


async def handle_processing_error(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Handle processing error webhook."""
    file_id = payload.get("file_id")
    batch_id = payload.get("batch_id")
    error_message = payload.get("error_message", "Unknown processing error")

    if not file_id and not batch_id:
        raise HTTPException(status_code=400, detail="Missing file_id or batch_id field")

    logger.error(f"Processing error reported: {error_message}")

    try:
        from datetime import datetime

        from app.core.database import db
        from app.models.enums import BatchStatus, FileStatus

        if file_id:
            # Update file with error status
            await db.supabase.table("processing_files").update(
                {
                    "status": FileStatus.PROCESSING_FAILED.value,
                    "error_message": error_message,
                    "updated_at": datetime.utcnow().isoformat(),
                }
            ).eq("id", file_id).execute()

            logger.info(f"Marked file {file_id} as failed due to error")

        if batch_id:
            # Update batch with error status
            await db.supabase.table("processing_jobs").update(
                {
                    "status": BatchStatus.FAILED.value,
                    "error_message": error_message,
                    "updated_at": datetime.utcnow().isoformat(),
                }
            ).eq("id", batch_id).execute()

            logger.info(f"Marked batch {batch_id} as failed due to error")

        return {
            "status": "processed",
            "file_id": file_id,
            "batch_id": batch_id,
            "error_handled": True,
        }

    except Exception as e:
        logger.error(f"Failed to handle processing error: {e}")
        raise HTTPException(status_code=500, detail="Failed to handle processing error")


@router.post("/test", tags=["Webhooks"])
async def test_webhook():
    """
    Test webhook endpoint for development and debugging.

    - Simple endpoint to test webhook connectivity
    - Returns success response with timestamp
    """
    from datetime import datetime

    return {
        "status": "success",
        "message": "Test webhook received",
        "timestamp": datetime.utcnow().isoformat(),
        "server": "TBG RAG Document Ingestion API",
    }


@router.get("/health", tags=["Webhooks"])
async def webhook_health():
    """
    Webhook health check endpoint.

    - Returns webhook service status
    - Used by monitoring systems to verify webhook availability
    """
    from datetime import datetime

    return {
        "status": "healthy",
        "service": "webhook",
        "timestamp": datetime.utcnow().isoformat(),
        "webhook_secret_configured": bool(settings.webhook_secret),
    }

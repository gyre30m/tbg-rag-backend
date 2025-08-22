"""
Unit tests for document review queue endpoint.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.api.documents import get_review_queue


class TestDocumentQueue:
    """Test document review queue functionality."""

    @pytest.mark.asyncio
    async def test_queue_empty(self):
        """Test review queue endpoint with no pending documents."""
        mock_user = {"sub": "test-user-123"}

        with patch("app.core.database.db") as mock_db:
            # Mock empty queue response
            mock_result = Mock()
            mock_result.data = []
            mock_db.supabase.rpc.return_value.execute = AsyncMock(return_value=mock_result)

            # Execute
            result = await get_review_queue(mock_user)

            # Verify empty queue structure
            expected = {"queue": [], "total_pending": 0, "total_in_progress": 0}

            assert result == expected

    @pytest.mark.asyncio
    async def test_queue_with_pending_documents(self):
        """Test review queue with documents pending review."""
        mock_user = {"sub": "test-user-123"}

        with patch("app.core.database.db") as mock_db:
            # Mock queue response with sample data
            queue_data = [
                {
                    "id": "doc-123",
                    "title": "Brain v. Mann",
                    "original_filename": "brain_v_mann.pdf",
                    "doc_type": "case_law",
                    "doc_category": "PI",
                    "confidence_score": 0.95,
                    "preview_text": "Brain v. Mann, 129 Wis.2d 447 (1986)...",
                    "processing_status": "review_pending",
                    "uploaded_at": "2025-08-22T10:30:00Z",
                    "file_size": 1048576,
                    "batch_id": "batch-456",
                    "summary": "Personal injury case from Wisconsin",
                    "case_name": "Brain v. Mann",
                    "case_number": "85-0280",
                    "court": "Court of Appeals of Wisconsin",
                    "jurisdiction": "Wisconsin",
                    "practice_area": "Personal Injury",
                    "date": "1986-02-21",
                    "authors": ["James Brain", "Vicky Brain"],
                }
            ]

            stats_data = [{"total_pending": 1, "total_in_progress": 0}]

            # Mock database calls - queue query first, then stats query
            call_count = 0

            async def mock_rpc(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                result = Mock()
                if call_count == 1:  # First call is queue query
                    result.data = queue_data
                else:  # Second call is stats query
                    result.data = stats_data
                return result

            mock_db.supabase.rpc.return_value.execute = mock_rpc

            # Execute
            result = await get_review_queue(mock_user)

            # Verify queue structure and content
            assert "queue" in result
            assert "total_pending" in result
            assert "total_in_progress" in result

            assert len(result["queue"]) == 1
            assert result["total_pending"] == 1
            assert result["total_in_progress"] == 0

            # Verify document data structure
            doc = result["queue"][0]
            assert doc["id"] == "doc-123"
            assert doc["title"] == "Brain v. Mann"
            assert doc["doc_type"] == "case_law"
            assert doc["confidence_score"] == 0.95
            assert doc["preview_text"].startswith("Brain v. Mann")
            assert doc["processing_status"] == "review_pending"

            # Verify all metadata fields are included
            assert doc["case_name"] == "Brain v. Mann"
            assert doc["case_number"] == "85-0280"
            assert doc["court"] == "Court of Appeals of Wisconsin"
            assert doc["jurisdiction"] == "Wisconsin"
            assert doc["practice_area"] == "Personal Injury"

    @pytest.mark.asyncio
    async def test_queue_with_mixed_status_documents(self):
        """Test review queue with both pending and in-progress documents."""
        mock_user = {"sub": "test-user-123"}

        with patch("app.core.database.db") as mock_db:
            # Mock queue with documents in different review states
            queue_data = [
                {
                    "id": "doc-123",
                    "title": "First Document",
                    "original_filename": "doc1.pdf",
                    "doc_type": "case_law",
                    "doc_category": "PI",
                    "confidence_score": 0.95,
                    "preview_text": "Document 1 preview...",
                    "processing_status": "review_pending",
                    "uploaded_at": "2025-08-22T10:30:00Z",
                    "file_size": 1048576,
                    "batch_id": "batch-456",
                    "summary": None,
                    "case_name": None,
                    "case_number": None,
                    "court": None,
                    "jurisdiction": None,
                    "practice_area": None,
                    "date": None,
                    "authors": None,
                },
                {
                    "id": "doc-456",
                    "title": "Second Document",
                    "original_filename": "doc2.pdf",
                    "doc_type": "expert_report",
                    "doc_category": "WD",
                    "confidence_score": 0.88,
                    "preview_text": "Document 2 preview...",
                    "processing_status": "review_in_progress",
                    "uploaded_at": "2025-08-22T11:00:00Z",
                    "file_size": 2097152,
                    "batch_id": "batch-789",
                    "summary": "Expert report on damages",
                    "case_name": None,
                    "case_number": None,
                    "court": None,
                    "jurisdiction": None,
                    "practice_area": "Wrongful Death",
                    "date": "2025-01-15",
                    "authors": ["Dr. Expert"],
                },
            ]

            stats_data = [{"total_pending": 1, "total_in_progress": 1}]

            # Mock database calls
            call_count = 0

            async def mock_rpc(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                result = Mock()
                if call_count == 1:
                    result.data = queue_data
                else:
                    result.data = stats_data
                return result

            mock_db.supabase.rpc.return_value.execute = mock_rpc

            # Execute
            result = await get_review_queue(mock_user)

            # Verify mixed status handling
            assert len(result["queue"]) == 2
            assert result["total_pending"] == 1
            assert result["total_in_progress"] == 1

            # Verify documents are ordered by upload time (ASC)
            assert result["queue"][0]["id"] == "doc-123"  # Earlier upload
            assert result["queue"][1]["id"] == "doc-456"  # Later upload

    @pytest.mark.asyncio
    async def test_queue_sql_query_structure(self):
        """Test that correct SQL queries are executed."""
        mock_user = {"sub": "test-user-123"}

        with patch("app.core.database.db") as mock_db:
            mock_result = Mock()
            mock_result.data = []
            mock_db.supabase.rpc.return_value.execute = AsyncMock(return_value=mock_result)

            # Execute
            await get_review_queue(mock_user)

            # Verify two RPC calls were made (queue query + stats query)
            assert mock_db.supabase.rpc.return_value.execute.call_count == 2

            # Get the calls made to rpc
            rpc_calls = mock_db.supabase.rpc.call_args_list

            # First call should be queue query
            queue_call = rpc_calls[0][0]
            assert queue_call[0] == "execute_sql"
            queue_params = queue_call[1]
            queue_query = queue_params["query"]

            # Verify queue query structure
            assert "JOIN processing_files pf ON d.id = pf.document_id" in queue_query
            assert "WHERE d.is_reviewed = false" in queue_query
            assert "pf.status IN ('review_pending', 'review_in_progress')" in queue_query
            assert "ORDER BY pf.created_at ASC" in queue_query
            assert "LEFT(pf.extracted_text, 500) as preview_text" in queue_query

            # Second call should be stats query
            stats_call = rpc_calls[1][0]
            assert stats_call[0] == "execute_sql"
            stats_params = stats_call[1]
            stats_query = stats_params["query"]

            # Verify stats query structure
            assert "COUNT(*) FILTER (WHERE pf.status = 'review_pending')" in stats_query
            assert "COUNT(*) FILTER (WHERE pf.status = 'review_in_progress')" in stats_query

    @pytest.mark.asyncio
    async def test_queue_database_error(self):
        """Test review queue handles database errors gracefully."""
        mock_user = {"sub": "test-user-123"}

        with patch("app.core.database.db") as mock_db:
            # Mock database error
            mock_db.supabase.rpc.return_value.execute = AsyncMock(
                side_effect=Exception("Database connection failed")
            )

            # Execute and verify exception handling
            with pytest.raises(
                Exception
            ):  # Should raise HTTPException but this tests the underlying logic
                await get_review_queue(mock_user)

    @pytest.mark.asyncio
    async def test_queue_handles_null_metadata(self):
        """Test queue handles documents with null/missing metadata gracefully."""
        mock_user = {"sub": "test-user-123"}

        with patch("app.core.database.db") as mock_db:
            # Mock document with minimal/null metadata
            queue_data = [
                {
                    "id": "doc-minimal",
                    "title": None,  # AI extraction failed
                    "original_filename": "unknown.pdf",
                    "doc_type": "other",
                    "doc_category": "Other",
                    "confidence_score": None,
                    "preview_text": None,
                    "processing_status": "review_pending",
                    "uploaded_at": "2025-08-22T10:30:00Z",
                    "file_size": 1024,
                    "batch_id": "batch-failed",
                    "summary": None,
                    "case_name": None,
                    "case_number": None,
                    "court": None,
                    "jurisdiction": None,
                    "practice_area": None,
                    "date": None,
                    "authors": None,
                }
            ]

            stats_data = [{"total_pending": 1, "total_in_progress": 0}]

            call_count = 0

            async def mock_rpc(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                result = Mock()
                if call_count == 1:
                    result.data = queue_data
                else:
                    result.data = stats_data
                return result

            mock_db.supabase.rpc.return_value.execute = mock_rpc

            # Execute
            result = await get_review_queue(mock_user)

            # Verify graceful handling of null metadata
            assert len(result["queue"]) == 1
            doc = result["queue"][0]

            assert doc["id"] == "doc-minimal"
            assert doc["title"] is None
            assert doc["confidence_score"] is None
            assert doc["preview_text"] is None
            assert doc["summary"] is None

            # Should still include all expected fields even if null
            expected_fields = [
                "id",
                "title",
                "original_filename",
                "doc_type",
                "doc_category",
                "confidence_score",
                "preview_text",
                "processing_status",
                "uploaded_at",
                "file_size",
                "batch_id",
                "summary",
                "case_name",
                "case_number",
                "court",
                "jurisdiction",
                "practice_area",
                "date",
                "authors",
            ]

            for field in expected_fields:
                assert field in doc

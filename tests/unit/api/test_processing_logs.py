"""
Unit tests for processing logs endpoint.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.api.documents import get_processing_logs


class TestProcessingLogs:
    """Test processing logs functionality."""

    @pytest.mark.asyncio
    async def test_logs_empty(self):
        """Test processing logs endpoint with no log entries."""
        mock_user = {"sub": "test-user-123"}

        with patch("app.core.database.db") as mock_db:
            # Mock empty logs response
            call_count = 0

            async def mock_rpc(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                result = Mock()
                if call_count == 1:  # First call is logs query
                    result.data = []
                else:  # Second call is count query
                    result.data = [{"total_logs": 0}]
                return result

            mock_db.supabase.rpc.return_value.execute = mock_rpc

            # Execute
            result = await get_processing_logs(mock_user)

            # Verify empty logs structure
            expected = {"logs": [], "total_logs": 0}

            assert result == expected

    @pytest.mark.asyncio
    async def test_logs_with_job_and_file_entries(self):
        """Test processing logs with mixed job and file log entries."""
        mock_user = {"sub": "test-user-123"}

        with patch("app.core.database.db") as mock_db:
            # Mock logs response with sample data
            logs_data = [
                {
                    "job_id": "123e4567-e89b-12d3-a456-426614174000",
                    "job_status": "processing",
                    "created_at": "2025-08-22T10:30:00Z",
                    "total_files": 3,
                    "completed_files": 1,
                    "failed_files": 0,
                    "log_message": "Batch processing job created",
                    "log_level": "info",
                },
                {
                    "job_id": "123e4567-e89b-12d3-a456-426614174000",
                    "job_status": "file_completed",
                    "created_at": "2025-08-22T10:31:00Z",
                    "total_files": 1,
                    "completed_files": 1,
                    "failed_files": 0,
                    "log_message": "File processed successfully: document1.pdf",
                    "log_level": "info",
                },
                {
                    "job_id": "123e4567-e89b-12d3-a456-426614174000",
                    "job_status": "file_failed",
                    "created_at": "2025-08-22T10:32:00Z",
                    "total_files": 1,
                    "completed_files": 0,
                    "failed_files": 1,
                    "log_message": "File processing failed: document2.pdf - Invalid file format",
                    "log_level": "error",
                },
            ]

            count_data = [{"total_logs": 3}]

            # Mock database calls
            call_count = 0

            async def mock_rpc(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                result = Mock()
                if call_count == 1:  # First call is logs query
                    result.data = logs_data
                else:  # Second call is count query
                    result.data = count_data
                return result

            mock_db.supabase.rpc.return_value.execute = mock_rpc

            # Execute
            result = await get_processing_logs(mock_user)

            # Verify logs structure and content
            assert "logs" in result
            assert "total_logs" in result

            assert len(result["logs"]) == 3
            assert result["total_logs"] == 3

            # Verify first log entry (job creation)
            job_log = result["logs"][0]
            assert job_log["job_id"] == "123e4567-e89b-12d3-a456-426614174000"
            assert job_log["job_status"] == "processing"
            assert job_log["total_files"] == 3
            assert job_log["log_message"] == "Batch processing job created"
            assert job_log["log_level"] == "info"

            # Verify second log entry (file success)
            success_log = result["logs"][1]
            assert success_log["job_status"] == "file_completed"
            assert success_log["completed_files"] == 1
            assert "processed successfully" in success_log["log_message"]
            assert success_log["log_level"] == "info"

            # Verify third log entry (file failure)
            error_log = result["logs"][2]
            assert error_log["job_status"] == "file_failed"
            assert error_log["failed_files"] == 1
            assert "processing failed" in error_log["log_message"]
            assert "Invalid file format" in error_log["log_message"]
            assert error_log["log_level"] == "error"

    @pytest.mark.asyncio
    async def test_logs_with_review_status_entries(self):
        """Test processing logs with review-related status updates."""
        mock_user = {"sub": "test-user-123"}

        with patch("app.core.database.db") as mock_db:
            # Mock logs with review statuses
            logs_data = [
                {
                    "job_id": "123e4567-e89b-12d3-a456-426614174000",
                    "job_status": "file_review_pending",
                    "created_at": "2025-08-22T11:00:00Z",
                    "total_files": 1,
                    "completed_files": 1,
                    "failed_files": 0,
                    "log_message": "File ready for review: legal_case.pdf",
                    "log_level": "info",
                },
                {
                    "job_id": "123e4567-e89b-12d3-a456-426614174000",
                    "job_status": "file_review_in_progress",
                    "created_at": "2025-08-22T11:05:00Z",
                    "total_files": 1,
                    "completed_files": 0,
                    "failed_files": 0,
                    "log_message": "File under review: legal_case.pdf",
                    "log_level": "debug",
                },
            ]

            count_data = [{"total_logs": 2}]

            call_count = 0

            async def mock_rpc(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                result = Mock()
                if call_count == 1:
                    result.data = logs_data
                else:
                    result.data = count_data
                return result

            mock_db.supabase.rpc.return_value.execute = mock_rpc

            # Execute
            result = await get_processing_logs(mock_user)

            # Verify review status handling
            assert len(result["logs"]) == 2

            # Check review pending log
            pending_log = result["logs"][0]
            assert pending_log["job_status"] == "file_review_pending"
            assert "ready for review" in pending_log["log_message"]
            assert pending_log["log_level"] == "info"

            # Check review in progress log
            progress_log = result["logs"][1]
            assert progress_log["job_status"] == "file_review_in_progress"
            assert "under review" in progress_log["log_message"]
            assert progress_log["log_level"] == "debug"

    @pytest.mark.asyncio
    async def test_logs_sql_query_structure(self):
        """Test that correct SQL queries are executed."""
        mock_user = {"sub": "test-user-123"}

        with patch("app.core.database.db") as mock_db:
            mock_result = Mock()
            mock_result.data = []
            mock_db.supabase.rpc.return_value.execute = AsyncMock(return_value=mock_result)

            # Execute
            await get_processing_logs(mock_user)

            # Verify two RPC calls were made (logs query + count query)
            assert mock_db.supabase.rpc.return_value.execute.call_count == 2

            # Get the calls made to rpc
            rpc_calls = mock_db.supabase.rpc.call_args_list

            # First call should be logs query
            logs_call = rpc_calls[0][0]
            assert logs_call[0] == "execute_sql"
            logs_params = logs_call[1]
            logs_query = logs_params["query"]

            # Verify logs query structure
            assert "FROM processing_jobs pj" in logs_query
            assert "UNION ALL" in logs_query
            assert "FROM processing_files pf" in logs_query
            assert "ORDER BY created_at DESC" in logs_query
            assert "LIMIT 100" in logs_query
            assert "WHEN pf.status = 'failed' THEN 'error'" in logs_query

            # Second call should be count query
            count_call = rpc_calls[1][0]
            assert count_call[0] == "execute_sql"
            count_params = count_call[1]
            count_query = count_params["query"]

            # Verify count query structure
            assert "SELECT COUNT(*) as total_logs" in count_query
            assert "FROM (" in count_query
            assert "SELECT pj.id FROM processing_jobs pj" in count_query

    @pytest.mark.asyncio
    async def test_logs_database_error(self):
        """Test processing logs handles database errors gracefully."""
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
                await get_processing_logs(mock_user)

    @pytest.mark.asyncio
    async def test_logs_handles_null_fields(self):
        """Test logs handles entries with null/missing fields gracefully."""
        mock_user = {"sub": "test-user-123"}

        with patch("app.core.database.db") as mock_db:
            # Mock log entry with minimal/null fields
            logs_data = [
                {
                    "job_id": "123e4567-e89b-12d3-a456-426614174000",
                    "job_status": "file_processing",
                    "created_at": "2025-08-22T10:30:00Z",
                    "total_files": None,  # Missing value
                    "completed_files": None,
                    "failed_files": None,
                    "log_message": "File status updated: test.pdf -> processing",
                    "log_level": "debug",
                }
            ]

            count_data = [{"total_logs": 1}]

            call_count = 0

            async def mock_rpc(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                result = Mock()
                if call_count == 1:
                    result.data = logs_data
                else:
                    result.data = count_data
                return result

            mock_db.supabase.rpc.return_value.execute = mock_rpc

            # Execute
            result = await get_processing_logs(mock_user)

            # Verify graceful handling of null fields
            assert len(result["logs"]) == 1
            log = result["logs"][0]

            assert log["job_id"] == "123e4567-e89b-12d3-a456-426614174000"
            assert log["total_files"] == 0  # Default value applied
            assert log["completed_files"] == 0
            assert log["failed_files"] == 0
            assert log["log_message"] is not None
            assert log["log_level"] == "debug"

            # Should still include all expected fields
            expected_fields = [
                "job_id",
                "job_status",
                "created_at",
                "total_files",
                "completed_files",
                "failed_files",
                "log_message",
                "log_level",
            ]

            for field in expected_fields:
                assert field in log

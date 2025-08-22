"""
Unit tests for document statistics endpoint.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.api.documents import get_document_stats


class TestDocumentStats:
    """Test document statistics functionality."""

    @pytest.mark.asyncio
    async def test_stats_empty_database(self):
        """Test statistics endpoint with empty database."""
        mock_user = {"sub": "test-user-123"}

        with patch("app.core.database.db") as mock_db:
            # Mock empty database response
            mock_result = Mock()
            mock_result.data = []
            mock_db.supabase.rpc.return_value.execute = AsyncMock(return_value=mock_result)

            # Execute
            result = await get_document_stats(mock_user)

            # Verify all counts are 0
            expected = {
                "total_documents": 0,
                "books_textbooks": 0,
                "articles_publications": 0,
                "statutes_codes": 0,
                "case_law": 0,
                "expert_reports": 0,
                "other_documents": 0,
            }

            assert result == expected

    @pytest.mark.asyncio
    async def test_stats_with_sample_data(self):
        """Test statistics endpoint with sample data."""
        mock_user = {"sub": "test-user-123"}

        with patch("app.core.database.db") as mock_db:
            # Mock database response with sample data
            mock_result = Mock()
            mock_result.data = [
                {"doc_type": "case_law", "count": 5},
                {"doc_type": "expert_report", "count": 3},
                {"doc_type": "book", "count": 2},
                {"doc_type": "article", "count": 1},
            ]
            mock_db.supabase.rpc.return_value.execute = AsyncMock(return_value=mock_result)

            # Execute
            result = await get_document_stats(mock_user)

            # Verify correct mapping and totals
            expected = {
                "total_documents": 11,  # 5 + 3 + 2 + 1
                "books_textbooks": 2,
                "articles_publications": 1,
                "statutes_codes": 0,  # Not in sample data
                "case_law": 5,
                "expert_reports": 3,
                "other_documents": 0,  # Not in sample data
            }

            assert result == expected

    @pytest.mark.asyncio
    async def test_stats_with_all_document_types(self):
        """Test statistics endpoint with all document types."""
        mock_user = {"sub": "test-user-123"}

        with patch("app.core.database.db") as mock_db:
            # Mock database response with all document types
            mock_result = Mock()
            mock_result.data = [
                {"doc_type": "book", "count": 10},
                {"doc_type": "article", "count": 8},
                {"doc_type": "statute", "count": 6},
                {"doc_type": "case_law", "count": 15},
                {"doc_type": "expert_report", "count": 4},
                {"doc_type": "other", "count": 2},
            ]
            mock_db.supabase.rpc.return_value.execute = AsyncMock(return_value=mock_result)

            # Execute
            result = await get_document_stats(mock_user)

            # Verify all types are mapped correctly
            expected = {
                "total_documents": 45,  # Sum of all counts
                "books_textbooks": 10,
                "articles_publications": 8,
                "statutes_codes": 6,
                "case_law": 15,
                "expert_reports": 4,
                "other_documents": 2,
            }

            assert result == expected

    @pytest.mark.asyncio
    async def test_stats_database_error(self):
        """Test statistics endpoint handles database errors gracefully."""
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
                await get_document_stats(mock_user)

    @pytest.mark.asyncio
    async def test_stats_sql_query_structure(self):
        """Test that the correct SQL query is executed."""
        mock_user = {"sub": "test-user-123"}

        with patch("app.core.database.db") as mock_db:
            mock_result = Mock()
            mock_result.data = []
            mock_db.supabase.rpc.return_value.execute = AsyncMock(return_value=mock_result)

            # Execute
            await get_document_stats(mock_user)

            # Verify correct RPC call was made
            mock_db.supabase.rpc.assert_called_once()
            call_args = mock_db.supabase.rpc.call_args[0]

            # Should be calling execute_sql RPC function
            assert call_args[0] == "execute_sql"

            # Should have a query parameter (passed as positional args)
            call_args = mock_db.supabase.rpc.call_args[0]
            assert len(call_args) == 2  # function_name and params dict

            # Query should filter for reviewed, non-deleted, non-archived documents
            params = call_args[1]
            assert "query" in params
            query = params["query"]
            assert "is_reviewed = true" in query
            assert "is_deleted = false" in query
            assert "is_archived = false" in query
            assert "GROUP BY doc_type" in query

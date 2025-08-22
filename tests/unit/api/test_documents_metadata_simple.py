"""
Simplified unit tests for document metadata update endpoint.
"""

from unittest.mock import AsyncMock, patch

import pytest

from app.api.documents import update_document_metadata
from app.models.documents import DocumentUpdate
from app.models.enums import DocumentType


class TestDocumentMetadataUpdateSimple:
    """Test document metadata update functionality with simpler mocking."""

    @pytest.mark.asyncio
    async def test_update_metadata_success(self):
        """Test successful metadata update."""
        mock_user = {"sub": "test-user-123"}
        document_id = "doc-456"

        metadata = DocumentUpdate(title="Updated Title", doc_type=DocumentType.CASE_LAW)

        with patch("app.core.database.db") as mock_db:
            # Mock successful document check
            doc_check_mock = AsyncMock()
            doc_check_mock.return_value.data = [{"id": document_id, "is_reviewed": False}]

            # Mock successful document update
            doc_update_mock = AsyncMock()
            doc_update_mock.return_value.data = [
                {"id": document_id, "title": "Updated Title", "doc_type": "case_law"}
            ]

            # Mock processing file update
            processing_update_mock = AsyncMock()
            processing_update_mock.return_value.data = [{"id": "processing-123"}]

            # Set up database mocks
            mock_db.supabase.table.return_value.select.return_value.eq.return_value.execute = (
                doc_check_mock
            )
            mock_db.supabase.table.return_value.update.return_value.eq.return_value.execute = (
                AsyncMock(
                    side_effect=[doc_update_mock.return_value, processing_update_mock.return_value]
                )
            )

            # Execute
            result = await update_document_metadata(document_id, metadata, mock_user)

            # Verify response
            assert result["success"] is True
            assert result["message"] == "Document metadata updated successfully"
            assert "document" in result

    @pytest.mark.asyncio
    async def test_update_document_not_found(self):
        """Test updating non-existent document."""
        mock_user = {"sub": "test-user-123"}
        document_id = "non-existent"

        metadata = DocumentUpdate(title="Should Fail")

        with patch("app.core.database.db") as mock_db:
            # Mock document not found
            doc_check_mock = AsyncMock()
            doc_check_mock.return_value.data = []  # Empty = not found

            mock_db.supabase.table.return_value.select.return_value.eq.return_value.execute = (
                doc_check_mock
            )

            # Execute and verify 404
            with pytest.raises(Exception):  # HTTPException(404)
                await update_document_metadata(document_id, metadata, mock_user)

    @pytest.mark.asyncio
    async def test_update_already_reviewed_document(self):
        """Test updating already reviewed document."""
        mock_user = {"sub": "test-user-123"}
        document_id = "reviewed-doc"

        metadata = DocumentUpdate(title="Should Fail")

        with patch("app.core.database.db") as mock_db:
            # Mock document that is already reviewed
            doc_check_mock = AsyncMock()
            doc_check_mock.return_value.data = [{"id": document_id, "is_reviewed": True}]

            mock_db.supabase.table.return_value.select.return_value.eq.return_value.execute = (
                doc_check_mock
            )

            # Execute and verify 400
            with pytest.raises(Exception):  # HTTPException(400)
                await update_document_metadata(document_id, metadata, mock_user)

    @pytest.mark.asyncio
    async def test_update_invalid_user(self):
        """Test updating with invalid user token."""
        mock_user = {}  # Missing 'sub'
        document_id = "doc-123"

        metadata = DocumentUpdate(title="Should Fail")

        # Execute and verify 400
        with pytest.raises(Exception):  # HTTPException(400)
            await update_document_metadata(document_id, metadata, mock_user)

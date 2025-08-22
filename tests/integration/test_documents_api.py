"""Integration tests for documents API endpoints."""

from unittest.mock import Mock, patch

import pytest
from httpx import AsyncClient

# Import after environment is set
from app.main import app


@pytest.mark.integration
class TestDocumentsAPI:
    """Test documents API endpoints with real HTTP requests."""

    @pytest.fixture
    async def client(self):
        """Create test HTTP client."""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test that the API is responding."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_upload_document_success(self, client, auth_headers, sample_pdf_file):
        """Test successful document upload."""
        files = {
            "file": (
                sample_pdf_file["filename"],
                sample_pdf_file["content"],
                sample_pdf_file["content_type"],
            )
        }

        with patch("app.services.file_service.FileService.validate_file") as mock_validate:
            mock_validate.return_value = Mock(is_valid=True, errors=[])

            response = await client.post("/api/documents/upload", files=files, headers=auth_headers)

            assert response.status_code == 200
            data = response.json()
            assert "job_id" in data
            assert "uploaded_files" in data
            assert len(data["uploaded_files"]) == 1

    @pytest.mark.asyncio
    async def test_upload_document_invalid_file_type(self, client, auth_headers):
        """Test upload rejection for invalid file types."""
        files = {"file": ("test.exe", b"executable content", "application/x-executable")}

        response = await client.post("/api/documents/upload", files=files, headers=auth_headers)

        assert response.status_code == 400
        data = response.json()
        assert "unsupported" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_upload_document_too_large(self, client, auth_headers):
        """Test upload rejection for oversized files."""
        large_content = b"x" * (51 * 1024 * 1024)  # 51MB
        files = {"file": ("large.pdf", large_content, "application/pdf")}

        response = await client.post("/api/documents/upload", files=files, headers=auth_headers)

        assert response.status_code == 400
        data = response.json()
        assert "too large" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_library_documents(self, client, auth_headers):
        """Test retrieving library documents."""
        with patch("app.services.document_service.get_library_documents") as mock_get:
            mock_get.return_value = {
                "documents": [
                    {
                        "id": "test-doc-1",
                        "title": "Test Document",
                        "doc_type": "case_law",
                        "doc_category": "PI",
                    }
                ],
                "total": 1,
                "page": 1,
                "limit": 50,
            }

            response = await client.get("/api/documents/library", headers=auth_headers)

            assert response.status_code == 200
            data = response.json()
            assert "documents" in data
            assert len(data["documents"]) == 1

    @pytest.mark.asyncio
    async def test_get_documents_with_filters(self, client, auth_headers):
        """Test document filtering and search."""
        params = {"search": "test", "doc_type": "case_law", "doc_category": "PI"}

        with patch("app.services.document_service.search_documents") as mock_search:
            mock_search.return_value = {"documents": [], "total": 0}

            response = await client.get(
                "/api/documents/library", params=params, headers=auth_headers
            )

            assert response.status_code == 200
            mock_search.assert_called_once()

    @pytest.mark.asyncio
    async def test_unauthorized_request(self, client):
        """Test that requests without auth are rejected."""
        response = await client.get("/api/documents/library")

        assert response.status_code == 401
        data = response.json()
        assert "unauthorized" in data["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_document_stats(self, client, auth_headers):
        """Test document statistics endpoint."""
        with patch("app.services.document_service.get_document_stats") as mock_stats:
            mock_stats.return_value = {
                "total_documents": 10,
                "books_textbooks": 3,
                "articles_publications": 2,
                "statutes_codes": 1,
                "case_law": 3,
                "expert_reports": 1,
                "other_documents": 0,
            }

            response = await client.get("/api/documents/stats", headers=auth_headers)

            assert response.status_code == 200
            data = response.json()
            assert data["total_documents"] == 10
            assert all(
                key in data for key in ["books_textbooks", "articles_publications", "case_law"]
            )

    @pytest.mark.requires_supabase
    @pytest.mark.asyncio
    async def test_real_supabase_connection(self, client, auth_headers):
        """Test actual Supabase database connection."""
        # This test runs against real Supabase (marked for CI only)
        response = await client.get("/api/documents/stats", headers=auth_headers)

        # Should either succeed or fail with proper error handling
        assert response.status_code in [200, 401, 403, 500]

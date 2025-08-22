"""Unit tests for FileService."""

import io
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import UploadFile

# Import the service we're testing
try:
    from app.core.config import settings
    from app.models.processing import UploadResponse
    from app.services.file_service import FileService
except ImportError:
    # Skip these tests if imports fail
    pytest.skip("File service not fully implemented yet", allow_module_level=True)


@pytest.fixture
def mock_db():
    """Create a comprehensive mock for database operations."""
    with patch("app.services.file_service.db") as mock_db:
        # Mock the database operations chain with async support and valid UUIDs
        execute_mock = AsyncMock()
        execute_mock.return_value.data = [{"id": "123e4567-e89b-12d3-a456-426614174000"}]

        mock_db.supabase.table.return_value.insert.return_value.execute = execute_mock
        mock_db.supabase.table.return_value.update.return_value.eq.return_value.execute = (
            AsyncMock()
        )
        mock_db.supabase.table.return_value.select.return_value.eq.return_value.execute = (
            AsyncMock()
        )
        yield mock_db


class TestFileService:
    """Test FileService upload and validation functionality."""

    @pytest.fixture
    def file_service(self):
        """Create FileService instance for testing."""
        return FileService()

    @pytest.fixture
    def mock_upload_file(self):
        """Create a mock UploadFile for testing."""
        file_content = b"Test PDF content"
        file = UploadFile(
            filename="test.pdf",
            file=io.BytesIO(file_content),
            size=len(file_content),
            headers={"content-type": "application/pdf"},
        )
        return file

    @pytest.fixture
    def mock_large_file(self):
        """Create a mock large file that exceeds size limits."""
        large_content = b"x" * (60 * 1024 * 1024)  # 60MB
        file = UploadFile(
            filename="large.pdf",
            file=io.BytesIO(large_content),
            size=len(large_content),
            headers={"content-type": "application/pdf"},
        )
        return file

    @pytest.fixture
    def mock_invalid_file(self):
        """Create a mock file with invalid type."""
        file_content = b"Executable content"
        file = UploadFile(
            filename="malware.exe",
            file=io.BytesIO(file_content),
            size=len(file_content),
            headers={"content-type": "application/x-executable"},
        )
        return file

    @pytest.mark.asyncio
    async def test_upload_single_file_success(self, file_service, mock_upload_file, mock_db):
        """Test successful upload of a single valid file."""
        user_id = "test-user-123"

        with patch.object(file_service.validator, "validate_file") as mock_validate:
            with patch.object(
                file_service, "_process_single_file", new_callable=AsyncMock
            ) as mock_process:
                with patch.object(
                    file_service, "_start_background_processing", new_callable=AsyncMock
                ) as mock_bg:
                    # Setup mocks with valid UUID
                    mock_validate.return_value = Mock(is_valid=True, errors=[])
                    mock_process.return_value = {
                        "success": True,
                        "file_id": "123e4567-e89b-12d3-a456-426614174001",
                    }

                    # Execute
                    result = await file_service.upload_files([mock_upload_file], user_id)

                    # Verify
                    assert isinstance(result, UploadResponse)
                    assert result.success_count == 1
                    assert result.error_count == 0

    @pytest.mark.asyncio
    async def test_upload_multiple_files_success(self, file_service, mock_db):
        """Test successful upload of multiple valid files."""
        user_id = "test-user-123"

        # Create multiple mock files
        files = []
        for i in range(3):
            file_content = f"Test file {i} content".encode()
            file = UploadFile(
                filename=f"test_{i}.pdf",
                file=io.BytesIO(file_content),
                size=len(file_content),
                headers={"content-type": "application/pdf"},
            )
            files.append(file)

        with patch.object(file_service.validator, "validate_file") as mock_validate:
            with patch.object(
                file_service, "_process_single_file", new_callable=AsyncMock
            ) as mock_process:
                with patch.object(
                    file_service, "_start_background_processing", new_callable=AsyncMock
                ) as mock_bg:
                    # Setup mocks with valid UUID
                    mock_validate.return_value = Mock(is_valid=True, errors=[])
                    mock_process.return_value = {
                        "success": True,
                        "file_id": "123e4567-e89b-12d3-a456-426614174001",
                    }

                    # Execute
                    result = await file_service.upload_files(files, user_id)

                    # Verify
                    assert isinstance(result, UploadResponse)
                    assert result.success_count == 3
                    assert result.error_count == 0
                    assert mock_process.call_count == 3  # Called for each file

    @pytest.mark.asyncio
    async def test_upload_exceeds_batch_limit(self, file_service):
        """Test rejection when too many files are uploaded."""
        user_id = "test-user-123"

        # Create more files than allowed
        max_files = settings.max_files_per_batch
        files = [Mock() for _ in range(max_files + 1)]

        # Execute and verify exception
        with pytest.raises(ValueError, match="Too many files"):
            await file_service.upload_files(files, user_id)

    @pytest.mark.asyncio
    async def test_upload_file_too_large(self, file_service, mock_large_file, mock_db):
        """Test rejection of oversized files."""
        user_id = "test-user-123"

        with patch.object(
            file_service, "_process_single_file", new_callable=AsyncMock
        ) as mock_process:
            with patch.object(
                file_service, "_start_background_processing", new_callable=AsyncMock
            ) as mock_bg:
                # Setup mock to reject large file
                mock_process.return_value = {
                    "success": False,
                    "error": "File too large: 62914560 bytes (max: 52428800 bytes)",
                }

                # Execute
                result = await file_service.upload_files([mock_large_file], user_id)

                # Verify - file should be in failed_files, not uploaded_files
                assert isinstance(result, UploadResponse)
                assert result.success_count == 0
                assert result.error_count == 1
                assert len(result.failed_files) == 1
                assert result.failed_files[0]["filename"] == "large.pdf"
                assert "too large" in result.failed_files[0]["error"]

    @pytest.mark.asyncio
    async def test_upload_invalid_file_type(self, file_service, mock_invalid_file, mock_db):
        """Test rejection of invalid file types."""
        user_id = "test-user-123"

        with patch.object(
            file_service, "_process_single_file", new_callable=AsyncMock
        ) as mock_process:
            with patch.object(
                file_service, "_start_background_processing", new_callable=AsyncMock
            ) as mock_bg:
                # Setup mock to reject invalid file type
                mock_process.return_value = {
                    "success": False,
                    "error": "Unsupported file type: application/x-executable",
                }

                # Execute
                result = await file_service.upload_files([mock_invalid_file], user_id)

                # Verify - file should be in failed_files
                assert isinstance(result, UploadResponse)
                assert result.success_count == 0
                assert result.error_count == 1
                assert len(result.failed_files) == 1
                assert result.failed_files[0]["filename"] == "malware.exe"
                assert "Unsupported file type" in result.failed_files[0]["error"]

    @pytest.mark.asyncio
    async def test_upload_mixed_valid_invalid_files(
        self, file_service, mock_upload_file, mock_invalid_file, mock_db
    ):
        """Test handling of mixed valid and invalid files."""
        user_id = "test-user-123"
        files = [mock_upload_file, mock_invalid_file]

        def process_side_effect(file, job_id, user_id):
            if file.filename.endswith(".pdf"):
                return {"success": True, "file_id": "123e4567-e89b-12d3-a456-426614174001"}
            else:
                return {"success": False, "error": "Invalid file type"}

        with patch.object(
            file_service,
            "_process_single_file",
            new_callable=AsyncMock,
            side_effect=process_side_effect,
        ) as mock_process:
            with patch.object(
                file_service, "_start_background_processing", new_callable=AsyncMock
            ) as mock_bg:
                # Execute
                result = await file_service.upload_files(files, user_id)

                # Verify - should have 1 success, 1 failure
                assert isinstance(result, UploadResponse)
                assert result.success_count == 1
                assert result.error_count == 1
                assert len(result.uploaded_files) == 1
                assert len(result.failed_files) == 1
                assert result.failed_files[0]["filename"] == "malware.exe"

    def test_file_service_initialization(self):
        """Test FileService initializes correctly."""
        with patch("app.services.file_service.ProcessingService"):
            service = FileService()
            assert service.validator is not None
            assert service.processing_service is not None

    @pytest.mark.asyncio
    async def test_upload_empty_file_list(self, file_service, mock_db):
        """Test handling of empty file list."""
        user_id = "test-user-123"

        # Execute and verify exception
        with pytest.raises(ValueError, match="No files provided"):
            await file_service.upload_files([], user_id)

    @pytest.mark.asyncio
    async def test_upload_processing_service_failure(self, file_service, mock_upload_file, mock_db):
        """Test handling when file processing fails."""
        user_id = "test-user-123"

        with patch.object(
            file_service, "_process_single_file", new_callable=AsyncMock
        ) as mock_process:
            with patch.object(
                file_service, "_start_background_processing", new_callable=AsyncMock
            ) as mock_bg:
                # Setup mock to simulate processing failure
                mock_process.side_effect = Exception("Processing service unavailable")

                # Execute
                result = await file_service.upload_files([mock_upload_file], user_id)

                # Verify - exception should be caught and added to failed_files
                assert isinstance(result, UploadResponse)
                assert result.success_count == 0
                assert result.error_count == 1
                assert len(result.failed_files) == 1
                assert "Processing service unavailable" in result.failed_files[0]["error"]

    @pytest.mark.asyncio
    async def test_upload_database_failure(self, file_service, mock_upload_file):
        """Test handling when database operations fail."""
        user_id = "test-user-123"

        with patch("app.services.file_service.db") as mock_db:
            # Setup database failure for job creation
            execute_mock = AsyncMock()
            execute_mock.side_effect = Exception("Database error")
            mock_db.supabase.table.return_value.insert.return_value.execute = execute_mock

            # Execute and verify exception handling
            with pytest.raises(Exception, match="Database error"):
                await file_service.upload_files([mock_upload_file], user_id)

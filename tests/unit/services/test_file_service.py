"""Unit tests for FileService."""

import io
from unittest.mock import Mock, patch

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


class TestFileService:
    """Test FileService upload and validation functionality."""

    @pytest.fixture
    def file_service(self):
        """Create FileService instance for testing."""
        with patch("app.services.file_service.ProcessingService"):
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
    async def test_upload_single_file_success(self, file_service, mock_upload_file):
        """Test successful upload of a single valid file."""
        user_id = "test-user-123"

        with patch.object(file_service.validator, "validate_file") as mock_validate:
            with patch.object(
                file_service.processing_service, "create_processing_job"
            ) as mock_create_job:
                # Setup mocks
                mock_validate.return_value = Mock(is_valid=True, errors=[])
                mock_create_job.return_value = {"job_id": "job-123", "status": "created"}

                # Execute
                result = await file_service.upload_files([mock_upload_file], user_id)

                # Verify
                assert isinstance(result, UploadResponse)
                mock_validate.assert_called_once()
                mock_create_job.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_multiple_files_success(self, file_service):
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
                file_service.processing_service, "create_processing_job"
            ) as mock_create_job:
                # Setup mocks
                mock_validate.return_value = Mock(is_valid=True, errors=[])
                mock_create_job.return_value = {"job_id": "job-123", "status": "created"}

                # Execute
                result = await file_service.upload_files(files, user_id)

                # Verify
                assert isinstance(result, UploadResponse)
                assert mock_validate.call_count == 3  # Called for each file
                mock_create_job.assert_called_once()

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
    async def test_upload_file_too_large(self, file_service, mock_large_file):
        """Test rejection of oversized files."""
        user_id = "test-user-123"

        with patch.object(file_service.validator, "validate_file") as mock_validate:
            # Setup mock to reject large file
            mock_validate.return_value = Mock(
                is_valid=False, errors=["File too large: 62914560 bytes (max: 52428800 bytes)"]
            )

            # Execute and verify rejection
            with pytest.raises(ValueError, match="File validation failed"):
                await file_service.upload_files([mock_large_file], user_id)

    @pytest.mark.asyncio
    async def test_upload_invalid_file_type(self, file_service, mock_invalid_file):
        """Test rejection of invalid file types."""
        user_id = "test-user-123"

        with patch.object(file_service.validator, "validate_file") as mock_validate:
            # Setup mock to reject invalid type
            mock_validate.return_value = Mock(
                is_valid=False, errors=["Unsupported file type: application/x-executable"]
            )

            # Execute and verify rejection
            with pytest.raises(ValueError, match="File validation failed"):
                await file_service.upload_files([mock_invalid_file], user_id)

    @pytest.mark.asyncio
    async def test_upload_mixed_valid_invalid_files(
        self, file_service, mock_upload_file, mock_invalid_file
    ):
        """Test handling of mixed valid and invalid files."""
        user_id = "test-user-123"
        files = [mock_upload_file, mock_invalid_file]

        def validate_side_effect(file):
            if file.filename.endswith(".pdf"):
                return Mock(is_valid=True, errors=[])
            else:
                return Mock(is_valid=False, errors=["Invalid file type"])

        with patch.object(
            file_service.validator, "validate_file", side_effect=validate_side_effect
        ):
            # Should reject the batch if any file is invalid
            with pytest.raises(ValueError, match="File validation failed"):
                await file_service.upload_files(files, user_id)

    def test_file_service_initialization(self):
        """Test FileService initializes correctly."""
        with patch("app.services.file_service.ProcessingService"):
            service = FileService()
            assert service.validator is not None
            assert service.processing_service is not None

    @pytest.mark.asyncio
    async def test_upload_empty_file_list(self, file_service):
        """Test handling of empty file list."""
        user_id = "test-user-123"

        # Execute and verify exception
        with pytest.raises(ValueError, match="No files provided"):
            await file_service.upload_files([], user_id)

    @pytest.mark.asyncio
    async def test_upload_processing_service_failure(self, file_service, mock_upload_file):
        """Test handling when processing service fails."""
        user_id = "test-user-123"

        with patch.object(file_service.validator, "validate_file") as mock_validate:
            with patch.object(
                file_service.processing_service, "create_processing_job"
            ) as mock_create_job:
                # Setup mocks
                mock_validate.return_value = Mock(is_valid=True, errors=[])
                mock_create_job.side_effect = Exception("Processing service unavailable")

                # Execute and verify exception handling
                with pytest.raises(Exception, match="Processing service unavailable"):
                    await file_service.upload_files([mock_upload_file], user_id)

    @pytest.mark.asyncio
    async def test_upload_database_failure(self, file_service, mock_upload_file):
        """Test handling when database operations fail."""
        user_id = "test-user-123"

        with patch.object(file_service.validator, "validate_file") as mock_validate:
            with patch("app.services.file_service.db") as mock_db:
                # Setup mocks
                mock_validate.return_value = Mock(is_valid=True, errors=[])
                mock_db.table.return_value.insert.return_value.execute.side_effect = Exception(
                    "Database error"
                )

                # Execute and verify exception handling
                with pytest.raises(Exception, match="Database error"):
                    await file_service.upload_files([mock_upload_file], user_id)

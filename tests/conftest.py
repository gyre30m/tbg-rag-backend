"""Shared pytest fixtures and configuration."""

import os
import sys
from unittest.mock import AsyncMock, Mock

import pytest

# Add app directory to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Set testing environment
os.environ["TESTING"] = "true"

# Import after setting environment and path
try:
    from app.core.config import settings
    from app.core.database import get_supabase_client
except ImportError:
    # For tests that don't need these imports
    settings = None
    get_supabase_client = None


@pytest.fixture(scope="session")
def test_settings():
    """Override settings for testing."""
    settings.testing = True
    settings.supabase_url = "http://localhost:54321"
    settings.supabase_key = "test-key"
    return settings


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for unit tests."""
    client = Mock()

    # Mock table operations
    client.table = Mock(
        return_value=Mock(
            select=Mock(
                return_value=Mock(execute=AsyncMock(return_value=Mock(data=[], error=None)))
            ),
            insert=Mock(
                return_value=Mock(
                    execute=AsyncMock(return_value=Mock(data=[{"id": "test-id"}], error=None))
                )
            ),
            update=Mock(
                return_value=Mock(
                    eq=Mock(
                        return_value=Mock(
                            execute=AsyncMock(
                                return_value=Mock(data=[{"id": "test-id"}], error=None)
                            )
                        )
                    )
                )
            ),
            delete=Mock(
                return_value=Mock(
                    eq=Mock(
                        return_value=Mock(execute=AsyncMock(return_value=Mock(data=[], error=None)))
                    )
                )
            ),
        )
    )

    # Mock storage operations
    client.storage = Mock()
    client.storage.from_ = Mock(
        return_value=Mock(
            upload=AsyncMock(return_value=Mock(error=None)),
            download=AsyncMock(return_value=b"file content"),
            remove=AsyncMock(return_value=Mock(error=None)),
        )
    )

    # Mock auth operations
    client.auth = Mock()
    client.auth.get_user = AsyncMock(
        return_value=Mock(user=Mock(id="test-user-id", email="test@example.com"))
    )

    return client


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for unit tests."""
    client = Mock()

    # Mock embeddings
    client.embeddings = Mock()
    client.embeddings.create = AsyncMock(
        return_value=Mock(data=[Mock(embedding=[0.1] * 1536)])  # Mock embedding vector
    )

    return client


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client for unit tests."""
    client = Mock()

    # Mock messages
    client.messages = Mock()
    client.messages.create = AsyncMock(
        return_value=Mock(content=[Mock(text='{"doc_type": "case_law", "title": "Test Case"}')])
    )

    return client


@pytest.fixture
def sample_pdf_file():
    """Create a sample PDF file for testing."""
    return {
        "filename": "test_document.pdf",
        "content": b"%PDF-1.4\n%Test PDF content",
        "content_type": "application/pdf",
        "size": 1024,
    }


@pytest.fixture
def sample_text_file():
    """Create a sample text file for testing."""
    return {
        "filename": "test_document.txt",
        "content": b"This is a test document for the RAG system.",
        "content_type": "text/plain",
        "size": 44,
    }


@pytest.fixture
def sample_document_metadata():
    """Sample document metadata for testing."""
    return {
        "title": "Smith v. Jones",
        "doc_type": "case_law",
        "doc_category": "PI",
        "authors": ["Judge Smith"],
        "citation": "123 F.3d 456 (9th Cir. 2023)",
        "summary": "Personal injury case involving premises liability.",
        "tags": ["personal_injury", "premises_liability", "negligence"],
        "case_name": "Smith v. Jones",
        "case_number": "23-CV-1234",
        "court": "Ninth Circuit",
        "jurisdiction": "Federal",
        "practice_area": "Personal Injury",
        "confidence_score": 0.95,
    }


@pytest.fixture
def auth_headers():
    """Generate test authentication headers."""
    return {"Authorization": "Bearer test-jwt-token", "Content-Type": "application/json"}


@pytest.fixture
async def test_database():
    """Create a test database connection."""
    # This would connect to a test database
    # For now, return a mock
    return Mock()


@pytest.fixture
def temp_upload_dir(tmp_path):
    """Create a temporary directory for file uploads."""
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    return upload_dir


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset any singleton instances between tests."""
    # Reset any global state here
    yield
    # Cleanup after test


@pytest.fixture
def mock_redis_client():
    """Mock Redis client for background tasks."""
    client = Mock()
    client.get = AsyncMock(return_value=None)
    client.set = AsyncMock(return_value=True)
    client.delete = AsyncMock(return_value=True)
    client.lpush = AsyncMock(return_value=1)
    client.rpop = AsyncMock(return_value=None)
    return client


# Markers for test categories
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line("markers", "requires_supabase: Requires Supabase")
    config.addinivalue_line("markers", "requires_ai: Requires AI API access")

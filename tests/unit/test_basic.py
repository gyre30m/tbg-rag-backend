"""Basic tests to verify test infrastructure works."""

import os

import pytest


class TestBasicInfrastructure:
    """Test that the test infrastructure is working correctly."""

    def test_pytest_works(self):
        """Test that pytest is functioning."""
        assert True

    def test_environment_variables(self):
        """Test that test environment is set up."""
        assert os.environ.get("TESTING") == "true"

    def test_basic_math(self):
        """Test basic arithmetic to verify Python works."""
        assert 2 + 2 == 4
        assert 10 / 2 == 5

    def test_string_operations(self):
        """Test string operations."""
        test_string = "TBG RAG Backend"
        assert "RAG" in test_string
        assert test_string.startswith("TBG")
        assert test_string.endswith("Backend")

    def test_list_operations(self):
        """Test list operations."""
        doc_types = ["book", "article", "statute", "case_law", "expert_report", "other"]
        assert len(doc_types) == 6
        assert "case_law" in doc_types
        assert doc_types[0] == "book"

    def test_dict_operations(self):
        """Test dictionary operations."""
        doc_categories = {
            "PI": "Personal Injury",
            "WD": "Wrongful Death",
            "EM": "Employment",
            "BV": "Business Valuation",
            "Other": "General",
        }
        assert doc_categories["PI"] == "Personal Injury"
        assert len(doc_categories) == 5
        assert "PI" in doc_categories


@pytest.mark.asyncio
class TestAsyncInfrastructure:
    """Test async functionality works."""

    async def test_async_function(self):
        """Test that async tests work."""

        async def sample_async():
            return "async result"

        result = await sample_async()
        assert result == "async result"

    async def test_async_with_mock(self):
        """Test async functionality with mocking."""
        from unittest.mock import AsyncMock

        mock_func = AsyncMock(return_value="mocked result")
        result = await mock_func()

        assert result == "mocked result"
        mock_func.assert_called_once()

# Testing Strategy for TBG RAG Backend

## Executive Summary

This document outlines a comprehensive testing strategy for the TBG RAG Backend system, covering unit tests, integration tests, end-to-end tests, and continuous integration practices. The goal is to maintain high code quality, prevent regressions, and ensure reliable document processing workflows.

## 🎯 Testing Philosophy

1. **Test Early, Test Often**: Write tests alongside new features
2. **Fail Fast**: Catch issues before they reach production
3. **Automate Everything**: Tests should run automatically on commits
4. **Document Through Tests**: Tests serve as living documentation
5. **Focus on Critical Paths**: Prioritize testing document ingestion and RAG queries

## 📊 Test Coverage Goals

- **Unit Tests**: 80% coverage minimum
- **Integration Tests**: All API endpoints covered
- **E2E Tests**: Critical user workflows tested
- **Performance Tests**: Baseline metrics established

## 🧪 Testing Layers

### 1. Unit Tests (`tests/unit/`)

**Purpose**: Test individual functions and classes in isolation

**What to Test**:
- Service methods (AI service, extraction service, embedding service)
- Utility functions (file processing, validation)
- Model validation and serialization
- Security functions (JWT verification, access control)

**Example Structure**:
```python
# tests/unit/services/test_ai_service.py
import pytest
from unittest.mock import Mock, patch
from app.services.ai_service import AIService

class TestAIService:
    @pytest.fixture
    def ai_service(self):
        return AIService()

    @pytest.mark.asyncio
    async def test_extract_metadata_success(self, ai_service):
        """Test successful metadata extraction from text."""
        sample_text = "Sample legal document text..."

        with patch('app.services.ai_service.anthropic_client') as mock_client:
            mock_client.messages.create.return_value = Mock(
                content=[Mock(text='{"doc_type": "case_law", "title": "Test Case"}')]
            )

            result = await ai_service.extract_metadata(sample_text)

            assert result.doc_type == "case_law"
            assert result.title == "Test Case"

    @pytest.mark.asyncio
    async def test_extract_metadata_handles_api_error(self, ai_service):
        """Test graceful handling of API errors."""
        # Test implementation
```

**Run Command**: `pytest tests/unit/ -v`

### 2. Integration Tests (`tests/integration/`)

**Purpose**: Test interactions between components and external services

**What to Test**:
- API endpoint functionality
- Database operations (using test database)
- Supabase integration
- File storage operations
- Authentication flows

**Example Structure**:
```python
# tests/integration/api/test_documents_api.py
import pytest
from httpx import AsyncClient
from app.main import app

class TestDocumentsAPI:
    @pytest.fixture
    async def client(self):
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.fixture
    def auth_headers(self):
        """Generate test auth headers."""
        return {"Authorization": "Bearer test-token"}

    @pytest.mark.asyncio
    async def test_upload_document(self, client, auth_headers):
        """Test document upload endpoint."""
        files = {"file": ("test.pdf", b"fake pdf content", "application/pdf")}

        response = await client.post(
            "/api/documents/upload",
            files=files,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "document_id" in data
        assert data["status"] == "processing"

    @pytest.mark.asyncio
    async def test_get_documents_library(self, client, auth_headers):
        """Test retrieving documents from library."""
        response = await client.get(
            "/api/documents/library",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert isinstance(data["documents"], list)
```

**Run Command**: `pytest tests/integration/ -v`

### 3. End-to-End Tests (`tests/e2e/`)

**Purpose**: Test complete user workflows from start to finish

**What to Test**:
- Complete document upload → processing → review → approval workflow
- RAG query with document retrieval
- Batch upload and processing
- Error recovery scenarios

**Example Structure**:
```python
# tests/e2e/test_document_workflow.py
import pytest
import asyncio
from pathlib import Path

class TestDocumentWorkflow:
    @pytest.mark.asyncio
    async def test_complete_document_workflow(self, test_client, test_db):
        """Test complete workflow from upload to library."""
        # 1. Upload document
        test_file = Path("tests/fixtures/sample_case.pdf")
        upload_response = await upload_document(test_client, test_file)
        assert upload_response["status"] == "success"

        # 2. Wait for processing
        document_id = upload_response["document_id"]
        await wait_for_processing(test_client, document_id, timeout=30)

        # 3. Review metadata
        metadata = await get_document_metadata(test_client, document_id)
        assert metadata["status"] == "review_pending"

        # 4. Update and approve
        updated_metadata = {
            "title": "Updated Title",
            "doc_type": "case_law",
            "doc_category": "PI"
        }
        await update_metadata(test_client, document_id, updated_metadata)
        await approve_document(test_client, document_id)

        # 5. Verify in library
        library = await get_library_documents(test_client)
        approved_doc = next(
            (d for d in library if d["id"] == document_id),
            None
        )
        assert approved_doc is not None
        assert approved_doc["is_reviewed"] == True
```

**Run Command**: `pytest tests/e2e/ -v --timeout=60`

## 🔧 Testing Tools & Configuration

### Required Dependencies

```txt
# requirements-dev.txt
pytest>=7.4.3
pytest-asyncio>=0.21.1
pytest-cov>=4.1.0
pytest-timeout>=2.2.0
pytest-mock>=3.12.0
httpx>=0.25.0
factory-boy>=3.3.0
faker>=20.0.0
black>=23.11.0
flake8>=6.1.0
mypy>=1.7.0
pre-commit>=3.5.0
```

### Pytest Configuration

```ini
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
addopts =
    -v
    --strict-markers
    --tb=short
    --cov=app
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-fail-under=70
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow tests
    requires_supabase: Tests requiring Supabase connection
```

## 🏃 Test Execution Strategy

### Local Development

```bash
# Run all tests
pytest

# Run only unit tests
pytest tests/unit/ -m unit

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/services/test_ai_service.py

# Run tests matching pattern
pytest -k "test_extract"

# Run tests in parallel (faster)
pytest -n auto
```

### Pre-Commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: ['--max-line-length=100', '--ignore=E203,W503']

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]

  - repo: local
    hooks:
      - id: pytest-unit
        name: pytest unit tests
        entry: pytest tests/unit/ -x --tb=short
        language: system
        pass_filenames: false
        always_run: true
```

**Installation**:
```bash
pip install pre-commit
pre-commit install
```

### GitHub Actions CI/CD

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Cache dependencies
        uses: actions/cache@v3
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('requirements*.txt') }}

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run linting
        run: |
          black --check app tests
          flake8 app tests
          mypy app

      - name: Run unit tests
        run: pytest tests/unit/ -v --cov=app

      - name: Run integration tests
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
        run: pytest tests/integration/ -v

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml

      - name: Build Docker image
        run: docker build -t tbg-backend .

      - name: Run security scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: tbg-backend
```

## 🎨 Code Quality Standards

### Black Formatting
```bash
# Format all code
black app tests

# Check without changing
black --check app tests
```

### Flake8 Linting
```bash
# Run linting
flake8 app tests

# With specific rules
flake8 --max-line-length=100 --ignore=E203,W503
```

### Type Checking with MyPy
```bash
# Type check the app
mypy app

# With stricter settings
mypy --strict app
```

## 📦 Test Data Management

### Fixtures Directory Structure
```
tests/
├── fixtures/
│   ├── sample_documents/
│   │   ├── case_law.pdf
│   │   ├── expert_report.pdf
│   │   └── article.txt
│   ├── api_responses/
│   │   ├── openai_embedding.json
│   │   └── anthropic_metadata.json
│   └── test_data.py
```

### Factory Pattern for Test Data
```python
# tests/fixtures/factories.py
import factory
from app.models.documents import Document

class DocumentFactory(factory.Factory):
    class Meta:
        model = Document

    title = factory.Faker('sentence')
    doc_type = factory.Faker('random_element', elements=['case_law', 'article', 'book'])
    doc_category = factory.Faker('random_element', elements=['PI', 'WD', 'EM', 'BV'])
    content_hash = factory.Faker('sha256')
    file_size = factory.Faker('random_int', min=1000, max=1000000)
```

## 🚨 Critical Test Scenarios

### Must-Have Tests

1. **Document Upload Validation**
   - File size limits
   - Supported formats
   - Duplicate detection

2. **Processing Pipeline**
   - Text extraction from PDF/DOCX
   - AI metadata extraction
   - Embedding generation
   - Error recovery

3. **Security**
   - JWT validation
   - RLS policy enforcement
   - Rate limiting

4. **Data Integrity**
   - Content hash verification
   - Version control
   - Soft delete behavior

## 📈 Performance Testing

### Load Testing with Locust
```python
# tests/performance/locustfile.py
from locust import HttpUser, task, between

class DocumentUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def upload_document(self):
        with open('tests/fixtures/sample.pdf', 'rb') as f:
            self.client.post(
                '/api/documents/upload',
                files={'file': f},
                headers={'Authorization': 'Bearer test-token'}
            )

    @task(3)
    def search_documents(self):
        self.client.get('/api/documents/search?q=test')
```

**Run**: `locust -f tests/performance/locustfile.py --host=http://localhost:8000`

## 📊 Monitoring & Reporting

### Coverage Reports
- Generate HTML reports: `pytest --cov-report=html`
- View at: `htmlcov/index.html`
- Minimum coverage: 70% (enforced in CI)

### Test Results Dashboard
Consider integrating:
- Codecov for coverage tracking
- Sentry for error monitoring
- DataDog/New Relic for performance

## 🔄 Continuous Improvement

### Weekly Test Review
1. Review failed tests from the week
2. Identify flaky tests and fix
3. Add tests for new bugs found
4. Update test data as needed

### Monthly Metrics
- Test coverage percentage
- Test execution time
- Failure rate
- Time to fix test failures

## 🚀 Getting Started

1. **Install dev dependencies**:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. **Set up pre-commit hooks**:
   ```bash
   pre-commit install
   ```

3. **Run your first test**:
   ```bash
   pytest tests/unit/ -v
   ```

4. **Check coverage**:
   ```bash
   pytest --cov=app --cov-report=term-missing
   ```

## 📝 Test Writing Guidelines

1. **Use descriptive test names**: `test_should_reject_oversized_files`
2. **One assertion per test** (when possible)
3. **Use fixtures for common setup**
4. **Mock external dependencies**
5. **Test both success and failure paths**
6. **Document complex test scenarios**

## 🎯 Priority Implementation Plan

### Phase 1 (Week 1)
- [ ] Set up pytest configuration
- [ ] Create test directory structure
- [ ] Write unit tests for critical services
- [ ] Set up GitHub Actions CI

### Phase 2 (Week 2)
- [ ] Add integration tests for API endpoints
- [ ] Implement test fixtures and factories
- [ ] Set up coverage reporting
- [ ] Add pre-commit hooks

### Phase 3 (Week 3)
- [ ] Create E2E tests for main workflows
- [ ] Add performance testing
- [ ] Document test patterns
- [ ] Train team on testing practices

## 📚 Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Test-Driven Development with Python](https://www.obeythetestinggoat.com/)
- [Python Testing 101](https://realpython.com/python-testing/)

---

*Last Updated: 2025-08-22*
*Maintained by: TBG Development Team*

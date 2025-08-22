#!/bin/bash

# Test runner script for TBG RAG Backend
# Provides different test execution modes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "${BLUE}$1${NC}"
    echo "=================================="
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Default values
RUN_UNIT=true
RUN_INTEGRATION=false
RUN_E2E=false
RUN_COVERAGE=false
RUN_LINT=false
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --unit-only)
            RUN_UNIT=true
            RUN_INTEGRATION=false
            RUN_E2E=false
            shift
            ;;
        --integration-only)
            RUN_UNIT=false
            RUN_INTEGRATION=true
            RUN_E2E=false
            shift
            ;;
        --e2e-only)
            RUN_UNIT=false
            RUN_INTEGRATION=false
            RUN_E2E=true
            shift
            ;;
        --all)
            RUN_UNIT=true
            RUN_INTEGRATION=true
            RUN_E2E=true
            shift
            ;;
        --coverage)
            RUN_COVERAGE=true
            shift
            ;;
        --lint)
            RUN_LINT=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            echo "TBG RAG Backend Test Runner"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --unit-only       Run only unit tests (default)"
            echo "  --integration-only Run only integration tests"
            echo "  --e2e-only        Run only end-to-end tests"
            echo "  --all             Run all test suites"
            echo "  --coverage        Generate coverage reports"
            echo "  --lint            Run linting checks"
            echo "  --verbose         Verbose output"
            echo "  --help            Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                      # Run unit tests"
            echo "  $0 --all --coverage     # Run all tests with coverage"
            echo "  $0 --lint --unit-only   # Lint then unit tests"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check if we're in the right directory
if [[ ! -f "pytest.ini" ]]; then
    print_error "pytest.ini not found. Are you in the webapp-backend directory?"
    exit 1
fi

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    print_warning "Virtual environment not activated. Consider activating with 'source venv/bin/activate'"
fi

# Set test verbosity
PYTEST_ARGS="-x --tb=short"
if [[ "$VERBOSE" == "true" ]]; then
    PYTEST_ARGS="-v --tb=long"
fi

# Add coverage if requested
if [[ "$RUN_COVERAGE" == "true" ]]; then
    PYTEST_ARGS="$PYTEST_ARGS --cov=app --cov-report=term-missing --cov-report=html:htmlcov"
fi

print_header "TBG RAG Backend Test Suite"

# Run linting if requested
if [[ "$RUN_LINT" == "true" ]]; then
    print_header "Running Code Quality Checks"

    echo "Running Black formatter..."
    if black --check app tests --line-length=100; then
        print_success "Black formatting check passed"
    else
        print_error "Black formatting check failed"
        exit 1
    fi

    echo "Running Flake8 linter..."
    if flake8 app tests --max-line-length=100 --ignore=E203,W503,E501; then
        print_success "Flake8 linting passed"
    else
        print_error "Flake8 linting failed"
        exit 1
    fi

    echo "Running MyPy type checker..."
    if mypy app --ignore-missing-imports; then
        print_success "MyPy type checking passed"
    else
        print_warning "MyPy type checking failed (continuing anyway)"
    fi
fi

# Run unit tests
if [[ "$RUN_UNIT" == "true" ]]; then
    print_header "Running Unit Tests"
    if pytest tests/unit/ $PYTEST_ARGS -m "unit or not (integration or e2e)"; then
        print_success "Unit tests passed"
    else
        print_error "Unit tests failed"
        exit 1
    fi
fi

# Run integration tests
if [[ "$RUN_INTEGRATION" == "true" ]]; then
    print_header "Running Integration Tests"

    # Check if Supabase credentials are available
    if [[ -z "$SUPABASE_URL" && -f ".env" ]]; then
        print_warning "Loading Supabase credentials from .env file"
        export $(cat .env | grep SUPABASE_ | xargs) 2>/dev/null || true
    fi

    if pytest tests/integration/ $PYTEST_ARGS -m "integration"; then
        print_success "Integration tests passed"
    else
        print_error "Integration tests failed"
        exit 1
    fi
fi

# Run E2E tests
if [[ "$RUN_E2E" == "true" ]]; then
    print_header "Running End-to-End Tests"

    if pytest tests/e2e/ $PYTEST_ARGS -m "e2e" --timeout=60; then
        print_success "E2E tests passed"
    else
        print_error "E2E tests failed"
        exit 1
    fi
fi

# Generate coverage report
if [[ "$RUN_COVERAGE" == "true" ]]; then
    print_header "Coverage Report"
    echo "HTML report generated at: htmlcov/index.html"

    # Open coverage report if on macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open htmlcov/index.html 2>/dev/null || true
    fi
fi

print_header "Test Suite Complete"
print_success "All requested tests passed!"

# Show next steps
echo ""
echo "Next steps:"
echo "  • Run 'scripts/run-tests.sh --all --coverage' for full test suite"
echo "  • View coverage: open htmlcov/index.html"
echo "  • Run specific tests: pytest tests/unit/test_specific.py"
echo "  • Install pre-commit hooks: pre-commit install"

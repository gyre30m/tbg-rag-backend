#!/bin/bash
# Production startup script for Railway

echo "Starting TBG RAG Backend API..."
echo "Python version: $(python --version)"
echo "Environment: $RAILWAY_ENVIRONMENT"

# Use production requirements if available
if [ -f "requirements-production.txt" ]; then
    echo "Using production requirements..."
    pip install -r requirements-production.txt
else
    echo "Using standard requirements..."
    pip install -r requirements.txt
fi

# Start the FastAPI application
echo "Starting uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1
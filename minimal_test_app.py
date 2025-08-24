#!/usr/bin/env python3
"""
Minimal FastAPI server for testing Railway deployment.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create minimal FastAPI app
app = FastAPI(
    title="Minimal Test API",
    version="1.0.0",
    description="Minimal FastAPI server for testing deployment",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Minimal FastAPI server is running!", "status": "healthy"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "server": "minimal"}


@app.get("/test/{item_id}")
async def test_endpoint(item_id: int):
    """Test endpoint with parameter."""
    return {"item_id": item_id, "message": f"Test item {item_id}"}


if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 8000))
    # Use WARNING level to avoid Railway treating INFO logs as errors
    uvicorn.run("minimal_test_app:app", host="0.0.0.0", port=port, log_level="warning")

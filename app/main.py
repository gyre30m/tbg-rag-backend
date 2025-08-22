"""
Main FastAPI application for TBG RAG Document Ingestion System.
"""

import logging
from datetime import datetime

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import documents, processing, webhooks
from app.core.config import settings
from app.core.database import db

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="TBG RAG Document Ingestion API",
    version="1.0.0",
    description="Backend API for document upload, processing, and metadata management in the TBG RAG system",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# CORS middleware for NextJS frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # NextJS dev server
        "http://127.0.0.1:3000",
        # Add production origins as needed
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Application startup tasks."""
    logger.info("Starting TBG RAG Document Ingestion API")

    # Test database connection
    if await db.health_check():
        logger.info("Database connection successful")
    else:
        logger.error("Database connection failed")
        raise Exception("Cannot connect to database")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks."""
    logger.info("Shutting down TBG RAG Document Ingestion API")


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint for health checking."""
    return {"message": "TBG RAG Document Ingestion API", "version": "1.0.0", "status": "healthy"}


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check endpoint."""
    try:
        db_healthy = await db.health_check()

        return {
            "status": "healthy" if db_healthy else "unhealthy",
            "database": "connected" if db_healthy else "disconnected",
            "timestamp": str(datetime.utcnow()),
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


# Custom exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# Include API routers
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])

app.include_router(processing.router, prefix="/api/processing", tags=["Processing"])

app.include_router(webhooks.router, prefix="/api/webhooks", tags=["Webhooks"])


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )

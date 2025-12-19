"""
Main FastAPI application

TOR Metadata Correlation System
Tamil Nadu Police Hackathon 2025

This application provides a RESTful API for analyzing TOR network metadata
to generate investigative leads using timing correlation and statistical inference.

LEGAL NOTICE:
- Uses only publicly available TOR relay metadata
- Analyzes timing patterns, not payload content
- Generates probabilistic leads, not identities
- Designed for lawful law enforcement use only
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.api import router
from app.utils import setup_logging
from config import settings


# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware (configure appropriately for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")

# Root endpoint
@app.get("/")
async def root():
    """System information and legal notice"""
    return {
        "system": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "operational",
        "api_docs": "/docs",
        "legal_notice": {
            "purpose": "Law enforcement analytical platform for TOR metadata correlation",
            "data_sources": "Publicly available TOR relay metadata only",
            "methodology": "Timing correlation and statistical inference",
            "output": "Probabilistic investigative leads with confidence scores",
            "limitations": [
                "Does NOT decrypt TOR traffic",
                "Does NOT deanonymize users",
                "Does NOT identify individuals",
                "Generates hypotheses only, not proof"
            ],
            "ethical_framework": "Designed for lawful law enforcement use with proper authorization"
        },
        "endpoints": {
            "api": "/api",
            "documentation": "/docs",
            "health": "/api/health"
        }
    }


@app.on_event("startup")
async def startup_event():
    """Application startup tasks"""
    logger.info("=" * 80)
    logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info("Starting up...")
    logger.info("=" * 80)
    
    # Ensure directories exist
    settings.create_directories()
    
    logger.info("Application ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    logger.info("Shutting down...")
    logger.info("=" * 80)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    )

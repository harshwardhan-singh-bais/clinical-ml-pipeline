"""
FastAPI Application
Phase 1: Application Bootstrap
Phase 2: API Request Intake
Phase 17: API Response
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.settings import settings, validate_environment
import logging

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Clinical ML Pipeline API",
    description="GenAI-Powered Clinical Note Summarization and Hypothesis Generation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """
    Application startup event.
    Phase 1: Application Bootstrap & Environment Setup
    
    If this fails → app must not start.
    """
    logger.info("=" * 50)
    logger.info("Starting Clinical ML Pipeline API")
    logger.info("=" * 50)
    
    try:
        # Validate environment variables
        validate_environment()
        logger.info("✓ Environment validation passed")
        
        # Log configuration
        logger.info(f"✓ Environment: {settings.APP_ENV}")
        logger.info(f"✓ API Host: {settings.API_HOST}:{settings.API_PORT}")
        logger.info(f"✓ Embedding Model: {settings.EMBEDDING_MODEL}")
        logger.info(f"✓ LLM Model: {settings.GEMINI_MODEL}")
        logger.info(f"✓ Supabase URL: {settings.SUPABASE_URL}")
        
        # Test database connection (optional)
        try:
            from utils.db import SupabaseVectorStore
            vector_store = SupabaseVectorStore()
            count = vector_store.count_embeddings()
            logger.info(f"✓ Database connection successful ({count} embeddings indexed)")
        except Exception as e:
            logger.warning(f"⚠ Database connection test failed: {e}")
            logger.warning("  (Proceeding anyway - database may not be initialized yet)")
        
        logger.info("=" * 50)
        logger.info("Clinical ML Pipeline API started successfully")
        logger.info("=" * 50)
        
    except Exception as e:
        logger.error(f"✗ Startup failed: {e}")
        raise RuntimeError(f"Application startup failed: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Shutting down Clinical ML Pipeline API")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Clinical ML Pipeline API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "environment": settings.APP_ENV,
        "model": settings.GEMINI_MODEL
    }


# Import and include routers
from app.routes import router as api_router
app.include_router(api_router, prefix="/api/v1")

"""
FastAPI Main Application Entry Point
Phase 1: Application Bootstrap

Run with: uvicorn app.main:app --reload
"""

from app import app

if __name__ == "__main__":
    import uvicorn
    from config.settings import settings
    
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )

"""
Main application module for NYC Landmarks Vector Database.

This module initializes the FastAPI application and registers all routes.
"""

import logging
from typing import Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from nyc_landmarks.api import query, chat
from nyc_landmarks.config.settings import settings

# Configure logging
logging.basicConfig(level=settings.LOG_LEVEL.value)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="NYC Landmarks Vector Database API",
    description="API for accessing NYC landmarks information and semantic search functionality",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify the allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(query.router)
app.include_router(chat.router)


# Add global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for the application."""
    logger.error(f"Global exception handler caught: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )


# Add health check endpoint
@app.get("/health", tags=["health"])
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


# Add root endpoint
@app.get("/", tags=["root"])
async def root() -> Dict[str, str]:
    """Root endpoint that returns a welcome message."""
    return {
        "message": "Welcome to the NYC Landmarks Vector Database API",
        "version": "0.1.0",
        "docs_url": "/docs",
    }


if __name__ == "__main__":
    """Run the application using Uvicorn when this module is executed directly."""
    import uvicorn
    
    logger.info(f"Starting application on {settings.APP_HOST}:{settings.APP_PORT}")
    uvicorn.run(
        "nyc_landmarks.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.ENV == "development",
    )

"""
Main application module for NYC Landmarks Vector Database.

This module initializes the FastAPI application and registers all routes.
"""

import time
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import AnyUrl, BaseModel, Field

from nyc_landmarks.api import chat, query
from nyc_landmarks.api.middleware import setup_api_middleware
from nyc_landmarks.config.settings import settings
from nyc_landmarks.utils.logger import get_logger, log_error

# Configure logging
logger = get_logger(__name__)


# Response models for basic endpoints
class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Overall health status of the API")
    services: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="Health status of individual services"
    )


class RootResponse(BaseModel):
    """Root endpoint response model."""

    message: str = Field(..., description="Welcome message")
    version: str = Field(..., description="API version number")
    docs_url: str = Field(..., description="URL to API documentation")


# Define server models for OpenAPI documentation
class ServerVariable(BaseModel):
    """Server variable model for OpenAPI."""

    default: str
    description: str = ""
    enum: List[str] = []


class Server(BaseModel):
    """Server model for OpenAPI."""

    url: AnyUrl
    description: str = ""
    variables: Dict[str, ServerVariable] = {}


# Create list of servers for OpenAPI based on environment
servers = []
if settings.ENV == "production":
    # In production, only show the production server URL
    if settings.DEPLOYMENT_URL:
        servers.append(
            {"url": settings.DEPLOYMENT_URL, "description": "Production server"}
        )
else:
    # In development, show the local server URL
    servers.append(
        {
            "url": f"http://127.0.0.1:{settings.APP_PORT}",
            "description": "Local development server",
        }
    )
    # Optionally include production URL in development for testing
    if settings.DEPLOYMENT_URL and settings.SHOW_PROD_URL_IN_DEV:
        servers.append(
            {"url": settings.DEPLOYMENT_URL, "description": "Production server"}
        )

# Create FastAPI application
app = FastAPI(
    title="NYC Landmarks Vector Database API",
    description="API for accessing NYC landmarks information and semantic search functionality",
    version="0.1.0",
    servers=servers,  # Add servers configuration
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For production, specify the allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup API middleware for request tracking and performance monitoring
setup_api_middleware(app)

# Register routers
app.include_router(query.router)
app.include_router(chat.router)


# Add global exception handler
@app.exception_handler(Exception)  # type: ignore[misc]
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for the application."""
    # Don't catch HTTPException - let FastAPI handle validation errors properly
    if isinstance(exc, HTTPException):
        # Re-raise HTTPException to let FastAPI handle it with proper status codes
        raise exc

    # Log the error with standardized classification and structure
    log_error(
        logger,
        error=exc,
        error_type="server",
        message=f"Global exception handler caught: {exc}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "client_host": request.client.host if request.client else None,
            "error_location": "global_handler",
        },
    )

    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )


# Add health check endpoint
@app.get("/health", response_model=HealthResponse, tags=["health"])  # type: ignore[misc]
async def health_check() -> HealthResponse:
    """Health check endpoint that tests connections to critical services."""
    services = {}

    # Check Pinecone connection
    try:
        from nyc_landmarks.vectordb.pinecone_db import PineconeDB

        pinecone_db = PineconeDB()
        stats = pinecone_db.get_index_stats()

        # Consider the connection successful if we get some data back
        if (
            stats
            and isinstance(stats, dict)
            and ("dimension" in stats or "namespaces" in stats)
        ):
            pinecone_status = "healthy"
            vector_count = stats.get("total_vector_count", 0)
            services["pinecone"] = {
                "status": pinecone_status,
                "index": pinecone_db.index_name,
                "vector_count": vector_count,
                "timestamp": time.time(),
            }
        else:
            pinecone_status = "degraded"
            services["pinecone"] = {
                "status": pinecone_status,
                "error": "Could not retrieve index stats",
                "timestamp": time.time(),
            }
    except Exception as e:
        # Use structured error logging
        log_error(
            logger,
            error=e,
            error_type="dependency",
            message="Pinecone health check failed",
            extra={"component": "pinecone", "operation": "health_check"},
        )
        services["pinecone"] = {
            "status": "error",
            "error": str(e),
            "timestamp": time.time(),
        }

    # Determine overall status
    if any(service.get("status") == "error" for service in services.values()):
        overall_status = "error"
    elif any(service.get("status") == "degraded" for service in services.values()):
        overall_status = "degraded"
    else:
        overall_status = "healthy"

    return HealthResponse(status=overall_status, services=services)


# Add root endpoint
@app.get("/", response_model=RootResponse, tags=["root"])  # type: ignore[misc]
async def root() -> RootResponse:
    """Root endpoint that returns a welcome message."""
    return RootResponse(
        message="Welcome to the NYC Landmarks Vector Database API",
        version="0.1.0",
        docs_url="/docs",
    )


if __name__ == "__main__":
    """Run the application using Uvicorn when this module is executed directly."""
    import uvicorn

    logger.info(
        f"Starting application on {settings.APP_HOST}:{settings.APP_PORT}",
        extra={
            "environment": settings.ENV,
            "app_host": settings.APP_HOST,
            "app_port": settings.APP_PORT,
            "log_provider": settings.LOG_PROVIDER.value,
            "startup_event": "application_start",
        },
    )
    uvicorn.run(
        "nyc_landmarks.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.ENV == "development",
    )

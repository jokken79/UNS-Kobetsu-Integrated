"""
UNS Kobetsu Keiyakusho - Main FastAPI Application

個別契約書管理システム (Individual Contract Management System)
For managing 派遣契約 (dispatch contracts) under 労働者派遣法第26条
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.database import check_db_connection
from app.core.rate_limit import limiter, rate_limit_exceeded_handler
from app.api.v1 import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    # Startup
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # Check database connection
    if not check_db_connection():
        print("WARNING: Database connection failed!")
    else:
        print("Database connection successful")

    yield

    # Shutdown
    print("Shutting down application...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="""
## UNS Kobetsu Keiyakusho API

個別契約書管理システム - Individual Contract Management System

### Features
- 📝 Create and manage individual dispatch contracts (個別契約書)
- 📋 Track all 16 legally required items under 労働者派遣法第26条
- 📊 Dashboard with contract statistics
- 📄 Generate PDF/DOCX contracts
- 🔒 JWT-based authentication

### Legal Compliance
This system ensures compliance with Japan's Worker Dispatch Law (労働者派遣法),
specifically Article 26 which requires 16 specific items in individual contracts.
    """,
    version=settings.APP_VERSION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # Only configured origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],  # Explicit methods
    allow_headers=["Authorization", "Content-Type", "Accept"],  # Specific headers
    expose_headers=["Content-Disposition", "X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],  # For file downloads and rate limit info
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Add rate limiter to the app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions globally."""
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )


# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# Root endpoint
@app.get("/", tags=["Root"])
@limiter.limit("200 per minute")
async def root(request: Request):
    """Root endpoint with API information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "個別契約書管理システム - Individual Contract Management System",
        "docs_url": "/docs",
        "api_prefix": settings.API_V1_PREFIX,
    }


# Health check endpoint
@app.get("/health", tags=["Health"])
@limiter.limit("1000 per minute")  # Very permissive for health checks
async def health_check(request: Request):
    """Health check endpoint for container orchestration."""
    db_healthy = check_db_connection()

    return {
        "status": "healthy" if db_healthy else "degraded",
        "database": "connected" if db_healthy else "disconnected",
        "version": settings.APP_VERSION,
    }


# Ready check endpoint
@app.get("/ready", tags=["Health"])
@limiter.limit("1000 per minute")  # Very permissive for health checks
async def readiness_check(request: Request):
    """Readiness check for load balancers."""
    db_healthy = check_db_connection()

    if not db_healthy:
        return JSONResponse(
            status_code=503,
            content={"status": "not ready", "reason": "database unavailable"}
        )

    return {"status": "ready"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )

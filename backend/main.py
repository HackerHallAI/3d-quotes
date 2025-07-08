"""
FastAPI main application for the 3D Quotes tool.

This is the entry point for the 3D printing quotes application.
"""
import logging
import os
from contextlib import asynccontextmanager
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from config.settings import settings
from utils.validators import ProcessingError, ValidationError

# Initial basic logging to console only
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler for startup and shutdown events.
    """
    # Startup
    logger.info("Starting 3D Quotes application...")

    # Create necessary directories
    os.makedirs(settings.temp_upload_dir, exist_ok=True)
    os.makedirs(os.path.dirname(settings.log_file), exist_ok=True)

    # Now configure file logging after directories exist
    if settings.log_file:
        file_handler = logging.FileHandler(settings.log_file)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(file_handler)
        logger.info("File logging configured")

    # Include routers
    include_routers()

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down 3D Quotes application...")

    # Clean up temporary files
    import shutil
    if os.path.exists(settings.temp_upload_dir):
        try:
            shutil.rmtree(settings.temp_upload_dir)
            os.makedirs(settings.temp_upload_dir, exist_ok=True)
            logger.info("Cleaned up temporary files")
        except Exception as e:
            logger.error(f"Failed to clean up temporary files: {e}")

    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="A web-based quoting tool for instant 3D printing estimates",
    version=settings.app_version,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add trusted host middleware in production
if not settings.debug:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", settings.host]
    )


# Global exception handlers
@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """
    Handle custom validation errors.
    """
    logger.warning(f"Validation error: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "Validation Error",
            "message": exc.message,
            "field": exc.field
        }
    )


@app.exception_handler(ProcessingError)
async def processing_exception_handler(request: Request, exc: ProcessingError):
    """
    Handle custom processing errors.
    """
    logger.error(f"Processing error: {exc.message}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Processing Error",
            "message": exc.message
        }
    )


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle Pydantic validation errors.
    """
    logger.warning(f"Request validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Request Validation Error",
            "message": "Invalid request data",
            "details": exc.errors()
        }
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Handle HTTP exceptions.
    """
    logger.error(f"HTTP error {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP Error",
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle unexpected errors.
    """
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred"
        }
    )


# Middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log all incoming requests.
    """
    logger.info(f"Request: {request.method} {request.url}")

    response = await call_next(request)

    logger.info(f"Response: {response.status_code}")
    return response


# Health check endpoint
@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.
    """
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "debug": settings.debug
    }


# Root endpoint
@app.get("/")
async def root() -> Dict[str, str]:
    """
    Root endpoint with basic information.
    """
    return {
        "message": "3D Quotes API",
        "version": settings.app_version,
        "docs": "/docs" if settings.debug else "Documentation disabled in production"
    }


# API configuration endpoint
@app.get("/api/config")
async def get_api_config() -> Dict[str, Any]:
    """
    Get API configuration for frontend.
    """
    return {
        "material_types": ["PA12_GREY", "PA12_BLACK", "PA12_GB"],
        "max_file_size": settings.max_file_size,
        "allowed_extensions": settings.allowed_extensions,
        "minimum_order": settings.minimum_order_usd,
        "currency": settings.currency,
        "stripe_publishable_key": settings.stripe_publishable_key,
        "printer_constraints": settings.printer_constraints,
        "material_rates": settings.material_rates,
        "shipping_costs": settings.shipping_costs
    }


# Include routers (will be added as we create them)
# Note: Import here to avoid circular imports
def include_routers():
    """
    Include all routers after they are created.
    """
    try:
        from routers.quote import router as quote_router
        app.include_router(quote_router, prefix="/api/quote", tags=["quotes"])
        logger.info("Included quote router")
    except ImportError as e:
        logger.warning(f"Quote router not available: {e}")

    try:
        from routers.payment import router as payment_router
        app.include_router(payment_router, prefix="/api/payment", tags=["payments"])
        logger.info("Included payment router")
    except ImportError as e:
        logger.warning(f"Payment router not available: {e}")

    try:
        from routers.order import router as order_router
        app.include_router(order_router, prefix="/api/order", tags=["orders"])
        logger.info("Included order router")
    except ImportError as e:
        logger.warning(f"Order router not available: {e}")


# Note: Routers are included in the lifespan function above


def create_app() -> FastAPI:
    """
    Application factory function.
    """
    return app


if __name__ == "__main__":
    # Run the application
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )

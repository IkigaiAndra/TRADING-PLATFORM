"""Main FastAPI application entry point"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.logging_config import setup_logging, get_logger

# Setup logging
setup_logging(settings.log_level)
logger = get_logger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Trading Analytics Platform API",
    description="Full-stack market analytics and portfolio platform",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Application startup event handler"""
    logger.info(
        "Starting Trading Analytics Platform API",
        extra={
            "context": {
                "environment": settings.environment,
                "log_level": settings.log_level
            }
        }
    )
    
    # Validate configuration
    try:
        settings.validate_required_settings()
        logger.info("Configuration validated successfully")
    except ValueError as e:
        logger.critical(
            "Configuration validation failed",
            extra={"context": {"error": str(e)}}
        )
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event handler"""
    logger.info("Shutting down Trading Analytics Platform API")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Trading Analytics Platform API",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.environment
    }

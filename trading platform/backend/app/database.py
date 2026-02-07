"""Database connection and session management"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)

# Create SQLAlchemy engine with connection pooling
engine = create_engine(
    settings.database_url,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True,  # Verify connections before using
    echo=False  # Set to True for SQL query logging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(
            "Database session error",
            extra={"context": {"error": str(e)}}
        )
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """Initialize database tables"""
    logger.info("Initializing database tables")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully")

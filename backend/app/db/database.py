"""
Database configuration and session management.
Supports both SQLite (development) and PostgreSQL (production).
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool, QueuePool
import os
from typing import Generator

# Database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./nyx.db"  # Default to SQLite for development
)


def get_database_url() -> str:
    """Get database URL with proper defaults."""
    return DATABASE_URL


def create_db_engine(database_url: str = None):
    """
    Create SQLAlchemy engine with appropriate settings.
    
    Features:
    - Connection pooling for production
    - Echo mode for debugging
    - SQLite compatibility
    """
    db_url = database_url or DATABASE_URL
    
    # Detect database type
    is_sqlite = db_url.startswith("sqlite")
    
    if is_sqlite:
        # SQLite settings
        engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=os.getenv("DB_ECHO", "false").lower() == "true"
        )
    else:
        # PostgreSQL/other databases with connection pooling
        pool_size = int(os.getenv("DB_POOL_SIZE", "10"))
        max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "20"))
        
        engine = create_engine(
            db_url,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,  # Enable connection health checks
            echo=os.getenv("DB_ECHO", "false").lower() == "true"
        )
    
    return engine


# Create engine instance
engine = create_db_engine()


# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI endpoints.
    Provides database session with automatic cleanup.
    
    Usage in endpoints:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database tables.
    Call this on application startup.
    """
    from app.models import Base
    Base.metadata.create_all(bind=engine)


def reset_db():
    """
    Drop all tables and recreate.
    USE WITH CAUTION - only for testing!
    """
    from app.models import Base
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

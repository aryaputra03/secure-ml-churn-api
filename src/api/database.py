# """
# Database Configuration with SQLAlchemy
# """

# from sqlalchemy import create_engine
# from sqlalchemy.orm import declarative_base
# from sqlalchemy.orm import sessionmaker
# import os

# DATABASE_URL = os.getenv(
#     "DATABASE_URL",
#     "sqlite:///./churn_predictions.db"
# )

# engine = create_engine(
#     DATABASE_URL,
#     connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
# )

# Sessionlocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base = declarative_base()

# def get_db():
#     """
#     Dependency to get database session
    
#     Usage in FastAPI:
#         @app.get("/")
#         def read_root(db: Session = Depends(get_db)):
#             ...
#     """
#     db = Sessionlocal()
#     try:
#         yield db
#     finally:
#         db.close()

"""
Database Configuration and Session Management

SQLAlchemy setup for PostgreSQL/SQLite database.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os

from src.utils import logger

# ==========================================
# Database Configuration
# ==========================================

# Get database URL from environment or use SQLite as fallback
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./churn_api.db"
)

# Handle PostgreSQL URL format (for Heroku/Railway)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# ==========================================
# Engine Configuration
# ==========================================

# Create engine with appropriate settings
if DATABASE_URL.startswith("sqlite"):
    # SQLite specific settings
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )
    logger.info("Using SQLite database")
else:
    # PostgreSQL specific settings
    engine = create_engine(
        DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        echo=False
    )
    logger.info("Using PostgreSQL database")

# ==========================================
# Session Configuration
# ==========================================

# Create SessionLocal class
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Create Base class for models
Base = declarative_base()

# ==========================================
# Database Dependency
# ==========================================

def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency for FastAPI
    
    Usage:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            ...
    
    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# Database Initialization
# ==========================================

def init_db():
    """
    Initialize database tables
    
    Creates all tables defined in models
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise

def drop_db():
    """
    Drop all database tables
    
    WARNING: This will delete all data!
    """
    try:
        Base.metadata.drop_all(bind=engine)
        logger.warning("All database tables dropped")
    except Exception as e:
        logger.error(f"Failed to drop database tables: {e}")
        raise

# ==========================================
# Health Check
# ==========================================

def check_db_connection() -> bool:
    """
    Check if database connection is working
    
    Returns:
        True if connection is successful
    """
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False
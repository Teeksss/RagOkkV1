"""
Database connection and session management.
"""
import logging
import os
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from ..config import settings

logger = logging.getLogger(__name__)

# Create engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.SQL_ECHO,
    pool_size=settings.POOL_SIZE,
    max_overflow=settings.MAX_OVERFLOW,
    connect_args={
        # Required for SQLite
        "check_same_thread": False if settings.DATABASE_URL.startswith("sqlite") else {}
    }
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Add event listeners
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set SQLite pragma for foreign key constraints."""
    if settings.DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

def get_db() -> Generator[Session, None, None]:
    """
    Get database session.
    
    Yields:
        Database session
        
    Raises:
        Exception: Any database exception
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db() -> None:
    """
    Initialize database.
    """
    from .models import Base, User
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create admin user if it doesn't exist
    if settings.ADMIN_USERNAME and settings.ADMIN_PASSWORD:
        from ..auth.auth_service import get_password_hash
        
        db = SessionLocal()
        try:
            # Check if admin user exists
            admin = db.query(User).filter(User.username == settings.ADMIN_USERNAME).first()
            
            if not admin:
                import uuid
                
                # Create admin user
                admin = User(
                    id=str(uuid.uuid4()),
                    username=settings.ADMIN_USERNAME,
                    email=settings.ADMIN_EMAIL or f"{settings.ADMIN_USERNAME}@example.com",
                    hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
                    is_active=True,
                    is_admin=True,
                    full_name="System Administrator"
                )
                
                db.add(admin)
                db.commit()
                
                logger.info(f"Created admin user: {settings.ADMIN_USERNAME}")
        
        except Exception as e:
            logger.error(f"Error creating admin user: {str(e)}")
        
        finally:
            db.close()
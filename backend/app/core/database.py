from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import logging
from .config import settings

logger = logging.getLogger(__name__)

SQLALCHEMY_DATABASE_URL = settings.database_url

# Database engine configuration based on database type
if SQLALCHEMY_DATABASE_URL.startswith("postgresql"):
    # PostgreSQL configuration with connection pooling
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_pre_ping=True,
        pool_recycle=3600,  # Recycle connections after 1 hour
        echo=settings.debug and settings.is_development,  # SQL query logging in development
    )
    logger.info(f"✅ PostgreSQL engine created with pool_size={settings.database_pool_size}")
    
elif SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    # SQLite configuration (for development/testing only)
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        poolclass=StaticPool,
        connect_args={
            "check_same_thread": False,
            "timeout": 20
        },
        echo=settings.debug and settings.is_development,
    )
    logger.warning("⚠️  Using SQLite - not recommended for production")
    
else:
    raise ValueError(f"Unsupported database URL: {SQLALCHEMY_DATABASE_URL}")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Database event listeners for connection management
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set SQLite pragmas for better performance and reliability"""
    if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=10000")
        cursor.close()


@event.listens_for(engine, "connect")
def set_postgresql_settings(dbapi_connection, connection_record):
    """Set PostgreSQL connection settings"""
    if SQLALCHEMY_DATABASE_URL.startswith("postgresql"):
        with dbapi_connection.cursor() as cursor:
            cursor.execute("SET timezone = 'UTC'")


def get_db():
    """Database dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def create_database():
    """Create database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
    except Exception as e:
        logger.error(f"❌ Failed to create database tables: {e}")
        raise


def check_database_connection():
    """Check if database connection is working"""
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        logger.info("✅ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False


def get_database_info():
    """Get database connection information"""
    try:
        with engine.connect() as connection:
            if SQLALCHEMY_DATABASE_URL.startswith("postgresql"):
                result = connection.execute("SELECT version()")
                version = result.scalar()
                return {"type": "PostgreSQL", "version": version}
            elif SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
                result = connection.execute("SELECT sqlite_version()")
                version = result.scalar()
                return {"type": "SQLite", "version": version}
    except Exception as e:
        logger.error(f"Failed to get database info: {e}")
        return {"type": "Unknown", "version": "Unknown"}
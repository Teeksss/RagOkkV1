"""
Configuration for RAG system.
"""
import os
import logging
from typing import Dict, Any, Optional, List, Union
from pydantic import BaseSettings, Field, validator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Application settings.
    """
    # Environment
    ENVIRONMENT: str = Field("development", env="ENVIRONMENT")
    DEBUG: bool = Field(False, env="DEBUG")
    
    # Server settings
    HOST: str = Field("0.0.0.0", env="HOST")
    PORT: int = Field(8000, env="PORT")
    
    # Database settings
    DATABASE_URL: str = Field(
        "postgresql://postgres:postgres@localhost:5432/rag_system",
        env="DATABASE_URL"
    )
    SQL_ECHO: bool = Field(False, env="SQL_ECHO")
    POOL_SIZE: int = Field(5, env="POOL_SIZE")
    MAX_OVERFLOW: int = Field(10, env="MAX_OVERFLOW")
    
    # Authentication settings
    SECRET_KEY: str = Field(
        "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7",
        env="SECRET_KEY"
    )
    ALGORITHM: str = Field("HS256", env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # Admin user settings
    ADMIN_USERNAME: Optional[str] = Field(None, env="ADMIN_USERNAME")
    ADMIN_PASSWORD: Optional[str] = Field(None, env="ADMIN_PASSWORD")
    ADMIN_EMAIL: Optional[str] = Field(None, env="ADMIN_EMAIL")
    
    # File upload settings
    UPLOAD_DIR: str = Field("./uploads", env="UPLOAD_DIR")
    MAX_UPLOAD_SIZE: int = Field(10 * 1024 * 1024, env="MAX_UPLOAD_SIZE")  # 10 MB
    ALLOWED_EXTENSIONS: List[str] = Field(
        ["pdf", "docx", "txt", "md", "json", "csv", "xlsx", "pptx", "html", "png", "jpg", "jpeg"],
        env="ALLOWED_EXTENSIONS"
    )
    
    # Vector store settings
    VECTOR_INDEX_PATH: str = Field("./data/vector_index", env="VECTOR_INDEX_PATH")
    VECTOR_DIMENSION: int = Field(384, env="VECTOR_DIMENSION")
    
    # LLM settings
    LLM_PROVIDER: str = Field("openai", env="LLM_PROVIDER")
    LLM_MODEL: str = Field("gpt-3.5-turbo", env="LLM_MODEL")
    OPENAI_API_KEY: str = Field("", env="OPENAI_API_KEY")
    AZURE_OPENAI_KEY: str = Field("", env="AZURE_OPENAI_KEY")
    AZURE_OPENAI_ENDPOINT: str = Field("", env="AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_VERSION: str = Field("2023-05-15", env="AZURE_OPENAI_API_VERSION")
    HUGGINGFACE_TOKEN: str = Field("", env="HUGGINGFACE_TOKEN")
    
    # Caching settings
    CACHE_TYPE: str = Field("memory", env="CACHE_TYPE")  # memory, redis
    CACHE_TTL: int = Field(3600, env="CACHE_TTL")  # 1 hour
    REDIS_HOST: str = Field("localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(6379, env="REDIS_PORT")
    REDIS_PASSWORD: str = Field("", env="REDIS_PASSWORD")
    REDIS_DB: int = Field(0, env="REDIS_DB")
    
    # CORS settings
    CORS_ORIGINS: List[str] = Field(
        ["http://localhost:3000", "http://localhost:8000"],
        env="CORS_ORIGINS"
    )
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = Field(True, env="RATE_LIMIT_ENABLED")
    RATE_LIMIT_REQUESTS: int = Field(100, env="RATE_LIMIT_REQUESTS")  # requests per minute
    
    # Logging
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    LOG_TO_FILE: bool = Field(False, env="LOG_TO_FILE")
    LOG_FILE: str = Field("./logs/app.log", env="LOG_FILE")
    
    class Config:
        """
        Config class for Settings.
        """
        env_file = ".env"
        case_sensitive = True
    
    @validator("UPLOAD_DIR", "VECTOR_INDEX_PATH")
    def create_directories(cls, v: str) -> str:
        """
        Create directories if they don't exist.
        
        Args:
            v: Directory path
            
        Returns:
            Directory path
        """
        if not os.path.exists(v):
            os.makedirs(v, exist_ok=True)
            logger.info(f"Created directory: {v}")
        return v
    
    @validator("LOG_FILE")
    def create_log_directory(cls, v: str) -> str:
        """
        Create log directory if it doesn't exist.
        
        Args:
            v: Log file path
            
        Returns:
            Log file path
        """
        log_dir = os.path.dirname(v)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            logger.info(f"Created log directory: {log_dir}")
        return v


# Create settings instance
settings = Settings()

# Configure logging
if settings.LOG_LEVEL:
    logging.root.setLevel(settings.LOG_LEVEL)

if settings.LOG_TO_FILE:
    file_handler = logging.FileHandler(settings.LOG_FILE)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logging.root.addHandler(file_handler)

# Log settings (excluding sensitive info)
logger.info(f"Environment: {settings.ENVIRONMENT}")
logger.info(f"Debug: {settings.DEBUG}")
logger.info(f"Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'local'}")
logger.info(f"Vector dimension: {settings.VECTOR_DIMENSION}")
logger.info(f"LLM provider: {settings.LLM_PROVIDER}")
logger.info(f"LLM model: {settings.LLM_MODEL}")
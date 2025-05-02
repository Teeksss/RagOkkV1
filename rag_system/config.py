"""
Configuration management for RAG system.
"""
import os
import logging
import json
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from pydantic import BaseSettings, Field, validator

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables with fallbacks.
    """
    # Application info
    APP_NAME: str = "RAG System"
    APP_VERSION: str = "1.0.0"
    API_VERSION: str = "v1"
    DEBUG: bool = Field(False, env="DEBUG")
    ENVIRONMENT: str = Field("production", env="ENVIRONMENT")
    
    # Server settings
    HOST: str = Field("0.0.0.0", env="HOST")
    PORT: int = Field(8000, env="PORT")
    
    # Database settings
    DATABASE_URL: str = Field(
        "sqlite:///./rag_system.db", 
        env="DATABASE_URL"
    )
    SQL_ECHO: bool = Field(False, env="SQL_ECHO")
    POOL_SIZE: int = Field(5, env="POOL_SIZE")
    MAX_OVERFLOW: int = Field(10, env="MAX_OVERFLOW")
    
    # Authentication
    SECRET_KEY: str = Field("your-secret-key-here", env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(60 * 24, env="ACCESS_TOKEN_EXPIRE_MINUTES")  # 24 hours
    ALGORITHM: str = Field("HS256", env="ALGORITHM")
    
    # File storage
    UPLOAD_DIR: str = Field("uploads", env="UPLOAD_DIR")
    MAX_UPLOAD_SIZE: int = Field(50 * 1024 * 1024, env="MAX_UPLOAD_SIZE")  # 50MB
    ALLOWED_EXTENSIONS: List[str] = Field(
        ["pdf", "txt", "doc", "docx", "ppt", "pptx", "xls", "xlsx", "md", "json", "html"],
        env="ALLOWED_EXTENSIONS"
    )
    
    # Vector storage
    VECTOR_INDEX_PATH: str = Field("./data/vector_index", env="VECTOR_INDEX_PATH")
    VECTOR_DIMENSION: int = Field(384, env="VECTOR_DIMENSION")
    FAISS_INDEX_TYPE: str = Field("IVF100,PQ8", env="FAISS_INDEX_TYPE")
    FAISS_METRIC: str = Field("cosine", env="FAISS_METRIC")
    
    # Embedding model
    EMBEDDINGS_MODEL: str = Field("all-MiniLM-L6-v2", env="EMBEDDINGS_MODEL")
    MULTILINGUAL_MODEL: str = Field("paraphrase-multilingual-MiniLM-L12-v2", env="MULTILINGUAL_MODEL")
    USE_GPU: bool = Field(True, env="USE_GPU")
    BATCH_SIZE: int = Field(32, env="BATCH_SIZE")
    MODEL_CACHE_DIR: str = Field("./models", env="MODEL_CACHE_DIR")
    
    # LLM settings
    LLM_PROVIDER: str = Field("openai", env="LLM_PROVIDER")
    LLM_MODEL: str = Field("gpt-3.5-turbo", env="LLM_MODEL")
    LLM_TEMPERATURE: float = Field(0.7, env="LLM_TEMPERATURE")
    LLM_MAX_TOKENS: int = Field(1024, env="LLM_MAX_TOKENS")
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = Field(None, env="OPENAI_API_KEY")
    
    # Azure OpenAI
    AZURE_OPENAI_KEY: Optional[str] = Field(None, env="AZURE_OPENAI_KEY")
    AZURE_OPENAI_ENDPOINT: Optional[str] = Field(None, env="AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_API_VERSION: Optional[str] = Field("2023-05-15", env="AZURE_OPENAI_API_VERSION")
    
    # Hugging Face
    HUGGINGFACE_TOKEN: Optional[str] = Field(None, env="HUGGINGFACE_TOKEN")
    
    # Caching
    ENABLE_CACHE: bool = Field(True, env="ENABLE_CACHE")
    CACHE_TYPE: str = Field("memory", env="CACHE_TYPE")  # memory, redis, disk
    CACHE_TTL: int = Field(3600, env="CACHE_TTL")  # 1 hour
    REDIS_URL: Optional[str] = Field(None, env="REDIS_URL")
    
    # Redis
    REDIS_HOST: str = Field("localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(6379, env="REDIS_PORT")
    REDIS_DB: int = Field(0, env="REDIS_DB")
    REDIS_PASSWORD: Optional[str] = Field(None, env="REDIS_PASSWORD")
    
    # Performance
    MAX_WORKERS: int = Field(4, env="MAX_WORKERS")
    
    # CORS
    CORS_ORIGINS: List[str] = Field(["*"], env="CORS_ORIGINS")
    
    # Logging
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
        env="LOG_FORMAT"
    )
    LOG_FILE: Optional[str] = Field(None, env="LOG_FILE")
    
    @validator("DATABASE_URL")
    def validate_database_url(cls, v: str) -> str:
        """Validate DATABASE_URL."""
        # For SQLite, make sure the directory exists
        if v.startswith("sqlite:///"):
            # Get database path (remove sqlite:/// prefix)
            db_path = v[10:]
            if db_path != ":memory:":
                # Create directory if it doesn't exist
                db_dir = os.path.dirname(db_path)
                if db_dir and not os.path.exists(db_dir):
                    os.makedirs(db_dir)
        return v
    
    @validator("UPLOAD_DIR")
    def validate_upload_dir(cls, v: str) -> str:
        """Validate UPLOAD_DIR."""
        # Create directory if it doesn't exist
        if not os.path.exists(v):
            os.makedirs(v)
        return v
    
    @validator("VECTOR_INDEX_PATH")
    def validate_vector_index_path(cls, v: str) -> str:
        """Validate VECTOR_INDEX_PATH."""
        # Create directory if it doesn't exist
        if not os.path.exists(v):
            os.makedirs(v)
        return v
    
    @validator("MODEL_CACHE_DIR")
    def validate_model_cache_dir(cls, v: str) -> str:
        """Validate MODEL_CACHE_DIR."""
        # Create directory if it doesn't exist
        if not os.path.exists(v):
            os.makedirs(v)
        return v
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Initialize settings
settings = Settings()

# Configure logging
logging_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
logging_config = {
    "level": logging_level,
    "format": settings.LOG_FORMAT,
    "handlers": []
}

# Add file handler if LOG_FILE is set
if settings.LOG_FILE:
    log_dir = os.path.dirname(settings.LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    logging_config["handlers"].append(
        logging.FileHandler(settings.LOG_FILE)
    )

# Add console handler
logging_config["handlers"].append(logging.StreamHandler())

# Apply logging configuration
logging.basicConfig(**logging_config)

def get_settings() -> Settings:
    """
    Get application settings.
    
    Returns:
        Application settings
    """
    return settings

def load_config_from_file(file_path: str) -> Dict[str, Any]:
    """
    Load configuration from file.
    
    Args:
        file_path: Path to config file
        
    Returns:
        Config dictionary
    """
    if not os.path.exists(file_path):
        logger.warning(f"Config file not found: {file_path}")
        return {}
    
    try:
        # Load config based on file extension
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == ".json":
            with open(file_path, "r") as f:
                return json.load(f)
        
        elif file_ext in [".yml", ".yaml"]:
            import yaml
            with open(file_path, "r") as f:
                return yaml.safe_load(f)
        
        else:
            logger.warning(f"Unsupported config file format: {file_ext}")
            return {}
    
    except Exception as e:
        logger.error(f"Error loading config file: {str(e)}")
        return {}

def save_config_to_file(config: Dict[str, Any], file_path: str) -> bool:
    """
    Save configuration to file.
    
    Args:
        config: Config dictionary
        file_path: Path to config file
        
    Returns:
        Success status
    """
    try:
        # Create directory if it doesn't exist
        dir_path = os.path.dirname(file_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)
        
        # Save config based on file extension
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == ".json":
            with open(file_path, "w") as f:
                json.dump(config, f, indent=2)
        
        elif file_ext in [".yml", ".yaml"]:
            import yaml
            with open(file_path, "w") as f:
                yaml.dump(config, f)
        
        else:
            logger.warning(f"Unsupported config file format: {file_ext}")
            return False
        
        return True
    
    except Exception as e:
        logger.error(f"Error saving config file: {str(e)}")
        return False
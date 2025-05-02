"""
Database logger utility.
"""
import logging
import traceback
import json
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from sqlalchemy.orm import Session

from ..database.models import Log
from ..config import settings

logger = logging.getLogger(__name__)

class DBLogger:
    """
    Database logger for storing logs in the database.
    """
    
    def __init__(self, db: Session):
        """
        Initialize database logger.
        
        Args:
            db: Database session
        """
        self.db = db
    
    def log(
        self,
        level: str,
        operation: str,
        message: str,
        user_id: Optional[str] = None,
        request_path: Optional[str] = None,
        request_method: Optional[str] = None,
        status_code: Optional[int] = None,
        ip_address: Optional[str] = None,
        response_time: Optional[float] = None,
        error_message: Optional[str] = None,
        exception: Optional[Exception] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log message to database.
        
        Args:
            level: Log level (INFO, WARNING, ERROR)
            operation: Operation name
            message: Log message
            user_id: User ID
            request_path: Request path
            request_method: Request method
            status_code: Response status code
            ip_address: Client IP address
            response_time: Response time in seconds
            error_message: Error message
            exception: Exception object
            data: Additional data
        """
        # Validate level
        valid_levels = ["INFO", "WARNING", "ERROR", "DEBUG"]
        if level not in valid_levels:
            level = "INFO"
        
        # Create log data
        log_data = data or {}
        
        # Add exception details if provided
        if exception:
            log_data["exception"] = {
                "type": type(exception).__name__,
                "message": str(exception),
                "traceback": traceback.format_exception(
                    type(exception), exception, exception.__traceback__
                )
            }
        
        # Create log entry
        log_entry = Log(
            id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            level=level,
            operation=operation,
            message=message,
            user_id=user_id,
            request_path=request_path,
            request_method=request_method,
            status_code=status_code,
            response_time=response_time,
            ip_address=ip_address,
            data=log_data
        )
        
        try:
            # Add log entry to database
            self.db.add(log_entry)
            self.db.commit()
        
        except Exception as e:
            # Rollback session
            self.db.rollback()
            
            # Log error to console
            logger.error(f"Failed to write log to database: {str(e)}")
            logger.debug(f"Log entry: {message}, Operation: {operation}")
    
    def log_info(
        self,
        operation: str,
        message: str,
        user_id: Optional[str] = None,
        request_path: Optional[str] = None,
        request_method: Optional[str] = None,
        status_code: Optional[int] = None,
        ip_address: Optional[str] = None,
        response_time: Optional[float] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log info message to database.
        
        Args:
            operation: Operation name
            message: Log message
            user_id: User ID
            request_path: Request path
            request_method: Request method
            status_code: Response status code
            ip_address: Client IP address
            response_time: Response time in seconds
            data: Additional data
        """
        self.log(
            level="INFO",
            operation=operation,
            message=message,
            user_id=user_id,
            request_path=request_path,
            request_method=request_method,
            status_code=status_code,
            ip_address=ip_address,
            response_time=response_time,
            data=data
        )
    
    def log_warning(
        self,
        operation: str,
        message: str,
        user_id: Optional[str] = None,
        request_path: Optional[str] = None,
        request_method: Optional[str] = None,
        status_code: Optional[int] = None,
        ip_address: Optional[str] = None,
        response_time: Optional[float] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log warning message to database.
        
        Args:
            operation: Operation name
            message: Log message
            user_id: User ID
            request_path: Request path
            request_method: Request method
            status_code: Response status code
            ip_address: Client IP address
            response_time: Response time in seconds
            data: Additional data
        """
        self.log(
            level="WARNING",
            operation=operation,
            message=message,
            user_id=user_id,
            request_path=request_path,
            request_method=request_method,
            status_code=status_code,
            ip_address=ip_address,
            response_time=response_time,
            data=data
        )
    
    def log_error(
        self,
        operation: str,
        error_message: str,
        user_id: Optional[str] = None,
        request_path: Optional[str] = None,
        request_method: Optional[str] = None,
        status_code: Optional[int] = None,
        ip_address: Optional[str] = None,
        response_time: Optional[float] = None,
        exception: Optional[Exception] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log error message to database.
        
        Args:
            operation: Operation name
            error_message: Error message
            user_id: User ID
            request_path: Request path
            request_method: Request method
            status_code: Response status code
            ip_address: Client IP address
            response_time: Response time in seconds
            exception: Exception object
            data: Additional data
        """
        self.log(
            level="ERROR",
            operation=operation,
            message=error_message,
            user_id=user_id,
            request_path=request_path,
            request_method=request_method,
            status_code=status_code,
            ip_address=ip_address,
            response_time=response_time,
            error_message=error_message,
            exception=exception,
            data=data
        )
    
    def log_debug(
        self,
        operation: str,
        message: str,
        user_id: Optional[str] = None,
        request_path: Optional[str] = None,
        request_method: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log debug message to database.
        
        Args:
            operation: Operation name
            message: Log message
            user_id: User ID
            request_path: Request path
            request_method: Request method
            data: Additional data
        """
        # Only log debug messages in debug mode
        if settings.DEBUG:
            self.log(
                level="DEBUG",
                operation=operation,
                message=message,
                user_id=user_id,
                request_path=request_path,
                request_method=request_method,
                data=data
            )
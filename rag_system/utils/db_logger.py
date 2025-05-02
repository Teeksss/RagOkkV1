"""
Database logger for tracking system operations.
"""
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
import uuid
from sqlalchemy.orm import Session

from ..database.models import Log

logger = logging.getLogger(__name__)

class DBLogger:
    """
    Logger that stores operations in the database.
    """
    
    def __init__(self, db_session: Session):
        """
        Initialize database logger.
        
        Args:
            db_session: Database session
        """
        self.db = db_session
    
    def log_operation(self,
                     level: str,
                     message: str,
                     operation: str,
                     user_id: Optional[str] = None,
                     request_path: Optional[str] = None,
                     request_method: Optional[str] = None,
                     status_code: Optional[int] = None,
                     response_time: Optional[float] = None,
                     ip_address: Optional[str] = None,
                     data: Optional[Dict[str, Any]] = None) -> None:
        """
        Log an operation to the database.
        
        Args:
            level: Log level (INFO, WARNING, ERROR)
            message: Log message
            operation: Operation type
            user_id: User ID
            request_path: Request path
            request_method: Request method
            status_code: Response status code
            response_time: Response time in seconds
            ip_address: Client IP address
            data: Additional data
        """
        try:
            log_entry = Log(
                id=str(uuid.uuid4()),
                timestamp=datetime.utcnow(),
                level=level.upper(),
                message=message,
                operation=operation,
                user_id=user_id,
                request_path=request_path,
                request_method=request_method,
                status_code=status_code,
                response_time=response_time,
                ip_address=ip_address,
                data=data
            )
            
            self.db.add(log_entry)
            self.db.commit()
        except Exception as e:
            logger.error(f"Error logging to database: {str(e)}")
            self.db.rollback()
    
    def log_info(self,
                operation: str,
                message: str,
                user_id: Optional[str] = None,
                request_path: Optional[str] = None,
                request_method: Optional[str] = None,
                status_code: Optional[int] = None,
                response_time: Optional[float] = None,
                data: Optional[Dict[str, Any]] = None) -> None:
        """
        Log an info event.
        
        Args:
            operation: Operation type
            message: Log message
            user_id: User ID
            request_path: Request path
            request_method: Request method
            status_code: Response status code
            response_time: Response time in seconds
            data: Additional data
        """
        self.log_operation(
            level="INFO",
            message=message,
            operation=operation,
            user_id=user_id,
            request_path=request_path,
            request_method=request_method,
            status_code=status_code,
            response_time=response_time,
            data=data
        )
    
    def log_warning(self,
                   operation: str,
                   message: str,
                   user_id: Optional[str] = None,
                   request_path: Optional[str] = None,
                   request_method: Optional[str] = None,
                   status_code: Optional[int] = None,
                   response_time: Optional[float] = None,
                   data: Optional[Dict[str, Any]] = None) -> None:
        """
        Log a warning event.
        
        Args:
            operation: Operation type
            message: Log message
            user_id: User ID
            request_path: Request path
            request_method: Request method
            status_code: Response status code
            response_time: Response time in seconds
            data: Additional data
        """
        self.log_operation(
            level="WARNING",
            message=message,
            operation=operation,
            user_id=user_id,
            request_path=request_path,
            request_method=request_method,
            status_code=status_code,
            response_time=response_time,
            data=data
        )
    
    def log_error(self,
                 operation: str,
                 error_message: str,
                 user_id: Optional[str] = None,
                 request_path: Optional[str] = None,
                 request_method: Optional[str] = None,
                 status_code: Optional[int] = None,
                 latency: Optional[float] = None,
                 data: Optional[Dict[str, Any]] = None) -> None:
        """
        Log an error event.
        
        Args:
            operation: Operation type
            error_message: Error message
            user_id: User ID
            request_path: Request path
            request_method: Request method
            status_code: Response status code
            latency: Response time in seconds
            data: Additional data
        """
        self.log_operation(
            level="ERROR",
            message=error_message,
            operation=operation,
            user_id=user_id,
            request_path=request_path,
            request_method=request_method,
            status_code=status_code,
            response_time=latency,
            data=data
        )
    
    def log_search(self,
                  query: str,
                  user_id: Optional[str] = None,
                  result_count: int = 0,
                  filters: Optional[Dict[str, Any]] = None,
                  latency: Optional[float] = None) -> None:
        """
        Log a search operation.
        
        Args:
            query: Search query
            user_id: User ID
            result_count: Number of results
            filters: Search filters
            latency: Search latency in seconds
        """
        data = {
            "query": query,
            "result_count": result_count
        }
        
        if filters:
            data["filters"] = filters
        
        self.log_operation(
            level="INFO",
            message=f"Search: '{query}' ({result_count} results)",
            operation="search",
            user_id=user_id,
            response_time=latency,
            status_code=200,
            data=data
        )
    
    def log_upload(self,
                  filename: str,
                  content_type: str,
                  file_size: int,
                  user_id: Optional[str] = None,
                  document_id: Optional[str] = None,
                  latency: Optional[float] = None) -> None:
        """
        Log a document upload.
        
        Args:
            filename: Uploaded filename
            content_type: Content type
            file_size: File size in bytes
            user_id: User ID
            document_id: Document ID
            latency: Upload latency in seconds
        """
        data = {
            "filename": filename,
            "content_type": content_type,
            "file_size": file_size,
            "document_id": document_id
        }
        
        self.log_operation(
            level="INFO",
            message=f"Upload: '{filename}' ({file_size} bytes)",
            operation="upload",
            user_id=user_id,
            response_time=latency,
            status_code=200,
            data=data
        )
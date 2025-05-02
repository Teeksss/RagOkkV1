"""
File upload handler for the RAG system.
Handles different file types and initiates appropriate processing pipelines.
"""
import os
import logging
from datetime import datetime
from typing import List, Dict, Any, BinaryIO, Optional

from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from .metadata_extractor import extract_metadata
from .ocr_processor import process_image_with_ocr
from ..database.models import Document
from ..utils.logging import log_operation

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {
    'pdf': 'application/pdf',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'doc': 'application/msword',
    'txt': 'text/plain',
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg'
}

class FileUploadManager:
    def __init__(self, upload_dir: str, db_session: Session):
        """
        Initialize the file upload manager.
        
        Args:
            upload_dir: Directory to store uploaded files
            db_session: Database session
        """
        self.upload_dir = upload_dir
        self.db_session = db_session
        os.makedirs(upload_dir, exist_ok=True)
        
    async def process_upload(self, file: UploadFile, user_id: str) -> Dict[str, Any]:
        """
        Process an uploaded file and store it in the system.
        
        Args:
            file: The uploaded file
            user_id: ID of the user uploading the file
            
        Returns:
            Dict containing document information and status
        """
        # Log the upload operation
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        log_operation(f"File upload started - {timestamp}", user_id)
        
        # Validate file type
        file_ext = self._get_file_extension(file.filename)
        if file_ext not in SUPPORTED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_ext}")
        
        # Save file to disk
        file_path = os.path.join(self.upload_dir, f"{user_id}_{datetime.now().timestamp()}_{file.filename}")
        try:
            contents = await file.read()
            with open(file_path, "wb") as f:
                f.write(contents)
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to save file")
        
        # Extract metadata based on file type
        metadata = extract_metadata(file_path, file_ext)
        
        # Process OCR if needed (for images or scanned PDFs)
        requires_ocr = file_ext in ['png', 'jpg', 'jpeg'] or metadata.get('requires_ocr', False)
        text_content = None
        
        if requires_ocr:
            text_content = process_image_with_ocr(file_path)
        
        # Create document record in database
        document = Document(
            filename=file.filename,
            file_path=file_path,
            content_type=file.content_type,
            user_id=user_id,
            upload_date=datetime.utcnow(),
            metadata=metadata,
            requires_ocr=requires_ocr,
            processing_status="processing" if requires_ocr else "ready"
        )
        
        self.db_session.add(document)
        self.db_session.commit()
        
        # Return document info
        return {
            "document_id": document.id,
            "filename": document.filename,
            "upload_date": document.upload_date.isoformat(),
            "status": document.processing_status,
            "metadata": metadata
        }
    
    def _get_file_extension(self, filename: Optional[str]) -> str:
        """Extract the extension from a filename."""
        if not filename:
            return ""
        return filename.split(".")[-1].lower()
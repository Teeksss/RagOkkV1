"""
Document versioning and change tracking.
"""
import logging
import time
import difflib
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Union
import hashlib
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_

from ..database.models import Document, DocumentVersion, DocumentChunk

logger = logging.getLogger(__name__)

class DocumentVersionManager:
    """
    Manages document versions and change tracking.
    """
    
    def __init__(self, db_session: Session):
        """
        Initialize document version manager.
        
        Args:
            db_session: Database session
        """
        self.db = db_session
    
    def create_version(self, 
                       document_id: str, 
                       content: str, 
                       metadata: Optional[Dict[str, Any]] = None, 
                       created_by: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new version of a document.
        
        Args:
            document_id: Document ID
            content: Document content
            metadata: Document metadata
            created_by: User who created the version
            
        Returns:
            Version information
        """
        # Get document
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"Document not found: {document_id}")
            return {"status": "error", "error": "Document not found"}
        
        # Generate content hash for version comparison
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        
        # Get latest version
        latest_version = self.db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id
        ).order_by(desc(DocumentVersion.version_number)).first()
        
        # Determine version number
        version_number = 1 if not latest_version else latest_version.version_number + 1
        
        # Check if content is unchanged since last version
        if latest_version and latest_version.content_hash == content_hash:
            logger.info(f"Content unchanged since version {latest_version.version_number}")
            return {
                "status": "unchanged",
                "version": latest_version.version_number,
                "document_id": document_id
            }
        
        # Create new version
        version = DocumentVersion(
            document_id=document_id,
            version_number=version_number,
            content=content,
            content_hash=content_hash,
            metadata=metadata or {},
            created_at=datetime.utcnow(),
            created_by=created_by
        )
        
        # If it's the first version, create a diff against empty string
        if not latest_version:
            version.diff = json.dumps(self._create_diff("", content))
        else:
            # Create diff against latest version
            version.diff = json.dumps(self._create_diff(latest_version.content, content))
        
        # Save version
        self.db.add(version)
        self.db.commit()
        
        # Update document's current_version
        document.current_version = version_number
        document.last_updated_at = datetime.utcnow()
        self.db.commit()
        
        logger.info(f"Created version {version_number} for document {document_id}")
        
        return {
            "status": "success",
            "version": version_number,
            "document_id": document_id,
            "content_hash": content_hash
        }
    
    def get_version(self, 
                   document_id: str, 
                   version_number: Optional[int] = None) -> Dict[str, Any]:
        """
        Get a specific version of a document.
        
        Args:
            document_id: Document ID
            version_number: Version number (if None, get latest)
            
        Returns:
            Version information
        """
        # Get document
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"Document not found: {document_id}")
            return {"status": "error", "error": "Document not found"}
        
        # Get version
        if version_number is None:
            # Get latest version
            version = self.db.query(DocumentVersion).filter(
                DocumentVersion.document_id == document_id
            ).order_by(desc(DocumentVersion.version_number)).first()
        else:
            # Get specific version
            version = self.db.query(DocumentVersion).filter(
                DocumentVersion.document_id == document_id,
                DocumentVersion.version_number == version_number
            ).first()
        
        if not version:
            logger.error(f"Version not found: document {document_id}, version {version_number}")
            return {"status": "error", "error": "Version not found"}
        
        # Return version information
        return {
            "status": "success",
            "document_id": document_id,
            "version": version.version_number,
            "content": version.content,
            "metadata": version.metadata,
            "created_at": version.created_at.isoformat(),
            "created_by": version.created_by,
            "content_hash": version.content_hash
        }
    
    def list_versions(self, document_id: str) -> Dict[str, Any]:
        """
        List all versions of a document.
        
        Args:
            document_id: Document ID
            
        Returns:
            List of versions
        """
        # Get document
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"Document not found: {document_id}")
            return {"status": "error", "error": "Document not found"}
        
        # Get versions
        versions = self.db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id
        ).order_by(desc(DocumentVersion.version_number)).all()
        
        # Format versions
        version_list = []
        for version in versions:
            version_list.append({
                "version": version.version_number,
                "created_at": version.created_at.isoformat(),
                "created_by": version.created_by,
                "content_hash": version.content_hash,
                "metadata": version.metadata
            })
        
        return {
            "status": "success",
            "document_id": document_id,
            "filename": document.filename,
            "current_version": document.current_version,
            "versions": version_list
        }
    
    def compare_versions(self, 
                        document_id: str, 
                        version1: int, 
                        version2: int) -> Dict[str, Any]:
        """
        Compare two versions of a document.
        
        Args:
            document_id: Document ID
            version1: First version number
            version2: Second version number
            
        Returns:
            Comparison information
        """
        # Get document
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"Document not found: {document_id}")
            return {"status": "error", "error": "Document not found"}
        
        # Get versions
        v1 = self.db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id,
            DocumentVersion.version_number == version1
        ).first()
        
        v2 = self.db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id,
            DocumentVersion.version_number == version2
        ).first()
        
        if not v1 or not v2:
            logger.error(f"Versions not found: document {document_id}, versions {version1} and {version2}")
            return {"status": "error", "error": "Versions not found"}
        
        # Create diff
        diff = self._create_diff(v1.content, v2.content)
        
        # Return comparison information
        return {
            "status": "success",
            "document_id": document_id,
            "filename": document.filename,
            "version1": version1,
            "version2": version2,
            "diff": diff,
            "v1_created_at": v1.created_at.isoformat(),
            "v2_created_at": v2.created_at.isoformat(),
            "v1_created_by": v1.created_by,
            "v2_created_by": v2.created_by
        }
    
    def revert_to_version(self, 
                         document_id: str, 
                         version_number: int,
                         user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Revert a document to a previous version.
        
        Args:
            document_id: Document ID
            version_number: Version number to revert to
            user_id: User performing the revert
            
        Returns:
            Revert result
        """
        # Get document
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"Document not found: {document_id}")
            return {"status": "error", "error": "Document not found"}
        
        # Get version to revert to
        version = self.db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id,
            DocumentVersion.version_number == version_number
        ).first()
        
        if not version:
            logger.error(f"Version not found: document {document_id}, version {version_number}")
            return {"status": "error", "error": "Version not found"}
        
        # Create new version with content from old version
        metadata = version.metadata.copy() if version.metadata else {}
        metadata["reverted_from"] = version_number
        
        revert_result = self.create_version(
            document_id=document_id,
            content=version.content,
            metadata=metadata,
            created_by=user_id
        )
        
        if revert_result["status"] == "success":
            logger.info(f"Reverted document {document_id} to version {version_number}")
            return {
                "status": "success",
                "document_id": document_id,
                "reverted_to": version_number,
                "new_version": revert_result["version"]
            }
        else:
            return revert_result
    
    def _create_diff(self, old_content: str, new_content: str) -> List[Dict[str, Any]]:
        """
        Create a structured diff between two content versions.
        
        Args:
            old_content: Old content
            new_content: New content
            
        Returns:
            Structured diff
        """
        # Split content into lines
        old_lines = old_content.splitlines()
        new_lines = new_content.splitlines()
        
        # Create diff using difflib
        diff = difflib.unified_diff(old_lines, new_lines, lineterm='')
        
        # Convert diff to structured format
        result = []
        
        for line in list(diff)[2:]:  # Skip the header lines
            if line.startswith('+'):
                result.append({"type": "added", "content": line[1:]})
            elif line.startswith('-'):
                result.append({"type": "removed", "content": line[1:]})
            elif line.startswith(' '):
                result.append({"type": "unchanged", "content": line[1:]})
            else:
                # Skip other lines (headers, etc.)
                pass
        
        return result
    
    def get_document_history(self, document_id: str) -> Dict[str, Any]:
        """
        Get complete history of a document including versions and changes.
        
        Args:
            document_id: Document ID
            
        Returns:
            Document history
        """
        # Get document
        document = self.db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"Document not found: {document_id}")
            return {"status": "error", "error": "Document not found"}
        
        # Get versions
        versions = self.db.query(DocumentVersion).filter(
            DocumentVersion.document_id == document_id
        ).order_by(DocumentVersion.version_number).all()
        
        # Format history
        history = []
        for version in versions:
            # Format diff for readability
            try:
                diff = json.loads(version.diff) if version.diff else []
                diff_summary = {
                    "added": sum(1 for d in diff if d["type"] == "added"),
                    "removed": sum(1 for d in diff if d["type"] == "removed"),
                    "unchanged": sum(1 for d in diff if d["type"] == "unchanged")
                }
            except Exception as e:
                logger.error(f"Error parsing diff: {str(e)}")
                diff_summary = {"error": "Invalid diff format"}
            
            history.append({
                "version": version.version_number,
                "created_at": version.created_at.isoformat(),
                "created_by": version.created_by,
                "metadata": version.metadata,
                "diff_summary": diff_summary
            })
        
        return {
            "status": "success",
            "document_id": document_id,
            "filename": document.filename,
            "content_type": document.content_type,
            "current_version": document.current_version,
            "created_at": document.created_at.isoformat(),
            "updated_at": document.last_updated_at.isoformat() if document.last_updated_at else None,
            "versions": history
        }
"""
Document processing and management extensions for document routes.
"""
import os
import uuid
import time
import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta

from fastapi import HTTPException, Response, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_

from ...config import settings
from ...database.models import Document, DocumentChunk, Tag, DocumentTag
from ...utils.db_logger import DBLogger
from ...data_processing.embeddings import SentenceEmbedder
from ...data_processing.text_chunker import TextChunker

logger = logging.getLogger(__name__)

async def process_document_background(
    document_id: str,
    db: Session,
    update_only: bool = False
) -> None:
    """
    Process document in background task.
    
    Args:
        document_id: Document ID
        db: Database session
        update_only: Whether to only update existing chunks
    """
    try:
        # Get document
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.deleted == False
        ).first()
        
        if not document:
            logger.error(f"Document {document_id} not found for processing")
            return
        
        # Update processing status
        document.processing_status = "processing"
        db.commit()
        
        # Get document file path
        file_path = document.file_path
        
        if not os.path.exists(file_path):
            logger.error(f"Document file not found: {file_path}")
            document.processing_status = "error"
            document.metadata = document.metadata or {}
            document.metadata["error"] = "Document file not found"
            db.commit()
            return
        
        # Extract text based on file type
        text_content = extract_text_from_file(file_path, document.content_type)
        
        if not text_content:
            logger.warning(f"No text content extracted from {document_id}")
            document.processing_status = "ready"
            document.metadata = document.metadata or {}
            document.metadata["warning"] = "No text content extracted"
            db.commit()
            return
        
        # Chunk text
        chunker = TextChunker()
        chunks = chunker.chunk_text(text_content, max_chunk_size=1024, overlap=200)
        
        # Initialize embedder
        embedder = SentenceEmbedder()
        
        # Process chunks
        if update_only:
            # Delete existing chunks
            db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()
        
        # Add chunks
        for i, chunk_text in enumerate(chunks):
            # Create chunk
            chunk = DocumentChunk(
                id=str(uuid.uuid4()),
                document_id=document_id,
                chunk_index=i,
                content=chunk_text,
                metadata={
                    "start_index": i * (1024 - 200) if i > 0 else 0,
                    "length": len(chunk_text)
                },
                created_at=datetime.utcnow()
            )
            
            # Generate embedding
            try:
                embedding = embedder.embed_text(chunk_text)
                chunk.embedding_vector = embedding.astype('float32').tobytes()
                chunk.embedding_stored = True
            except Exception as e:
                logger.error(f"Error generating embedding for chunk: {str(e)}")
                chunk.embedding_stored = False
            
            db.add(chunk)
        
        # Update document
        document.processing_status = "ready"
        document.last_updated_at = datetime.utcnow()
        
        # Update document metadata
        document.metadata = document.metadata or {}
        document.metadata["chunk_count"] = len(chunks)
        document.metadata["processed_at"] = datetime.utcnow().isoformat()
        
        # Commit changes
        db.commit()
        
        logger.info(f"Document {document_id} processed successfully with {len(chunks)} chunks")
    
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {str(e)}")
        
        try:
            # Update document status
            document = db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.processing_status = "error"
                document.metadata = document.metadata or {}
                document.metadata["error"] = str(e)
                db.commit()
        except Exception as inner_e:
            logger.error(f"Error updating document status: {str(inner_e)}")

def extract_text_from_file(file_path: str, content_type: str) -> str:
    """
    Extract text from file based on content type.
    
    Args:
        file_path: Path to file
        content_type: File content type
        
    Returns:
        Extracted text
    """
    try:
        # PDF
        if content_type and "pdf" in content_type.lower():
            return extract_text_from_pdf(file_path)
        
        # Word document
        elif content_type and ("word" in content_type.lower() or "docx" in content_type.lower()):
            return extract_text_from_docx(file_path)
        
        # Text file
        elif content_type and ("text" in content_type.lower() or "txt" in content_type.lower()):
            return extract_text_from_text(file_path)
        
        # Markdown
        elif content_type and "markdown" in content_type.lower():
            return extract_text_from_text(file_path)
        
        # JSON
        elif content_type and "json" in content_type.lower():
            return extract_text_from_text(file_path)
        
        # HTML
        elif content_type and "html" in content_type.lower():
            return extract_text_from_html(file_path)
        
        # CSV
        elif content_type and "csv" in content_type.lower():
            return extract_text_from_csv(file_path)
        
        # Default: try as text
        else:
            return extract_text_from_text(file_path)
    
    except Exception as e:
        logger.error(f"Error extracting text from file: {str(e)}")
        return ""

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from PDF file.
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        Extracted text
    """
    try:
        import PyPDF2
        
        with open(file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            
            # Extract text from each page
            for page in reader.pages:
                text += page.extract_text() + "\n\n"
            
            return text
    
    except ImportError:
        logger.error("PyPDF2 not installed. Please install with: pip install PyPDF2")
        return ""
    
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        return ""

def extract_text_from_docx(file_path: str) -> str:
    """
    Extract text from Word document.
    
    Args:
        file_path: Path to Word document
        
    Returns:
        Extracted text
    """
    try:
        import docx
        
        doc = docx.Document(file_path)
        text = ""
        
        # Extract text from paragraphs
        for para in doc.paragraphs:
            text += para.text + "\n"
        
        # Extract text from tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    text += cell.text + " "
                text += "\n"
        
        return text
    
    except ImportError:
        logger.error("python-docx not installed. Please install with: pip install python-docx")
        return ""
    
    except Exception as e:
        logger.error(f"Error extracting text from Word document: {str(e)}")
        return ""

def extract_text_from_text(file_path: str) -> str:
    """
    Extract text from text file.
    
    Args:
        file_path: Path to text file
        
    Returns:
        Extracted text
    """
    try:
        import chardet
        
        # Detect encoding
        with open(file_path, "rb") as file:
            raw_data = file.read()
            result = chardet.detect(raw_data)
            encoding = result["encoding"]
        
        # Read text with detected encoding
        with open(file_path, "r", encoding=encoding) as file:
            return file.read()
    
    except ImportError:
        # Fallback to utf-8
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return file.read()
        except UnicodeDecodeError:
            # Try with latin-1
            with open(file_path, "r", encoding="latin-1") as file:
                return file.read()
    
    except Exception as e:
        logger.error(f"Error extracting text from text file: {str(e)}")
        return ""

def extract_text_from_html(file_path: str) -> str:
    """
    Extract text from HTML file.
    
    Args:
        file_path: Path to HTML file
        
    Returns:
        Extracted text
    """
    try:
        from bs4 import BeautifulSoup
        
        with open(file_path, "r", encoding="utf-8") as file:
            soup = BeautifulSoup(file.read(), "html.parser")
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()
            
            # Get text
            text = soup.get_text()
            
            # Break into lines and remove leading and trailing space on each
            lines = (line.strip() for line in text.splitlines())
            
            # Break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            
            # Drop blank lines
            text = "\n".join(chunk for chunk in chunks if chunk)
            
            return text
    
    except ImportError:
        logger.error("BeautifulSoup not installed. Please install with: pip install beautifulsoup4")
        return ""
    
    except Exception as e:
        logger.error(f"Error extracting text from HTML file: {str(e)}")
        return ""

def extract_text_from_csv(file_path: str) -> str:
    """
    Extract text from CSV file.
    
    Args:
        file_path: Path to CSV file
        
    Returns:
        Extracted text
    """
    try:
        import csv
        import chardet
        
        # Detect encoding
        with open(file_path, "rb") as file:
            raw_data = file.read(10000)  # Read first 10K bytes
            result = chardet.detect(raw_data)
            encoding = result["encoding"]
        
        text = ""
        
        with open(file_path, "r", encoding=encoding) as file:
            csv_reader = csv.reader(file)
            headers = next(csv_reader, [])
            
            # Add headers
            text += ", ".join(headers) + "\n"
            
            # Add rows
            for row in csv_reader:
                text += ", ".join(row) + "\n"
            
            return text
    
    except ImportError:
        logger.error("CSV module error")
        return ""
    
    except Exception as e:
        logger.error(f"Error extracting text from CSV file: {str(e)}")
        return ""

async def add_document_tags(
    document_id: str,
    tags: List[str],
    db: Session
) -> Dict[str, Any]:
    """
    Add tags to document.
    
    Args:
        document_id: Document ID
        tags: List of tag names
        db: Database session
        
    Returns:
        Dictionary with document ID and tags
    """
    # Get document
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.deleted == False
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Update document metadata with tags
    if not document.metadata:
        document.metadata = {}
    
    document.metadata["tags"] = tags
    document.last_updated_at = datetime.utcnow()
    
    # Update tags in the database (DocumentTag relationship)
    # First, get all existing document tags
    existing_doc_tags = db.query(DocumentTag).filter(
        DocumentTag.document_id == document_id
    ).all()
    
    # Delete all existing document tags
    for doc_tag in existing_doc_tags:
        db.delete(doc_tag)
    
    # Create new document tags
    for tag_name in tags:
        # Find or create tag
        tag = db.query(Tag).filter(func.lower(Tag.name) == func.lower(tag_name)).first()
        
        if not tag:
            tag = Tag(id=str(uuid.uuid4()), name=tag_name)
            db.add(tag)
            db.flush()  # Flush to get tag ID
        
        # Create document tag association
        doc_tag = DocumentTag(document_id=document_id, tag_id=tag.id)
        db.add(doc_tag)
    
    db.commit()
    
    return {
        "document_id": document_id,
        "tags": tags
    }

async def search_documents_with_filters(
    query: Optional[str],
    tags: Optional[List[str]],
    types: Optional[List[str]],
    from_date: Optional[str],
    to_date: Optional[str],
    skip: int,
    limit: int,
    user_id: str,
    db: Session
) -> Dict[str, Any]:
    """
    Search documents with filters.
    
    Args:
        query: Search query
        tags: Filter by tags
        types: Filter by file types
        from_date: Filter from date (YYYY-MM-DD)
        to_date: Filter to date (YYYY-MM-DD)
        skip: Number of documents to skip
        limit: Maximum number of documents to return
        user_id: User ID
        db: Database session
        
    Returns:
        Dictionary with search results
    """
    # Start building query
    base_query = db.query(Document).filter(
        Document.user_id == user_id,
        Document.deleted == False
    )
    
    # Apply text search filter if provided
    if query:
        # For simple string matching in metadata and filename
        base_query = base_query.filter(
            or_(
                Document.filename.ilike(f"%{query}%"),
                Document.metadata["title"].astext.ilike(f"%{query}%"),
                Document.metadata["description"].astext.ilike(f"%{query}%")
            )
        )
    
    # Apply tag filters if provided
    if tags and len(tags) > 0:
        # Query documents that have ALL the specified tags
        for tag_name in tags:
            tag_subquery = db.query(DocumentTag.document_id).join(
                Tag, Tag.id == DocumentTag.tag_id
            ).filter(
                func.lower(Tag.name) == func.lower(tag_name)
            ).subquery()
            
            base_query = base_query.filter(Document.id.in_(tag_subquery))
    
    # Apply file type filters
    if types and len(types) > 0:
        # Create a list of content_type conditions
        type_conditions = []
        for file_type in types:
            if file_type == 'pdf':
                type_conditions.append(Document.content_type.ilike('%pdf%'))
            elif file_type == 'doc':
                type_conditions.append(Document.content_type.ilike('%word%'))
                type_conditions.append(Document.content_type.ilike('%doc%'))
            elif file_type == 'image':
                type_conditions.append(Document.content_type.ilike('%image%'))
                type_conditions.append(Document.content_type.ilike('%png%'))
                type_conditions.append(Document.content_type.ilike('%jpg%'))
                type_conditions.append(Document.content_type.ilike('%jpeg%'))
            elif file_type == 'text':
                type_conditions.append(Document.content_type.ilike('%text%'))
        
        # Add the conditions to the query
        if type_conditions:
            base_query = base_query.filter(or_(*type_conditions))
    
    # Apply date filters
    if from_date:
        try:
            from_datetime = datetime.strptime(from_date, '%Y-%m-%d')
            base_query = base_query.filter(Document.created_at >= from_datetime)
        except ValueError:
            logger.warning(f"Invalid from_date format: {from_date}")
    
    if to_date:
        try:
            to_datetime = datetime.strptime(to_date, '%Y-%m-%d')
            # Add one day to include the end date fully
            to_datetime = to_datetime + timedelta(days=1)
            base_query = base_query.filter(Document.created_at < to_datetime)
        except ValueError:
            logger.warning(f"Invalid to_date format: {to_date}")
    
    # Get total count (before pagination)
    total_count = base_query.count()
    
    # Apply pagination and ordering
    documents = base_query.order_by(desc(Document.created_at)).offset(skip).limit(limit).all()
    
    # Format documents
    results = []
    for doc in documents:
        results.append({
            "id": doc.id,
            "filename": doc.filename,
            "content_type": doc.content_type,
            "created_at": doc.created_at.isoformat(),
            "processing_status": doc.processing_status,
            "file_size": doc.file_size,
            "metadata": doc.metadata
        })
    
    return {
        "total": total_count,
        "results": results,
        "filters": {
            "query": query,
            "tags": tags,
            "types": types,
            "from_date": from_date,
            "to_date": to_date
        }
    }
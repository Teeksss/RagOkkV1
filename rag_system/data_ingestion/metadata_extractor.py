"""
Metadata extraction for various document types.
"""
import os
import logging
from typing import Dict, Any, Optional
import fitz  # PyMuPDF
import docx
from PIL import Image
from datetime import datetime

logger = logging.getLogger(__name__)

def extract_metadata(file_path: str, file_ext: str) -> Dict[str, Any]:
    """
    Extract metadata from a file based on its type.
    
    Args:
        file_path: Path to the file
        file_ext: File extension
        
    Returns:
        Dict containing metadata
    """
    metadata = {
        "extraction_date": datetime.utcnow().isoformat(),
        "file_size": os.path.getsize(file_path),
        "file_type": file_ext
    }
    
    try:
        if file_ext == 'pdf':
            pdf_metadata = extract_pdf_metadata(file_path)
            metadata.update(pdf_metadata)
        elif file_ext in ['docx', 'doc']:
            docx_metadata = extract_docx_metadata(file_path)
            metadata.update(docx_metadata)
        elif file_ext in ['png', 'jpg', 'jpeg']:
            image_metadata = extract_image_metadata(file_path)
            metadata.update(image_metadata)
        elif file_ext == 'txt':
            txt_metadata = extract_txt_metadata(file_path)
            metadata.update(txt_metadata)
    except Exception as e:
        logger.error(f"Error extracting metadata from {file_path}: {str(e)}")
        metadata["extraction_error"] = str(e)
    
    return metadata

def extract_pdf_metadata(file_path: str) -> Dict[str, Any]:
    """Extract metadata from PDF files using PyMuPDF."""
    metadata = {}
    
    try:
        doc = fitz.open(file_path)
        
        # Get basic document info
        if doc.metadata:
            metadata["title"] = doc.metadata.get("title", "")
            metadata["author"] = doc.metadata.get("author", "")
            metadata["subject"] = doc.metadata.get("subject", "")
            metadata["keywords"] = doc.metadata.get("keywords", "")
            metadata["creator"] = doc.metadata.get("creator", "")
            metadata["producer"] = doc.metadata.get("producer", "")
            
            # Try to parse creation date
            if doc.metadata.get("creationDate"):
                try:
                    # Convert PDF date format to ISO
                    date_str = doc.metadata["creationDate"][2:16]
                    year = int(date_str[0:4])
                    month = int(date_str[4:6])
                    day = int(date_str[6:8])
                    hour = int(date_str[8:10])
                    minute = int(date_str[10:12])
                    second = int(date_str[12:14])
                    metadata["creation_date"] = f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"
                except Exception as e:
                    logger.warning(f"Could not parse PDF creation date: {e}")
        
        # Document statistics
        metadata["page_count"] = len(doc)
        
        # Check if OCR might be needed (heuristic based on text extraction)
        first_page = doc[0]
        text = first_page.get_text()
        metadata["requires_ocr"] = len(text.strip()) < 50  # Heuristic: if first page has little text, might need OCR
        
        doc.close()
    except Exception as e:
        logger.error(f"Error in PDF metadata extraction: {str(e)}")
        metadata["extraction_error"] = str(e)
    
    return metadata

def extract_docx_metadata(file_path: str) -> Dict[str, Any]:
    """Extract metadata from DOCX files."""
    metadata = {}
    
    try:
        doc = docx.Document(file_path)
        core_props = doc.core_properties
        
        metadata["title"] = core_props.title or ""
        metadata["author"] = core_props.author or ""
        metadata["comments"] = core_props.comments or ""
        metadata["keywords"] = core_props.keywords or ""
        metadata["created"] = core_props.created.isoformat() if core_props.created else ""
        metadata["modified"] = core_props.modified.isoformat() if core_props.modified else ""
        metadata["last_modified_by"] = core_props.last_modified_by or ""
        metadata["revision"] = core_props.revision or ""
        metadata["category"] = core_props.category or ""
        
        # Document statistics
        metadata["paragraph_count"] = len(doc.paragraphs)
        metadata["requires_ocr"] = False  # DOCX files typically don't need OCR
    except Exception as e:
        logger.error(f"Error in DOCX metadata extraction: {str(e)}")
        metadata["extraction_error"] = str(e)
    
    return metadata

def extract_image_metadata(file_path: str) -> Dict[str, Any]:
    """Extract metadata from image files."""
    metadata = {
        "requires_ocr": True  # Images always need OCR for text extraction
    }
    
    try:
        with Image.open(file_path) as img:
            metadata["width"] = img.width
            metadata["height"] = img.height
            metadata["mode"] = img.mode
            metadata["format"] = img.format
            
            # Extract EXIF data if available
            if hasattr(img, '_getexif') and img._getexif():
                exif = {
                    ExifTags.TAGS[k]: v
                    for k, v in img._getexif().items()
                    if k in ExifTags.TAGS
                }
                
                if "DateTimeOriginal" in exif:
                    metadata["date_taken"] = exif["DateTimeOriginal"]
                if "Make" in exif:
                    metadata["camera_make"] = exif["Make"]
                if "Model" in exif:
                    metadata["camera_model"] = exif["Model"]
    except Exception as e:
        logger.error(f"Error in image metadata extraction: {str(e)}")
        metadata["extraction_error"] = str(e)
    
    return metadata

def extract_txt_metadata(file_path: str) -> Dict[str, Any]:
    """Extract metadata from text files."""
    metadata = {
        "requires_ocr": False  # Text files don't need OCR
    }
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            
        metadata["character_count"] = len(content)
        metadata["line_count"] = content.count('\n') + 1
        metadata["word_count"] = len(content.split())
    except Exception as e:
        logger.error(f"Error in text file metadata extraction: {str(e)}")
        metadata["extraction_error"] = str(e)
    
    return metadata
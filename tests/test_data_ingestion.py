"""
Tests for data ingestion components.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi import UploadFile

from rag_system.data_ingestion.file_upload import FileUploadManager
from rag_system.data_ingestion.metadata_extractor import extract_metadata
from rag_system.data_ingestion.ocr_processor import OCRProcessor

# Sample test data
TEST_PDF_PATH = "tests/data/sample.pdf"
TEST_IMAGE_PATH = "tests/data/sample_image.jpg"
TEST_DOCX_PATH = "tests/data/sample.docx"
TEST_TXT_PATH = "tests/data/sample.txt"

@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = MagicMock()
    return session

@pytest.fixture
def upload_manager(mock_db_session):
    """Create upload manager with mock session."""
    return FileUploadManager(upload_dir="./test_uploads", db_session=mock_db_session)

def test_extract_pdf_metadata():
    """Test PDF metadata extraction."""
    if not os.path.exists(TEST_PDF_PATH):
        pytest.skip("Test PDF file not found")
    
    metadata = extract_metadata(TEST_PDF_PATH, "pdf")
    
    # Check basic metadata fields
    assert "file_size" in metadata
    assert "file_type" in metadata
    assert metadata["file_type"] == "pdf"
    
    # Check PDF-specific fields
    assert "page_count" in metadata
    assert isinstance(metadata["page_count"], int)
    assert "requires_ocr" in metadata

def test_extract_docx_metadata():
    """Test DOCX metadata extraction."""
    if not os.path.exists(TEST_DOCX_PATH):
        pytest.skip("Test DOCX file not found")
    
    metadata = extract_metadata(TEST_DOCX_PATH, "docx")
    
    # Check basic metadata fields
    assert "file_size" in metadata
    assert "file_type" in metadata
    assert metadata["file_type"] == "docx"
    
    # Check DOCX-specific fields
    assert "paragraph_count" in metadata
    assert "requires_ocr" in metadata
    assert metadata["requires_ocr"] is False  # DOCX shouldn't require OCR

def test_ocr_processor():
    """Test OCR processing."""
    if not os.path.exists(TEST_IMAGE_PATH):
        pytest.skip("Test image file not found")
    
    processor = OCRProcessor()
    result = processor.process_image(TEST_IMAGE_PATH)
    
    # Check result structure
    assert "text" in result
    assert "confidence_avg" in result
    assert "processing_status" in result
    assert result["processing_status"] == "success"

@pytest.mark.asyncio
async def test_file_upload(upload_manager):
    """Test file upload processing."""
    if not os.path.exists(TEST_TXT_PATH):
        pytest.skip("Test text file not found")
    
    # Mock UploadFile
    with open(TEST_TXT_PATH, "rb") as f:
        content = f.read()
    
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "test.txt"
    mock_file.content_type = "text/plain"
    mock_file.read = MagicMock(return_value=content)
    
    # Test upload processing
    result = await upload_manager.process_upload(mock_file, "test_user")
    
    # Check result
    assert "document_id" in result
    assert "filename" in result
    assert result["filename"] == "test.txt"
    assert "status" in result
    
    # Verify DB interaction
    assert upload_manager.db_session.add.called
    assert upload_manager.db_session.commit.called
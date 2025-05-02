"""
Multilingual document processing pipeline.
"""
import os
import logging
import tempfile
from typing import List, Dict, Any, Optional, BinaryIO
from datetime import datetime
import shutil
from pathlib import Path
import pickle
import json
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database.models import Document, DocumentChunk
from ..utils.language import LanguageDetector
from ..data_processing.multilingual_embeddings import MultilingualEmbedder
from ..data_processing.text_splitter import TokenTextSplitter

logger = logging.getLogger(__name__)

class OCRProcessor:
    """
    OCR processor for extracting text from images and scanned documents.
    """
    
    def __init__(self, 
                tesseract_path: Optional[str] = None,
                languages: List[str] = None):
        """
        Initialize OCR processor.
        
        Args:
            tesseract_path: Path to Tesseract executable
            languages: List of language codes for OCR
        """
        self.tesseract_path = tesseract_path
        self.languages = languages or ['eng', 'tur', 'deu', 'fra', 'spa', 'rus', 'ara', 'chi_sim', 'jpn']
        
        # Set environment variable if path provided
        if tesseract_path:
            os.environ['TESSERACT_CMD'] = tesseract_path
    
    def process_image(self, image_path: str) -> Dict[str, Any]:
        """
        Process image with OCR.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary with OCR results
        """
        try:
            import pytesseract
            from PIL import Image
            
            # Check if file exists
            if not os.path.exists(image_path):
                return {
                    "processing_status": "error",
                    "error": f"File not found: {image_path}"
                }
            
            # Open image
            image = Image.open(image_path)
            
            # Determine language
            # First try with all languages to detect
            try:
                lang_result = pytesseract.image_to_osd(image)
                detected_lang = 'eng'  # Default
                
                # Extract script info if available
                if 'Script' in lang_result:
                    script = lang_result.split('Script: ')[1].split('\n')[0]
                    # Map script to language
                    script_to_lang = {
                        'Latin': 'eng',
                        'Arabic': 'ara',
                        'Cyrillic': 'rus',
                        'Han': 'chi_sim',
                        'Hiragana': 'jpn',
                        'Katakana': 'jpn'
                    }
                    detected_lang = script_to_lang.get(script, 'eng')
            except:
                # If detection fails, use multi-language
                detected_lang = '+'.join(self.languages)
            
            # Perform OCR
            ocr_result = pytesseract.image_to_data(
                image, 
                lang=detected_lang,
                output_type=pytesseract.Output.DICT
            )
            
            # Extract text
            text_parts = []
            confidence_values = []
            
            for i in range(len(ocr_result['text'])):
                if int(ocr_result['conf'][i]) > -1:  # Filter out low confidence values (-1)
                    text = ocr_result['text'][i].strip()
                    if text:
                        text_parts.append(text)
                        confidence_values.append(int(ocr_result['conf'][i]))
            
            # Combine text
            extracted_text = ' '.join(text_parts)
            
            # Calculate average confidence
            avg_confidence = sum(confidence_values) / len(confidence_values) if confidence_values else 0
            
            return {
                "processing_status": "success",
                "text": extracted_text,
                "confidence_avg": avg_confidence,
                "language": detected_lang
            }
            
        except ImportError as e:
            return {
                "processing_status": "error",
                "error": f"Missing dependencies: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Error processing image with OCR: {str(e)}")
            return {
                "processing_status": "error",
                "error": f"OCR processing error: {str(e)}"
            }
    
    def process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        Process PDF with OCR.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with OCR results
        """
        try:
            import pytesseract
            from pdf2image import convert_from_path
            from PIL import Image
            
            # Check if file exists
            if not os.path.exists(pdf_path):
                return {
                    "processing_status": "error",
                    "error": f"File not found: {pdf_path}"
                }
            
            # Convert PDF to images
            pages = convert_from_path(pdf_path)
            
            # Process each page
            extracted_texts = []
            confidence_values = []
            
            for i, page in enumerate(pages):
                # Determine language (use multi-language for simplicity)
                lang = '+'.join(self.languages)
                
                # Perform OCR
                ocr_result = pytesseract.image_to_data(
                    page, 
                    lang=lang,
                    output_type=pytesseract.Output.DICT
                )
                
                # Extract text
                page_text_parts = []
                page_confidence = []
                
                for j in range(len(ocr_result['text'])):
                    if int(ocr_result['conf'][j]) > -1:  # Filter out low confidence values (-1)
                        text = ocr_result['text'][j].strip()
                        if text:
                            page_text_parts.append(text)
                            page_confidence.append(int(ocr_result['conf'][j]))
                
                # Combine page text
                page_text = ' '.join(page_text_parts)
                extracted_texts.append(page_text)
                
                # Extend confidence values
                confidence_values.extend(page_confidence)
            
            # Combine all pages
            full_text = '\n\n'.join(extracted_texts)
            
            # Calculate average confidence
            avg_confidence = sum(confidence_values) / len(confidence_values) if confidence_values else 0
            
            return {
                "processing_status": "success",
                "text": full_text,
                "confidence_avg": avg_confidence,
                "page_count": len(pages)
            }
            
        except ImportError as e:
            return {
                "processing_status": "error",
                "error": f"Missing dependencies: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Error processing PDF with OCR: {str(e)}")
            return {
                "processing_status": "error",
                "error": f"OCR processing error: {str(e)}"
            }


class DocumentChunker:
    """
    Document chunker for different content types.
    """
    
    def __init__(self, 
                 text_splitter: Optional[TokenTextSplitter] = None,
                 chunk_size: int = 512,
                 chunk_overlap: int = 77):
        """
        Initialize document chunker.
        
        Args:
            text_splitter: Text splitter instance
            chunk_size: Chunk size in tokens
            chunk_overlap: Chunk overlap in tokens
        """
        self.text_splitter = text_splitter or TokenTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
    
    def chunk_document(self, 
                      text: str,
                      metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Split document text into chunks.
        
        Args:
            text: Document text
            metadata: Document metadata
            
        Returns:
            List of chunks with text and metadata
        """
        if not text:
            return []
        
        # Initialize metadata
        metadata = metadata or {}
        
        # Split text
        chunks = self.text_splitter.split_text(text)
        
        # Create chunk objects
        result = []
        
        for i, chunk_text in enumerate(chunks):
            # Estimate token count
            token_count = self.text_splitter.estimate_tokens(chunk_text)
            
            # Create chunk object
            chunk = {
                "content": chunk_text,
                "chunk_index": i,
                "metadata": {
                    "chunk_index": i,
                    "token_count": token_count,
                    **metadata
                }
            }
            
            result.append(chunk)
        
        return result


class MultilingualDocumentProcessor:
    """
    Document processor with multilingual support.
    """
    
    def __init__(self, 
                 db_session: Session,
                 embedder: Optional[MultilingualEmbedder] = None,
                 chunker: Optional[DocumentChunker] = None,
                 ocr_processor: Optional[OCRProcessor] = None,
                 language_detector: Optional[LanguageDetector] = None,
                 temp_dir: Optional[str] = None):
        """
        Initialize multilingual document processor.
        
        Args:
            db_session: Database session
            embedder: Multilingual embedder
            chunker: Document chunker
            ocr_processor: OCR processor
            language_detector: Language detector
            temp_dir: Temporary directory for processing
        """
        self.db = db_session
        self.embedder = embedder or MultilingualEmbedder()
        self.chunker = chunker or DocumentChunker()
        self.ocr_processor = ocr_processor or OCRProcessor()
        self.language_detector = language_detector or LanguageDetector()
        
        # Create temp directory if not provided
        if temp_dir:
            self.temp_dir = temp_dir
            os.makedirs(temp_dir, exist_ok=True)
        else:
            self.temp_dir = tempfile.mkdtemp(prefix="multilingual_processor_")
    
    def __del__(self):
        """Clean up temporary files."""
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                logger.warning(f"Error cleaning up temp directory: {str(e)}")
    
    def process_document(self, document_id: str) -> Dict[str, Any]:
        """
        Process document with language detection and embedding.
        
        Args:
            document_id: Document ID
            
        Returns:
            Processing result
        """
        # Get document
        document = self.db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            logger.error(f"Document not found: {document_id}")
            return {"status": "error", "error": "Document not found"}
        
        # Update status
        document.processing_status = "processing"
        self.db.commit()
        
        try:
            # Process based on content type
            if document.content_type == "application/pdf":
                result = self._process_pdf(document)
            elif document.content_type == "text/plain":
                result = self._process_text(document)
            elif document.content_type in ["image/jpeg", "image/png", "image/tiff"]:
                result = self._process_image(document)
            elif document.content_type in ["application/msword", 
                                         "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
                result = self._process_word(document)
            else:
                logger.error(f"Unsupported content type: {document.content_type}")
                document.processing_status = "error"
                document.metadata = {
                    **(document.metadata or {}),
                    "error": f"Unsupported content type: {document.content_type}"
                }
                self.db.commit()
                return {"status": "error", "error": "Unsupported content type"}
            
            # Update document status based on result
            if result["status"] == "success":
                document.processing_status = "ready"
                
                # Update language detection
                document.metadata = {
                    **(document.metadata or {}),
                    "detected_language": result.get("language"),
                    "language_confidence": result.get("language_confidence")
                }
            else:
                document.processing_status = "error"
                document.metadata = {
                    **(document.metadata or {}),
                    "error": result.get("error")
                }
            
            self.db.commit()
            return result
            
        except Exception as e:
            logger.exception(f"Error processing document {document_id}: {str(e)}")
            
            # Update document status
            document.processing_status = "error"
            document.metadata = {
                **(document.metadata or {}),
                "error": str(e)
            }
            self.db.commit()
            
            return {"status": "error", "error": str(e)}
    
    def _process_pdf(self, document: Document) -> Dict[str, Any]:
        """
        Process PDF document.
        
        Args:
            document: Document model
            
        Returns:
            Processing result
        """
        file_path = document.file_path
        
        # Check if file exists
        if not os.path.exists(file_path):
            return {"status": "error", "error": f"File not found: {file_path}"}
        
        # Check if OCR is needed
        ocr_enabled = document.metadata.get("enable_ocr", True) if document.metadata else True
        needs_ocr = self._check_if_pdf_needs_ocr(file_path)
        
        # Extract text
        if needs_ocr and ocr_enabled:
            logger.info(f"Performing OCR on PDF: {document.filename}")
            
            # Process with OCR
            ocr_result = self.ocr_processor.process_pdf(file_path)
            
            if ocr_result["processing_status"] != "success":
                return {
                    "status": "error",
                    "error": ocr_result.get("error", "OCR processing failed")
                }
            
            text_content = ocr_result["text"]
            
            # Update metadata
            document.metadata = {
                **(document.metadata or {}),
                "page_count": ocr_result.get("page_count", 0),
                "ocr_confidence": ocr_result.get("confidence_avg", 0),
                "requires_ocr": True,
                "ocr_processed": True
            }
        else:
            # Extract text using pdfminer
            try:
                from pdfminer.high_level import extract_text
                from pdfminer.pdfpage import PDFPage
                
                text_content = extract_text(file_path)
                
                # Count pages
                with open(file_path, 'rb') as f:
                    page_count = len(list(PDFPage.get_pages(f)))
                
                # Update metadata
                document.metadata = {
                    **(document.metadata or {}),
                    "page_count": page_count,
                    "requires_ocr": False
                }
                
            except Exception as e:
                logger.error(f"Error extracting text from PDF: {str(e)}")
                return {"status": "error", "error": f"Error extracting text: {str(e)}"}
        
        # Detect language
        language, confidence = self.language_detector.detect_language(text_content)
        
        # Create chunks with language information
        chunks = self._create_chunks_with_language(document, text_content, language)
        
        # Generate embeddings
        embedding_result = self._generate_embeddings(chunks, language)
        
        return {
            "status": "success",
            "document_id": document.id,
            "chunks_created": len(chunks),
            "embeddings_created": embedding_result["count"],
            "language": language,
            "language_confidence": confidence
        }
    
    def _process_text(self, document: Document) -> Dict[str, Any]:
        """
        Process text document.
        
        Args:
            document: Document model
            
        Returns:
            Processing result
        """
        file_path = document.file_path
        
        # Check if file exists
        if not os.path.exists(file_path):
            return {"status": "error", "error": f"File not found: {file_path}"}
        
        # Read text content with encoding detection
        try:
            text_content = self._read_text_with_encoding(file_path)
        except Exception as e:
            logger.error(f"Error reading text file: {str(e)}")
            return {"status": "error", "error": f"Error reading text file: {str(e)}"}
        
        # Detect language
        language, confidence = self.language_detector.detect_language(text_content)
        
        # Update document metadata
        document.metadata = {
            **(document.metadata or {}),
            "character_count": len(text_content),
            "line_count": text_content.count('\n') + 1,
            "word_count": len(text_content.split()),
            "detected_language": language,
            "language_confidence": confidence
        }
        
        # Create chunks with language information
        chunks = self._create_chunks_with_language(document, text_content, language)
        
        # Generate embeddings
        embedding_result = self._generate_embeddings(chunks, language)
        
        return {
            "status": "success",
            "document_id": document.id,
            "chunks_created": len(chunks),
            "embeddings_created": embedding_result["count"],
            "language": language,
            "language_confidence": confidence
        }
    
    def _process_image(self, document: Document) -> Dict[str, Any]:
        """
        Process image document with OCR.
        
        Args:
            document: Document model
            
        Returns:
            Processing result
        """
        file_path = document.file_path
        
        # Check if file exists
        if not os.path.exists(file_path):
            return {"status": "error", "error": f"File not found: {file_path}"}
        
        # Process with OCR
        ocr_result = self.ocr_processor.process_image(file_path)
        
        if ocr_result["processing_status"] != "success":
            return {
                "status": "error",
                "error": ocr_result.get("error", "OCR processing failed")
            }
        
        text_content = ocr_result["text"]
        
        # Update metadata
        document.metadata = {
            **(document.metadata or {}),
            "ocr_confidence": ocr_result.get("confidence_avg", 0),
            "ocr_processed": True
        }
        
        # Detect language
        language, confidence = self.language_detector.detect_language(text_content)
        
        # Create chunks with language information
        chunks = self._create_chunks_with_language(document, text_content, language)
        
        # Generate embeddings
        embedding_result = self._generate_embeddings(chunks, language)
        
        return {
            "status": "success",
            "document_id": document.id,
            "chunks_created": len(chunks),
            "embeddings_created": embedding_result["count"],
            "language": language,
            "language_confidence": confidence
        }
    
    def _process_word(self, document: Document) -> Dict[str, Any]:
        """
        Process Word document.
        
        Args:
            document: Document model
            
        Returns:
            Processing result
        """
        file_path = document.file_path
        
        # Check if file exists
        if not os.path.exists(file_path):
            return {"status": "error", "error": f"File not found: {file_path}"}
        
        # Extract text from Word document
        try:
            # Try with docx2txt first (for .docx)
            if document.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                import docx2txt
                text_content = docx2txt.process(file_path)
            else:
                # For .doc files try textract
                import textract
                text_content = textract.process(file_path).decode('utf-8', errors='replace')
                
        except ImportError as e:
            logger.error(f"Missing dependency for Word processing: {str(e)}")
            return {"status": "error", "error": f"Missing dependency: {str(e)}"}
        except Exception as e:
            logger.error(f"Error extracting text from Word document: {str(e)}")
            return {"status": "error", "error": f"Error extracting text: {str(e)}"}
        
        # Detect language
        language, confidence = self.language_detector.detect_language(text_content)
        
        # Update document metadata
        document.metadata = {
            **(document.metadata or {}),
            "character_count": len(text_content),
            "word_count": len(text_content.split()),
            "detected_language": language,
            "language_confidence": confidence
        }
        
        # Create chunks with language information
        chunks = self._create_chunks_with_language(document, text_content, language)
        
        # Generate embeddings
        embedding_result = self._generate_embeddings(chunks, language)
        
        return {
            "status": "success",
            "document_id": document.id,
            "chunks_created": len(chunks),
            "embeddings_created": embedding_result["count"],
            "language": language,
            "language_confidence": confidence
        }
    
    def _check_if_pdf_needs_ocr(self, file_path: str) -> bool:
        """
        Check if a PDF file needs OCR processing.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            True if OCR is needed, False otherwise
        """
        try:
            # Extract text from first few pages
            from pdfminer.high_level import extract_text
            text = extract_text(file_path, page_numbers=[0, 1])
            
            # If text is too short, it might be a scanned document
            if len(text.strip()) < 100:
                return True
            
            return False
        except Exception as e:
            logger.warning(f"Error checking if PDF needs OCR: {str(e)}")
            # If there's an error, assume OCR is needed
            return True
    
    def _read_text_with_encoding(self, file_path: str) -> str:
        """
        Read a text file with encoding detection.
        
        Args:
            file_path: Path to text file
            
        Returns:
            File content as string
        """
        # Try UTF-8 first
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            pass
        
        # Try other common encodings
        encodings = ['latin-1', 'cp1252', 'iso-8859-1', 'iso-8859-9', 'windows-1254']  # Added Turkish encodings
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                    # Convert to UTF-8
                    return content.encode('utf-8', errors='replace').decode('utf-8')
            except UnicodeDecodeError:
                continue
        
        # If all fail, use latin-1 with replacement character for invalid bytes
        with open(file_path, 'r', encoding='latin-1', errors='replace') as f:
            return f.read()
    
    def _create_chunks_with_language(self, document: Document, text_content: str, language: str) -> List[DocumentChunk]:
        """
        Create document chunks with language information.
        
        Args:
            document: Document model
            text_content: Extracted text content
            language: Detected language code
            
        Returns:
            List of created chunks
        """
        # Split document into chunks
        chunks = self.chunker.chunk_document(text_content, {
            "document_id": document.id,
            "filename": document.filename,
            "title": document.metadata.get("title", document.filename) if document.metadata else document.filename,
            "language": language
        })
        
        # Create database records
        db_chunks = []
        
        for i, chunk in enumerate(chunks):
            db_chunk = DocumentChunk(
                document_id=document.id,
                chunk_index=i,
                content=chunk["content"],
                metadata={
                    **(chunk["metadata"] or {}),
                    "language": language
                },
                embedding_stored=False
            )
            
            self.db.add(db_chunk)
            db_chunks.append(db_chunk)
        
        self.db.commit()
        
        logger.info(f"Created {len(db_chunks)} chunks for document {document.id}")
        
        return db_chunks
    
    def _generate_embeddings(self, chunks: List[DocumentChunk], language: str) -> Dict[str, Any]:
        """
        Generate embeddings for chunks.
        
        Args:
            chunks: List of document chunks
            language: Document language code
            
        Returns:
            Embedding result
        """
        # Prepare chunk data for embedding
        chunk_data = []
        for chunk in chunks:
            chunk_data.append({
                "id": chunk.id,
                "content": chunk.content,
                "metadata": chunk.metadata,
                "language": language
            })
        
        try:
            # Generate embeddings
            embedded_chunks = self.embedder.embed_chunks_with_metadata(chunk_data, language_key="language")
            
            # Update embedding status in database
            for i, chunk in enumerate(chunks):
                # Also store the embedding vector in the database
                if i < len(embedded_chunks) and "embedding" in embedded_chunks[i]:
                    # Serialize embedding vector
                    vector = embedded_chunks[i]["embedding"]
                    chunk.embedding_vector = pickle.dumps(vector)
                
                chunk.embedding_stored = True
            
            self.db.commit()
            
            return {
                "status": "success",
                "count": len(embedded_chunks)
            }
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            return {
                "status": "error",
                "error": f"Error generating embeddings: {str(e)}",
                "count": 0
            }
    
    def process_batch(self, document_ids: List[str], max_concurrency: int = 4) -> Dict[str, Any]:
        """
        Process a batch of documents.
        
        Args:
            document_ids: List of document IDs
            max_concurrency: Maximum concurrent processing
            
        Returns:
            Batch processing result
        """
        import concurrent.futures
        
        results = {}
        processed_count = 0
        error_count = 0
        
        # Process documents in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrency) as executor:
            future_to_id = {executor.submit(self.process_document, doc_id): doc_id for doc_id in document_ids}
            
            for future in concurrent.futures.as_completed(future_to_id):
                doc_id = future_to_id[future]
                try:
                    result = future.result()
                    results[doc_id] = result
                    
                    if result["status"] == "success":
                        processed_count += 1
                    else:
                        error_count += 1
                except Exception as e:
                    logger.error(f"Error processing document {doc_id}: {str(e)}")
                    results[doc_id] = {"status": "error", "error": str(e)}
                    error_count += 1
        
        return {
            "status": "completed",
            "total": len(document_ids),
            "processed": processed_count,
            "errors": error_count,
            "results": results
        }
    
    def rebuild_embeddings(self, document_id: str, force: bool = False) -> Dict[str, Any]:
        """
        Rebuild embeddings for a document.
        
        Args:
            document_id: Document ID
            force: Force rebuild even if embeddings exist
            
        Returns:
            Rebuild result
        """
        # Get document
        document = self.db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            logger.error(f"Document not found: {document_id}")
            return {"status": "error", "error": "Document not found"}
        
        # Get chunks
        query = self.db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id)
        
        if not force:
            # Only get chunks without embeddings
            query = query.filter(DocumentChunk.embedding_stored == False)
        
        chunks = query.all()
        
        if not chunks:
            return {
                "status": "warning",
                "message": "No chunks found that need embedding" if not force else "No chunks found",
                "document_id": document_id
            }
        
        # Get document language
        language = document.metadata.get("detected_language", "en") if document.metadata else "en"
        
        # Generate embeddings
        embedding_result = self._generate_embeddings(chunks, language)
        
        return {
            "status": embedding_result["status"],
            "document_id": document_id,
            "chunks_processed": len(chunks),
            "message": f"Rebuilt embeddings for {len(chunks)} chunks"
        }
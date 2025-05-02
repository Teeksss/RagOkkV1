"""
Document chunking utilities for RAG system.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
import re
import uuid

from .text_splitter import TokenTextSplitter

logger = logging.getLogger(__name__)

class DocumentChunker:
    """
    Document chunker for splitting content into manageable chunks.
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
    
    def chunk_document_with_sections(self,
                                    text: str,
                                    section_markers: Optional[List[str]] = None,
                                    metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Split document with awareness of section markers.
        
        Args:
            text: Document text
            section_markers: List of section marker patterns (regex)
            metadata: Document metadata
            
        Returns:
            List of chunks with text and metadata
        """
        if not text:
            return []
        
        # Initialize metadata
        metadata = metadata or {}
        
        # Default section markers for common documents
        if section_markers is None:
            section_markers = [
                r"^# .*$",          # Markdown h1
                r"^## .*$",         # Markdown h2
                r"^### .*$",        # Markdown h3
                r"^Chapter \d+.*$", # Chapter headings
                r"^Section \d+.*$", # Section headings
            ]
        
        # Compile patterns
        patterns = [re.compile(marker, re.MULTILINE) for marker in section_markers]
        
        # Find section boundaries
        sections = []
        current_section_start = 0
        current_section_title = "Introduction"
        
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            # Calculate line offset in original text
            if i > 0:
                line_offset = sum(len(lines[j]) + 1 for j in range(i))
            else:
                line_offset = 0
            
            # Check if line matches any section marker
            for pattern in patterns:
                if pattern.match(line):
                    # Add previous section if it exists
                    if current_section_start < line_offset:
                        section_text = text[current_section_start:line_offset]
                        sections.append({
                            "title": current_section_title,
                            "text": section_text,
                            "start": current_section_start,
                            "end": line_offset
                        })
                    
                    # Start new section
                    current_section_start = line_offset
                    current_section_title = line.strip()
                    break
        
        # Add final section
        if current_section_start < len(text):
            section_text = text[current_section_start:]
            sections.append({
                "title": current_section_title,
                "text": section_text,
                "start": current_section_start,
                "end": len(text)
            })
        
        # If no sections were found, treat whole document as one section
        if not sections:
            sections.append({
                "title": metadata.get("title", "Document"),
                "text": text,
                "start": 0,
                "end": len(text)
            })
        
        # Split each section into chunks
        result = []
        global_chunk_index = 0
        
        for section in sections:
            section_chunks = self.text_splitter.split_text(section["text"])
            
            for i, chunk_text in enumerate(section_chunks):
                # Estimate token count
                token_count = self.text_splitter.estimate_tokens(chunk_text)
                
                # Create chunk object
                chunk = {
                    "content": chunk_text,
                    "chunk_index": global_chunk_index,
                    "metadata": {
                        "chunk_index": global_chunk_index,
                        "section_title": section["title"],
                        "section_index": sections.index(section),
                        "section_chunk_index": i,
                        "token_count": token_count,
                        **metadata
                    }
                }
                
                result.append(chunk)
                global_chunk_index += 1
        
        return result
    
    def chunk_code_document(self,
                           text: str,
                           language: Optional[str] = None,
                           metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Split code document with awareness of code structures.
        
        Args:
            text: Document text (code)
            language: Programming language
            metadata: Document metadata
            
        Returns:
            List of chunks with text and metadata
        """
        if not text:
            return []
        
        # Initialize metadata
        metadata = metadata or {}
        
        # Try to detect language if not provided
        if not language and "filename" in metadata:
            filename = metadata["filename"]
            extension = filename.split(".")[-1].lower() if "." in filename else ""
            
            # Map common extensions to languages
            extension_to_language = {
                "py": "python",
                "js": "javascript",
                "ts": "typescript",
                "java": "java",
                "cpp": "cpp",
                "c": "c",
                "cs": "csharp",
                "php": "php",
                "rb": "ruby",
                "go": "go",
                "rs": "rust",
                "swift": "swift",
                "kt": "kotlin",
                "scala": "scala",
                "pl": "perl",
                "sh": "bash",
                "sql": "sql",
                "html": "html",
                "css": "css",
                "json": "json",
                "xml": "xml",
                "yaml": "yaml",
                "yml": "yaml",
                "md": "markdown"
            }
            
            language = extension_to_language.get(extension)
        
        # Define function pattern based on language
        function_patterns = {
            "python": r"(async\s+)?def\s+\w+\s*\([^)]*\)\s*(\s*->.*?)?\s*:",
            "javascript": r"(async\s+)?(function\s+\w+|const\s+\w+\s*=\s*(\([^)]*\)|async)?(\s*\([^)]*\))?\s*=>|class\s+\w+|^\s*\w+\s*\([^)]*\)\s*{)",
            "typescript": r"(async\s+)?(function\s+\w+|const\s+\w+\s*=\s*(\([^)]*\)|async)?(\s*\([^)]*\))?\s*=>|class\s+\w+|^\s*\w+\s*\([^)]*\)(\s*:\s*\w+)?\s*{)",
            "java": r"(public|private|protected|static|\s)+[\w<>\[\]]+\s+(\w+)\s*\([^)]*\)\s*(\{|throws)",
            "cpp": r"([\w:]+\s+)?\w+\s*\([^)]*\)(\s*const)?\s*(\{|;|throws)",
            "csharp": r"(public|private|protected|static|\s)+[\w<>\[\]]+\s+(\w+)\s*\([^)]*\)\s*\{",
            "go": r"func\s+\w+\s*\([^)]*\)\s*(\([^)]*\))?\s*\{",
        }
        
        # Default chunk by line if no specific logic
        if not language or language not in function_patterns:
            # Fall back to regular chunking
            return self.chunk_document(text, metadata)
        
        # Split by function/class definitions
        pattern = re.compile(function_patterns[language], re.MULTILINE)
        matches = list(pattern.finditer(text))
        
        if not matches:
            # No function/class matches, fall back to regular chunking
            return self.chunk_document(text, metadata)
        
        # Create sections based on function/class boundaries
        sections = []
        
        # Add first section (imports and global code)
        if matches[0].start() > 0:
            sections.append({
                "title": "Imports and Global Scope",
                "text": text[:matches[0].start()],
                "start": 0,
                "end": matches[0].start()
            })
        
        # Add function/class sections
        for i, match in enumerate(matches):
            section_start = match.start()
            
            # Determine end of section (next match or end of file)
            if i < len(matches) - 1:
                section_end = matches[i + 1].start()
            else:
                section_end = len(text)
            
            # Get function/class name
            function_line = text[section_start:text.find('\n', section_start)]
            section_title = function_line.strip()
            
            sections.append({
                "title": section_title,
                "text": text[section_start:section_end],
                "start": section_start,
                "end": section_end
            })
        
        # Split sections into chunks
        result = []
        global_chunk_index = 0
        
        for section in sections:
            # Check if section is too large
            token_count = self.text_splitter.estimate_tokens(section["text"])
            
            if token_count <= self.text_splitter.chunk_size:
                # Section fits in one chunk
                chunk = {
                    "content": section["text"],
                    "chunk_index": global_chunk_index,
                    "metadata": {
                        "chunk_index": global_chunk_index,
                        "section_title": section["title"],
                        "section_index": sections.index(section),
                        "token_count": token_count,
                        "language": language,
                        **metadata
                    }
                }
                
                result.append(chunk)
                global_chunk_index += 1
            else:
                # Section needs to be split
                section_chunks = self.text_splitter.split_text(section["text"])
                
                for i, chunk_text in enumerate(section_chunks):
                    sub_token_count = self.text_splitter.estimate_tokens(chunk_text)
                    
                    chunk = {
                        "content": chunk_text,
                        "chunk_index": global_chunk_index,
                        "metadata": {
                            "chunk_index": global_chunk_index,
                            "section_title": section["title"],
                            "section_index": sections.index(section),
                            "section_chunk_index": i,
                            "token_count": sub_token_count,
                            "language": language,
                            **metadata
                        }
                    }
                    
                    result.append(chunk)
                    global_chunk_index += 1
        
        return result
"""
Text chunking utilities.
"""
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class TextChunker:
    """
    Class for splitting text into manageable chunks for processing.
    """
    
    def __init__(self):
        """Initialize text chunker."""
        pass
    
    def chunk_text(self, 
                  text: str, 
                  max_chunk_size: int = 1000, 
                  overlap: int = 200,
                  respect_paragraphs: bool = True) -> List[str]:
        """
        Split text into chunks with overlap.
        
        Args:
            text: Text to chunk
            max_chunk_size: Maximum chunk size in characters
            overlap: Number of characters to overlap between chunks
            respect_paragraphs: Whether to respect paragraph boundaries
            
        Returns:
            List of text chunks
        """
        if not text:
            return []
        
        # Clean text: normalize newlines and remove excessive whitespace
        text = self._clean_text(text)
        
        # If respect_paragraphs is True, try to chunk by paragraphs
        if respect_paragraphs:
            chunks = self._chunk_by_paragraphs(text, max_chunk_size, overlap)
        else:
            chunks = self._chunk_by_size(text, max_chunk_size, overlap)
        
        # Remove empty chunks and trim whitespace
        chunks = [chunk.strip() for chunk in chunks if chunk.strip()]
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text.
        
        Args:
            text: Input text
            
        Returns:
            Cleaned text
        """
        # Normalize newlines
        text = re.sub(r'\r\n', '\n', text)
        
        # Replace multiple newlines with a single one
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Replace multiple spaces with a single one
        text = re.sub(r' {2,}', ' ', text)
        
        return text.strip()
    
    def _chunk_by_paragraphs(self, 
                           text: str, 
                           max_chunk_size: int, 
                           overlap: int) -> List[str]:
        """
        Split text into chunks respecting paragraph boundaries.
        
        Args:
            text: Text to chunk
            max_chunk_size: Maximum chunk size in characters
            overlap: Number of characters to overlap between chunks
            
        Returns:
            List of text chunks
        """
        # Split text into paragraphs
        paragraphs = re.split(r'\n\s*\n', text)
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # If adding this paragraph would exceed max_chunk_size
            if len(current_chunk) + len(paragraph) + 1 > max_chunk_size and current_chunk:
                # Add current chunk to chunks
                chunks.append(current_chunk)
                
                # Start new chunk with overlap from previous chunk
                if overlap > 0 and len(current_chunk) > overlap:
                    # Try to find paragraph boundary within overlap
                    overlap_text = current_chunk[-overlap:]
                    boundary = overlap_text.find('\n\n')
                    
                    if boundary != -1:
                        # Found paragraph boundary in overlap
                        current_chunk = current_chunk[-(overlap-boundary):]
                    else:
                        # No paragraph boundary, use sentence boundary if possible
                        current_chunk = self._get_overlap_at_sentence_boundary(current_chunk, overlap)
                else:
                    current_chunk = ""
            
            # Add paragraph to current chunk
            if current_chunk:
                current_chunk += "\n\n" + paragraph
            else:
                current_chunk = paragraph
            
            # Check if current chunk exceeds max_chunk_size
            while len(current_chunk) > max_chunk_size:
                # This paragraph alone is too large, need to split it
                split_point = self._find_split_point(current_chunk, max_chunk_size)
                
                # Add first part to chunks
                chunks.append(current_chunk[:split_point])
                
                # Continue with remainder and overlap
                remainder = current_chunk[split_point:].strip()
                
                if overlap > 0 and split_point > overlap:
                    # Get overlap text
                    overlap_text = current_chunk[split_point-overlap:split_point]
                    
                    # Start new chunk with overlap + remainder
                    current_chunk = overlap_text + remainder
                else:
                    current_chunk = remainder
        
        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _chunk_by_size(self, 
                     text: str, 
                     max_chunk_size: int, 
                     overlap: int) -> List[str]:
        """
        Split text into chunks of maximum size with overlap.
        
        Args:
            text: Text to chunk
            max_chunk_size: Maximum chunk size in characters
            overlap: Number of characters to overlap between chunks
            
        Returns:
            List of text chunks
        """
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            # Calculate end point
            end = start + max_chunk_size
            
            # If we're at the end of the text
            if end >= text_length:
                chunks.append(text[start:])
                break
            
            # Find a good split point
            split_point = self._find_split_point(text[start:end], max_chunk_size)
            
            # Add chunk
            chunks.append(text[start:start+split_point])
            
            # Move start position, accounting for overlap
            start = start + split_point - min(overlap, split_point)
        
        return chunks
    
    def _find_split_point(self, text: str, max_size: int) -> int:
        """
        Find a good split point within text, preferring sentence boundaries.
        
        Args:
            text: Text to split
            max_size: Maximum size
            
        Returns:
            Index of split point
        """
        # If text is shorter than max_size, return its length
        if len(text) <= max_size:
            return len(text)
        
        # Try to find a sentence boundary
        for pattern in [r'[.!?]\s+', r'[.!?]"?\s+', r'\n\s*\n', r'\n', r'. ']:
            matches = list(re.finditer(pattern, text[:max_size]))
            if matches:
                # Return the position after the last sentence boundary
                last_match = matches[-1]
                return last_match.end()
        
        # If no sentence boundary found, try to split on word boundary
        matches = list(re.finditer(r'\s+', text[:max_size]))
        if matches:
            # Return the position after the last space
            last_match = matches[-1]
            return last_match.end()
        
        # If all else fails, just split at max_size
        return max_size
    
    def _get_overlap_at_sentence_boundary(self, text: str, overlap: int) -> str:
        """
        Get overlap text trying to respect sentence boundaries.
        
        Args:
            text: Text to get overlap from
            overlap: Desired overlap size
            
        Returns:
            Overlap text
        """
        if len(text) <= overlap:
            return text
        
        # Get overlap text
        overlap_text = text[-overlap:]
        
        # Try to find a sentence start
        match = re.search(r'[.!?]\s+[A-Z]', overlap_text)
        if match:
            # Return from the start of the last sentence
            return overlap_text[match.end()-1:]
        
        # If no sentence boundary, find word boundary
        match = re.search(r'\s+', overlap_text)
        if match:
            # Return from the first word boundary
            return overlap_text[match.end():]
        
        return overlap_text


class MarkdownChunker(TextChunker):
    """
    Specialized chunker for Markdown text.
    """
    
    def chunk_text(self, 
                  text: str, 
                  max_chunk_size: int = 1000, 
                  overlap: int = 200,
                  respect_headers: bool = True) -> List[str]:
        """
        Split markdown text into chunks, respecting headers when possible.
        
        Args:
            text: Markdown text to chunk
            max_chunk_size: Maximum chunk size in characters
            overlap: Number of characters to overlap between chunks
            respect_headers: Whether to respect header boundaries
            
        Returns:
            List of text chunks
        """
        if not text:
            return []
        
        # Clean text
        text = self._clean_text(text)
        
        if respect_headers:
            # Split by headers
            chunks = self._chunk_by_headers(text, max_chunk_size, overlap)
        else:
            # Fall back to paragraph chunking
            chunks = self._chunk_by_paragraphs(text, max_chunk_size, overlap)
        
        # Remove empty chunks and trim whitespace
        chunks = [chunk.strip() for chunk in chunks if chunk.strip()]
        
        return chunks
    
    def _chunk_by_headers(self, 
                        text: str, 
                        max_chunk_size: int, 
                        overlap: int) -> List[str]:
        """
        Split markdown text into chunks based on headers.
        
        Args:
            text: Markdown text to chunk
            max_chunk_size: Maximum chunk size in characters
            overlap: Number of characters to overlap between chunks
            
        Returns:
            List of text chunks
        """
        # Find all headers
        header_pattern = r'^#{1,6}\s+.+$'
        header_matches = list(re.finditer(header_pattern, text, re.MULTILINE))
        
        if not header_matches:
            # No headers found, fall back to paragraph chunking
            return self._chunk_by_paragraphs(text, max_chunk_size, overlap)
        
        chunks = []
        start_idx = 0
        
        # Process each header section
        for i, match in enumerate(header_matches):
            header_start = match.start()
            
            # If this isn't the first header, process the text before it
            if i > 0 and header_start > start_idx:
                section_text = text[start_idx:header_start]
                
                # If section is too large, chunk it further
                if len(section_text) > max_chunk_size:
                    section_chunks = self._chunk_by_paragraphs(section_text, max_chunk_size, overlap)
                    chunks.extend(section_chunks)
                else:
                    chunks.append(section_text)
            
            # Update start position for next section
            start_idx = header_start
        
        # Process the last section
        if start_idx < len(text):
            last_section = text[start_idx:]
            
            # If last section is too large, chunk it
            if len(last_section) > max_chunk_size:
                last_chunks = self._chunk_by_paragraphs(last_section, max_chunk_size, overlap)
                chunks.extend(last_chunks)
            else:
                chunks.append(last_section)
        
        return chunks
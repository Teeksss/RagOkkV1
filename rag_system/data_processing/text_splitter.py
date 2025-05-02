"""
Text splitting utilities for RAG system.
"""
import logging
import re
from typing import List, Dict, Any, Optional, Union, Tuple

logger = logging.getLogger(__name__)

class TokenTextSplitter:
    """
    Text splitter that splits text into chunks of tokens.
    """
    
    def __init__(self, 
                 chunk_size: int = 512, 
                 chunk_overlap: int = 77,
                 model_name: str = "gpt-3.5-turbo"):
        """
        Initialize text splitter.
        
        Args:
            chunk_size: Maximum chunk size in tokens
            chunk_overlap: Overlap between chunks in tokens
            model_name: Model name for token count estimation
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.model_name = model_name
        
        # Regex patterns for better splitting
        self.paragraph_split = r"\n\n+"
        self.sentence_split = r"(?<=[.!?])\s+"
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate number of tokens in text.
        
        Args:
            text: Input text
            
        Returns:
            Estimated token count
        """
        # Rough token count estimation (words / 0.75)
        # More accurate would be to use a tokenizer specific to the model
        try:
            from transformers import AutoTokenizer
            
            if not hasattr(self, 'tokenizer'):
                # Use cl100k_base for recent OpenAI models
                if self.model_name.startswith("gpt-3.5") or self.model_name.startswith("gpt-4"):
                    self.tokenizer = AutoTokenizer.from_pretrained("openai-community/gpt2")
                else:
                    self.tokenizer = AutoTokenizer.from_pretrained("openai-community/gpt2")
            
            tokens = self.tokenizer.encode(text)
            return len(tokens)
        except:
            # Fallback to rough estimation if tokenizer not available
            return len(text.split()) // 0.75
    
    def split_text(self, text: str) -> List[str]:
        """
        Split text into chunks of specified token size.
        
        Args:
            text: Input text
            
        Returns:
            List of text chunks
        """
        if not text:
            return []
        
        # First try to split by paragraphs
        paragraphs = re.split(self.paragraph_split, text)
        paragraphs = [p for p in paragraphs if p.strip()]
        
        # Get chunks by keeping paragraphs together when possible
        chunks = []
        current_chunk = []
        current_chunk_size = 0
        
        for paragraph in paragraphs:
            paragraph_size = self.estimate_tokens(paragraph)
            
            # If paragraph is larger than chunk size, split it by sentences
            if paragraph_size > self.chunk_size:
                sentences = re.split(self.sentence_split, paragraph)
                sentences = [s for s in sentences if s.strip()]
                
                for sentence in sentences:
                    sentence_size = self.estimate_tokens(sentence)
                    
                    # If sentence is too large, add it to chunks directly
                    if sentence_size > self.chunk_size:
                        # If we have accumulated text, store it as a chunk
                        if current_chunk:
                            chunks.append("\n\n".join(current_chunk))
                            current_chunk = []
                            current_chunk_size = 0
                        
                        # Split the large sentence into multiple chunks
                        sentence_chunks = self._split_text_by_size(sentence, self.chunk_size)
                        chunks.extend(sentence_chunks)
                    
                    # If adding the sentence would exceed chunk size, create a new chunk
                    elif current_chunk_size + sentence_size > self.chunk_size:
                        chunks.append("\n\n".join(current_chunk))
                        current_chunk = [sentence]
                        current_chunk_size = sentence_size
                    
                    # Otherwise, add the sentence to the current chunk
                    else:
                        current_chunk.append(sentence)
                        current_chunk_size += sentence_size
            
            # If adding the paragraph would exceed chunk size, create a new chunk
            elif current_chunk_size + paragraph_size > self.chunk_size:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = [paragraph]
                current_chunk_size = paragraph_size
            
            # Otherwise, add the paragraph to the current chunk
            else:
                current_chunk.append(paragraph)
                current_chunk_size += paragraph_size
        
        # Add any remaining text as a chunk
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))
        
        # Add overlap between chunks
        if self.chunk_overlap > 0 and len(chunks) > 1:
            chunks_with_overlap = self._add_chunk_overlap(chunks)
            return chunks_with_overlap
        
        return chunks
    
    def _split_text_by_size(self, text: str, max_size: int) -> List[str]:
        """
        Split text into chunks by token size.
        
        Args:
            text: Input text
            max_size: Maximum chunk size in tokens
            
        Returns:
            List of text chunks
        """
        words = text.split()
        chunks = []
        current_chunk = []
        current_size = 0
        
        for word in words:
            word_size = self.estimate_tokens(word)
            
            if current_size + word_size > max_size:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                    current_chunk = [word]
                    current_size = word_size
                else:
                    # If a single word is too large, add it anyway
                    chunks.append(word)
            else:
                current_chunk.append(word)
                current_size += word_size
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    def _add_chunk_overlap(self, chunks: List[str]) -> List[str]:
        """
        Add overlap between chunks.
        
        Args:
            chunks: List of text chunks
            
        Returns:
            List of overlapping text chunks
        """
        if len(chunks) <= 1:
            return chunks
        
        result = []
        
        for i in range(len(chunks)):
            if i == 0:
                # First chunk doesn't need prefix overlap
                result.append(chunks[i])
            else:
                # Get overlap from previous chunk
                prev_chunk = chunks[i-1]
                current_chunk = chunks[i]
                
                # Get overlap words
                prev_words = prev_chunk.split()
                overlap_size = min(self.chunk_overlap, len(prev_words))
                overlap_text = " ".join(prev_words[-overlap_size:])
                
                # Add overlap to current chunk
                result.append(f"{overlap_text} {current_chunk}")
        
        return result
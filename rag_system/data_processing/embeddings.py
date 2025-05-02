"""
Embedding models for text vectorization.
"""
import logging
import os
from typing import List, Dict, Any, Optional, Union
import numpy as np
import torch
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class SentenceEmbedder:
    """
    Embedder for text using sentence transformer models.
    """
    
    def __init__(self, 
                 model_name: str = "all-MiniLM-L6-v2",
                 device: Optional[str] = None,
                 cache_dir: Optional[str] = None,
                 use_fp16: bool = True):
        """
        Initialize sentence embedder.
        
        Args:
            model_name: Name of the model to use
            device: Device to use (cuda, cpu)
            cache_dir: Directory to cache models
            use_fp16: Whether to use FP16 for inference
        """
        self.model_name = model_name
        self.cache_dir = cache_dir
        self.use_fp16 = use_fp16
        self.embedding_dim = 0
        self.model = None
        self.device = device
        
        # Load model
        self._load_model()
    
    def _load_model(self) -> None:
        """Load the embedding model."""
        try:
            from sentence_transformers import SentenceTransformer
            
            # Set device
            if self.device is None:
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
            
            # Configure model path
            model_kwargs = {}
            if self.cache_dir:
                model_kwargs["cache_folder"] = self.cache_dir
            
            # Load the model
            logger.info(f"Loading embedding model: {self.model_name} on {self.device}")
            self.model = SentenceTransformer(self.model_name, device=self.device, **model_kwargs)
            
            # Set embedding dimension
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            
            # Use half precision if requested and supported
            if self.use_fp16 and self.device == "cuda" and torch.cuda.is_available():
                self.model.half()
                logger.info("Using FP16 for inference")
            
            logger.info(f"Model loaded successfully. Embedding dimension: {self.embedding_dim}")
        
        except ImportError:
            logger.error("Failed to import sentence_transformers. Please install with: pip install sentence-transformers")
            raise
        except Exception as e:
            logger.error(f"Error loading embedding model: {str(e)}")
            raise
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for text.
        
        Args:
            text: Input text
            
        Returns:
            Text embedding
        """
        if not text or not text.strip():
            # Return zero vector for empty text
            return np.zeros(self.embedding_dim, dtype=np.float32)
        
        try:
            # Generate embedding
            with torch.no_grad():
                embedding = self.model.encode(text, convert_to_numpy=True, show_progress_bar=False)
            
            return embedding
        
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            # Return zero vector on error
            return np.zeros(self.embedding_dim, dtype=np.float32)
    
    def embed_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Generate embeddings for a batch of texts.
        
        Args:
            texts: List of input texts
            batch_size: Batch size for processing
            
        Returns:
            Array of embeddings
        """
        if not texts:
            return np.array([])
        
        # Filter empty texts and replace with space to avoid errors
        processed_texts = [text if text and text.strip() else " " for text in texts]
        
        try:
            # Generate embeddings
            with torch.no_grad():
                embeddings = self.model.encode(
                    processed_texts, 
                    batch_size=batch_size,
                    convert_to_numpy=True, 
                    show_progress_bar=False
                )
            
            return embeddings
        
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {str(e)}")
            # Return zero vectors on error
            return np.zeros((len(texts), self.embedding_dim), dtype=np.float32)
    
    def embed_chunks_with_metadata(self, chunks: List[Dict[str, Any]], text_key: str = "content") -> List[Dict[str, Any]]:
        """
        Generate embeddings for chunks with metadata.
        
        Args:
            chunks: List of chunk dictionaries
            text_key: Key for text content in chunks
            
        Returns:
            List of chunks with embeddings
        """
        # Prepare texts and track original indices
        texts = []
        indices = []
        
        for i, chunk in enumerate(chunks):
            if text_key in chunk:
                texts.append(chunk[text_key])
                indices.append(i)
        
        if not texts:
            return chunks
        
        # Generate embeddings
        embeddings = self.embed_batch(texts)
        
        # Add embeddings to chunks
        result = []
        for i, chunk in enumerate(chunks):
            new_chunk = chunk.copy()
            
            # Add embedding if available
            if i in indices:
                idx = indices.index(i)
                new_chunk["embedding"] = embeddings[idx]
            
            result.append(new_chunk)
        
        return result
    
    def cosine_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Cosine similarity
        """
        # Normalize embeddings
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        embedding1_normalized = embedding1 / norm1
        embedding2_normalized = embedding2 / norm2
        
        # Calculate cosine similarity
        return float(np.dot(embedding1_normalized, embedding2_normalized))
    
    def calculate_similarities(self, query_embedding: np.ndarray, embeddings: np.ndarray) -> np.ndarray:
        """
        Calculate similarities between query and multiple embeddings.
        
        Args:
            query_embedding: Query embedding
            embeddings: Matrix of embeddings to compare against
            
        Returns:
            Array of similarity scores
        """
        # Normalize query embedding
        query_norm = np.linalg.norm(query_embedding)
        if query_norm > 0:
            query_normalized = query_embedding / query_norm
        else:
            return np.zeros(embeddings.shape[0])
        
        # Normalize all embeddings
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1  # Avoid division by zero
        embeddings_normalized = embeddings / norms
        
        # Calculate dot product (cosine similarity since embeddings are normalized)
        similarities = np.dot(embeddings_normalized, query_normalized)
        
        return similarities
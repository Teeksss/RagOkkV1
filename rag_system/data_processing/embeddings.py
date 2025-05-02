"""
Embedding generation utilities.
"""
import logging
import os
import pickle
from typing import List, Dict, Any, Optional, Union
import numpy as np

logger = logging.getLogger(__name__)

class SentenceEmbedder:
    """
    Class for generating embeddings from text.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedder with specified model.
        
        Args:
            model_name: Name of the embedding model to use
        """
        self.model_name = model_name
        self._model = None
        self._load_model()
    
    def _load_model(self) -> None:
        """Load embedding model."""
        try:
            from sentence_transformers import SentenceTransformer
            
            # Log model loading
            logger.info(f"Loading embedding model: {self.model_name}")
            
            # Load model
            self._model = SentenceTransformer(self.model_name)
            
            # Log model details
            logger.info(f"Model loaded with dimension: {self._model.get_sentence_embedding_dimension()}")
        
        except ImportError:
            logger.error("sentence-transformers not installed. Please install with: pip install sentence-transformers")
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
            Embedding vector
        """
        if not self._model:
            self._load_model()
        
        if not text:
            # Return zero vector for empty text
            return np.zeros(self._model.get_sentence_embedding_dimension(), dtype=np.float32)
        
        # Generate embedding
        try:
            embedding = self._model.encode(text, show_progress_bar=False)
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            # Return zero vector on error
            return np.zeros(self._model.get_sentence_embedding_dimension(), dtype=np.float32)
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of input texts
            
        Returns:
            Array of embedding vectors
        """
        if not self._model:
            self._load_model()
        
        if not texts:
            return np.array([])
        
        # Generate embeddings
        try:
            embeddings = self._model.encode(texts, show_progress_bar=False)
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            # Return empty array on error
            return np.array([])
    
    def get_dimension(self) -> int:
        """
        Get embedding dimension.
        
        Returns:
            Embedding dimension
        """
        if not self._model:
            self._load_model()
        
        return self._model.get_sentence_embedding_dimension()
    
    def similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score between 0 and 1
        """
        if not text1 or not text2:
            return 0.0
        
        # Generate embeddings
        emb1 = self.embed_text(text1)
        emb2 = self.embed_text(text2)
        
        # Calculate cosine similarity
        similarity = self._cosine_similarity(emb1, emb2)
        
        return similarity
    
    def _cosine_similarity(self, vector1: np.ndarray, vector2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vector1: First vector
            vector2: Second vector
            
        Returns:
            Cosine similarity
        """
        norm1 = np.linalg.norm(vector1)
        norm2 = np.linalg.norm(vector2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return np.dot(vector1, vector2) / (norm1 * norm2)
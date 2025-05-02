"""
Multilingual embedding models for vector representations.
"""
import logging
import os
from typing import List, Dict, Any, Optional, Union
import numpy as np
import torch
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class MultilingualEmbedder:
    """
    Embedder for multilingual text using various models.
    """
    
    def __init__(self, 
                 model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
                 device: Optional[str] = None,
                 cache_dir: Optional[str] = None,
                 use_fp16: bool = True):
        """
        Initialize multilingual embedder.
        
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
        
        # List of supported languages and their model mapping
        self.supported_languages = {
            "en": "paraphrase-MiniLM-L6-v2",  # English
            "de": "paraphrase-multilingual-MiniLM-L12-v2",  # German
            "fr": "paraphrase-multilingual-MiniLM-L12-v2",  # French
            "es": "paraphrase-multilingual-MiniLM-L12-v2",  # Spanish
            "tr": "paraphrase-multilingual-MiniLM-L12-v2",  # Turkish
            "it": "paraphrase-multilingual-MiniLM-L12-v2",  # Italian
            "nl": "paraphrase-multilingual-MiniLM-L12-v2",  # Dutch
            "pt": "paraphrase-multilingual-MiniLM-L12-v2",  # Portuguese
            "zh": "paraphrase-multilingual-MiniLM-L12-v2",  # Chinese
            "ar": "paraphrase-multilingual-MiniLM-L12-v2",  # Arabic
            "ru": "paraphrase-multilingual-MiniLM-L12-v2",  # Russian
            "ja": "paraphrase-multilingual-MiniLM-L12-v2",  # Japanese
            "ko": "paraphrase-multilingual-MiniLM-L12-v2",  # Korean
            "hi": "paraphrase-multilingual-MiniLM-L12-v2",  # Hindi
            "default": "paraphrase-multilingual-MiniLM-L12-v2"  # Default multilingual model
        }
        
        # Language-specific models (loaded on demand)
        self.language_models = {}
        
        # Load default model
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
            logger.info(f"Loading multilingual embedding model: {self.model_name} on {self.device}")
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
    
    def _get_model_for_language(self, language_code: str):
        """
        Get appropriate model for a language.
        
        Args:
            language_code: ISO language code
            
        Returns:
            Embedding model for the language
        """
        from sentence_transformers import SentenceTransformer
        
        language_code = language_code.lower()
        
        # If model for this language is already loaded, return it
        if language_code in self.language_models:
            return self.language_models[language_code]
        
        # Get appropriate model name for language
        if language_code in self.supported_languages:
            model_name = self.supported_languages[language_code]
        else:
            # Use default multilingual model for unsupported languages
            logger.warning(f"Language {language_code} not specifically supported, using default multilingual model")
            model_name = self.supported_languages["default"]
        
        # Check if this is the same as our default model
        if model_name == self.model_name:
            return self.model
        
        # Load language-specific model
        try:
            logger.info(f"Loading language-specific model for {language_code}: {model_name}")
            
            # Configure model path
            model_kwargs = {}
            if self.cache_dir:
                model_kwargs["cache_folder"] = self.cache_dir
            
            # Load model
            model = SentenceTransformer(model_name, device=self.device, **model_kwargs)
            
            # Use half precision if requested and supported
            if self.use_fp16 and self.device == "cuda" and torch.cuda.is_available():
                model.half()
            
            # Cache model
            self.language_models[language_code] = model
            
            return model
        
        except Exception as e:
            logger.error(f"Error loading language-specific model for {language_code}: {str(e)}")
            # Fall back to default model
            return self.model
    
    def embed_text(self, 
                  text: str, 
                  language: Optional[str] = None) -> np.ndarray:
        """
        Generate embedding for text.
        
        Args:
            text: Input text
            language: Language code (optional)
            
        Returns:
            Text embedding
        """
        if not text or not text.strip():
            # Return zero vector for empty text
            return np.zeros(self.embedding_dim, dtype=np.float32)
        
        try:
            # Get appropriate model
            model = self.model
            if language:
                model = self._get_model_for_language(language)
            
            # Generate embedding
            with torch.no_grad():
                embedding = model.encode(text, convert_to_numpy=True, show_progress_bar=False)
            
            return embedding
        
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            # Return zero vector on error
            return np.zeros(self.embedding_dim, dtype=np.float32)
    
    def embed_batch(self, 
                   texts: List[str], 
                   language: Optional[str] = None,
                   batch_size: int = 32) -> np.ndarray:
        """
        Generate embeddings for a batch of texts.
        
        Args:
            texts: List of input texts
            language: Language code (optional)
            batch_size: Batch size for processing
            
        Returns:
            Array of embeddings
        """
        if not texts:
            return np.array([])
        
        # Filter empty texts and replace with space to avoid errors
        processed_texts = [text if text and text.strip() else " " for text in texts]
        
        try:
            # Get appropriate model
            model = self.model
            if language:
                model = self._get_model_for_language(language)
            
            # Generate embeddings
            with torch.no_grad():
                embeddings = model.encode(
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
    
    def embed_chunks_with_metadata(self, 
                                 chunks: List[Dict[str, Any]],
                                 text_key: str = "content",
                                 language_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Generate embeddings for chunks with metadata.
        
        Args:
            chunks: List of chunk dictionaries
            text_key: Key for text content in chunks
            language_key: Key for language in metadata
            
        Returns:
            List of chunks with embeddings
        """
        # Prepare texts and track original indices
        texts = []
        languages = []
        indices = []
        
        for i, chunk in enumerate(chunks):
            if text_key in chunk:
                text = chunk[text_key]
                language = None
                
                # Get language if specified
                if language_key and language_key in chunk:
                    language = chunk[language_key]
                
                texts.append(text)
                languages.append(language)
                indices.append(i)
        
        # Group by language for efficient processing
        language_groups = {}
        for i, lang in enumerate(languages):
            if lang not in language_groups:
                language_groups[lang] = {"texts": [], "indices": []}
            
            language_groups[lang]["texts"].append(texts[indices[i]])
            language_groups[lang]["indices"].append(indices[i])
        
        # Process each language group
        all_embeddings = {}
        
        for lang, group in language_groups.items():
            # Generate embeddings for this language group
            lang_embeddings = self.embed_batch(group["texts"], language=lang)
            
            # Map embeddings back to original indices
            for j, idx in enumerate(group["indices"]):
                all_embeddings[idx] = lang_embeddings[j]
        
        # Add embeddings to chunks
        result = []
        for i, chunk in enumerate(chunks):
            new_chunk = chunk.copy()
            
            if i in all_embeddings:
                new_chunk["embedding"] = all_embeddings[i]
            
            result.append(new_chunk)
        
        return result
    
    def get_supported_languages(self) -> Dict[str, str]:
        """
        Get dictionary of supported languages.
        
        Returns:
            Dictionary mapping language codes to model names
        """
        return self.supported_languages.copy()
    
    def is_language_supported(self, language_code: str) -> bool:
        """
        Check if language is supported.
        
        Args:
            language_code: ISO language code
            
        Returns:
            Whether language is supported
        """
        return language_code.lower() in self.supported_languages
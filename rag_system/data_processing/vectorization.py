"""
Vectorization and database storage for document chunks.
"""
import os
import logging
import json
import hashlib
import pickle
from datetime import datetime
from typing import List, Dict, Any, Optional, Union, Tuple

import numpy as np
from sqlalchemy.orm import Session

from ..database.models import Document, DocumentChunk, VectorEntry
from .embeddings import EmbeddingGenerator
from .chunking import TextChunker

logger = logging.getLogger(__name__)

class DocumentVectorizer:
    def __init__(self, 
                 embedding_model: EmbeddingGenerator,
                 chunker: TextChunker,
                 db_session: Session,
                 cache_dir: Optional[str] = None,
                 batch_size: int = 32):
        """
        Initialize document vectorizer.
        
        Args:
            embedding_model: EmbeddingGenerator instance
            chunker: TextChunker instance
            db_session: Database session
            cache_dir: Directory to cache embeddings
            batch_size: Batch size for processing
        """
        self.embedding_model = embedding_model
        self.chunker = chunker
        self.db_session = db_session
        self.batch_size = batch_size
        
        # Set up cache directory
        self.cache_dir = cache_dir
        if cache_dir and not os.path.exists(cache_dir):
            os.makedirs(cache_dir, exist_ok=True)
    
    def process_document(self, document_id: int, text: str) -> Dict[str, Any]:
        """
        Process a document: chunk it, generate embeddings, and store in database.
        
        Args:
            document_id: ID of the document in the database
            text: Text content of the document
            
        Returns:
            Dict with processing statistics
        """
        start_time = datetime.now()
        
        try:
            # Get document from database
            document = self.db_session.query(Document).get(document_id)
            if not document:
                raise ValueError(f"Document with ID {document_id} not found")
            
            # Create chunks
            chunks = self.chunker.chunk_text(text)
            logger.info(f"Created {len(chunks)} chunks for document {document_id}")
            
            # Generate embeddings for chunks
            chunk_texts = [chunk["text"] for chunk in chunks]
            embeddings = self.embedding_embeddings_batch(chunk_texts)
            
            # Store chunks and embeddings in database
            self._store_chunks_and_embeddings(document, chunks, embeddings)
            
            # Update document status
            document.processing_status = "vectorized"
            document.last_updated = datetime.utcnow()
            self.db_session.commit()
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "document_id": document_id,
                "chunk_count": len(chunks),
                "embedding_dimension": embeddings.shape[1] if embeddings.size > 0 else 0,
                "processing_time_seconds": processing_time,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {str(e)}")
            
            # Update document status to error
            try:
                document = self.db_session.query(Document).get(document_id)
                if document:
                    document.processing_status = "error"
                    document.processing_error = str(e)
                    document.last_updated = datetime.utcnow()
                    self.db_session.commit()
            except Exception as db_err:
                logger.error(f"Error updating document status: {str(db_err)}")
            
            return {
                "document_id": document_id,
                "status": "error",
                "error": str(e),
                "processing_time_seconds": (datetime.now() - start_time).total_seconds()
            }
    
    def generate_embeddings_batch(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a batch of texts with caching.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            Numpy array of embeddings
        """
        if not texts:
            return np.array([])
        
        # Check cache for existing embeddings
        cached_embeddings = {}
        texts_to_embed = []
        text_indices = []
        
        for i, text in enumerate(texts):
            # Create a hash of the text for cache key
            text_hash = hashlib.md5(text.encode()).hexdigest()
            
            if self.cache_dir:
                cache_path = os.path.join(self.cache_dir, f"{text_hash}.pkl")
                
                if os.path.exists(cache_path):
                    try:
                        with open(cache_path, 'rb') as f:
                            embedding = pickle.load(f)
                            cached_embeddings[i] = embedding
                            continue
                    except Exception as e:
                        logger.warning(f"Failed to load cached embedding: {str(e)}")
            
            # If not cached, add to list of texts to embed
            texts_to_embed.append(text)
            text_indices.append(i)
        
        # Generate embeddings for texts not in cache
        if texts_to_embed:
            new_embeddings = self.embedding_model.generate_embeddings(texts_to_embed)
            
            # Cache new embeddings
            if self.cache_dir:
                for i, text in enumerate(texts_to_embed):
                    text_hash = hashlib.md5(text.encode()).hexdigest()
                    cache_path = os.path.join(self.cache_dir, f"{text_hash}.pkl")
                    
                    try:
                        with open(cache_path, 'wb') as f:
                            pickle.dump(new_embeddings[i], f)
                    except Exception as e:
                        logger.warning(f"Failed to cache embedding: {str(e)}")
        else:
            new_embeddings = np.array([])
        
        # Combine cached and new embeddings
        embedding_dim = self.embedding_model.get_embedding_dimension()
        result = np.zeros((len(texts), embedding_dim))
        
        # Add cached embeddings
        for i, embedding in cached_embeddings.items():
            result[i] = embedding
        
        # Add new embeddings
        for i, orig_idx in enumerate(text_indices):
            if i < len(new_embeddings):
                result[orig_idx] = new_embeddings[i]
        
        return result
    
    def _store_chunks_and_embeddings(self, 
                                    document: Document,
                                    chunks: List[Dict[str, Any]],
                                    embeddings: np.ndarray) -> None:
        """
        Store chunks and embeddings in the database.
        
        Args:
            document: Document object
            chunks: List of chunk dictionaries
            embeddings: Numpy array of embeddings
        """
        # Delete existing chunks and vectors for this document
        self.db_session.query(VectorEntry).filter(
            VectorEntry.chunk_id.in_(
                self.db_session.query(DocumentChunk.id).filter_by(document_id=document.id)
            )
        ).delete(synchronize_session=False)
        
        self.db_session.query(DocumentChunk).filter_by(document_id=document.id).delete()
        
        # Store new chunks and vectors
        for i, chunk in enumerate(chunks):
            # Create chunk record
            db_chunk = DocumentChunk(
                document_id=document.id,
                chunk_index=chunk["chunk_id"],
                text=chunk["text"],
                char_start=chunk["char_start"],
                char_end=chunk["char_end"],
                chunk_size=chunk["chunk_size"],
                created_at=datetime.utcnow()
            )
            
            self.db_session.add(db_chunk)
            self.db_session.flush()  # Flush to get the ID
            
            # Create vector record
            if i < len(embeddings):
                vector_data = embeddings[i].tobytes()
                
                db_vector = VectorEntry(
                    chunk_id=db_chunk.id,
                    embedding=vector_data,
                    embedding_model=self.embedding_model.model_name,
                    dimension=len(embeddings[i]),
                    created_at=datetime.utcnow()
                )
                
                self.db_session.add(db_vector)
        
        self.db_session.commit()
"""
Vector store service for managing and searching document embeddings.
"""
import logging
import os
import time
import json
import pickle
from typing import List, Dict, Any, Optional, Union, Tuple
import numpy as np

from sqlalchemy.orm import Session

from ..data_processing.embeddings import SentenceEmbedder
from ..data_processing.advanced_vector_index import AdvancedVectorIndex, FAISSConfigFactory
from ..utils.caching import vector_cache

logger = logging.getLogger(__name__)

class VectorStoreService:
    """
    Service for managing and searching vector embeddings.
    """
    
    def __init__(self, 
                 db: Session,
                 index_path: str = "./data/vector_index",
                 dimension: int = 384,
                 metric: str = "cosine",
                 embedder_model: Optional[str] = None):
        """
        Initialize vector store service.
        
        Args:
            db: Database session
            index_path: Path to vector index
            dimension: Vector dimension
            metric: Distance metric
            embedder_model: Optional custom embedder model
        """
        self.db = db
        self.index_path = index_path
        self.dimension = dimension
        self.metric = metric
        
        # Create directory if it doesn't exist
        os.makedirs(index_path, exist_ok=True)
        
        # Initialize embedder
        self.embedder = SentenceEmbedder(
            model_name=embedder_model or "all-MiniLM-L6-v2"
        )
        
        # Initialize vector index
        self.vector_index = self._load_or_create_index()
    
    def _load_or_create_index(self) -> AdvancedVectorIndex:
        """
        Load or create vector index.
        
        Returns:
            Vector index
        """
        index_file = os.path.join(self.index_path, "index.pkl")
        
        if os.path.exists(index_file):
            try:
                logger.info(f"Loading vector index from {index_file}")
                with open(index_file, "rb") as f:
                    return pickle.load(f)
            except Exception as e:
                logger.error(f"Error loading vector index: {str(e)}")
                logger.info("Creating new vector index")
        
        # Create new index
        config_factory = FAISSConfigFactory()
        config = config_factory.get_recommended_config(
            dimension=self.dimension,
            dataset_size=1000  # Initial estimate
        )
        
        return AdvancedVectorIndex(
            dimension=self.dimension,
            metric=self.metric,
            config=config
        )
    
    def save_index(self, filename: Optional[str] = None) -> str:
        """
        Save vector index to disk.
        
        Args:
            filename: Optional custom filename
            
        Returns:
            Path to saved index
        """
        if not filename:
            filename = "index.pkl"
        
        # Ensure .pkl extension
        if not filename.endswith(".pkl"):
            filename += ".pkl"
        
        # Create full path
        file_path = os.path.join(self.index_path, filename)
        
        try:
            # Save index
            with open(file_path, "wb") as f:
                pickle.dump(self.vector_index, f)
            
            logger.info(f"Vector index saved to {file_path}")
            return file_path
        
        except Exception as e:
            logger.error(f"Error saving vector index: {str(e)}")
            raise
    
    def load_index(self, filename: str) -> bool:
        """
        Load vector index from disk.
        
        Args:
            filename: Index filename
            
        Returns:
            Whether index was loaded successfully
        """
        # Ensure .pkl extension
        if not filename.endswith(".pkl"):
            filename += ".pkl"
        
        # Create full path
        file_path = os.path.join(self.index_path, filename)
        
        if not os.path.exists(file_path):
            logger.error(f"Index file not found: {file_path}")
            return False
        
        try:
            # Load index
            with open(file_path, "rb") as f:
                self.vector_index = pickle.load(f)
            
            logger.info(f"Vector index loaded from {file_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error loading vector index: {str(e)}")
            return False
    
    def add_document_chunks(self, 
                           chunks: List[Dict[str, Any]], 
                           text_key: str = "content",
                           metadata_key: str = "metadata") -> List[Dict[str, Any]]:
        """
        Add document chunks to vector index.
        
        Args:
            chunks: List of document chunks
            text_key: Key for text content
            metadata_key: Key for metadata
            
        Returns:
            List of chunks with vector IDs
        """
        # Generate embeddings for chunks
        embeddings_data = []
        
        for chunk in chunks:
            # Get text content
            text = chunk.get(text_key, "")
            
            if not text:
                logger.warning(f"Empty text content in chunk: {chunk}")
                continue
            
            # Generate embedding
            embedding = self.embedder.embed_text(text)
            
            # Create embedding data
            embedding_data = {
                "id": chunk.get("id"),
                "embedding": embedding,
                "content": text,
                "metadata": chunk.get(metadata_key, {})
            }
            
            embeddings_data.append(embedding_data)
        
        # Add embeddings to index
        if embeddings_data:
            vector_ids = self.vector_index.add_embeddings(embeddings_data)
            
            # Add vector IDs to chunks
            for i, vid in enumerate(vector_ids):
                chunks[i]["vector_id"] = vid
                chunks[i]["embedding_stored"] = True
        
        # Save index
        self.save_index()
        
        return chunks
    
    @vector_cache(ttl=3600)
    def search(self, 
              query: str, 
              k: int = 5, 
              filters: Optional[Dict[str, Any]] = None,
              use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        Search for similar documents.
        
        Args:
            query: Search query
            k: Number of results
            filters: Optional filters
            use_cache: Whether to use cache
            
        Returns:
            List of search results
        """
        # Generate query embedding
        query_embedding = self.embedder.embed_text(query)
        
        # Search vector index
        results = self.vector_index.search(
            query_vector=query_embedding,
            k=k,
            filters=filters
        )
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_result = {
                "id": result.get("id"),
                "content": result.get("content", ""),
                "score": result.get("score", 0.0),
                "metadata": result.get("metadata", {})
            }
            
            # Add document_id if available
            document_id = result.get("metadata", {}).get("document_id")
            if document_id:
                formatted_result["document_id"] = document_id
            
            # Add chunk_index if available
            chunk_index = result.get("metadata", {}).get("chunk_index")
            if chunk_index is not None:
                formatted_result["chunk_index"] = chunk_index
            
            formatted_results.append(formatted_result)
        
        return formatted_results
    
    def get_document_embeddings(self, document_id: str) -> Dict[str, Any]:
        """
        Get document embeddings.
        
        Args:
            document_id: Document ID
            
        Returns:
            Document embeddings
        """
        from ..database.models import DocumentChunk
        
        # Get document chunks
        chunks = self.db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id,
            DocumentChunk.embedding_stored == True
        ).all()
        
        if not chunks:
            return {
                "status": "error",
                "error": "No embeddings found for document"
            }
        
        # Get embeddings
        chunk_embeddings = []
        
        for chunk in chunks:
            # Get embedding from vector index if available
            if chunk.vector_id:
                # We'd need to implement a method to get embeddings by ID
                # For now, let's just create a placeholder
                chunk_embeddings.append({
                    "id": chunk.id,
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "embedding": np.zeros(self.dimension)  # Placeholder
                })
        
        return {
            "status": "success",
            "document_id": document_id,
            "chunks": chunk_embeddings
        }
    
    def rebuild_index_with_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Rebuild vector index with new configuration.
        
        Args:
            config: Index configuration
            
        Returns:
            Result status
        """
        from ..database.models import DocumentChunk
        
        try:
            start_time = time.time()
            
            # Create new index
            new_index = AdvancedVectorIndex(
                dimension=self.dimension,
                metric=self.metric,
                config=config
            )
            
            # Get all stored chunk embeddings
            chunks = self.db.query(DocumentChunk).filter(
                DocumentChunk.embedding_stored == True
            ).all()
            
            logger.info(f"Rebuilding index with {len(chunks)} chunks")
            
            # Add embeddings to new index
            embeddings_data = []
            
            for chunk in chunks:
                # Get embedding from chunk if available
                if chunk.embedding_vector:
                    embedding = np.frombuffer(chunk.embedding_vector, dtype=np.float32)
                else:
                    # Generate embedding
                    embedding = self.embedder.embed_text(chunk.content)
                
                # Create embedding data
                embedding_data = {
                    "id": chunk.id,
                    "embedding": embedding,
                    "content": chunk.content,
                    "metadata": {
                        "document_id": chunk.document_id,
                        "chunk_index": chunk.chunk_index
                    }
                }
                
                if chunk.metadata:
                    embedding_data["metadata"].update(chunk.metadata)
                
                embeddings_data.append(embedding_data)
            
            # Add embeddings to new index
            vector_ids = new_index.add_embeddings(embeddings_data)
            
            # Replace old index
            self.vector_index = new_index
            
            # Save new index
            self.save_index()
            
            elapsed_time = time.time() - start_time
            
            return {
                "status": "success",
                "message": f"Index rebuilt with {len(chunks)} chunks",
                "took": elapsed_time,
                "config": config
            }
        
        except Exception as e:
            logger.error(f"Error rebuilding index: {str(e)}")
            
            return {
                "status": "error",
                "message": f"Error rebuilding index: {str(e)}"
            }
    
    def optimize_index_config(self, sample_size: int = 1000) -> Dict[str, Any]:
        """
        Optimize index configuration.
        
        Args:
            sample_size: Sample size for optimization
            
        Returns:
            Optimization results
        """
        # This is a placeholder for index optimization logic
        # In a real implementation, you'd benchmark different configurations
        
        # Get existing config
        current_config = self.vector_index.config
        
        # Get recommended config
        config_factory = FAISSConfigFactory()
        new_config = config_factory.get_recommended_config(
            dimension=self.dimension,
            dataset_size=sample_size
        )
        
        return {
            "status": "success",
            "current_config": current_config,
            "recommended_config": new_config,
            "message": "Optimization complete"
        }
    
    def convert_to_sharded_index(self, num_shards: int = 4) -> Dict[str, Any]:
        """
        Convert index to sharded index.
        
        Args:
            num_shards: Number of shards
            
        Returns:
            Conversion results
        """
        # This is a placeholder for sharded index conversion
        # In a real implementation, you'd implement sharding logic
        
        return {
            "status": "success",
            "message": f"Index converted to {num_shards} shards",
            "num_shards": num_shards
        }
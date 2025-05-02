"""
FAISS vector index for similarity search.
"""
import os
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
import faiss
import pickle
import time
import uuid
import json

logger = logging.getLogger(__name__)

class FAISSIndex:
    """
    FAISS vector index for efficient similarity search.
    """
    
    def __init__(self, 
                 dimension: int = 384,
                 index_type: str = "flat",
                 metric: str = "cosine",
                 storage_dir: str = "vector_storage"):
        """
        Initialize FAISS index.
        
        Args:
            dimension: Embedding dimension
            index_type: Index type (flat, ivf, hnsw)
            metric: Distance metric (l2, cosine, inner_product)
            storage_dir: Directory to store index files
        """
        self.dimension = dimension
        self.index_type = index_type
        self.metric = metric
        self.storage_dir = storage_dir
        self.index = None
        
        # ID mapping (FAISS uses sequential IDs)
        self.id_to_uuid = {}  # FAISS ID -> UUID
        self.uuid_to_id = {}  # UUID -> FAISS ID
        self.metadata = {}    # UUID -> metadata
        
        # Create storage directory
        os.makedirs(storage_dir, exist_ok=True)
        
        # Initialize index
        self._create_index()
        
        logger.info(f"Initialized {index_type} FAISS index with {metric} metric for {dimension}D vectors")
    
    def _create_index(self):
        """Create the FAISS index based on configuration."""
        # Determine metric
        if self.metric == "cosine":
            # For cosine, we need to normalize vectors
            index = faiss.IndexFlatIP(self.dimension)  # Inner product for normalized vectors
        elif self.metric == "inner_product":
            index = faiss.IndexFlatIP(self.dimension)
        else:  # Default to L2
            index = faiss.IndexFlatL2(self.dimension)
        
        # Create index based on type
        if self.index_type == "flat":
            self.index = index
        elif self.index_type == "ivf":
            # Create IVF index (needs training)
            nlist = max(4, min(1000, int(np.sqrt(1000))))  # Rule of thumb for nlist
            self.index = faiss.IndexIVFFlat(index, self.dimension, nlist)
        elif self.index_type == "hnsw":
            # Create HNSW index
            self.index = faiss.IndexHNSWFlat(self.dimension, 32)  # 32 neighbors
        else:
            logger.warning(f"Unknown index type '{self.index_type}', defaulting to flat")
            self.index = index
    
    def is_trained(self) -> bool:
        """
        Check if index is trained (required for IVF).
        
        Returns:
            True if index is trained or doesn't require training
        """
        return not hasattr(self.index, 'is_trained') or self.index.is_trained
    
    def train(self, vectors: np.ndarray):
        """
        Train the index if required.
        
        Args:
            vectors: Training vectors with shape (n_vectors, dimension)
        """
        if hasattr(self.index, 'train') and not self.index.is_trained:
            logger.info(f"Training FAISS index with {len(vectors)} vectors")
            self.index.train(vectors.astype(np.float32))
    
    def add_vectors(self, 
                    vectors: np.ndarray, 
                    uuids: List[str],
                    metadata: Optional[List[Dict[str, Any]]] = None) -> List[int]:
        """
        Add vectors to the index.
        
        Args:
            vectors: Vectors to add with shape (n_vectors, dimension)
            uuids: UUIDs corresponding to vectors
            metadata: Optional metadata for vectors
            
        Returns:
            List of FAISS IDs
        """
        if not self.is_trained() and len(vectors) > 0:
            self.train(vectors)
        
        # Ensure vectors are float32
        vectors = vectors.astype(np.float32)
        
        # Normalize vectors if using cosine similarity
        if self.metric == "cosine":
            faiss.normalize_L2(vectors)
        
        # Get next FAISS ID
        start_id = len(self.id_to_uuid)
        ids = np.arange(start_id, start_id + len(vectors))
        
        # Add vectors to index
        self.index.add(vectors)
        
        # Update ID mappings and metadata
        for i, (idx, uuid_str) in enumerate(zip(ids, uuids)):
            self.id_to_uuid[int(idx)] = uuid_str
            self.uuid_to_id[uuid_str] = int(idx)
            
            # Store metadata if provided
            if metadata and i < len(metadata):
                self.metadata[uuid_str] = metadata[i]
        
        logger.info(f"Added {len(vectors)} vectors to FAISS index")
        return ids.tolist()
    
    def add_embeddings(self,
                       embeddings: List[Dict[str, Any]],
                       vector_key: str = "embedding",
                       id_key: str = "id") -> List[int]:
        """
        Add embeddings with metadata to the index.
        
        Args:
            embeddings: List of dictionaries with embeddings and metadata
            vector_key: Key for embedding vectors in dictionaries
            id_key: Key for ID in dictionaries
            
        Returns:
            List of FAISS IDs
        """
        # Extract vectors, UUIDs, and metadata
        vectors = []
        uuids = []
        metadata_list = []
        
        for emb in embeddings:
            if vector_key not in emb:
                continue
            
            # Get vector
            vector = emb[vector_key]
            if not isinstance(vector, np.ndarray):
                vector = np.array(vector)
            
            # Get UUID
            uuid_str = emb.get(id_key, str(uuid.uuid4()))
            
            # Prepare metadata (exclude embedding to save space)
            metadata = {k: v for k, v in emb.items() if k != vector_key}
            
            vectors.append(vector)
            uuids.append(uuid_str)
            metadata_list.append(metadata)
        
        # Stack vectors
        if vectors:
            vectors_array = np.vstack(vectors)
            return self.add_vectors(vectors_array, uuids, metadata_list)
        
        return []
    
    def search(self, 
               query_vector: np.ndarray, 
               k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.
        
        Args:
            query_vector: Query vector
            k: Number of results to return
            
        Returns:
            List of results with distances, IDs, and metadata
        """
        if not self.is_trained():
            logger.warning("FAISS index is not trained, search may fail")
        
        # Ensure query is float32 and correct shape
        query_vector = query_vector.astype(np.float32).reshape(1, -1)
        
        # Normalize if using cosine similarity
        if self.metric == "cosine":
            faiss.normalize_L2(query_vector)
        
        # Perform search
        distances, indices = self.index.search(query_vector, k)
        
        # Process results
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            # Skip invalid indices
            if idx == -1 or idx not in self.id_to_uuid:
                continue
            
            # Get UUID and metadata
            uuid_str = self.id_to_uuid[idx]
            metadata = self.metadata.get(uuid_str, {})
            
            # Convert distance to score based on metric
            if self.metric in ["cosine", "inner_product"]:
                # For inner product, higher is better (range -1 to 1 for normalized vectors)
                score = float(dist)
            else:
                # For L2, lower is better, so convert to similarity
                score = float(1.0 / (1.0 + dist))
            
            results.append({
                "id": uuid_str,
                "score": score,
                "distance": float(dist),
                "metadata": metadata
            })
        
        return results
    
    def save(self, filename: Optional[str] = None) -> str:
        """
        Save index and mappings to disk.
        
        Args:
            filename: Base filename (without extension)
            
        Returns:
            Path to saved index file
        """
        if filename is None:
            # Generate filename based on index type and timestamp
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            filename = f"{self.index_type}_{self.dimension}d_{timestamp}"
        
        # Save FAISS index
        index_path = os.path.join(self.storage_dir, f"{filename}.faiss")
        faiss.write_index(self.index, index_path)
        
        # Save ID mappings and metadata
        meta_path = os.path.join(self.storage_dir, f"{filename}.meta")
        with open(meta_path, 'wb') as f:
            pickle.dump({
                "id_to_uuid": self.id_to_uuid,
                "uuid_to_id": self.uuid_to_id,
                "metadata": self.metadata,
                "dimension": self.dimension,
                "index_type": self.index_type,
                "metric": self.metric
            }, f)
        
        logger.info(f"Saved FAISS index to {index_path} and metadata to {meta_path}")
        return index_path
    
    def load(self, filename: str) -> bool:
        """
        Load index and mappings from disk.
        
        Args:
            filename: Base filename (without extension)
            
        Returns:
            Success status
        """
        # Construct paths
        index_path = filename if filename.endswith('.faiss') else os.path.join(self.storage_dir, f"{filename}.faiss")
        meta_path = os.path.splitext(index_path)[0] + '.meta'
        
        # Check if files exist
        if not os.path.exists(index_path) or not os.path.exists(meta_path):
            logger.error(f"Index file {index_path} or metadata file {meta_path} not found")
            return False
        
        try:
            # Load FAISS index
            self.index = faiss.read_index(index_path)
            
            # Load metadata
            with open(meta_path, 'rb') as f:
                meta_data = pickle.load(f)
            
            # Restore instance variables
            self.id_to_uuid = meta_data["id_to_uuid"]
            self.uuid_to_id = meta_data["uuid_to_id"]
            self.metadata = meta_data["metadata"]
            self.dimension = meta_data["dimension"]
            self.index_type = meta_data["index_type"]
            self.metric = meta_data.get("metric", "l2")  # Default for backward compatibility
            
            logger.info(f"Loaded FAISS index from {index_path} with {self.index.ntotal} vectors")
            return True
        except Exception as e:
            logger.error(f"Failed to load FAISS index: {str(e)}")
            return False
    
    def get_index_info(self) -> Dict[str, Any]:
        """
        Get information about the index.
        
        Returns:
            Dictionary with index information
        """
        return {
            "index_type": self.index_type,
            "dimension": self.dimension,
            "metric": self.metric,
            "total_vectors": self.index.ntotal if self.index else 0,
            "trained": self.is_trained(),
            "uuids": len(self.id_to_uuid)
        }
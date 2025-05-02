"""
Advanced vector indexing with FAISS.
"""
import logging
import os
import time
import pickle
import json
import uuid
import tempfile
from typing import List, Dict, Any, Optional, Union, Tuple
import numpy as np

logger = logging.getLogger(__name__)

class FAISSConfigFactory:
    """
    Factory for creating FAISS index configurations.
    """
    
    def __init__(self):
        """Initialize FAISS config factory."""
        pass
    
    def get_available_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        Get available index configurations.
        
        Returns:
            Dictionary of index configurations
        """
        return {
            "flat": {
                "description": "Flat index (exact search, slow for large datasets)",
                "parameters": {}
            },
            "ivf": {
                "description": "IVF index (approximate search, good for medium-sized datasets)",
                "parameters": {
                    "nlist": "Number of clusters (16-1024)",
                    "nprobe": "Number of clusters to search (1-nlist)"
                }
            },
            "ivfpq": {
                "description": "IVF with Product Quantization (very efficient for large datasets)",
                "parameters": {
                    "nlist": "Number of clusters (16-1024)",
                    "m": "Number of subquantizers (1-dimension/2)",
                    "nbits": "Number of bits per subquantizer (8-16)",
                    "nprobe": "Number of clusters to search (1-nlist)"
                }
            },
            "hnsw": {
                "description": "Hierarchical Navigable Small World (fast and accurate)",
                "parameters": {
                    "M": "Number of connections per layer (12-64)",
                    "efConstruction": "Construction-time exploration factor (40-800)",
                    "efSearch": "Search-time exploration factor (40-800)"
                }
            }
        }
    
    def get_recommended_config(self, dimension: int, dataset_size: int) -> Dict[str, Any]:
        """
        Get recommended index configuration based on dataset size.
        
        Args:
            dimension: Vector dimension
            dataset_size: Estimated dataset size
            
        Returns:
            Recommended index configuration
        """
        if dataset_size < 10000:
            # For small datasets, use flat index
            return {
                "index_type": "flat",
                "metric": "cosine",
                "parameters": {}
            }
        elif dataset_size < A=100000:
            # For medium datasets, use IVF
            nlist = min(max(dataset_size // 50, 16), 1024)
            return {
                "index_type": "ivf",
                "metric": "cosine",
                "parameters": {
                    "nlist": nlist,
                    "nprobe": min(nlist // 4, 64)
                }
            }
        else:
            # For large datasets, use IVFPQ
            nlist = min(max(dataset_size // 100, 64), 4096)
            
            # Calculate m (number of subquantizers)
            # m should divide dimension
            m = dimension // 2
            
            # Find largest divisor of dimension that is <= m
            while m > 1:
                if dimension % m == 0:
                    break
                m -= 1
            
            return {
                "index_type": "ivfpq",
                "metric": "cosine",
                "parameters": {
                    "nlist": nlist,
                    "m": m,
                    "nbits": 8,
                    "nprobe": min(nlist // 4, 64)
                }
            }


class AdvancedVectorIndex:
    """
    Advanced vector index using FAISS.
    """
    
    def __init__(self, 
                 dimension: int = 384,
                 metric: str = "cosine",
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize advanced vector index.
        
        Args:
            dimension: Vector dimension
            metric: Distance metric (cosine, l2, ip)
            config: Index configuration
        """
        self.dimension = dimension
        self.metric = metric
        self.config = config or {}
        
        # UUIDs to IDs mapping
        self.uuid_to_id = {}
        
        # Metadata storage
        self.metadata = {}
        
        # Performance tracking
        self.search_times = []
        
        # Initialize FAISS index
        self._initialize_index()
    
    def _initialize_index(self) -> None:
        """Initialize FAISS index."""
        try:
            import faiss
            
            # Determine index type
            index_type = self.config.get("index_type", "flat")
            
            # Convert metric to FAISS metric
            if self.metric == "cosine":
                faiss_metric = faiss.METRIC_INNER_PRODUCT
                self.normalize = True
            elif self.metric == "l2":
                faiss_metric = faiss.METRIC_L2
                self.normalize = False
            elif self.metric == "ip":
                faiss_metric = faiss.METRIC_INNER_PRODUCT
                self.normalize = False
            else:
                logger.warning(f"Unknown metric: {self.metric}, using cosine")
                faiss_metric = faiss.METRIC_INNER_PRODUCT
                self.normalize = True
            
            # Create index based on type
            if index_type == "flat":
                self.index = faiss.IndexFlatIP(self.dimension) if faiss_metric == faiss.METRIC_INNER_PRODUCT else faiss.IndexFlatL2(self.dimension)
            
            elif index_type == "ivf":
                # Get parameters
                nlist = self.config.get("parameters", {}).get("nlist", 100)
                
                # Create quantizer
                quantizer = faiss.IndexFlatIP(self.dimension) if faiss_metric == faiss.METRIC_INNER_PRODUCT else faiss.IndexFlatL2(self.dimension)
                
                # Create IVF index
                self.index = faiss.IndexIVFFlat(quantizer, self.dimension, nlist, faiss_metric)
                
                # Index needs to be trained before adding vectors
                self.needs_training = True
            
            elif index_type == "ivfpq":
                # Get parameters
                nlist = self.config.get("parameters", {}).get("nlist", 100)
                m = self.config.get("parameters", {}).get("m", self.dimension // 2)
                nbits = self.config.get("parameters", {}).get("nbits", 8)
                
                # Create quantizer
                quantizer = faiss.IndexFlatIP(self.dimension) if faiss_metric == faiss.METRIC_INNER_PRODUCT else faiss.IndexFlatL2(self.dimension)
                
                # Create IVF-PQ index
                self.index = faiss.IndexIVFPQ(quantizer, self.dimension, nlist, m, nbits, faiss_metric)
                
                # Index needs to be trained before adding vectors
                self.needs_training = True
            
            elif index_type == "hnsw":
                # Get parameters
                M = self.config.get("parameters", {}).get("M", 32)
                efConstruction = self.config.get("parameters", {}).get("efConstruction", 200)
                
                # Create HNSW index
                self.index = faiss.IndexHNSWFlat(self.dimension, M, faiss_metric)
                self.index.hnsw.efConstruction = efConstruction
                
                # HNSW doesn't need training
                self.needs_training = False
            
            else:
                logger.warning(f"Unknown index type: {index_type}, using flat index")
                self.index = faiss.IndexFlatIP(self.dimension) if faiss_metric == faiss.METRIC_INNER_PRODUCT else faiss.IndexFlatL2(self.dimension)
                self.needs_training = False
            
            # Store configuration
            self.index_type = index_type
            self.faiss_metric = faiss_metric
            
            # Set search parameters if specified
            if index_type == "ivf" or index_type == "ivfpq":
                nprobe = self.config.get("parameters", {}).get("nprobe")
                if nprobe:
                    self.index.nprobe = nprobe
            
            elif index_type == "hnsw":
                efSearch = self.config.get("parameters", {}).get("efSearch")
                if efSearch:
                    self.index.hnsw.efSearch = efSearch
            
            logger.info(f"Initialized FAISS index of type {index_type} with dimension {self.dimension}")
        
        except ImportError:
            logger.error("FAISS not found. Please install FAISS: pip install faiss-cpu or faiss-gpu")
            raise
    
    def add_embeddings(self, 
                      embeddings: List[Dict[str, Any]],
                      train_if_needed: bool = True) -> List[int]:
        """
        Add embeddings to the index.
        
        Args:
            embeddings: List of embeddings with metadata
            train_if_needed: Whether to train index if needed
            
        Returns:
            List of assigned IDs
        """
        if not embeddings:
            return []
        
        # Extract vectors and metadata
        vectors = []
        uuids = []
        metadata_list = []
        
        for i, item in enumerate(embeddings):
            # Get embedding
            if "embedding" not in item:
                logger.warning(f"Embedding missing for item {i}")
                continue
            
            vector = item["embedding"]
            
            # Convert to numpy array if needed
            if not isinstance(vector, np.ndarray):
                vector = np.array(vector, dtype=np.float32)
            
            # Ensure correct shape
            if vector.shape != (self.dimension,):
                logger.warning(f"Embedding has wrong dimension: {vector.shape} vs {self.dimension}")
                continue
            
            # Normalize if using cosine similarity
            if self.normalize:
                vector = self._normalize_vector(vector)
            
            # Get UUID
            uuid_str = item.get("id", str(uuid.uuid4()))
            
            # Get metadata
            metadata = {
                "id": uuid_str,
                "content": item.get("content", ""),
            }
            
            # Add any other metadata
            if "metadata" in item:
                metadata.update(item["metadata"])
            
            # Add to lists
            vectors.append(vector)
            uuids.append(uuid_str)
            metadata_list.append(metadata)
        
        # Convert vectors to numpy array
        vectors_array = np.array(vectors, dtype=np.float32)
        
        # Train index if needed
        if self.needs_training and train_if_needed and not self.index.is_trained:
            logger.info(f"Training index with {len(vectors)} vectors")
            try:
                self.index.train(vectors_array)
            except Exception as e:
                logger.error(f"Error training index: {str(e)}")
                raise
        
        # Add vectors to index
        try:
            # Get current size
            current_size = self.index.ntotal
            
            # Add vectors
            self.index.add(vectors_array)
            
            # Generate IDs
            ids = list(range(current_size, current_size + len(vectors)))
            
            # Update UUID mapping and metadata
            for i, (uuid_str, metadata) in enumerate(zip(uuids, metadata_list)):
                faiss_id = ids[i]
                self.uuid_to_id[uuid_str] = faiss_id
                self.metadata[faiss_id] = metadata
            
            return ids
        
        except Exception as e:
            logger.error(f"Error adding vectors to index: {str(e)}")
            raise
    
    def search(self, 
              query_vector: Union[List[float], np.ndarray],
              k: int = 5,
              filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.
        
        Args:
            query_vector: Query vector
            k: Number of results
            filters: Metadata filters
            
        Returns:
            List of search results
        """
        start_time = time.time()
        
        # Convert query vector to numpy array if needed
        if not isinstance(query_vector, np.ndarray):
            query_vector = np.array(query_vector, dtype=np.float32)
        
        # Ensure correct shape
        if query_vector.shape != (self.dimension,):
            query_vector = query_vector.reshape(1, -1)
        else:
            query_vector = query_vector.reshape(1, -1)
        
        # Normalize if using cosine similarity
        if self.normalize:
            query_vector = self._normalize_vector(query_vector)
        
        try:
            # Perform search
            scores, indices = self.index.search(query_vector, k)
            
            # Extract results
            results = []
            for i, (idx, score) in enumerate(zip(indices[0], scores[0])):
                # Skip invalid indices
                if idx == -1:
                    continue
                
                # Get metadata
                metadata = self.metadata.get(idx, {})
                
                # Apply filters
                if filters and not self._apply_filters(metadata, filters):
                    continue
                
                # Add to results
                results.append({
                    "id": metadata.get("id"),
                    "score": float(score),
                    "metadata": metadata,
                    "content": metadata.get("content", "")
                })
            
            search_time = time.time() - start_time
            self.search_times.append(search_time)
            
            return results
        
        except Exception as e:
            logger.error(f"Error searching index: {str(e)}")
            return []
    
    def search_by_uuid(self, 
                      uuid_str: str,
                      k: int = 5,
                      filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for similar vectors by UUID.
        
        Args:
            uuid_str: UUID of vector to search for
            k: Number of results
            filters: Metadata filters
            
        Returns:
            List of search results
        """
        # Get FAISS ID
        faiss_id = self.uuid_to_id.get(uuid_str)
        
        if faiss_id is None:
            logger.warning(f"UUID not found: {uuid_str}")
            return []
        
        try:
            import faiss
            
            # Get vector
            vector = faiss.reconstruct(self.index, faiss_id)
            
            # Search
            return self.search(vector, k=k, filters=filters)
        
        except Exception as e:
            logger.error(f"Error searching by UUID: {str(e)}")
            return []
    
    def delete(self, uuids: List[str]) -> bool:
        """
        Delete vectors from index.
        
        Args:
            uuids: List of UUIDs to delete
            
        Returns:
            Success status
        """
        try:
            import faiss
            
            # Check if index supports removal
            if not hasattr(self.index, "remove_ids"):
                logger.warning("This index type doesn't support removal")
                return False
            
            # Convert UUIDs to FAISS IDs
            ids = []
            for uuid_str in uuids:
                faiss_id = self.uuid_to_id.get(uuid_str)
                if faiss_id is not None:
                    ids.append(faiss_id)
            
            if not ids:
                logger.warning("No valid IDs to remove")
                return False
            
            # Create ID array
            id_array = np.array(ids, dtype=np.int64)
            
            # Remove from index
            
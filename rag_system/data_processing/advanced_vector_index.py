"""
Advanced vector indexing with FAISS.
"""
import logging
import os
import time
import json
import pickle
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np

logger = logging.getLogger(__name__)

class FAISSConfigFactory:
    """
    Factory for FAISS index configurations.
    """
    
    def get_recommended_config(self, 
                             dimension: int, 
                             dataset_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Get recommended FAISS index configuration based on dimension and dataset size.
        
        Args:
            dimension: Vector dimension
            dataset_size: Estimated dataset size
            
        Returns:
            FAISS configuration dictionary
        """
        if not dataset_size or dataset_size < 1000:
            # Small dataset: use flat index
            return self.get_flat_config()
        elif dataset_size < 10000:
            # Medium dataset: use IVF index
            return self.get_ivf_config(dimension)
        elif dataset_size < 1000000:
            # Large dataset: use IVF with PQ compression
            return self.get_ivf_pq_config(dimension)
        else:
            # Very large dataset: use HNSW
            return self.get_hnsw_config(dimension)
    
    def get_flat_config(self) -> Dict[str, Any]:
        """
        Get configuration for a flat (exact) index.
        
        Returns:
            FAISS configuration dictionary
        """
        return {
            "index_type": "flat",
            "metric": "cosine",
            "description": "Exact search with cosine similarity"
        }
    
    def get_ivf_config(self, dimension: int) -> Dict[str, Any]:
        """
        Get configuration for an IVF (Inverted File) index.
        
        Args:
            dimension: Vector dimension
            
        Returns:
            FAISS configuration dictionary
        """
        # Determine number of centroids
        nlist = 100  # Default
        
        return {
            "index_type": "ivf",
            "metric": "cosine",
            "nlist": nlist,  # Number of centroids
            "nprobe": 10,    # Number of centroids to visit during search
            "description": "Approximate search with IVF clustering"
        }
    
    def get_ivf_pq_config(self, dimension: int) -> Dict[str, Any]:
        """
        Get configuration for an IVF-PQ (Inverted File with Product Quantization) index.
        
        Args:
            dimension: Vector dimension
            
        Returns:
            FAISS configuration dictionary
        """
        # Determine number of centroids and subquantizers
        nlist = 100  # Default
        
        # Number of sub-quantizers (M) should divide the dimension
        m = dimension // 4
        if m == 0:
            m = 1
        elif dimension % m != 0:
            # Find a divisor of dimension for m
            for i in range(m, 0, -1):
                if dimension % i == 0:
                    m = i
                    break
        
        # Number of bits per subquantizer
        nbits = 8
        
        return {
            "index_type": "ivfpq",
            "metric": "cosine",
            "nlist": nlist,  # Number of centroids
            "nprobe": 10,    # Number of centroids to visit during search
            "m": m,          # Number of subquantizers
            "nbits": nbits,  # Number of bits per subquantizer
            "description": "Approximate search with IVF clustering and PQ compression"
        }
    
    def get_hnsw_config(self, dimension: int) -> Dict[str, Any]:
        """
        Get configuration for an HNSW (Hierarchical Navigable Small World) index.
        
        Args:
            dimension: Vector dimension
            
        Returns:
            FAISS configuration dictionary
        """
        return {
            "index_type": "hnsw",
            "metric": "cosine",
            "M": 32,         # Number of connections per layer
            "efConstruction": 200,  # Size of the dynamic candidate list during construction
            "efSearch": 128,       # Size of the dynamic candidate list during search
            "description": "Approximate search with HNSW graph"
        }


class AdvancedVectorIndex:
    """
    Advanced vector index for efficient similarity search.
    """
    
    def __init__(self, 
                 dimension: int, 
                 metric: str = "cosine", 
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize vector index.
        
        Args:
            dimension: Vector dimension
            metric: Distance metric (cosine, l2, or ip)
            config: Index configuration
        """
        self.dimension = dimension
        self.metric = metric
        self.config = config or FAISSConfigFactory().get_flat_config()
        
        # Data storage
        self.ids: List[str] = []
        self.vectors: List[np.ndarray] = []
        self.id_to_index: Dict[str, int] = {}
        self.metadata: List[Dict[str, Any]] = []
        
        # Initialize index
        self._index = None
        self._initialize_index()
    
    def _initialize_index(self) -> None:
        """Initialize FAISS index."""
        try:
            import faiss
            
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
                logger.warning(f"Unsupported metric: {self.metric}, using cosine")
                faiss_metric = faiss.METRIC_INNER_PRODUCT
                self.normalize = True
            
            # Create index based on configuration
            index_type = self.config.get("index_type", "flat")
            
            if index_type == "flat":
                self._index = faiss.IndexFlatIP(self.dimension) if faiss_metric == faiss.METRIC_INNER_PRODUCT else faiss.IndexFlatL2(self.dimension)
            
            elif index_type == "ivf":
                # IVF index requires a trained quantizer
                quantizer = faiss.IndexFlatIP(self.dimension) if faiss_metric == faiss.METRIC_INNER_PRODUCT else faiss.IndexFlatL2(self.dimension)
                nlist = self.config.get("nlist", 100)
                self._index = faiss.IndexIVFFlat(quantizer, self.dimension, nlist, faiss_metric)
                self._index.nprobe = self.config.get("nprobe", 10)
            
            elif index_type == "ivfpq":
                # IVF with Product Quantization
                quantizer = faiss.IndexFlatIP(self.dimension) if faiss_metric == faiss.METRIC_INNER_PRODUCT else faiss.IndexFlatL2(self.dimension)
                nlist = self.config.get("nlist", 100)
                m = self.config.get("m", self.dimension // 4)
                nbits = self.config.get("nbits", 8)
                self._index = faiss.IndexIVFPQ(quantizer, self.dimension, nlist, m, nbits, faiss_metric)
                self._index.nprobe = self.config.get("nprobe", 10)
            
            elif index_type == "hnsw":
                # HNSW index
                M = self.config.get("M", 32)
                self._index = faiss.IndexHNSWFlat(self.dimension, M, faiss_metric)
                self._index.hnsw.efConstruction = self.config.get("efConstruction", 200)
                self._index.hnsw.efSearch = self.config.get("efSearch", 128)
            
            else:
                # Default to flat index
                logger.warning(f"Unsupported index type: {index_type}, using flat")
                self._index = faiss.IndexFlatIP(self.dimension) if faiss_metric == faiss.METRIC_INNER_PRODUCT else faiss.IndexFlatL2(self.dimension)
            
            logger.info(f"Initialized FAISS index: {self._index}")
        
        except ImportError:
            logger.error("FAISS not installed. Please install with: pip install faiss-cpu or faiss-gpu")
            raise
    
    def add_embeddings(self, embeddings_data: List[Dict[str, Any]]) -> List[str]:
        """
        Add multiple embeddings to index.
        
        Args:
            embeddings_data: List of dictionaries with id, embedding, and optional metadata
            
        Returns:
            List of IDs of added embeddings
        """
        # Extract vectors, IDs, and metadata
        vectors = []
        ids = []
        metadata_list = []
        
        for item in embeddings_data:
            # Extract embedding vector
            vector = item.get("embedding")
            if vector is None:
                logger.warning(f"Skipping item without embedding: {item.get('id')}")
                continue
            
            # Convert to numpy array if needed
            if not isinstance(vector, np.ndarray):
                try:
                    vector = np.array(vector, dtype=np.float32)
                except:
                    logger.warning(f"Could not convert embedding to numpy array: {item.get('id')}")
                    continue
            
            # Ensure vector has correct dimension
            if vector.shape != (self.dimension,):
                logger.warning(f"Vector has wrong dimension {vector.shape}, expected ({self.dimension},)")
                continue
            
            # Generate ID if not provided
            item_id = item.get("id")
            if item_id is None:
                import uuid
                item_id = str(uuid.uuid4())
            
            # Extract metadata
            metadata = {
                "id": item_id,
                "content": item.get("content", ""),
            }
            
            # Add additional metadata if provided
            if "metadata" in item:
                metadata.update(item["metadata"])
            
            # Append to lists
            vectors.append(vector.astype(np.float32))
            ids.append(item_id)
            metadata_list.append(metadata)
        
        if not vectors:
            logger.warning("No valid embeddings to add")
            return []
        
        # Convert to numpy array
        vectors_array = np.array(vectors, dtype=np.float32)
        
        # Normalize vectors for cosine similarity if needed
        if self.normalize:
            vectors_array = self._normalize_vectors(vectors_array)
        
        # Check if the index requires training
        if hasattr(self._index, 'ntotal') and self._index.ntotal == 0 and hasattr(self._index, 'train'):
            if self._index.is_trained:
                logger.info("Index already trained")
            else:
                logger.info(f"Training index with {len(vectors_array)} vectors")
                try:
                    self._index.train(vectors_array)
                except Exception as e:
                    logger.error(f"Error training index: {str(e)}")
                    # Fall back to flat index
                    self._reset_to_flat_index()
                    self._index.add(vectors_array)
        else:
            # Add vectors to index
            try:
                self._index.add(vectors_array)
            except Exception as e:
                logger.error(f"Error adding vectors to index: {str(e)}")
                # Fall back to flat index
                self._reset_to_flat_index()
                self._index.add(vectors_array)
        
        # Update internal storage
        start_index = len(self.ids)
        for i, item_id in enumerate(ids):
            index = start_index + i
            self.id_to_index[item_id] = index
            self.ids.append(item_id)
            self.vectors.append(vectors_array[i])
            self.metadata.append(metadata_list[i])
        
        logger.info(f"Added {len(vectors)} vectors to index, total: {len(self.ids)}")
        
        return ids
    
    def search(self, 
              query_vector: np.ndarray, 
              k: int = 5, 
              filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.
        
        Args:
            query_vector: Query vector
            k: Number of results
            filters: Metadata filters
            
        Returns:
            List of search results with id, score, and metadata
        """
        if len(self.ids) == 0:
            logger.warning("Index is empty")
            return []
        
        # Ensure query vector has correct shape
        if not isinstance(query_vector, np.ndarray):
            try:
                query_vector = np.array(query_vector, dtype=np.float32)
            except:
                logger.error("Could not convert query to numpy array")
                return []
        
        # Ensure query vector has correct dimension
        if query_vector.shape != (self.dimension,):
            logger.error(f"Query vector has wrong dimension {query_vector.shape}, expected ({self.dimension},)")
            return []
        
        # Normalize query vector for cosine similarity if needed
        if self.normalize:
            query_vector = self._normalize_vectors(query_vector.reshape(1, -1))[0]
        
        # Reshape query vector if needed
        if len(query_vector.shape) == 1:
            query_vector = query_vector.reshape(1, -1)
        
        # Increase k if filters are used
        search_k = k * 4 if filters else k
        search_k = min(search_k, len(self.ids))
        
        # Perform search
        try:
            scores, indices = self._index.search(query_vector, search_k)
        except Exception as e:
            logger.error(f"Error searching index: {str(e)}")
            return []
        
        # Convert to flat lists
        scores = scores[0].tolist()
        indices = indices[0].tolist()
        
        # Prepare results
        results = []
        for i, idx in enumerate(indices):
            if idx == -1:  # FAISS returns -1 for not enough results
                continue
            
            # Get metadata
            item_metadata = self.metadata[idx]
            
            # Apply filters
            if filters and not self._matches_filters(item_metadata, filters):
                continue
            
            # Add to results
            result = {
                "id": self.ids[idx],
                "score": float(scores[i]),
                "metadata": item_metadata
            }
            
            # Add content if available
            if "content" in item_metadata:
                result["content"] = item_metadata["content"]
            
            results.append(result)
            
            # Stop after k results
            if len(results) >= k:
                break
        
        return results
    
    def _matches_filters(self, metadata: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """
        Check if metadata matches filters.
        
        Args:
            metadata: Item metadata
            filters: Metadata filters
            
        Returns:
            Whether metadata matches filters
        """
        for key, value in filters.items():
            # Handle nested keys with dot notation
            if "." in key:
                parts = key.split(".")
                current = metadata
                for part in parts[:-1]:
                    if part not in current:
                        return False
                    current = current[part]
                
                if parts[-1] not in current or current[parts[-1]] != value:
                    return False
            
            # Handle simple keys
            elif key not in metadata or metadata[key] != value:
                return False
        
        return True
    
    def _normalize_vectors(self, vectors: np.ndarray) -> np.ndarray:
        """
        Normalize vectors for cosine similarity.
        
        Args:
            vectors: Vectors to normalize
            
        Returns:
            Normalized vectors
        """
        # Calculate norm
        norm = np.linalg.norm(vectors, axis=1, keepdims=True)
        
        # Handle zero norm
        norm = np.maximum(norm, 1e-12)
        
        # Normalize
        return vectors / norm
    
    def _reset_to_flat_index(self) -> None:
        """Reset to flat index when complex index fails."""
        try:
            import faiss
            
            logger.warning("Resetting to flat index")
            
            if self.metric == "cosine" or self.metric == "ip":
                self._index = faiss.IndexFlatIP(self.dimension)
            else:
                self._index = faiss.IndexFlatL2(self.dimension)
            
            # Re-add vectors if available
            if self.vectors:
                vectors_array = np.array(self.vectors, dtype=np.float32)
                self._index.add(vectors_array)
        
        except Exception as e:
            logger.error(f"Error resetting to flat index: {str(e)}")
    
    def save(self, path: str) -> None:
        """
        Save index to file.
        
        Args:
            path: Path to save file
        """
        try:
            import faiss
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            # Prepare data to save
            data = {
                "dimension": self.dimension,
                "metric": self.metric,
                "config": self.config,
                "ids": self.ids,
                "id_to_index": self.id_to_index,
                "metadata": self.metadata,
                "normalize": self.normalize
            }
            
            # Save data and index
            with open(path + ".data", "wb") as f:
                pickle.dump(data, f)
            
            faiss.write_index(self._index, path + ".index")
            
            logger.info(f"Index saved to {path}")
        
        except Exception as e:
            logger.error(f"Error saving index: {str(e)}")
            raise
    
    @classmethod
    def load(cls, path: str) -> 'AdvancedVectorIndex':
        """
        Load index from file.
        
        Args:
            path: Path to load file
            
        Returns:
            Loaded vector index
        """
        try:
            import faiss
            
            # Load data
            with open(path + ".data", "rb") as f:
                data = pickle.load(f)
            
            # Create instance
            index = cls(
                dimension=data["dimension"],
                metric=data["metric"],
                config=data["config"]
            )
            
            # Load FAISS index
            index._index = faiss.read_index(path + ".index")
            
            # Restore data
            index.ids = data["ids"]
            index.id_to_index = data["id_to_index"]
            index.metadata = data["metadata"]
            index.normalize = data["normalize"]
            
            # Reconstruct vectors if needed
            if hasattr(index._index, "reconstruct"):
                index.vectors = []
                for i in range(len(index.ids)):
                    vector = np.zeros((index.dimension,), dtype=np.float32)
                    index._index.reconstruct(i, vector)
                    index.vectors.append(vector)
            
            logger.info(f"Index loaded from {path} with {len(index.ids)} vectors")
            
            return index
        
        except Exception as e:
            logger.error(f"Error loading index: {str(e)}")
            raise
"""
Distributed vector index for scaling to large datasets.
"""
import os
import logging
import time
import threading
import uuid
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np
import json
import pickle
from concurrent.futures import ThreadPoolExecutor, as_completed

from .advanced_vector_index import AdvancedVectorIndex, FAISSConfigFactory

logger = logging.getLogger(__name__)

class ShardedVectorIndex:
    """
    Sharded vector index for distributing vectors across multiple indices.
    """
    
    def __init__(self,
                num_shards: int = 4,
                index_config: Optional[Dict[str, Any]] = None,
                dimension: int = 384,
                metric: str = "cosine",
                storage_dir: str = "vector_storage"):
        """
        Initialize sharded vector index.
        
        Args:
            num_shards: Number of shards
            index_config: Index configuration
            dimension: Vector dimension
            metric: Distance metric
            storage_dir: Storage directory
        """
        self.num_shards = num_shards
        self.dimension = dimension
        self.metric = metric
        self.storage_dir = storage_dir
        
        # Create storage directory
        os.makedirs(storage_dir, exist_ok=True)
        
        # Default config if not provided
        if index_config is None:
            self.index_config = FAISSConfigFactory.get_index_config(
                index_type="ivf",
                dimension=dimension,
                metric=metric
            )
        else:
            self.index_config = index_config
        
        # Initialize shards
        self.shards = []
        for i in range(num_shards):
            shard_dir = os.path.join(storage_dir, f"shard_{i}")
            os.makedirs(shard_dir, exist_ok=True)
            
            shard = AdvancedVectorIndex(
                config=self.index_config,
                storage_dir=shard_dir
            )
            self.shards.append(shard)
        
        # Metadata
        self.uuid_to_shard = {}  # Maps UUID to shard index
        self.metadata = {}       # Maps UUID to metadata
        
        # Threading
        self.lock = threading.RLock()
        
        logger.info(f"Initialized sharded vector index with {num_shards} shards")
    
    def _get_shard_for_vector(self, vector: np.ndarray) -> int:
        """
        Determine which shard a vector should go to.
        
        Args:
            vector: Vector to add
            
        Returns:
            Shard index
        """
        # Simple hash-based sharding
        # Use the first few values of the vector to determine shard
        # For reproducibility, we use a deterministic approach
        hash_value = np.sum(vector[:min(8, self.dimension)] * np.arange(1, min(9, self.dimension + 1)))
        return int(abs(hash_value)) % self.num_shards
    
    def _get_shard_for_uuid(self, uuid_str: str) -> int:
        """
        Get shard index for a UUID.
        
        Args:
            uuid_str: UUID
            
        Returns:
            Shard index
        """
        with self.lock:
            return self.uuid_to_shard.get(uuid_str, -1)
    
    def add_vectors(self,
                   vectors: np.ndarray,
                   uuids: List[str],
                   metadata: Optional[List[Dict[str, Any]]] = None) -> List[int]:
        """
        Add vectors to sharded index.
        
        Args:
            vectors: Vectors to add
            uuids: UUIDs for vectors
            metadata: Optional metadata
            
        Returns:
            List of internal IDs
        """
        if len(vectors) != len(uuids):
            raise ValueError("Number of vectors and UUIDs must match")
        
        if metadata is not None and len(metadata) != len(vectors):
            raise ValueError("Number of metadata entries must match vectors")
        
        # Group vectors by shard
        shard_groups = {}
        for i, (vector, uuid_str) in enumerate(zip(vectors, uuids)):
            shard_idx = self._get_shard_for_vector(vector)
            
            if shard_idx not in shard_groups:
                shard_groups[shard_idx] = {
                    "vectors": [],
                    "uuids": [],
                    "metadata": [] if metadata else None,
                    "indices": []
                }
            
            shard_groups[shard_idx]["vectors"].append(vector)
            shard_groups[shard_idx]["uuids"].append(uuid_str)
            if metadata:
                shard_groups[shard_idx]["metadata"].append(metadata[i])
            shard_groups[shard_idx]["indices"].append(i)
            
            # Record shard assignment
            with self.lock:
                self.uuid_to_shard[uuid_str] = shard_idx
                if metadata:
                    self.metadata[uuid_str] = metadata[i]
        
        # Add vectors to shards
        all_results = [None] * len(vectors)
        
        with ThreadPoolExecutor(max_workers=min(self.num_shards, 8)) as executor:
            futures = {}
            
            # Submit add tasks
            for shard_idx, group in shard_groups.items():
                vectors_array = np.stack(group["vectors"])
                
                future = executor.submit(
                    self._add_to_shard,
                    shard_idx,
                    vectors_array,
                    group["uuids"],
                    group["metadata"]
                )
                futures[future] = (shard_idx, group["indices"])
            
            # Process results
            for future in as_completed(futures):
                shard_idx, indices = futures[future]
                try:
                    shard_results = future.result()
                    
                    # Map shard results back to original positions
                    for i, result_id in enumerate(shard_results):
                        all_results[indices[i]] = result_id
                        
                except Exception as e:
                    logger.error(f"Error adding vectors to shard {shard_idx}: {str(e)}")
        
        return all_results
    
    def _add_to_shard(self,
                     shard_idx: int,
                     vectors: np.ndarray,
                     uuids: List[str],
                     metadata: Optional[List[Dict[str, Any]]]) -> List[int]:
        """
        Add vectors to a specific shard.
        
        Args:
            shard_idx: Shard index
            vectors: Vectors to add
            uuids: UUIDs for vectors
            metadata: Optional metadata
            
        Returns:
            List of internal IDs
        """
        try:
            return self.shards[shard_idx].add_vectors(vectors, uuids, metadata)
        except Exception as e:
            logger.error(f"Error adding to shard {shard_idx}: {str(e)}")
            raise
    
    def search(self,
              query_vector: np.ndarray,
              k: int = 5,
              search_all_shards: bool = True) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.
        
        Args:
            query_vector: Query vector
            k: Number of results
            search_all_shards: Whether to search all shards
            
        Returns:
            List of search results
        """
        if search_all_shards:
            # Search all shards in parallel
            all_results = []
            
            with ThreadPoolExecutor(max_workers=self.num_shards) as executor:
                future_to_shard = {
                    executor.submit(self._search_shard, i, query_vector, k): i
                    for i in range(self.num_shards)
                }
                
                for future in as_completed(future_to_shard):
                    shard_idx = future_to_shard[future]
                    try:
                        shard_results = future.result()
                        all_results.extend(shard_results)
                    except Exception as e:
                        logger.error(f"Error searching shard {shard_idx}: {str(e)}")
            
            # Sort by score and take top k
            all_results.sort(key=lambda x: x["score"], reverse=True)
            return all_results[:k]
        else:
            # Only search the appropriate shard
            shard_idx = self._get_shard_for_vector(query_vector)
            return self._search_shard(shard_idx, query_vector, k)
    
    def _search_shard(self, shard_idx: int, query_vector: np.ndarray, k: int) -> List[Dict[str, Any]]:
        """
        Search a specific shard.
        
        Args:
            shard_idx: Shard index
            query_vector: Query vector
            k: Number of results
            
        Returns:
            List of search results
        """
        try:
            return self.shards[shard_idx].search(query_vector, k)
        except Exception as e:
            logger.error(f"Error searching shard {shard_idx}: {str(e)}")
            return []
    
    def search_by_uuid(self, uuid_str: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search by UUID.
        
        Args:
            uuid_str: UUID of vector to search for
            k: Number of results
            
        Returns:
            List of search results
        """
        # Find shard for UUID
        shard_idx = self._get_shard_for_uuid(uuid_str)
        
        if shard_idx < 0:
            logger.warning(f"UUID {uuid_str} not found in any shard")
            return []
        
        # Search from that shard
        try:
            return self.shards[shard_idx].search_by_uuid(uuid_str, k)
        except Exception as e:
            logger.error(f"Error searching by UUID in shard {shard_idx}: {str(e)}")
            return []
    
    def batch_search(self,
                    query_vectors: np.ndarray,
                    k: int = 5,
                    search_all_shards: bool = True) -> List[List[Dict[str, Any]]]:
        """
        Perform batch search.
        
        Args:
            query_vectors: Query vectors
            k: Number of results per query
            search_all_shards: Whether to search all shards
            
        Returns:
            List of result lists
        """
        results = []
        
        # Process queries in parallel
        with ThreadPoolExecutor(max_workers=min(len(query_vectors), 16)) as executor:
            futures = [
                executor.submit(self.search, query, k, search_all_shards)
                for query in query_vectors
            ]
            
            for future in as_completed(futures):
                try:
                    query_results = future.result()
                    results.append(query_results)
                except Exception as e:
                    logger.error(f"Error in batch search: {str(e)}")
                    results.append([])
        
        return results
    
    def save(self, filename: Optional[str] = None) -> str:
        """
        Save sharded index.
        
        Args:
            filename: Base filename
            
        Returns:
            Path to saved index
        """
        if filename is None:
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            filename = f"sharded_{self.num_shards}_{timestamp}"
        
        # Save each shard
        shard_paths = []
        for i, shard in enumerate(self.shards):
            shard_path = shard.save(f"{filename}_shard_{i}")
            shard_paths.append(shard_path)
        
        # Save metadata
        meta_path = os.path.join(self.storage_dir, f"{filename}_meta.json")
        
        with open(meta_path, 'w') as f:
            json.dump({
                "num_shards": self.num_shards,
                "dimension": self.dimension,
                "metric": self.metric,
                "index_config": self.index_config,
                "uuid_to_shard": self.uuid_to_shard,
                "metadata": self.metadata,
                "shard_paths": shard_paths
            }, f, indent=2, default=lambda o: str(o) if isinstance(o, np.ndarray) else o)
        
        logger.info(f"Saved sharded index to {meta_path}")
        
        return meta_path
    
    def load(self, filename: str) -> bool:
        """
        Load sharded index.
        
        Args:
            filename: Path to metadata file
            
        Returns:
            Success status
        """
        if not filename.endswith('_meta.json'):
            filename = os.path.join(self.storage_dir, f"{filename}_meta.json")
        
        if not os.path.exists(filename):
            logger.error(f"Metadata file not found: {filename}")
            return False
        
        try:
            # Load metadata
            with open(filename, 'r') as f:
                metadata = json.load(f)
            
            # Check compatibility
            if metadata.get("dimension") != self.dimension:
                logger.error(f"Dimension mismatch: {metadata.get('dimension')} vs {self.dimension}")
                return False
            
            # Update instance variables
            self.num_shards = metadata.get("num_shards", self.num_shards)
            self.metric = metadata.get("metric", self.metric)
            self.index_config = metadata.get("index_config", self.index_config)
            self.uuid_to_shard = metadata.get("uuid_to_shard", {})
            self.metadata = metadata.get("metadata", {})
            
            # Ensure we have enough shards
            while len(self.shards) < self.num_shards:
                shard_dir = os.path.join(self.storage_dir, f"shard_{len(self.shards)}")
                os.makedirs(shard_dir, exist_ok=True)
                
                shard = AdvancedVectorIndex(
                    config=self.index_config,
                    storage_dir=shard_dir
                )
                self.shards.append(shard)
            
            # Load each shard
            success = True
            for i, shard in enumerate(self.shards[:self.num_shards]):
                shard_path = metadata.get("shard_paths", [])[i] if i < len(metadata.get("shard_paths", [])) else None
                
                if shard_path and os.path.exists(shard_path):
                    success = shard.load(shard_path) and success
                else:
                    # Try to load from default location
                    base_name = os.path.splitext(os.path.basename(filename))[0].replace('_meta', '')
                    default_path = os.path.join(self.storage_dir, f"shard_{i}", f"{base_name}_shard_{i}")
                    
                    if os.path.exists(f"{default_path}.faiss"):
                        success = shard.load(default_path) and success
                    else:
                        logger.warning(f"Shard {i} not found at {shard_path} or {default_path}")
                        success = False
            
            logger.info(f"Loaded sharded index with {self.num_shards} shards, success={success}")
            return success
            
        except Exception as e:
            logger.error(f"Error loading sharded index: {str(e)}")
            return False
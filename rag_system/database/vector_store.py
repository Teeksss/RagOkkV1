"""
Vector database interface for storing and retrieving embeddings.
"""
import os
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
import faiss
import json
import pickle
from datetime import datetime

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, dimension: int, index_type: str = "flat", 
                 storage_path: str = "./vector_storage",
                 use_gpu: bool = False):
        """
        Initialize vector store.
        
        Args:
            dimension: Embedding dimension
            index_type: FAISS index type (flat, ivf, hnsw)
            storage_path: Path to store index files
            use_gpu: Whether to use GPU acceleration
        """
        self.dimension = dimension
        self.index_type = index_type
        self.storage_path = storage_path
        self.use_gpu = use_gpu
        self.index = None
        self.metadata = {}
        self.id_map = {}  # Maps internal FAISS IDs to document IDs
        
        # Create storage directory if it doesn't exist
        os.makedirs(storage_path, exist_ok=True)
        
        # Initialize index
        self._create_index()
        
        # Use GPU if available and requested
        if use_gpu:
            try:
                import faiss.contrib.torch_utils
                self._move_index_to_gpu()
                logger.info("FAISS index moved to GPU")
            except Exception as e:
                logger.warning(f"Failed to move index to GPU: {str(e)}")
    
    def _create_index(self):
        """Create FAISS index based on the specified type."""
        if self.index_type == "flat":
            # Simple flat index (exact search, but slower)
            self.index = faiss.IndexFlatL2(self.dimension)
        elif self.index_type == "ivf":
            # IVF index (approximate search, faster)
            quantizer = faiss.IndexFlatL2(self.dimension)
            nlist = 100  # Number of clusters
            self.index = faiss.IndexIVFFlat(quantizer, self.dimension, nlist)
            self.index.train(np.random.random((1000, self.dimension)).astype('float32'))
        elif self.index_type == "hnsw":
            # HNSW index (hierarchical navigable small world, very fast)
            self.index = faiss.IndexHNSWFlat(self.dimension, 32)  # 32 is the number of neighbors
        else:
            # Default to flat index
            logger.warning(f"Unknown index type '{self.index_type}', defaulting to flat")
            self.index = faiss.IndexFlatL2(self.dimension)
    
    def _move_index_to_gpu(self):
        """Move index to GPU if available."""
        res = faiss.StandardGpuResources()
        self.index = faiss.index_cpu_to_gpu(res, 0, self.index)
    
    def add_embeddings(self, embeddings: np.ndarray, document_ids: List[str], 
                       metadata: List[Dict[str, Any]]) -> bool:
        """
        Add embeddings to the vector store.
        
        Args:
            embeddings: Array of embeddings
            document_ids: List of document IDs
            metadata: List of metadata dictionaries
            
        Returns:
            Success status
        """
        try:
            # Convert embeddings to float32
            embeddings = np.array(embeddings).astype('float32')
            
            # Generate internal IDs
            start_id = len(self.id_map)
            internal_ids = np.arange(start_id, start_id + len(embeddings))
            
            # Add to index
            self.index.add(embeddings)
            
            # Update ID map and metadata
            for i, (doc_id, meta) in enumerate(zip(document_ids, metadata)):
                internal_id = int(internal_ids[i])
                self.id_map[internal_id] = doc_id
                self.metadata[doc_id] = meta
            
            logger.info(f"Added {len(embeddings)} embeddings to vector store")
            return True
        
        except Exception as e:
            logger.error(f"Error adding embeddings: {str(e)}")
            return False
    
    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar embeddings.
        
        Args:
            query_embedding: Query embedding
            k: Number of results to return
            
        Returns:
            List of results with document IDs, scores, and metadata
        """
        try:
            # Convert query to float32
            query_embedding = np.array([query_embedding]).astype('float32')
            
            # Search index
            distances, indices = self.index.search(query_embedding, k)
            
            # Prepare results
            results = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                # Skip invalid indices
                if idx == -1 or idx not in self.id_map:
                    continue
                
                doc_id = self.id_map[idx]
                meta = self.metadata.get(doc_id, {})
                
                results.append({
                    "document_id": doc_id,
                    "score": float(1.0 / (1.0 + distance)),  # Convert distance to similarity score
                    "distance": float(distance),
                    "metadata": meta
                })
            
            return results
        
        except Exception as e:
            logger.error(f"Error searching embeddings: {str(e)}")
            return []
    
    def save(self, filename: Optional[str] = None) -> bool:
        """
        Save index and metadata to disk.
        
        Args:
            filename: Base filename (without extension)
            
        Returns:
            Success status
        """
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"vector_index_{timestamp}"
            
            # Save index
            index_path = os.path.join(self.storage_path, f"{filename}.index")
            
            # Move to CPU if on GPU
            if self.use_gpu:
                cpu_index = faiss.index_gpu_to_cpu(self.index)
                faiss.write_index(cpu_index, index_path)
            else:
                faiss.write_index(self.index, index_path)
            
            # Save metadata and ID map
            meta_path = os.path.join(self.storage_path, f"{filename}.meta")
            with open(meta_path, 'wb') as f:
                pickle.dump({
                    "metadata": self.metadata,
                    "id_map": self.id_map,
                    "dimension": self.dimension,
                    "index_type": self.index_type
                }, f)
            
            logger.info(f"Saved vector index to {index_path} and {meta_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving vector index: {str(e)}")
            return False
    
    def load(self, filename: str) -> bool:
        """
        Load index and metadata from disk.
        
        Args:
            filename: Base filename (without extension)
            
        Returns:
            Success status
        """
        try:
            # Load index
            index_path = os.path.join(self.storage_path, f"{filename}.index")
            self.index = faiss.read_index(index_path)
            
            # Load metadata and ID map
            meta_path = os.path.join(self.storage_path, f"{filename}.meta")
            with open(meta_path, 'rb') as f:
                data = pickle.load(f)
                self.metadata = data["metadata"]
                self.id_map = data["id_map"]
                self.dimension = data["dimension"]
                self.index_type = data["index_type"]
            
            # Move to GPU if requested
            if self.use_gpu:
                self._move_index_to_gpu()
            
            logger.info(f"Loaded vector index from {index_path} and {meta_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error loading vector index: {str(e)}")
            return False
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document and its embeddings from the store.
        
        Note: FAISS doesn't support direct deletion. This method marks
        the document as deleted in metadata but doesn't remove it from the index.
        A full rebuild is needed for actual removal.
        
        Args:
            document_id: Document ID to delete
            
        Returns:
            Success status
        """
        try:
            # Find internal IDs for this document
            internal_ids = [k for k, v in self.id_map.items() if v == document_id]
            
            # Mark as deleted in metadata
            if document_id in self.metadata:
                self.metadata[document_id]["deleted"] = True
            
            logger.info(f"Marked document {document_id} as deleted")
            return True
        
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store.
        
        Returns:
            Dictionary with statistics
        """
        return {
            "total_vectors": self.index.ntotal,
            "dimension": self.dimension,
            "index_type": self.index_type,
            "documents": len(set(self.id_map.values())),
            "use_gpu": self.use_gpu
        }
"""
Document retrieval components for RAG system.
"""
import logging
import time
from typing import List, Dict, Any, Optional, Tuple

from ..data_processing.vector_store_service import VectorStoreService
from ..utils.caching import memoize, vector_cache

logger = logging.getLogger(__name__)

class Retriever:
    """
    Document retriever that combines different retrieval methods.
    """
    
    def __init__(self, 
                 vector_store: VectorStoreService,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize retriever.
        
        Args:
            vector_store: Vector store service
            config: Retrieval configuration
        """
        self.vector_store = vector_store
        self.config = config or {}
        
        # Default configuration
        self.default_top_k = self.config.get("default_top_k", 5)
        self.min_score_threshold = self.config.get("min_score_threshold", 0.6)
        self.use_hybrid_search = self.config.get("use_hybrid_search", False)
        self.hybrid_alpha = self.config.get("hybrid_alpha", 0.5)  # Weight for blending scores
        
        # Performance tracking
        self.timing_stats = {
            "vector_search": [],
            "keyword_search": [],
            "hybrid_search": [],
            "reranking": []
        }
    
    @vector_cache(ttl=300)  # Cache for 5 minutes
    def retrieve(self, 
                query: str, 
                k: Optional[int] = None,
                filters: Optional[Dict[str, Any]] = None,
                min_score: Optional[float] = None,
                return_all_scores: bool = False) -> Dict[str, Any]:
        """
        Retrieve relevant document chunks for a query.
        
        Args:
            query: User query
            k: Number of results to return
            filters: Optional metadata filters
            min_score: Minimum relevance score threshold
            return_all_scores: Whether to return scores for all documents
            
        Returns:
            Dictionary with retrieved documents and metadata
        """
        start_time = time.time()
        
        # Set defaults
        k = k or self.default_top_k
        min_score = min_score or self.min_score_threshold
        
        # Perform vector search
        vector_start = time.time()
        vector_results = self.vector_store.search(
            query=query,
            k=k * 2,  # Get more results for filtering
            filters=filters,
            use_cache=True
        )
        vector_time = time.time() - vector_start
        self.timing_stats["vector_search"].append(vector_time)
        
        # Filter by score threshold
        filtered_results = [
            result for result in vector_results
            if result.get("score", 0) >= min_score
        ]
        
        # Limit to top k
        top_results = filtered_results[:k] if len(filtered_results) > k else filtered_results
        
        # Prepare retrieval results
        retrieval_results = {
            "query": query,
            "total_results": len(filtered_results),
            "returned_results": len(top_results),
            "results": top_results,
            "timing": {
                "total": time.time() - start_time,
                "vector_search": vector_time
            }
        }
        
        # Add retrieval metadata
        if return_all_scores:
            retrieval_results["all_scores"] = [
                {"id": r.get("id"), "score": r.get("score", 0)}
                for r in vector_results
            ]
        
        return retrieval_results
    
    def retrieve_for_document(self, 
                             document_id: str,
                             k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve similar chunks for a document.
        
        Args:
            document_id: Document ID
            k: Number of results per chunk
            
        Returns:
            List of similar chunks
        """
        # Get document chunks
        db = self.vector_store.db
        chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).all()
        
        if not chunks:
            logger.warning(f"No chunks found for document {document_id}")
            return []
        
        # Retrieve similar chunks for each chunk
        similar_chunks = []
        
        for chunk in chunks:
            # Get chunk text
            query = chunk.content
            
            # Retrieve similar chunks
            results = self.retrieve(
                query=query,
                k=k,
                filters={"document_id": {"$ne": document_id}},  # Exclude the source document
                min_score=self.min_score_threshold
            )
            
            # Add source chunk info
            if results["results"]:
                similar_chunks.append({
                    "source_chunk": {
                        "id": chunk.id,
                        "document_id": document_id,
                        "content": chunk.content,
                        "metadata": chunk.metadata
                    },
                    "similar_chunks": results["results"]
                })
        
        return similar_chunks
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get retriever performance statistics.
        
        Returns:
            Dictionary with performance statistics
        """
        stats = {}
        
        for key, times in self.timing_stats.items():
            if times:
                stats[key] = {
                    "count": len(times),
                    "avg_time": sum(times) / len(times),
                    "min_time": min(times),
                    "max_time": max(times)
                }
            else:
                stats[key] = {"count": 0}
        
        return stats
    
    def clear_stats(self) -> None:
        """Clear performance statistics."""
        for key in self.timing_stats:
            self.timing_stats[key] = []
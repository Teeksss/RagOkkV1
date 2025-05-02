"""
Vector-based search functionality.
"""
import logging
import time
from typing import List, Dict, Any, Optional
import numpy as np

from ..data_processing.embeddings import EmbeddingGenerator
from ..database.vector_store import VectorStore

logger = logging.getLogger(__name__)

class VectorSearchEngine:
    def __init__(self, vector_store: VectorStore, embedding_generator: EmbeddingGenerator,
                 reranking_enabled: bool = True):
        """
        Initialize vector search engine.
        
        Args:
            vector_store: Vector database
            embedding_generator: Embedding generator
            reranking_enabled: Whether to enable reranking
        """
        self.vector_store = vector_store
        self.embedding_generator = embedding_generator
        self.reranking_enabled = reranking_enabled
    
    def search(self, query: str, top_k: int = 5, 
               filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for documents using vector search.
        
        Args:
            query: Search query
            top_k: Number of results to return
            filters: Metadata filters to apply
            
        Returns:
            List of search results
        """
        start_time = time.time()
        
        # Generate query embedding
        query_embedding = self.embedding_generator.generate_embedding(query)
        
        # Search vector store (get more results for reranking)
        k_multiplier = 3 if self.reranking_enabled else 1
        search_k = top_k * k_multiplier
        
        raw_results = self.vector_store.search(query_embedding, k=search_k)
        
        # Apply filters if provided
        if filters:
            filtered_results = self._apply_filters(raw_results, filters)
        else:
            filtered_results = raw_results
        
        # Rerank results if enabled
        if self.reranking_enabled and len(filtered_results) > top_k:
            reranked_results = self._rerank_results(query, filtered_results)
            results = reranked_results[:top_k]
        else:
            results = filtered_results[:top_k]
        
        elapsed_time = time.time() - start_time
        logger.info(f"Vector search completed in {elapsed_time:.4f} seconds")
        
        return results
    
    def _apply_filters(self, results: List[Dict[str, Any]], 
                       filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Apply metadata filters to search results.
        
        Args:
            results: Raw search results
            filters: Metadata filters
            
        Returns:
            Filtered results
        """
        filtered_results = []
        
        for result in results:
            metadata = result.get("metadata", {})
            match = True
            
            for key, value in filters.items():
                # Handle deleted flag specially
                if key == "deleted" and metadata.get("deleted", False) == value:
                    match = False
                    break
                
                # Check if key exists in metadata
                if key not in metadata:
                    match = False
                    break
                
                # Check if value matches
                if isinstance(value, list):
                    # List of possible values
                    if metadata[key] not in value:
                        match = False
                        break
                else:
                    # Single value
                    if metadata[key] != value:
                        match = False
                        break
            
            if match:
                filtered_results.append(result)
        
        return filtered_results
    
    def _rerank_results(self, query: str, 
                        results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Rerank search results using a different method.
        
        Args:
            query: Search query
            results: Initial search results
            
        Returns:
            Reranked results
        """
        try:
            # This is a simple BM25-inspired reranking
            # For production, consider using a dedicated reranking model
            
            query_terms = set(query.lower().split())
            
            # Calculate BM25-inspired scores
            for result in results:
                metadata = result.get("metadata", {})
                
                # Get text content from metadata
                content = metadata.get("text_content", "")
                if not content and "chunk_content" in metadata:
                    content = metadata["chunk_content"]
                
                # Count term occurrences
                content_lower = content.lower()
                term_scores = []
                
                for term in query_terms:
                    # Count occurrences
                    count = content_lower.count(term)
                    
                    # Simple term frequency score
                    term_scores.append(count)
                
                # Combine vector score with term frequency
                vector_score = result["score"]
                term_score = sum(term_scores) / max(1, len(query_terms))
                
                # Hybrid score (70% vector, 30% term frequency)
                hybrid_score = (0.7 * vector_score) + (0.3 * min(1.0, term_score / 5))
                
                # Update score
                result["original_score"] = result["score"]
                result["term_score"] = term_score
                result["score"] = hybrid_score
            
            # Sort by new score
            reranked_results = sorted(results, key=lambda x: x["score"], reverse=True)
            
            return reranked_results
            
        except Exception as e:
            logger.error(f"Error during reranking: {str(e)}")
            return results
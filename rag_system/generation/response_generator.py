"""
Response generation with source attribution.
"""
import logging
import re
from typing import List, Dict, Any, Optional, Tuple

from .llm_interface import LLMInterface
from ..retrieval.vector_search import VectorSearchEngine

logger = logging.getLogger(__name__)

class ResponseGenerator:
    def __init__(self, llm: LLMInterface, search_engine: VectorSearchEngine,
                 include_sources: bool = True,
                 max_context_docs: int = 5):
        """
        Initialize response generator.
        
        Args:
            llm: Language model interface
            search_engine: Vector search engine
            include_sources: Whether to include source attributions
            max_context_docs: Maximum number of context documents
        """
        self.llm = llm
        self.search_engine = search_engine
        self.include_sources = include_sources
        self.max_context_docs = max_context_docs
    
    def generate_response(self, query: str) -> Dict[str, Any]:
        """
        Generate response for a query.
        
        Args:
            query: User query
            
        Returns:
            Dict with response and metadata
        """
        # Search for relevant documents
        search_results = self.search_engine.search(query, top_k=self.max_context_docs)
        
        # Prepare context documents
        context_docs = []
        sources = []
        
        for result in search_results:
            doc_id = result["document_id"]
            metadata = result.get("metadata", {})
            score = result["score"]
            
            # Extract content
            content = metadata.get("text_content", "")
            if not content and "chunk_content" in metadata:
                content = metadata["chunk_content"]
            
            # Skip if no content
            if not content:
                continue
            
            # Prepare source information
            source_info = {
                "id": doc_id,
                "title": metadata.get("title", "Unknown"),
                "source": metadata.get("source", "Unknown"),
                "relevance_score": score
            }
            
            context_docs.append({
                "content": content,
                "metadata": metadata,
                "score": score
            })
            
            sources.append(source_info)
        
        # Generate response
        llm_response = self.llm.generate_response(query, context=context_docs)
        
        # Extract answer
        answer = llm_response["text"]
        
        # Add source attribution if enabled
        if self.include_sources and sources:
            sources_text = self._format_sources(sources)
            final_answer = f"{answer}\n\n{sources_text}"
        else:
            final_answer = answer
        
        # Prepare response
        response = {
            "query": query,
            "answer": final_answer,
            "raw_answer": answer,
            "sources": sources,
            "model": llm_response.get("model", "unknown"),
            "tokens_used": llm_response.get("total_tokens", 0),
            "response_time": llm_response.get("elapsed_time", 0)
        }
        
        return response
    
    def _format_sources(self, sources: List[Dict[str, Any]]) -> str:
        """
        Format source attributions.
        
        Args:
            sources: List of source information
            
        Returns:
            Formatted sources text
        """
        sources_text = "Sources:\n"
        
        for i, source in enumerate(sources):
            title = source.get("title", "Unknown")
            source_name = source.get("source", "Unknown")
            
            sources_text += f"{i+1}. {title} ({source_name})\n"
        
        return sources_text
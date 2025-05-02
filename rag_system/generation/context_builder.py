"""
Context builder for LLM prompts.
"""
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class ContextBuilder:
    """
    Builder for LLM context from retrieved documents.
    """
    
    def __init__(self, 
                 system_template: Optional[str] = None,
                 prompt_template: Optional[str] = None):
        """
        Initialize context builder.
        
        Args:
            system_template: System message template
            prompt_template: Prompt template for user message
        """
        self.system_template = system_template or self._default_system_template()
        self.prompt_template = prompt_template or self._default_prompt_template()
    
    def _default_system_template(self) -> str:
        """Get default system template."""
        return (
            "Sen bir yapay zeka asistanısın. "
            "Sana verilen bağlam bilgilerini kullanarak kullanıcının sorularına doğru ve net yanıtlar vermelisin. "
            "Eğer bağlam bilgilerinde yanıt bulamazsan, bunu dürüstçe belirt ve tahmin yürütme. "
            "Yanıtın kısa, öz ve anlaşılır olsun. Cevaplarında verilen bilgilerden alıntı yapabilirsin."
        )
    
    def _default_prompt_template(self) -> str:
        """Get default prompt template."""
        return (
            "Soru: {query}\n\n"
            "Bağlam:\n{context}\n\n"
            "Yanıt:"
        )
    
    def build_prompt(self, 
                     query: str,
                     context_str: str) -> Dict[str, str]:
        """
        Build prompt from query and context.
        
        Args:
            query: User query
            context_str: Context string from retriever
            
        Returns:
            Dictionary with system and user message
        """
        # Format user message with prompt template
        user_message = self.prompt_template.format(
            query=query,
            context=context_str
        )
        
        return {
            "system": self.system_template,
            "user": user_message
        }
    
    def build_prompt_with_chunks(self,
                                query: str,
                                chunks: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Build prompt from query and context chunks.
        
        Args:
            query: User query
            chunks: List of context chunks
            
        Returns:
            Dictionary with system and user message
        """
        # Build context string from chunks
        context_parts = []
        
        for i, chunk in enumerate(chunks):
            # Format context entry
            context_part = f"[{i+1}] "
            
            # Add document info if available
            if "document" in chunk and chunk["document"]:
                doc_title = chunk["document"].get("title", "Document")
                context_part += f"{doc_title}: "
            
            # Add content
            context_part += chunk.get("content", "")
            context_parts.append(context_part)
        
        # Join context parts
        context_str = "\n\n".join(context_parts)
        
        # Build prompt
        return self.build_prompt(query, context_str)
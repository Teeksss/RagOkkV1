"""
LLM service for generating responses based on retrieved content.
"""
import logging
import os
import time
import json
from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np

from sqlalchemy.orm import Session

from ..data_processing.vector_store_service import VectorStoreService
from ..utils.caching import memoize
from ..utils.db_logger import DBLogger
from ..config import settings

logger = logging.getLogger(__name__)

class LLMService:
    """
    Large Language Model service for generating responses.
    """
    
    def __init__(self, 
                 db: Session,
                 vector_store: VectorStoreService,
                 model: str = "gpt-3.5-turbo",
                 provider: str = "openai",
                 temperature: float = 0.7,
                 max_tokens: int = 1024):
        """
        Initialize LLM service.
        
        Args:
            db: Database session
            vector_store: Vector store service
            model: LLM model name
            provider: LLM provider (openai, azure, huggingface)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        """
        self.db = db
        self.vector_store = vector_store
        self.model = model
        self.provider = provider
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.logger = DBLogger(db)
        
        # Initialize LLM client
        self._init_llm_client()
    
    def _init_llm_client(self) -> None:
        """Initialize LLM client based on provider."""
        if self.provider == "openai":
            self._init_openai()
        elif self.provider == "azure":
            self._init_azure_openai()
        elif self.provider == "huggingface":
            self._init_huggingface()
        else:
            logger.warning(f"Unknown provider: {self.provider}, defaulting to OpenAI")
            self._init_openai()
    
    def _init_openai(self) -> None:
        """Initialize OpenAI client."""
        try:
            import openai
            
            # Set API key
            openai.api_key = settings.OPENAI_API_KEY
            
            # Store client
            self.client = openai
            logger.info(f"Initialized OpenAI client with model: {self.model}")
        
        except ImportError:
            logger.error("Failed to import openai. Please install with: pip install openai")
            raise
    
    def _init_azure_openai(self) -> None:
        """Initialize Azure OpenAI client."""
        try:
            import openai
            
            # Set Azure OpenAI settings
            openai.api_type = "azure"
            openai.api_key = settings.AZURE_OPENAI_KEY
            openai.api_base = settings.AZURE_OPENAI_ENDPOINT
            openai.api_version = settings.AZURE_OPENAI_API_VERSION
            
            # Store client
            self.client = openai
            logger.info(f"Initialized Azure OpenAI client with model: {self.model}")
        
        except ImportError:
            logger.error("Failed to import openai. Please install with: pip install openai")
            raise
    
    def _init_huggingface(self) -> None:
        """Initialize Hugging Face client."""
        try:
            from huggingface_hub import InferenceClient
            
            # Create client
            self.client = InferenceClient(token=settings.HUGGINGFACE_TOKEN)
            logger.info(f"Initialized Hugging Face client with model: {self.model}")
        
        except ImportError:
            logger.error("Failed to import huggingface_hub. Please install with: pip install huggingface_hub")
            raise
    
    @memoize(ttl=3600)
    def process_query(self, 
                     query: str,
                     conversation_id: Optional[str] = None,
                     context_window: int = 5,
                     user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process query and generate response using LLM.
        
        Args:
            query: User query
            conversation_id: Conversation ID
            context_window: Number of past messages to include as context
            user_id: User ID
            
        Returns:
            Dictionary with response
        """
        start_time = time.time()
        
        try:
            # Search for relevant documents
            search_results = self.vector_store.search(
                query=query,
                k=5,
                use_cache=True
            )
            
            # Get conversation context if conversation_id is provided
            conversation_context = []
            if conversation_id:
                conversation_context = self._get_conversation_context(
                    conversation_id=conversation_id,
                    window_size=context_window
                )
            
            # Generate response
            response = self._generate_response(
                query=query,
                search_results=search_results,
                conversation_context=conversation_context
            )
            
            # Log successful query
            elapsed_time = time.time() - start_time
            self.logger.log_info(
                operation="llm_query",
                message=f"LLM query processed successfully",
                user_id=user_id,
                response_time=elapsed_time,
                data={
                    "query": query,
                    "conversation_id": conversation_id,
                    "model": self.model,
                    "provider": self.provider
                }
            )
            
            return {
                "answer": response,
                "model": self.model,
                "context": search_results,
                "conversation_id": conversation_id,
                "elapsed_time": elapsed_time
            }
        
        except Exception as e:
            # Log error
            elapsed_time = time.time() - start_time
            self.logger.log_error(
                operation="llm_query",
                error_message=str(e),
                user_id=user_id,
                latency=elapsed_time,
                data={
                    "query": query,
                    "conversation_id": conversation_id,
                    "model": self.model,
                    "provider": self.provider
                }
            )
            
            # Re-raise
            raise
    
    def _get_conversation_context(self, 
                                conversation_id: str, 
                                window_size: int = 5) -> List[Dict[str, Any]]:
        """
        Get conversation context from database.
        
        Args:
            conversation_id: Conversation ID
            window_size: Number of past messages to include
            
        Returns:
            List of messages with role and content
        """
        from ..database.models import Message
        
        # Query last N messages
        messages = self.db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(
            Message.timestamp.desc()
        ).limit(window_size).all()
        
        # Format messages
        context = []
        for message in reversed(messages):
            context.append({
                "role": message.role,
                "content": message.content
            })
        
        return context
    
    def _generate_response(self, 
                         query: str, 
                         search_results: List[Dict[str, Any]],
                         conversation_context: List[Dict[str, Any]]) -> str:
        """
        Generate response using LLM.
        
        Args:
            query: User query
            search_results: Search results
            conversation_context: Conversation context
            
        Returns:
            Generated response
        """
        if self.provider == "openai" or self.provider == "azure":
            return self._generate_with_openai(query, search_results, conversation_context)
        elif self.provider == "huggingface":
            return self._generate_with_huggingface(query, search_results, conversation_context)
        else:
            # Fallback to OpenAI
            return self._generate_with_openai(query, search_results, conversation_context)
    
    def _generate_with_openai(self, 
                            query: str, 
                            search_results: List[Dict[str, Any]],
                            conversation_context: List[Dict[str, Any]]) -> str:
        """
        Generate response using OpenAI API.
        
        Args:
            query: User query
            search_results: Search results
            conversation_context: Conversation context
            
        Returns:
            Generated response
        """
        # Format context
        context_text = ""
        for i, result in enumerate(search_results, 1):
            context_text += f"[{i}] {result.get('content', '')}\n\n"
        
        # Create messages
        messages = [
            {"role": "system", "content": f"You are a helpful assistant with access to a knowledge base. Answer the user's query based on the provided context. If the answer is not in the context, say that you don't know. Do not make up information. Provide factual responses with source information where possible.\n\nCONTEXT:\n{context_text}"}
        ]
        
        # Add conversation context
        messages.extend(conversation_context)
        
        # Add user query
        messages.append({"role": "user", "content": query})
        
        # Generate response
        response = self.client.ChatCompletion.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        # Extract response text
        response_text = response.choices[0].message.content.strip()
        
        return response_text
    
    def _generate_with_huggingface(self, 
                                 query: str, 
                                 search_results: List[Dict[str, Any]],
                                 conversation_context: List[Dict[str, Any]]) -> str:
        """
        Generate response using Hugging Face.
        
        Args:
            query: User query
            search_results: Search results
            conversation_context: Conversation context
            
        Returns:
            Generated response
        """
        # Format context
        context_text = ""
        for i, result in enumerate(search_results, 1):
            context_text += f"[{i}] {result.get('content', '')}\n\n"
        
        # Create prompt
        system_prompt = f"You are a helpful assistant with access to a knowledge base. Answer the user's query based on the provided context. If the answer is not in the context, say that you don't know. Do not make up information. Provide factual responses with source information where possible.\n\nCONTEXT:\n{context_text}"
        
        # Format conversation context
        conversation_text = ""
        for message in conversation_context:
            role = message["role"].upper()
            conversation_text += f"{role}: {message['content']}\n\n"
        
        # Combine everything into one prompt
        prompt = f"{system_prompt}\n\n{conversation_text}USER: {query}\n\nASSISTANT:"
        
        # Generate response
        response_text = self.client.text_generation(
            prompt=prompt,
            model=self.model,
            temperature=self.temperature,
            max_new_tokens=self.max_tokens,
            do_sample=True
        )
        
        return response_text.strip()
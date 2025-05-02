"""
Interface for language models.
"""
import os
import logging
import time
from typing import List, Dict, Any, Optional, Union
import requests
import json

logger = logging.getLogger(__name__)

class LLMInterface:
    """Base class for LLM interfaces."""
    
    def generate_response(self, prompt: str, 
                          context: Optional[List[Dict[str, Any]]] = None,
                          max_tokens: int = 1024) -> Dict[str, Any]:
        """
        Generate response from the language model.
        
        Args:
            prompt: User prompt
            context: List of context documents
            max_tokens: Maximum tokens in response
            
        Returns:
            Dict with response and metadata
        """
        raise NotImplementedError("Subclasses must implement this method")


class OpenAIInterface(LLMInterface):
    """Interface for OpenAI models."""
    
    def __init__(self, api_key: Optional[str] = None, 
                 model: str = "gpt-3.5-turbo", 
                 temperature: float = 0.7):
        """
        Initialize OpenAI interface.
        
        Args:
            api_key: OpenAI API key (or from env)
            model: Model name
            temperature: Temperature parameter
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OpenAI API key not provided")
        
        self.model = model
        self.temperature = temperature
        self.api_url = "https://api.openai.com/v1/chat/completions"
    
    def generate_response(self, prompt: str, 
                          context: Optional[List[Dict[str, Any]]] = None,
                          max_tokens: int = 1024) -> Dict[str, Any]:
        """
        Generate response from OpenAI.
        
        Args:
            prompt: User prompt
            context: List of context documents
            max_tokens: Maximum tokens in response
            
        Returns:
            Dict with response and metadata
        """
        start_time = time.time()
        
        # Prepare system message with context
        system_message = self._prepare_system_message(context)
        
        # Prepare messages
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]
        
        # Prepare request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": max_tokens
        }
        
        try:
            # Make API call
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Extract response
            generated_text = result["choices"][0]["message"]["content"]
            
            # Calculate usage
            token_usage = result.get("usage", {})
            
            elapsed_time = time.time() - start_time
            
            return {
                "text": generated_text,
                "model": self.model,
                "elapsed_time": elapsed_time,
                "prompt_tokens": token_usage.get("prompt_tokens", 0),
                "completion_tokens": token_usage.get("completion_tokens", 0),
                "total_tokens": token_usage.get("total_tokens", 0)
            }
            
        except Exception as e:
            logger.error(f"Error generating response from OpenAI: {str(e)}")
            return {
                "text": f"Error generating response: {str(e)}",
                "error": str(e),
                "model": self.model,
                "elapsed_time": time.time() - start_time
            }
    
    def _prepare_system_message(self, context: Optional[List[Dict[str, Any]]]) -> str:
        """
        Prepare system message with context.
        
        Args:
            context: List of context documents
            
        Returns:
            System message
        """
        if not context:
            return "You are a helpful assistant. Answer the question based on your knowledge."
        
        system_message = "You are a helpful assistant. Answer the question based on the following context:\n\n"
        
        # Add context documents
        for i, doc in enumerate(context):
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})
            source = metadata.get("source", f"Document {i+1}")
            
            system_message += f"--- {source} ---\n{content}\n\n"
        
        system_message += "Use only the information from the context to answer the question. If the answer is not in the context, say 'I don't have enough information to answer this question.'"
        
        return system_message


class HuggingFaceInterface(LLMInterface):
    """Interface for Hugging Face models."""
    
    def __init__(self, api_key: Optional[str] = None,
                 model: str = "google/flan-t5-large",
                 api_url: Optional[str] = None):
        """
        Initialize Hugging Face interface.
        
        Args:
            api_key: Hugging Face API key (or from env)
            model: Model name
            api_url: API URL (or infer from model)
        """
        self.api_key = api_key or os.environ.get("HUGGINGFACE_API_KEY")
        if not self.api_key:
            logger.warning("Hugging Face API key not provided")
        
        self.model = model
        
        # Infer API URL if not provided
        if api_url:
            self.api_url = api_url
        else:
            self.api_url = f"https://api-inference.huggingface.co/models/{model}"
    
    def generate_response(self, prompt: str, 
                          context: Optional[List[Dict[str, Any]]] = None,
                          max_tokens: int = 1024) -> Dict[str, Any]:
        """
        Generate response from Hugging Face.
        
        Args:
            prompt: User prompt
            context: List of context documents
            max_tokens: Maximum tokens in response
            
        Returns:
            Dict with response and metadata
        """
        start_time = time.time()
        
        # Prepare prompt with context
        full_prompt = self._prepare_prompt(prompt, context)
        
        # Prepare request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": full_prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": 0.7
            }
        }
        
        try:
            # Make API call
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Extract response (format varies by model)
            if isinstance(result, list) and len(result) > 0:
                if "generated_text" in result[0]:
                    generated_text = result[0]["generated_text"]
                else:
                    generated_text = result[0]
            elif isinstance(result, dict) and "generated_text" in result:
                generated_text = result["generated_text"]
            else:
                generated_text = str(result)
            
            elapsed_time = time.time() - start_time
            
            return {
                "text": generated_text,
                "model": self.model,
                "elapsed_time": elapsed_time
            }
            
        except Exception as e:
            logger.error(f"Error generating response from Hugging Face: {str(e)}")
            return {
                "text": f"Error generating response: {str(e)}",
                "error": str(e),
                "model": self.model,
                "elapsed_time": time.time() - start_time
            }
    
    def _prepare_prompt(self, prompt: str, 
                        context: Optional[List[Dict[str, Any]]]) -> str:
        """
        Prepare prompt with context.
        
        Args:
            prompt: User prompt
            context: List of context documents
            
        Returns:
            Full prompt
        """
        if not context:
            return prompt
        
        full_prompt = "Context information:\n\n"
        
        # Add context documents
        for i, doc in enumerate(context):
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})
            source = metadata.get("source", f"Document {i+1}")
            
            full_prompt += f"[{source}]\n{content}\n\n"
        
        full_prompt += f"Question: {prompt}\n\nAnswer:"
        
        return full_prompt
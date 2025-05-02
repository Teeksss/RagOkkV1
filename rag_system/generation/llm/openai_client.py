"""
Client for OpenAI API integration.
"""
import os
import logging
import time
import json
from typing import Dict, Any, Optional, List, Union
import requests

logger = logging.getLogger(__name__)

class OpenAIClient:
    """
    Client for OpenAI API.
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 model_name: str = "gpt-3.5-turbo",
                 temperature: float = 0.7,
                 max_tokens: int = 1024):
        """
        Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key
            model_name: Model name
            temperature: Temperature parameter
            max_tokens: Maximum tokens to generate
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("OpenAI API key not provided")
            
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.api_url = "https://api.openai.com/v1/chat/completions"
    
    def generate(self, 
                 prompt: Union[str, Dict[str, str]],
                 stream: bool = False) -> Dict[str, Any]:
        """
        Generate response from OpenAI.
        
        Args:
            prompt: Text prompt or dictionary with system/user messages
            stream: Whether to stream response
            
        Returns:
            Response dictionary
        """
        if not self.api_key:
            return {
                "text": "Error: OpenAI API key not provided",
                "model": self.model_name,
                "elapsed_time": 0
            }
        
        start_time = time.time()
        
        # Prepare messages
        messages = self._prepare_messages(prompt)
        
        try:
            # Prepare request
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "model": self.model_name,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "stream": stream
            }
            
            # Make request
            if stream:
                response_text = self._handle_streaming(headers, payload)
            else:
                response = requests.post(
                    self.api_url,
                    headers=headers,
                    json=payload
                )
                
                if response.status_code != 200:
                    logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                    return {
                        "text": f"Error: {response.text}",
                        "model": self.model_name,
                        "elapsed_time": time.time() - start_time
                    }
                
                result = response.json()
                response_text = result["choices"][0]["message"]["content"]
                
                # Token usage
                usage = result.get("usage", {})
                prompt_tokens = usage.get("prompt_tokens", 0)
                completion_tokens = usage.get("completion_tokens", 0)
                total_tokens = usage.get("total_tokens", 0)
            
            elapsed_time = time.time() - start_time
            
            return {
                "text": response_text,
                "model": self.model_name,
                "elapsed_time": elapsed_time,
                "prompt_tokens": prompt_tokens if not stream else None,
                "completion_tokens": completion_tokens if not stream else None,
                "total_tokens": total_tokens if not stream else None
            }
            
        except Exception as e:
            logger.error(f"Error generating response from OpenAI: {str(e)}")
            return {
                "text": f"Error generating response: {str(e)}",
                "model": self.model_name,
                "elapsed_time": time.time() - start_time
            }
    
    def _prepare_messages(self, prompt: Union[str, Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Prepare messages for OpenAI API.
        
        Args:
            prompt: Text prompt or dictionary with system/user messages
            
        Returns:
            List of message dictionaries
        """
        if isinstance(prompt, dict):
            messages = []
            
            if "system" in prompt:
                messages.append({
                    "role": "system",
                    "content": prompt["system"]
                })
            
            if "user" in prompt:
                messages.append({
                    "role": "user",
                    "content": prompt["user"]
                })
                
            return messages
        else:
            # Simple prompt as user message
            return [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
    
    def _handle_streaming(self, headers: Dict[str, str], payload: Dict[str, Any]) -> str:
        """
        Handle streaming response from OpenAI.
        
        Args:
            headers: Request headers
            payload: Request payload
            
        Returns:
            Concatenated response text
        """
        response = requests.post(
            self.api_url,
            headers=headers,
            json=payload,
            stream=True
        )
        
        if response.status_code != 200:
            logger.error(f"OpenAI API streaming error: {response.status_code}")
            return f"Error: {response.text}"
        
        response_text = ""
        
        for line in response.iter_lines():
            if line:
                line_text = line.decode('utf-8')
                if line_text.startswith('data: '):
                    data_str = line_text[6:]  # Remove 'data: ' prefix
                    
                    if data_str == "[DONE]":
                        break
                    
                    try:
                        data = json.loads(data_str)
                        delta = data.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content", "")
                        response_text += content
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to decode JSON: {data_str}")
        
        return response_text
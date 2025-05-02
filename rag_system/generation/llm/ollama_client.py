"""
Client for Ollama local LLM integration.
"""
import os
import logging
import json
import time
import subprocess
from typing import Dict, Any, Optional, List, Union
import requests

logger = logging.getLogger(__name__)

class OllamaClient:
    """
    Client for Ollama local LLM.
    """
    
    def __init__(self, 
                 model_name: str = "phi",
                 api_url: Optional[str] = None,
                 temperature: float = 0.7,
                 max_tokens: int = 1024,
                 use_subprocess: bool = False):
        """
        Initialize Ollama client.
        
        Args:
            model_name: Ollama model name
            api_url: Ollama API URL
            temperature: Temperature parameter
            max_tokens: Maximum tokens to generate
            use_subprocess: Whether to use subprocess instead of API
        """
        self.model_name = model_name
        self.api_url = api_url or "http://localhost:11434"
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.use_subprocess = use_subprocess
        
        # Validate model exists if using API
        if not use_subprocess:
            try:
                self._check_model()
            except Exception as e:
                logger.warning(f"Could not verify model {model_name}: {str(e)}")
    
    def _check_model(self):
        """Check if model exists in Ollama."""
        try:
            response = requests.get(f"{self.api_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model.get("name") for model in models]
                
                if self.model_name not in model_names:
                    logger.warning(f"Model {self.model_name} not found in Ollama. Available models: {model_names}")
            else:
                logger.warning(f"Failed to get models from Ollama: {response.status_code}")
        except Exception as e:
            logger.error(f"Error checking Ollama models: {str(e)}")
            raise
    
    def generate(self, 
                 prompt: Union[str, Dict[str, str]],
                 stream: bool = False) -> Dict[str, Any]:
        """
        Generate response from Ollama.
        
        Args:
            prompt: Text prompt or dictionary with system/user messages
            stream: Whether to stream response
            
        Returns:
            Response dictionary
        """
        start_time = time.time()
        
        # Process prompt
        if isinstance(prompt, dict):
            if "system" in prompt and "user" in prompt:
                formatted_prompt = self._format_prompt_with_system(prompt["system"], prompt["user"])
            else:
                formatted_prompt = prompt.get("user", "")
        else:
            formatted_prompt = prompt
        
        # Generate response
        if self.use_subprocess:
            response_text = self._generate_subprocess(formatted_prompt)
        else:
            response_text = self._generate_api(formatted_prompt, stream)
        
        elapsed_time = time.time() - start_time
        
        return {
            "text": response_text,
            "model": self.model_name,
            "elapsed_time": elapsed_time
        }
    
    def _format_prompt_with_system(self, system: str, user: str) -> str:
        """
        Format prompt with system and user messages.
        
        Args:
            system: System message
            user: User message
            
        Returns:
            Formatted prompt
        """
        return f"<|system|>\n{system}\n<|user|>\n{user}\n<|assistant|>"
    
    def _generate_subprocess(self, prompt: str) -> str:
        """
        Generate response using subprocess.
        
        Args:
            prompt: Text prompt
            
        Returns:
            Generated text
        """
        try:
            # Create temporary file for prompt
            import tempfile
            
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                f.write(prompt)
                prompt_file = f.name
            
            # Build command
            cmd = [
                "ollama", "run", self.model_name,
                "--temp", str(self.temperature),
                "--num-predict", str(self.max_tokens),
                "-f", prompt_file
            ]
            
            # Run command
            logger.info(f"Running Ollama command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Clean up temp file
            os.unlink(prompt_file)
            
            if result.returncode != 0:
                logger.error(f"Ollama command failed: {result.stderr}")
                return f"Error generating response: {result.stderr}"
            
            return result.stdout.strip()
            
        except Exception as e:
            logger.error(f"Error in subprocess generation: {str(e)}")
            return f"Error generating response: {str(e)}"
    
    def _generate_api(self, prompt: str, stream: bool = False) -> str:
        """
        Generate response using Ollama API.
        
        Args:
            prompt: Text prompt
            stream: Whether to stream response
            
        Returns:
            Generated text
        """
        try:
            # Prepare request
            url = f"{self.api_url}/api/generate"
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
                "stream": stream
            }
            
            logger.info(f"Sending request to Ollama API for model {self.model_name}")
            
            if stream:
                # Handle streaming
                response_text = ""
                response = requests.post(url, json=payload, stream=True)
                
                if response.status_code != 200:
                    logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                    return f"Error: {response.text}"
                
                for line in response.iter_lines():
                    if line:
                        chunk = json.loads(line)
                        response_text += chunk.get("response", "")
                
                return response_text
            else:
                # Non-streaming request
                response = requests.post(url, json=payload)
                
                if response.status_code != 200:
                    logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                    return f"Error: {response.text}"
                
                result = response.json()
                return result.get("response", "")
                
        except Exception as e:
            logger.error(f"Error in API generation: {str(e)}")
            return f"Error generating response: {str(e)}"
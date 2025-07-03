"""OpenAI client wrapper for LLM interactions."""

from typing import List, Dict, Any, Optional
import requests
import json
from backend.config import get_config
from backend.logging import get_logger


class OpenAIClient:
    """Wrapper around OpenAI-compatible ChatCompletion endpoint."""
    
    def __init__(self) -> None:
        """Initialize the OpenAI client using configuration."""
        self.config = get_config()
        self.logger = get_logger(__name__)
        
        if not self.config.openai_base_url:
            raise ValueError("OpenAI base URL is required but not configured")
        if not self.config.openai_api_key:
            raise ValueError("OpenAI API key is required but not configured")
            
        self.base_url = self.config.openai_base_url
        self.api_key = self.config.openai_api_key
        
    def chat_completion(self, messages: List[Dict[str, Any]]) -> str:
        """Send messages to OpenAI-compatible chat completion endpoint.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            
        Returns:
            str: The response content from the LLM
            
        Raises:
            RuntimeError: If the API request fails
        """
        self.logger.debug(f"Sending {len(messages)} messages to OpenAI API")
        
        # Prepare the request
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.config.openai_model,
            "messages": messages,
            "temperature": self.config.openai_temperature,
            "max_tokens": self.config.openai_max_tokens
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            
            response_data = response.json()
            content = response_data["choices"][0]["message"]["content"]
            
            self.logger.debug("Successfully received response from OpenAI API")
            return content
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"OpenAI API request failed: {e}")
            raise RuntimeError(f"OpenAI API request failed: {e}")
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            self.logger.error(f"Failed to parse OpenAI API response: {e}")
            raise RuntimeError(f"Failed to parse OpenAI API response: {e}")
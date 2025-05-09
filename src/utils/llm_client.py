"""
LLM Client utility using instructor with litellm for provider flexibility.
"""

from typing import Dict, Any, Optional, Type, TypeVar
import instructor
from litellm import completion
from pydantic import BaseModel

from src.config.settings import get_api_keys, get_model_name

# Type variable for generic response schema
T = TypeVar('T', bound=BaseModel)

class LLMClient:
    """
    A client for making LLM requests using instructor with litellm.
    Supports different LLM providers and structured outputs via Pydantic schemas.
    """
    
    def __init__(self, provider: Optional[str] = None):
        """
        Initialize the LLM client.
        
        Args:
            provider: The LLM provider to use (openai, anthropic, cohere)
                     If None, uses the default provider from configuration.
        """
        self.provider = provider
        self._api_keys = get_api_keys()
        self.model = get_model_name(provider)
    
    def _get_client_params(self) -> Dict[str, Any]:
        """
        Get the parameters for the LLM client based on the provider.
        
        Returns:
            Dict[str, Any]: Parameters for the LLM client
        """
        provider = self.provider or "openai"
        
        return {
            "model": self.model,
            "api_key": self._api_keys.get(provider),
        }
    
    def generate_structured_output(self, 
                                  schema: Type[T], 
                                  prompt: str, 
                                  system_prompt: Optional[str] = None,
                                  **kwargs) -> T:
        """
        Generate a structured output using the LLM according to the provided schema.
        
        Args:
            schema: Pydantic model class defining the expected response structure
            prompt: The user prompt/question to send to the LLM
            system_prompt: Optional system prompt to guide the LLM
            **kwargs: Additional parameters to pass to the LLM client
            
        Returns:
            An instance of the provided schema with the LLM's response
        """
        # Create instructor client with litellm
        client = instructor.from_litellm(completion)
        
        # Prepare parameters
        params = self._get_client_params()
        params.update(kwargs)
        
        # Prepare messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Generate response with structured output
        response = client.chat.completions.create(
            messages=messages,
            response_model=schema,
            **params
        )
        
        return response 
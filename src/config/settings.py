"""
Configuration settings for the LLM utilities.
Handles loading environment variables and secrets management.
"""

import os
from typing import Dict, Optional
import boto3
from dotenv import load_dotenv
import json

# Load environment variables from .env file if present
load_dotenv()

# Base configuration from environment variables
DEFAULT_LLM_PROVIDER = os.getenv("DEFAULT_LLM_PROVIDER", "openai")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_SECRET_NAME = os.getenv("AWS_SECRET_NAME", "llm-utilities/api-keys")

# LLM Models configuration
DEFAULT_MODELS = {
    "openai": "gpt-4-turbo",
    "anthropic": "claude-3-opus-20240229",
    "cohere": "command-r-plus",
    "gemini": "gemini-pro",
}

def get_api_keys() -> Dict[str, str]:
    """
    Retrieve API keys from environment variables or AWS Secrets Manager.
    
    In local development, keys are loaded from .env file.
    In production (AWS Lambda), keys are retrieved from Secrets Manager.
    
    Returns:
        Dict[str, str]: Dictionary of API keys by provider
    """
    # First check environment variables (local development)
    api_keys = {
        "openai": os.getenv("OPENAI_API_KEY"),
        "anthropic": os.getenv("ANTHROPIC_API_KEY"),
        "cohere": os.getenv("COHERE_API_KEY"),
        "gemini": os.getenv("GEMINI_API_KEY"),
    }
    
    # If any key is missing and running in AWS Lambda environment
    if None in api_keys.values() and os.getenv("AWS_EXECUTION_ENV") is not None:
        try:
            # Use AWS Secrets Manager in production
            secrets_manager = boto3.client('secretsmanager', region_name=AWS_REGION)
            response = secrets_manager.get_secret_value(SecretId=AWS_SECRET_NAME)
            secrets = json.loads(response['SecretString'])
            
            # Update missing keys from secrets
            for provider in api_keys:
                if api_keys[provider] is None and f"{provider.upper()}_API_KEY" in secrets:
                    api_keys[provider] = secrets[f"{provider.upper()}_API_KEY"]
        except Exception as e:
            print(f"Error retrieving secrets: {str(e)}")
    
    return api_keys

def get_model_name(provider: Optional[str] = None) -> str:
    """
    Get the model name for the specified provider.
    
    Args:
        provider (Optional[str]): LLM provider name (openai, anthropic, cohere, gemini)
            If None, uses the default provider from environment.
            
    Returns:
        str: The model name to use
    """
    provider = provider or DEFAULT_LLM_PROVIDER
    
    # Check if custom model is specified in environment
    env_model = os.getenv(f"{provider.upper()}_MODEL")
    if env_model:
        return env_model
        
    # Fall back to default model
    return DEFAULT_MODELS.get(provider, DEFAULT_MODELS["openai"]) 
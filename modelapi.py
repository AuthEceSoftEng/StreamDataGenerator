# This file exposes the commands needed to communicate with an LLM
# It supports connecting to one of the following types of APIs:
# - an Open AI compatible API
# - an ollama API
# - a custom API (that follows the request/response format shown in file example_api.py)

import os
import json
import requests
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def chat(self, message, system_prompt = None, temperature = 0.7, max_tokens = 4096):
        """Send a chat message and get a response."""
        pass
    
    @abstractmethod
    def chat_stream(self, message, system_prompt = None, temperature = 0.7, max_tokens = 4096):
        """Send a chat message and get a streaming response."""
        pass


class OpenAICompatibleProvider(LLMProvider):
    """Provider for OpenAI-compatible APIs (OpenAI, Azure OpenAI, etc.)."""
    
    def __init__(self, api_key, base_url = "https://api.openai.com/v1", model = "gpt-4"):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.model = model
    
    def chat(self, message, system_prompt = None,
             temperature = 0.7, max_tokens = 4096):
        """Send a chat message and get a response."""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        data = response.json()
        return data["choices"][0]["message"]["content"]
    
    def chat_stream(self, message, system_prompt = None,
                    temperature = 0.7, max_tokens = 4096):
        """Send a chat message and get a streaming response."""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True
        }
        
        response = requests.post(url, headers=headers, json=payload, stream=True)
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                line_text = line.decode('utf-8')
                if line_text.startswith('data: '):
                    data_str = line_text[6:]
                    if data_str == '[DONE]':
                        break
                    try:
                        data = json.loads(data_str)
                        delta = data.get("choices", [{}])[0].get("delta", {})
                        if "content" in delta:
                            yield delta["content"]
                    except json.JSONDecodeError:
                        pass


class OllamaProvider(LLMProvider):
    """Provider for Ollama API."""
    
    def __init__(self, base_url = "http://localhost:11434", model = "llama3"):
        self.base_url = base_url.rstrip('/')
        self.model = model
    
    def chat(self, message, system_prompt = None,
             temperature = 0.7, max_tokens = 4096):
        """Send a chat message and get a response."""
        url = f"{self.base_url}/api/chat"
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        data = response.json()
        return data["message"]["content"]
    
    def chat_stream(self, message, system_prompt = None, temperature = 0.7, max_tokens = 4096):
        """Send a chat message and get a streaming response."""
        url = f"{self.base_url}/api/chat"
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        response = requests.post(url, json=payload, stream=True)
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line.decode('utf-8'))
                    if "message" in data and "content" in data["message"]:
                        yield data["message"]["content"]
                except json.JSONDecodeError:
                    pass


class CustomAPIProvider(LLMProvider):
    """
    Provider for custom API (following the format in example_api.py).
    This is designed for the Ariadne API or similar custom APIs.
    """
    
    def __init__(self, api_key, base_url = "https://ariadne.issel.ee.auth.gr/api", provider = "gcp", model = "gemini-2.5-pro"):
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.provider = provider
        self.model = model
    
    def chat(self, message, system_prompt = None, temperature = 0.7, max_tokens = 4096):
        """Send a chat message and get a response."""
        url = f"{self.base_url}/v1/chat"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # For custom API, include system prompt in the message if provided
        full_message = message
        if system_prompt:
            full_message = f"{system_prompt}\n\n{message}"
        
        payload = {
            "provider": self.provider,
            "model": self.model,
            "message": full_message,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        data = response.json()
        # Extract text from content array
        content = data.get("content", [])
        if content and isinstance(content, list):
            for item in content:
                if item.get("type") == "text":
                    return item.get("text", "")
        return ""
    
    def chat_stream(self, message, system_prompt = None, temperature = 0.7, max_tokens = 4096):
        """
        Send a chat message and get a streaming response.
        Note: Custom API may not support streaming, falls back to regular response.
        """
        # Custom API doesn't support streaming, return full response
        result = self.chat(message, system_prompt, temperature, max_tokens)
        yield result


def create_provider(provider_type, **kwargs):
    """
    Factory function to create an LLM provider.
    
    Args:
        provider_type: One of 'openai', 'ollama', or 'custom'
        **kwargs: Provider-specific configuration
        
    Returns:
        An LLMProvider instance
        
    Examples:
        # OpenAI
        provider = create_provider('openai', api_key='sk-...', model='gpt-4')
        
        # Ollama
        provider = create_provider('ollama', model='llama3')
        
        # Custom API
        provider = create_provider('custom', 
                                   api_key='sk-proj-...', 
                                   base_url='https://ariadne.issel.ee.auth.gr/api',
                                   provider='gcp',
                                   model='gemini-2.5-pro')
    """
    if provider_type.lower() == 'openai':
        return OpenAICompatibleProvider(
            api_key=kwargs.get('api_key', os.environ.get('OPENAI_API_KEY', '')),
            base_url=kwargs.get('base_url', 'https://api.openai.com/v1'),
            model=kwargs.get('model', 'gpt-4')
        )
    elif provider_type.lower() == 'ollama':
        return OllamaProvider(
            base_url=kwargs.get('base_url', 'http://localhost:11434'),
            model=kwargs.get('model', 'llama3')
        )
    elif provider_type.lower() == 'custom':
        return CustomAPIProvider(
            api_key=kwargs.get('api_key', os.environ.get('CUSTOM_API_KEY', '')),
            base_url=kwargs.get('base_url', 'https://ariadne.issel.ee.auth.gr/api'),
            provider=kwargs.get('provider', 'gcp'),
            model=kwargs.get('model', 'claude-sonnet-4')
        )
    else:
        raise ValueError(f"Unknown provider type: {provider_type}. "
                        f"Supported types: 'openai', 'ollama', 'custom'")


def load_config_from_env():
    """
    Load LLM configuration from environment variables.
    
    Environment variables:
        LLM_PROVIDER: Provider type ('openai', 'ollama', 'custom')
        LLM_API_KEY: API key for authentication
        LLM_BASE_URL: Base URL for the API
        LLM_MODEL: Model name/ID
        LLM_PROVIDER_NAME: Provider name for custom API (e.g., 'gcp')
    """
    return {
        'provider_type': os.environ.get('LLM_PROVIDER', 'openai'),
        'api_key': os.environ.get('LLM_API_KEY', ''),
        'base_url': os.environ.get('LLM_BASE_URL', ''),
        'model': os.environ.get('LLM_MODEL', 'gpt-4'),
        'provider': os.environ.get('LLM_PROVIDER_NAME', 'gcp')
    }


def create_provider_from_env():
    """
    Create an LLM provider using configuration from environment variables.
    """
    config = load_config_from_env()
    provider_type = config.pop('provider_type')
    # Remove empty values
    config = {k: v for k, v in config.items() if v}
    return create_provider(provider_type, **config)
"""AI Gateway for handling multiple LLM providers with structured output."""

import json
from typing import Dict, Any, Optional, List
from ..core.config import Config, ProviderConfig
from ..models.command import ShellCommand
from .providers import BaseProvider, MockProvider, GeminiProvider, OpenAIProvider, GroqProvider


class AIGateway:
    """Gateway for AI providers with structured output parsing."""
    
    def __init__(self, config: Config):
        self.config = config
        self.providers: Dict[str, BaseProvider] = {
            "mock": MockProvider(),
            "gemini": GeminiProvider(),
            "openai": OpenAIProvider(), 
            "groq": GroqProvider(),
        }
    
    def generate_command(self, prompt: str, provider_name: str) -> ShellCommand:
        """Generate a command using specified provider."""
        
        # Get provider instance
        provider = self.providers.get(provider_name)
        if not provider:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        # Get provider config
        provider_config = self.config.get_provider_config(provider_name)
        
        # Generate response
        try:
            response_text = provider.generate_command(prompt, provider_config)
            
            # Parse structured output
            return self._parse_command_response(response_text)
            
        except Exception as e:
            raise RuntimeError(f"Provider '{provider_name}' failed: {e}")
    
    def _parse_command_response(self, response_text: str) -> ShellCommand:
        """Parse AI response into ShellCommand object."""
        
        try:
            # Try to extract JSON from response
            # Look for JSON braces in the response
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            
            if start == -1 or end == 0:
                raise ValueError("No JSON found in response")
            
            json_str = response_text[start:end]
            data = json.loads(json_str)
            
            # Validate and create ShellCommand
            return ShellCommand(**data)
            
        except (json.JSONDecodeError, ValueError) as e:
            # Fallback: create a basic command from the response
            return ShellCommand(
                command=response_text.strip(),
                explanation="Generated command (parsing failed)",
                safety_flags=["parsing_error"],
                requires_confirmation=True
            )
    
    def list_available_providers(self) -> List[str]:
        """Get list of configured providers with API keys."""
        available = []
        
        for name, provider_config in self.config.providers.items():
            if provider_config.api_key:
                available.append(name)
        
        return available

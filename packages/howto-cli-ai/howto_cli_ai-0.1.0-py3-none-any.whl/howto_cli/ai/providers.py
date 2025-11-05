"""LLM provider implementations."""

import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import traceback

# Import SDKs conditionally to handle missing dependencies
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

from ..core.config import ProviderConfig
from ..models.command import ShellCommand


class BaseProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def generate_command(self, prompt: str, config: ProviderConfig) -> str:
        """Generate command from prompt."""
        pass


class MockProvider(BaseProvider):
    """Mock provider for testing and fallback."""
    
    def generate_command(self, prompt: str, config: ProviderConfig) -> str:
        """Return a mock command for demonstration."""
        return json.dumps({
            "command": "echo 'Mock command - install required dependencies'",
            "explanation": "This is a placeholder command. Configure real providers with 'how setup'.",
            "safety_flags": ["mock_provider"],
            "requires_confirmation": True
        })


class GeminiProvider(BaseProvider):
    """Google Gemini API provider."""
    
    def generate_command(self, prompt: str, config: ProviderConfig) -> str:
        """Generate command using Google Gemini."""
        
        if not GEMINI_AVAILABLE:
            raise RuntimeError("google-generativeai not installed. Install with: pip install google-generativeai")
        
        if not config.api_key:
            raise RuntimeError("GEMINI_API_KEY not configured")
        
        try:
            genai.configure(api_key=config.api_key)
            model = genai.GenerativeModel(config.default_model)
            
            response = model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            raise RuntimeError(f"Gemini API error: {e}")


class OpenAIProvider(BaseProvider):
    """OpenAI API provider."""
    
    def generate_command(self, prompt: str, config: ProviderConfig) -> str:
        """Generate command using OpenAI."""
        
        if not OPENAI_AVAILABLE:
            raise RuntimeError("openai not installed. Install with: pip install openai")
        
        if not config.api_key:
            raise RuntimeError("OPENAI_API_KEY not configured")
        
        try:
            client = openai.OpenAI(api_key=config.api_key)
            
            response = client.chat.completions.create(
                model=config.default_model,
                messages=[
                    {"role": "system", "content": "You are a shell command generator. Always return valid JSON that matches the required schema."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
            )
            
            return response.choices[0].message.content or ""
            
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {e}")


class GroqProvider(BaseProvider):
    """Groq API provider."""
    
    def generate_command(self, prompt: str, config: ProviderConfig) -> str:
        """Generate command using Groq."""
        
        if not GROQ_AVAILABLE:
            raise RuntimeError("groq not installed. Install with: pip install groq")
        
        if not config.api_key:
            raise RuntimeError("GROQ_API_KEY not configured")
        
        try:
            client = groq.Groq(api_key=config.api_key)
            
            response = client.chat.completions.create(
                model=config.default_model,
                messages=[
                    {"role": "system", "content": "You are a shell command generator. Always return valid JSON that matches the required schema."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
            )
            
            return response.choices[0].message.content or ""
            
        except Exception as e:
            raise RuntimeError(f"Groq API error: {e}")

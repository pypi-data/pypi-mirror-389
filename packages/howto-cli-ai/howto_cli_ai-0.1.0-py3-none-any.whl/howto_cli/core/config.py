"""Configuration management with secure API key storage."""

import os
import platform
import json
from typing import Dict, Optional, Any
from pathlib import Path
from pydantic import BaseModel, Field, field_validator


class ProviderConfig(BaseModel):
    """Configuration for an LLM provider."""
    
    api_key_env_var: str
    default_model: str
    available_models: list[str] = Field(default_factory=list)
    
    @property
    def api_key(self) -> Optional[str]:
        """Get API key from environment variables first, then config file."""
        # For mock provider, always return a fake key
        if self.api_key_env_var == "MOCK_API_KEY":
            return "mock-key-for-testing"
        
        # First try environment variable
        env_key = os.getenv(self.api_key_env_var)
        if env_key:
            return env_key
        
        # Then try stored config file
        # Extract provider name from environment variable (strip "_API_KEY" suffix)
        provider_name = self.api_key_env_var.replace("_API_KEY", "").lower()
        
        # Load config to get stored API key
        try:
            config = Config.load()
            return config.get_stored_api_key(provider_name)
        except Exception:
            return None
    
    @property 
    def has_api_key(self) -> bool:
        """Check if API key is available for a non-mock provider."""
        if self.api_key_env_var == "MOCK_API_KEY":
            return True  # Mock always has a key
        return bool(self.api_key)


class Config(BaseModel):
    """Main application configuration."""
    
    default_provider: str = Field(default_factory=lambda: Config.get_default_provider())
    providers: Dict[str, ProviderConfig] = Field(default_factory=lambda: {
        "mock": ProviderConfig(
            api_key_env_var="MOCK_API_KEY",
            default_model="mock-model",
            available_models=["mock-model"]
        ),
        "gemini": ProviderConfig(
            api_key_env_var="GEMINI_API_KEY",
            default_model="gemini-2.5-flash",
            available_models=["gemini-2.5-pro", "gemini-2.5-flash"]
        ),
        "openai": ProviderConfig(
            api_key_env_var="OPENAI_API_KEY", 
            default_model="gpt-3.5-turbo",
            available_models=["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"]
        ),
        "groq": ProviderConfig(
            api_key_env_var="GROQ_API_KEY",
            default_model="llama-3.3-70b-versatile", 
            available_models=["llama-3.3-70b-versatile", "llama-3.1-70b-versatile", "mixtral-8x7b-32768"]
        )
    })
    
    @staticmethod
    def get_config_dir() -> Path:
        """Get the configuration directory path."""
        home = Path.home()
        config_dir = home / ".howto-cli-ai"
        config_dir.mkdir(exist_ok=True)
        return config_dir
    
    @staticmethod
    def get_config_file() -> Path:
        """Get the configuration file path."""
        return Config.get_config_dir() / "config.json"
    
    @staticmethod
    def get_default_provider() -> str:
        """Get default provider from environment variable or fallback to 'gemini'."""
        env_provider = os.getenv('HOW_DEFAULT_PROVIDER')
        # Only return if it's a valid provider
        valid_providers = ["mock", "gemini", "openai", "groq"]
        if env_provider and env_provider in valid_providers:
            return env_provider
        return "gemini"
    
    @field_validator('default_provider')
    @classmethod
    def validate_provider_exists(cls, v, info):
        if 'providers' in info.data and v not in info.data['providers']:
            raise ValueError(f"Provider '{v}' not configured")
        return v
    
    @classmethod
    def load(cls) -> "Config":
        """Load configuration from config file or environment and defaults."""
        config_file = cls.get_config_file()
        
        # Try to load from config file first
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                
                # Extract api_keys before creating config (since base class doesn't have this field)
                api_keys = config_data.pop("api_keys", {})
                
                # Create config from file data
                config = cls(**config_data)
                
                # Store api_keys for later access
                config._stored_api_keys = api_keys
                
                return config
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Warning: Failed to load config file, using defaults: {e}")
        
        # Fallback to environment-based configuration
        default_provider = cls.get_default_provider()
        config = cls(default_provider=default_provider)
        config._stored_api_keys = {}
        return config
    
    def save(self) -> None:
        """Save configuration to config file."""
        config_file = self.get_config_file()
        
        # Convert to dictionary
        config_data = self.model_dump()
        
        # Write to file
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def set_api_key(self, provider_name: str, api_key: str, set_as_default: bool = True) -> None:
        """Store API key in config file."""
        # Add api_key field to provider configuration
        if provider_name not in self.providers:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        # Update environment variable for immediate use
        provider_env_var = self.providers[provider_name].api_key_env_var
        os.environ[provider_env_var] = api_key
        
        # Save config to file with API key
        config_file = self.get_config_file()
        
        # Load existing config if it exists
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
            except (json.JSONDecodeError, IOError):
                config_data = self.model_dump()
        else:
            config_data = self.model_dump()
        
        # Ensure api_keys section exists
        if "api_keys" not in config_data:
            config_data["api_keys"] = {}
        config_data["api_keys"][provider_name] = api_key
        
        # Update default provider if requested
        if set_as_default or "default_provider" not in config_data:
            config_data["default_provider"] = provider_name
        
        # Write to file
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def get_stored_api_key(self, provider_name: str) -> Optional[str]:
        """Get stored API key from config file."""
        # First check the in-memory stored keys
        if hasattr(self, '_stored_api_keys'):
            return self._stored_api_keys.get(provider_name)
        
        # Fallback to reading from file
        config_file = self.get_config_file()
        
        if not config_file.exists():
            return None
        
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            return config_data.get("api_keys", {}).get(provider_name)
        except (json.JSONDecodeError, KeyError):
            return None
    
    def get_provider_config(self, provider_name: str) -> ProviderConfig:
        """Get configuration for a specific provider."""
        if provider_name not in self.providers:
            raise ValueError(f"Unknown provider: {provider_name}")
        return self.providers[provider_name]
    
    def validate_provider_key(self, provider_name: str) -> bool:
        """Check if API key is available for a provider."""
        try:
            provider_config = self.get_provider_config(provider_name)
            return provider_config.has_api_key
        except ValueError:
            return False


def get_system_info() -> Dict[str, str]:
    """Get system information for context generation."""
    return {
        "os": platform.system().lower(),
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "shell": os.getenv("SHELL", "unknown"),
    }

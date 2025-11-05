"""Tests for configuration management."""

import pytest
import os
import shutil
from pathlib import Path
from howto_cli.core.config import Config, ProviderConfig, get_system_info


class TestConfig:
    """Test configuration loading and validation."""
    
    def test_default_config(self):
        """Test default configuration is valid."""
        config = Config()
        assert config.default_provider in ["gemini", "openai", "groq", "mock"]
        assert len(config.providers) == 4
        assert "mock" in config.providers
    
    def test_provider_config(self):
        """Test provider configuration."""
        config = Config()
        gemini = config.get_provider_config("gemini")
        assert gemini.api_key_env_var == "GEMINI_API_KEY"
        assert gemini.default_model == "gemini-2.5-flash"
    
    def test_invalid_provider(self):
        """Test error handling for unknown providers."""
        config = Config()
        with pytest.raises(ValueError):
            config.get_provider_config("unknown")
    
    def test_provider_key_validation(self):
        """Test API key validation."""
        # Save original env var
        original_gemini = os.environ.get("GEMINI_API_KEY")
        original_openai = os.environ.get("OPENAI_API_KEY")
        original_groq = os.environ.get("GROQ_API_KEY")
        
        try:
            # Clear API keys for testing
            for key in ["GEMINI_API_KEY", "OPENAI_API_KEY", "GROQ_API_KEY"]:
                if key in os.environ:
                    del os.environ[key]
            
            # Clean up existing config file for this test
            config_dir = Path.home() / ".howto-cli"
            if config_dir.exists():
                shutil.rmtree(config_dir)
            
            config = Config()
            
            # Should return False when env var not set
            assert not config.validate_provider_key("gemini")
            
            # Should return False for invalid provider
            assert not config.validate_provider_key("unknown")
            
        finally:
            # Restore original env vars
            if original_gemini:
                os.environ["GEMINI_API_KEY"] = original_gemini
            if original_openai:
                os.environ["OPENAI_API_KEY"] = original_openai
            if original_groq:
                os.environ["GROQ_API_KEY"] = original_groq


class TestSystemInfo:
    """Test system information gathering."""
    
    def test_get_system_info(self):
        """Test system info structure."""
        info = get_system_info()
        
        required_keys = ["os", "platform", "python_version", "shell"]
        for key in required_keys:
            assert key in info
            assert isinstance(info[key], str)

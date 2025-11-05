"""Tests for AI Gateway."""

import pytest
from howto_cli.core.config import Config
from howto_cli.ai.gateway import AIGateway
from howto_cli.models.command import ShellCommand


class TestAIGateway:
    """Test AI Gateway functionality."""
    
    def test_gateway_initialization(self):
        """Test gateway can be initialized."""
        config = Config()
        gateway = AIGateway(config)
        assert gateway.config == config
        assert "mock" in gateway.providers
        assert "gemini" in gateway.providers
    
    def test_mock_provider_response(self):
        """Test mock provider returns valid response."""
        config = Config()
        gateway = AIGateway(config)
        
        # Use mock provider which doesn't require API keys
        result = gateway.generate_command("test prompt", "mock")
        
        # Should return valid ShellCommand
        assert isinstance(result, ShellCommand)
        assert result.command
        assert result.explanation
        assert "mock_provider" in result.safety_flags
    
    def test_parse_command_response_success(self):
        """Test successful JSON parsing."""
        config = Config()
        gateway = AIGateway(config)
        
        response = '''
        Here's the command:
        {
            "command": "ls -la",
            "explanation": "List files in long format",
            "safety_flags": ["safe"],
            "requires_confirmation": true
        }
        '''
        
        result = gateway._parse_command_response(response)
        assert isinstance(result, ShellCommand)
        assert result.command == "ls -la"
    
    def test_parse_command_response_fallback(self):
        """Test fallback when JSON parsing fails."""
        config = Config()
        gateway = AIGateway(config)
        
        response = "ls -la"  # Plain text without JSON
        
        result = gateway._parse_command_response(response)
        assert isinstance(result, ShellCommand)
        assert result.command == "ls -la"
        assert "parsing_error" in result.safety_flags
    
    def test_unknown_provider_error(self):
        """Test error handling for unknown providers."""
        config = Config()
        gateway = AIGateway(config)
        
        with pytest.raises(ValueError, match="Unknown provider"):
            gateway.generate_command("test", "unknown")

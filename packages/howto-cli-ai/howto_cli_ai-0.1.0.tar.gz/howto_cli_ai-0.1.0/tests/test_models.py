"""Tests for Pydantic models."""

import pytest
from howto_cli.models.command import ShellCommand


class TestShellCommand:
    """Test ShellCommand model validation."""
    
    def test_valid_command(self):
        """Test creating valid shell command."""
        cmd = ShellCommand(
            command="ls -la",
            explanation="Lists all files in long format",
            safety_flags=["safe"],
            requires_confirmation=True
        )
        assert cmd.command == "ls -la"
        assert cmd.explanation == "Lists all files in long format"
        assert "safe" in cmd.safety_flags
    
    def test_empty_command_invalid(self):
        """Test empty command raises validation error."""
        with pytest.raises(ValueError):
            ShellCommand(
                command="",
                explanation="test"
            )
    
    def test_destructive_detection(self):
        """Test destructive command detection."""
        destructive = ShellCommand(
            command="rm -rf /",
            explanation="Delete everything"
        )
        assert destructive.is_destructive()
        
        safe = ShellCommand(
            command="ls -la",
            explanation="List files"
        )
        assert not safe.is_destructive()
    
    def test_system_modifying_detection(self):
        """Test system modification detection."""
        system_cmd = ShellCommand(
            command="systemctl restart nginx",
            explanation="Restart nginx service"
        )
        assert system_cmd.is_system_modifying()
        
        user_cmd = ShellCommand(
            command="cp file.txt backup.txt",
            explanation="Copy file"
        )
        assert not user_cmd.is_system_modifying()

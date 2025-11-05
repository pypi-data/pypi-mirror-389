"""Shell command schema for structured output validation."""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class ShellCommand(BaseModel):
    """Structured representation of a generated shell command."""
    
    command: str = Field(..., description="The shell command to execute")
    explanation: str = Field(..., description="Brief explanation of what the command does")
    safety_flags: List[str] = Field(default_factory=list, description="Safety concerns about the command")
    requires_confirmation: bool = Field(default=True, description="Whether command needs user confirmation")
    
    @field_validator('command')
    @classmethod
    def validate_command_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Command cannot be empty")
        return v.strip()
    
    @field_validator('explanation')
    @classmethod
    def validate_explanation_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Explanation cannot be empty")
        return v.strip()
    
    def is_destructive(self) -> bool:
        """Check if command has destructive flags."""
        destructive_flags = [
            'rm', 'delete', 'remove', 'format', 'fdisk', 
            'chmod', 'chown', 'systemctl', 'iptables'
        ]
        return any(flag in self.command.lower() for flag in destructive_flags)
    
    def is_system_modifying(self) -> bool:
        """Check if command modifies system state."""
        system_commands = [
            'systemctl', 'service', 'iptables', 'ufw', 'mount',
            'umount', 'fdisk', 'mkfs', 'reboot', 'shutdown'
        ]
        return any(cmd in self.command.lower() for cmd in system_commands)

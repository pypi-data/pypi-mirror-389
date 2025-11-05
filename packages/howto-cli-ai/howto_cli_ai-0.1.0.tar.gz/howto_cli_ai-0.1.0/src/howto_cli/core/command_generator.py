"""Core command generation logic with OS detection and prompt assembly."""

import platform
import os
from typing import List, Optional
from ..core.config import Config, get_system_info
from ..ai.gateway import AIGateway
from ..models.command import ShellCommand


class CommandGenerator:
    """Generates shell commands from natural language descriptions."""
    
    def __init__(self, config: Config):
        self.config = config
        self.ai_gateway = AIGateway(config)
        self.system_info = get_system_info()
    
    def generate_command(self, task: str, provider_override: Optional[str] = None) -> ShellCommand:
        """Generate a shell command from natural language input."""
        
        # Determine which provider to use
        provider_name = provider_override or self.config.default_provider
        
        # Validate provider has API key
        if not self.config.validate_provider_key(provider_name):
            raise ValueError(f"Provider '{provider_name}' not configured. Run 'how setup' first.")
        
        # Generate prompt with context
        prompt = self._build_prompt(task)
        
        # Get command from AI provider
        try:
            command = self.ai_gateway.generate_command(prompt, provider_name)
            return command
        except Exception as e:
            raise RuntimeError(f"Failed to generate command: {e}")
    
    def _build_prompt(self, task: str) -> str:
        """Build context-aware prompt for command generation."""
        
        os_name = self.system_info["os"]
        shell = self.system_info["shell"]
        
        prompt = f"""
You are an expert system administrator and shell command generator. 
Convert the following natural language request into a precise shell command.

SYSTEM CONTEXT:
- Operating System: {os_name}
- Shell Environment: {shell}
- Current Working Directory: {os.getcwd()}

REQUEST: {task}

Return the response in this exact JSON format:
{{
  "command": "the shell command to execute",
  "explanation": "brief explanation of what the command does",
  "safety_flags": ["list of any safety concerns", "e.g., 'destructive operation', 'system modification'"],
  "requires_confirmation": true
}}

Guidelines:
- Use commands appropriate for {os_name}
- Avoid destructive operations unless explicitly requested
- Include safety warnings for risky commands
- Compound commands should use && or ; appropriately
- Escape special characters properly
- Be specific and precise in the generated command
"""
        
        return prompt.strip()
    
    def detect_os_specific_needs(self, task: str) -> List[str]:
        """Detect OS-specific considerations for the task."""
        considerations = []
        os_name = self.system_info["os"].lower()
        
        if os_name == "windows":
            considerations.append("Use PowerShell cmdlets or Windows command syntax")
        elif os_name in ["linux", "darwin"]:
            considerations.append("Use Unix/Linux command syntax")
        
        return considerations

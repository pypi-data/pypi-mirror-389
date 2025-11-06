"""CLI engine module for command routing and handler management."""
from typing import Dict, Callable, Any, Optional
import argparse


class CommandRouter:
    """Routes CLI commands to appropriate handler functions."""
    
    def __init__(self):
        """Initialize command router with empty handler registry."""
        self._handlers: Dict[str, Callable] = {}
    
    def register(self, command: str, handler: Callable):
        """Register a command handler.
        
        Args:
            command: Command name (e.g., 'optimize', 'analyze')
            handler: Function to handle the command
        """
        self._handlers[command] = handler
    
    def route(self, command: str, args: argparse.Namespace) -> Any:
        """Route a command to its handler.
        
        Args:
            command: Command name
            args: Parsed command-line arguments
            
        Returns:
            Result from handler function
            
        Raises:
            ValueError: If command is not registered
        """
        if command not in self._handlers:
            raise ValueError(f"Unknown command: {command}")
        
        handler = self._handlers[command]
        return handler(args)
    
    def get_handlers(self) -> Dict[str, Callable]:
        """Get all registered handlers.
        
        Returns:
            Dictionary mapping command names to handlers
        """
        return self._handlers.copy()


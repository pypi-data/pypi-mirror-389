# lib/prompt.py
# Prompt wrapper with compile utilities

from typing import Any, Dict, Optional
from .variables import inject_variables


class Prompt:
    """Prompt wrapper class with compilation support"""

    def __init__(self, content: Any):
        """
        Initialize Prompt with content

        Args:
            content: The prompt content (string for text type, list for chat type)
        """
        self._content = content
        self._type = 'chat' if isinstance(content, list) else 'text'

    def get_content(self) -> Any:
        """Get the prompt content"""
        return self._content

    def get_type(self) -> str:
        """Get the prompt type (text or chat)"""
        return self._type

    def compile(self, variables: Optional[Dict[str, Any]] = None, **kwargs) -> 'Prompt':
        """
        Compile prompt with variables

        Args:
            variables: Dictionary of variables to inject
            **kwargs: Additional variables passed as keyword arguments

        Returns:
            New Prompt instance with variables injected
        """
        # Merge variables dict and kwargs
        all_variables = {}
        if variables:
            all_variables.update(variables)
        if kwargs:
            all_variables.update(kwargs)

        compiled_content = inject_variables(self._content, all_variables if all_variables else None)
        return Prompt(compiled_content)

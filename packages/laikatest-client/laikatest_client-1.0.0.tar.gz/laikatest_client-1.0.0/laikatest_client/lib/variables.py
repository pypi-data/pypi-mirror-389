# lib/variables.py
# Variable injection utilities for LaikaTest SDK

import re
from typing import Any, Dict, Optional
from .errors import ValidationError


def inject_variables_into_string(text: str, variables: Optional[Dict[str, Any]]) -> str:
    """Inject variables into a string using {{variable}} syntax"""
    if not text or not isinstance(text, str):
        return text

    regex = re.compile(r'\{\{([^}]+)\}\}')

    def replace_variable(match):
        variable_name = match.group(1).strip()

        if variables and variable_name in variables:
            return str(variables[variable_name])

        # Return original placeholder if variable not found
        return match.group(0)

    return regex.sub(replace_variable, text)


def is_plain_object(value: Any) -> bool:
    """Check if value is a plain dict object"""
    return isinstance(value, dict) and type(value) == dict


def inject_variables_into_value(value: Any, variables: Optional[Dict[str, Any]]) -> Any:
    """Recursively inject variables into any value type"""
    if isinstance(value, str):
        return inject_variables_into_string(value, variables)

    if isinstance(value, list):
        return [inject_variables_into_value(item, variables) for item in value]

    if is_plain_object(value):
        return {
            key: inject_variables_into_value(val, variables)
            for key, val in value.items()
        }

    return value


def inject_variables_into_chat(messages: list, variables: Optional[Dict[str, Any]]) -> list:
    """Inject variables into chat-type prompts (array of message objects)"""
    if not isinstance(messages, list):
        return messages

    return [inject_variables_into_value(message, variables) for message in messages]


def inject_variables(content: Any, variables: Optional[Dict[str, Any]]) -> Any:
    """
    Main function to inject variables into content (handles both text and chat types)

    Args:
        content: The content to inject variables into (string, list, or dict)
        variables: Dictionary of variables to inject

    Returns:
        Content with variables injected
    """
    # If no variables provided, return content as-is
    if not variables or len(variables) == 0:
        return content

    # Validate variables is a dict
    if not isinstance(variables, dict):
        raise ValidationError('Variables must be an object')

    # Handle text-type prompts (string)
    if isinstance(content, str):
        return inject_variables_into_string(content, variables)

    # Handle chat-type prompts (array) or plain objects
    if isinstance(content, (list, dict)):
        return inject_variables_into_value(content, variables)

    return content

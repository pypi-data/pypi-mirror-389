# lib/validation.py
# Input validation utilities for LaikaTest SDK

import re
from .errors import ValidationError


def validate_api_key(api_key):
    """Validate API key format"""
    if not api_key or not isinstance(api_key, str):
        raise ValidationError('API key is required and must be a string')


def validate_prompt_name(prompt_name):
    """Validate prompt name is a non-empty string"""
    if not prompt_name or not isinstance(prompt_name, str) or not prompt_name.strip():
        raise ValidationError('Prompt name is required and must be a non-empty string')


def validate_version_id(version_id):
    """Validate version ID is a safe string (if provided)"""
    if not version_id:
        return None  # versionId is optional

    if not isinstance(version_id, str):
        raise ValidationError('Version ID must be a string')

    if len(version_id) > 128:
        raise ValidationError('Version ID is too long. Maximum length is 128 characters.')

    # Allow either digits only (e.g., "10") or "v" followed by digits (e.g., "v10")
    version_id_regex = re.compile(r'^(?:v?\d+)$')
    if not version_id_regex.match(version_id):
        raise ValidationError('Version ID must be digits only (e.g., "10") or "v" followed by digits (e.g., "v10").')

    # Remove 'v' prefix if present
    return version_id.lstrip('v')

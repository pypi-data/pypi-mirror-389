# __init__.py
# LaikaTest SDK - Main entry point

from .lib.cache import PromptCache
from .lib.prompt_utils import fetch_prompt
from .lib.validation import validate_api_key, validate_prompt_name, validate_version_id
from .lib.prompt import Prompt
from .lib.errors import (
    LaikaServiceError,
    NetworkError,
    ValidationError,
    AuthenticationError
)


class LaikaTest:
    """Main LaikaTest client class"""

    def __init__(self, api_key: str, **options):
        """
        Initialize client with API key

        Args:
            api_key: API authentication key
            **options: Optional configuration
                - base_url: Base URL for API (default: https://api.laikatest.com)
                - timeout: Request timeout in milliseconds (default: 10000)
                - cache_ttl: Cache TTL in milliseconds (default: 30 minutes)
                - cache_enabled: Enable/disable caching (default: True)
        """
        validate_api_key(api_key)

        self.api_key = api_key
        self.base_url = options.get('base_url', 'https://api.laikatest.com')
        self.timeout = options.get('timeout', 10000)

        cache_ttl = options.get('cache_ttl', 30 * 60 * 1000)
        self.cache_enabled = options.get('cache_enabled', True)
        self.cache = PromptCache(cache_ttl) if self.cache_enabled else None

    def get_prompt(self, prompt_name: str, **options) -> Prompt:
        """
        Get prompt content by name with optional version

        Args:
            prompt_name: Name of the prompt to fetch
            **options: Optional parameters
                - version_id: Specific version ID to fetch
                - bypass_cache: Skip cache lookup (default: False)

        Returns:
            Prompt instance
        """
        validate_prompt_name(prompt_name)

        version_id = validate_version_id(options.get('version_id'))
        bypass_cache = options.get('bypass_cache', False)

        # Check cache first if enabled and not bypassed
        if self.cache is not None and not bypass_cache:
            cached = self.cache.get(prompt_name, version_id)
            if cached:
                return Prompt(cached)

        # Fetch from API
        content = fetch_prompt(
            self.api_key,
            self.base_url,
            prompt_name,
            version_id,
            self.timeout
        )

        # Store in cache if enabled
        if self.cache is not None:
            self.cache.set(prompt_name, version_id, content)

        return Prompt(content)

    def destroy(self) -> None:
        """Cleanup resources and cache"""
        if self.cache:
            self.cache.destroy()


# Export main class and error classes
__all__ = [
    'LaikaTest',
    'Prompt',
    'LaikaServiceError',
    'NetworkError',
    'ValidationError',
    'AuthenticationError'
]

__version__ = "1.0.0"

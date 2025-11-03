# lib/cache.py
# TTL-based caching for LaikaTest SDK

import time
from typing import Optional, Any


class PromptCache:
    """
    TTL-based cache for storing fetched prompts

    Uses lazy cleanup strategy - expired entries are removed on access
    rather than with a background thread. This is more efficient and Pythonic.
    """

    def __init__(self, ttl: int = 30 * 60 * 1000):
        """
        Initialize cache with TTL

        Args:
            ttl: Time-to-live in milliseconds (default: 30 minutes)
        """
        self._cache = {}
        self.ttl = ttl  # TTL in milliseconds
        self._last_cleanup = time.time() * 1000
        self._cleanup_threshold = 5 * 60 * 1000  # Cleanup every 5 minutes
        self.cleanup_interval = None  # For compatibility with tests

    def _current_time_ms(self) -> int:
        """Get current time in milliseconds"""
        return int(time.time() * 1000)

    def _is_expired(self, entry: dict) -> bool:
        """Check if cache entry is expired"""
        return self._current_time_ms() - entry['fetched_at'] > self.ttl

    def _lazy_cleanup(self) -> None:
        """
        Perform cleanup if enough time has passed since last cleanup
        This is called automatically during get/set operations
        """
        current_time = self._current_time_ms()

        # Only cleanup if threshold time has passed
        if current_time - self._last_cleanup < self._cleanup_threshold:
            return

        # Remove expired entries
        expired_keys = [
            key for key, entry in self._cache.items()
            if self._is_expired(entry)
        ]

        for key in expired_keys:
            self._cache.pop(key, None)  # Safe deletion, handles race conditions

        self._last_cleanup = current_time

    def generate_key(self, prompt_name: str, version_id: Optional[str]) -> str:
        """Generate cache key from prompt name and optional version"""
        return f"{prompt_name}:{version_id}" if version_id else prompt_name

    def set(self, prompt_name: str, version_id: Optional[str], content: Any) -> None:
        """
        Store prompt content with timestamp

        Performs lazy cleanup if needed before storing.
        """
        self._lazy_cleanup()

        key = self.generate_key(prompt_name, version_id)
        self._cache[key] = {
            'content': content,
            'fetched_at': self._current_time_ms()
        }

    def get(self, prompt_name: str, version_id: Optional[str]) -> Optional[Any]:
        """
        Retrieve prompt content if not expired

        Returns None if entry doesn't exist or is expired.
        Performs lazy cleanup if needed before retrieval.
        """
        self._lazy_cleanup()

        key = self.generate_key(prompt_name, version_id)
        entry = self._cache.get(key)

        if not entry:
            return None

        # Check if expired
        if self._is_expired(entry):
            del self._cache[key]
            return None

        return entry['content']

    def cleanup(self) -> None:
        """
        Manually remove all expired entries from cache

        This is called automatically during normal operations,
        but can be called manually if needed.
        """
        expired_keys = [
            key for key, entry in self._cache.items()
            if self._is_expired(entry)
        ]

        for key in expired_keys:
            self._cache.pop(key, None)  # Safe deletion, handles race conditions

        self._last_cleanup = self._current_time_ms()

    def clear(self) -> None:
        """Clear all cache entries immediately"""
        self._cache.clear()

    def destroy(self) -> None:
        """
        Clear all cache entries and cleanup resources

        In this implementation, there are no background threads to stop,
        so this just clears the cache.
        """
        self._cache.clear()
        self.cleanup_interval = None  # For compatibility with tests

    def __len__(self) -> int:
        """Return number of cached entries (including expired ones)"""
        return len(self._cache)

    def __contains__(self, key: str) -> bool:
        """Check if key exists in cache (doesn't check expiry)"""
        return key in self._cache

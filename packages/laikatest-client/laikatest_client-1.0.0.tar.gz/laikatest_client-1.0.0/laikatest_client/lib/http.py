# lib/http.py
# HTTP request utilities for LaikaTest SDK

import urllib.request
import urllib.error
from urllib.parse import urlparse
from typing import Dict, Tuple


def validate_secure_url(url: str) -> None:
    """Validate URL uses HTTPS (except localhost for testing)"""
    parsed = urlparse(url)
    scheme = (parsed.scheme or '').lower()

    if scheme == 'http':
        is_localhost = parsed.hostname in ('localhost', '127.0.0.1', '::1')
        if not is_localhost:
            raise ValueError('HTTP protocol is not allowed for security reasons. Please use HTTPS.')


def make_http_request(url: str, headers: Dict[str, str], timeout: float) -> Tuple[int, str]:
    """Make HTTP request with timeout and error handling"""
    validate_secure_url(url)

    # Convert timeout from milliseconds to seconds
    timeout_seconds = timeout / 1000.0

    req = urllib.request.Request(url, headers=headers, method='GET')

    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
            data = response.read().decode('utf-8')
            return response.status, data
    except urllib.error.URLError as e:
        if isinstance(e, urllib.error.HTTPError):
            # HTTP error with status code
            data = e.read().decode('utf-8')
            return e.code, data

        # Network error without status code
        raise e

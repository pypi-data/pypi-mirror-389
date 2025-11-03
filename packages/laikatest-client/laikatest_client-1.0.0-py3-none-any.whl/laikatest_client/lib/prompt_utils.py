# lib/prompt_utils.py
# Prompt-related operations for LaikaTest SDK

import json
from urllib.parse import urlencode, quote
from typing import Optional, Any
from .http import make_http_request
from .errors import LaikaServiceError, NetworkError, AuthenticationError


def build_prompt_url(base_url: str, prompt_name: str, version_id: Optional[str]) -> str:
    """Build API URL for fetching prompt"""
    encoded_name = quote(prompt_name, safe='')

    # Build query parameters
    params = {}
    if version_id:
        params['version_number'] = version_id

    query_string = urlencode(params) if params else ''
    url = f"{base_url}/api/v1/prompts/by-name/{encoded_name}"

    if query_string:
        url = f"{url}?{query_string}"

    return url


def parse_api_response(data: str) -> dict:
    """Parse API response JSON"""
    try:
        return json.loads(data)
    except json.JSONDecodeError as e:
        raise ValueError('Invalid JSON response from server') from e


def handle_api_error(status_code: int, parsed: dict) -> None:
    """Handle API error response"""
    if status_code == 401:
        error_msg = parsed.get('error', 'Invalid API key')
        raise AuthenticationError(error_msg)

    error_msg = parsed.get('error', 'API request failed')
    raise LaikaServiceError(error_msg, status_code, parsed)


def fetch_prompt(
    api_key: str,
    base_url: str,
    prompt_name: str,
    version_id: Optional[str],
    timeout: int
) -> Any:
    """
    Fetch prompt from API

    Args:
        api_key: API authentication key
        base_url: Base URL for API
        prompt_name: Name of the prompt to fetch
        version_id: Optional version ID
        timeout: Request timeout in milliseconds

    Returns:
        Prompt content (string or list)
    """
    url = build_prompt_url(base_url, prompt_name, version_id)

    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    try:
        status_code, response_data = make_http_request(url, headers, timeout)
    except Exception as e:
        raise NetworkError('Failed to connect to LaikaTest API', e) from e

    try:
        parsed = parse_api_response(response_data)
    except ValueError as e:
        error_msg = 'Invalid JSON response from server'
        if not response_data or not response_data.strip():
            error_msg = 'Empty response body from server'
        # Preserve raw payload so callers can introspect unexpected responses.
        raise LaikaServiceError(error_msg, status_code, {'raw': response_data}) from e

    if status_code == 200 and parsed.get('success'):
        try:
            # Validate response structure
            if 'data' not in parsed:
                raise LaikaServiceError('Invalid response: missing data field', status_code, parsed)

            data_obj = parsed['data']
            if 'content' not in data_obj or 'type' not in data_obj:
                raise LaikaServiceError('Invalid response: missing content or type field', status_code, parsed)

            # Parse content
            data = json.loads(data_obj['content'])

            # Return based on type
            if data_obj['type'] == 'text':
                if not isinstance(data, list) or len(data) == 0:
                    raise LaikaServiceError('Invalid response: text type must have non-empty array', status_code, parsed)
                if 'content' not in data[0]:
                    raise LaikaServiceError('Invalid response: text content missing', status_code, parsed)
                return data[0]['content']
            else:
                return data

        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise LaikaServiceError(f'Invalid response format: {e}', status_code, parsed) from e

    handle_api_error(status_code, parsed)

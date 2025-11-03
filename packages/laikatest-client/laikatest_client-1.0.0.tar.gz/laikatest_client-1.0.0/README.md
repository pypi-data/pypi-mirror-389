# LaikaTest Python Client

Official Python SDK for fetching and managing LaikaTest prompt templates via API.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)

## Features

- 🚀 **Simple API** - Clean, intuitive interface for fetching prompts
- 💾 **Built-in Caching** - TTL-based caching with automatic cleanup
- 🔒 **Secure** - HTTPS enforcement with localhost exception for testing
- 🎯 **Type Hints** - Full type annotations for better IDE support
- 🐍 **Pythonic** - Follows Python best practices and conventions
- 📦 **Zero Dependencies** - Uses only Python standard library
- ⚡ **Flexible** - Supports both dict and kwargs for parameters
- 🔄 **Variable Injection** - Template variable replacement with `{{variable}}` syntax

## Installation

```bash
# From source
pip install -e .

# From PyPI (when published)
pip install laikatest-client
```

## Quick Start

```python
from laikatest_client import LaikaTest

# Initialize the client
client = LaikaTest('your-api-key')

# Fetch a prompt
prompt = client.get_prompt('my-prompt')

# Get content
content = prompt.get_content()
print(content)

# Compile with variables (Pythonic kwargs!)
compiled = prompt.compile(name='John', role='developer')
print(compiled.get_content())

# Clean up when done
client.destroy()
```

## Usage Examples

### Basic Usage

```python
from laikatest_client import LaikaTest

client = LaikaTest(
    'your-api-key',
    base_url='https://api.laikatest.com',  # optional
    timeout=10000,  # milliseconds (optional)
    cache_enabled=True,  # optional
    cache_ttl=1800000  # 30 minutes in ms (optional)
)

# Fetch latest version
prompt = client.get_prompt('welcome-message')

# Get prompt details
print(f"Type: {prompt.get_type()}")  # 'text' or 'chat'
print(f"Content: {prompt.get_content()}")
```

### Version Management

```python
# Fetch specific version
prompt_v10 = client.get_prompt('my-prompt', version_id='v10')
prompt_v5 = client.get_prompt('my-prompt', version_id='5')  # 'v' prefix optional
```

### Variable Injection

The SDK supports `{{variable}}` syntax for template variables.

**Using kwargs (Recommended - Pythonic!):**
```python
prompt = client.get_prompt('greeting')
compiled = prompt.compile(
    name='Alice',
    role='Engineer',
    company='TechCorp'
)
```

**Using dictionary:**
```python
variables = {
    'name': 'Alice',
    'role': 'Engineer',
    'company': 'TechCorp'
}
compiled = prompt.compile(variables)
```

**Combining both (kwargs override dict values):**
```python
base_vars = {'name': 'Alice', 'role': 'Engineer'}
compiled = prompt.compile(base_vars, role='Senior Engineer', team='Backend')
# Result: name='Alice', role='Senior Engineer', team='Backend'
```

### Text vs Chat Prompts

**Text Prompt:**
```python
prompt = client.get_prompt('simple-text')
print(prompt.get_type())  # 'text'
content = prompt.get_content()  # Returns string
```

**Chat Prompt:**
```python
prompt = client.get_prompt('conversation')
print(prompt.get_type())  # 'chat'
messages = prompt.get_content()  # Returns list of message objects

# Compile with variables
compiled = prompt.compile(user_name='John', topic='Python')
```

### Cache Control

```python
# Use cached version (default)
prompt1 = client.get_prompt('my-prompt')

# Force fresh fetch, bypass cache
prompt2 = client.get_prompt('my-prompt', bypass_cache=True)

# Disable cache entirely
client_no_cache = LaikaTest('api-key', cache_enabled=False)
```

### Error Handling

```python
from laikatest_client import (
    LaikaTest,
    ValidationError,
    AuthenticationError,
    NetworkError,
    LaikaServiceError
)

try:
    client = LaikaTest('api-key')
    prompt = client.get_prompt('my-prompt')

except ValidationError as e:
    print(f"Invalid input: {e}")

except AuthenticationError as e:
    print(f"Auth failed: {e}")

except NetworkError as e:
    print(f"Network issue: {e}")
    print(f"Original error: {e.original_error}")

except LaikaServiceError as e:
    print(f"API error: {e}")
    print(f"Status code: {e.status_code}")
    print(f"Response: {e.response}")
```

## API Reference

### `LaikaTest`

Main client class for interacting with LaikaTest API.

**Constructor:**
```python
LaikaTest(api_key: str, **options)
```

**Parameters:**
- `api_key` (str, required): Your LaikaTest API key
- `base_url` (str, optional): API base URL (default: 'https://api.laikatest.com')
- `timeout` (int, optional): Request timeout in milliseconds (default: 10000)
- `cache_enabled` (bool, optional): Enable caching (default: True)
- `cache_ttl` (int, optional): Cache TTL in milliseconds (default: 1800000 / 30 min)

**Methods:**

#### `get_prompt(prompt_name: str, **options) -> Prompt`

Fetch a prompt by name.

**Parameters:**
- `prompt_name` (str, required): Name of the prompt
- `version_id` (str, optional): Specific version to fetch
- `bypass_cache` (bool, optional): Skip cache lookup (default: False)

**Returns:** `Prompt` instance

#### `destroy() -> None`

Cleanup resources and stop cache cleanup thread.

### `Prompt`

Wrapper class for prompt content with compilation support.

**Methods:**

#### `get_content() -> Union[str, List]`

Returns the prompt content (string for text, list for chat).

#### `get_type() -> str`

Returns prompt type: 'text' or 'chat'.

#### `compile(variables: dict = None, **kwargs) -> Prompt`

Compile prompt with variable injection.

**Parameters:**
- `variables` (dict, optional): Dictionary of variables to inject
- `**kwargs`: Variables as keyword arguments (merged with dict)

**Returns:** New `Prompt` instance with variables injected

### Exception Classes

- **`ValidationError`**: Invalid input parameters
- **`AuthenticationError`**: Authentication failed (401)
- **`NetworkError`**: Network connectivity issues
  - Properties: `original_error`
- **`LaikaServiceError`**: API/service errors (4xx, 5xx)
  - Properties: `status_code`, `response`

## Architecture

The SDK is organized into focused modules:

```
laikatest_client/
├── __init__.py          # Main client and exports
└── lib/
    ├── cache.py         # TTL-based caching
    ├── errors.py        # Exception classes
    ├── http.py          # HTTP request utilities
    ├── prompt.py        # Prompt wrapper class
    ├── prompt_utils.py  # Prompt fetching logic
    ├── validation.py    # Input validation
    └── variables.py     # Variable injection
```

## Development

### Running Tests

```bash
python test_example.py
```

### Building Distribution

```bash
python setup.py sdist bdist_wheel
```

### Installing in Development Mode

```bash
pip install -e .
```

## Comparison with JavaScript Client

This Python SDK maintains **100% logic parity** with the JavaScript client while adding Python-specific enhancements:

| Feature | JavaScript | Python |
|---------|------------|--------|
| Core Logic | ✅ | ✅ Identical |
| Caching | ✅ | ✅ Identical (threading) |
| Error Handling | ✅ | ✅ Identical hierarchy |
| Variable Injection | ✅ | ✅ Identical algorithm |
| API | `options = {}` | `**options` (Pythonic) |
| Variable Passing | Dict only | Dict + kwargs ✨ |
| Type Safety | TypeScript `.d.ts` | Type hints ✨ |
| Dependencies | 0 (Node stdlib) | 0 (Python stdlib) ✨ |

See [CODE_COMPARISON.md](../CODE_COMPARISON.md) for detailed comparison.

## Requirements

- Python 3.7 or higher
- No external dependencies (uses standard library only)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/ForecloseAI/laikatest_client_py/issues)
- **Documentation**: [API Docs](https://docs.laikatest.com)

## Contributing

Contributions are welcome! Please ensure:

1. Code follows PEP 8 style guidelines
2. All functions have type hints and docstrings
3. Logic remains consistent with JavaScript client
4. Tests pass

## Changelog

### v1.0.1 (2024)
- Initial release
- Feature parity with JavaScript client v1.0.1
- Added kwargs support for Pythonic API
- Full type hint coverage
- Zero external dependencies

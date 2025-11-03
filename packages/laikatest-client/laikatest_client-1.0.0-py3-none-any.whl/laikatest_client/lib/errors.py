# lib/errors.py
# Custom error classes for LaikaTest SDK


class LaikaServiceError(Exception):
    """API or service-related errors (4xx, 5xx responses)"""

    def __init__(self, message, status_code=None, response=None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class NetworkError(Exception):
    """Network connectivity or timeout errors"""

    def __init__(self, message, original_error=None):
        super().__init__(message)
        self.original_error = original_error


class ValidationError(Exception):
    """Input validation errors"""

    def __init__(self, message):
        super().__init__(message)


class AuthenticationError(Exception):
    """Authentication-related errors"""

    def __init__(self, message):
        super().__init__(message)

"""
SafeKey Lab SDK Exceptions
Custom exception classes for error handling
"""


class SafeKeyLabError(Exception):
    """Base exception for SafeKey Lab SDK"""
    pass


class AuthenticationError(SafeKeyLabError):
    """Raised when authentication fails"""
    pass


class RateLimitError(SafeKeyLabError):
    """Raised when API rate limit is exceeded"""
    pass


class ValidationError(SafeKeyLabError):
    """Raised when request validation fails"""
    pass


class APIError(SafeKeyLabError):
    """Raised when API returns an error"""
    pass


class TimeoutError(SafeKeyLabError):
    """Raised when request times out"""
    pass


class FileProcessingError(SafeKeyLabError):
    """Raised when file processing fails"""
    pass
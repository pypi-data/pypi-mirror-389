"""
Exception classes for B3 Data Client
"""

from typing import Optional, Any


class B3APIError(Exception):
    """Base exception for B3 API errors"""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response: Optional[Any] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response = response


class AuthenticationError(B3APIError):
    """Raised when API key is invalid or missing"""
    pass


class RateLimitError(B3APIError):
    """Raised when rate limit is exceeded"""
    pass


class InsufficientCreditsError(B3APIError):
    """Raised when account has insufficient credits"""
    pass


class ValidationError(B3APIError):
    """Raised when request parameters are invalid"""
    pass

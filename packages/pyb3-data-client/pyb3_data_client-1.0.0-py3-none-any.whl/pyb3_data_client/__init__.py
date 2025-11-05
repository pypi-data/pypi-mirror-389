"""
PyB3 Data Client - Python SDK for B3 Market Data API

Simple, powerful Python client for accessing Brazilian stock market data.

Quick Start:
    >>> from pyb3_data_client import B3Client
    >>>
    >>> client = B3Client(api_key="pk_live_...")
    >>>
    >>> # Get daily data
    >>> df = client.get_daily_data(
    ...     symbols=["PETR4", "VALE3"],
    ...     start_date="2024-01-01",
    ...     end_date="2024-01-31"
    ... )
    >>>
    >>> print(df.head())

For full documentation, visit: https://api.b3data.com/docs
"""

from .client import B3Client
from .exceptions import (
    B3APIError,
    AuthenticationError,
    RateLimitError,
    InsufficientCreditsError,
    ValidationError
)

__version__ = "1.0.0"
__all__ = [
    "B3Client",
    "B3APIError",
    "AuthenticationError",
    "RateLimitError",
    "InsufficientCreditsError",
    "ValidationError"
]

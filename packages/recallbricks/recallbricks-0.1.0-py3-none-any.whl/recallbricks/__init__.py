"""
RecallBricks Python SDK
The Memory Layer for AI

Usage:
    >>> from recallbricks import RecallBricks
    >>> memory = RecallBricks(api_key="your_api_key")
    >>> memory.save("Important information to remember")
    >>> memories = memory.get_all()
"""

from .client import RecallBricks
from .exceptions import (
    RecallBricksError,
    AuthenticationError,
    RateLimitError,
    APIError
)

__version__ = "0.1.0"
__all__ = [
    "RecallBricks",
    "RecallBricksError",
    "AuthenticationError", 
    "RateLimitError",
    "APIError"
]

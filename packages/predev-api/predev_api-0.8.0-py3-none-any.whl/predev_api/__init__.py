"""
predev_api - Python client for the Pre.dev Architect API

Generate comprehensive software specifications using AI.
"""

from .client import PredevAPI, ZippedDocsUrl
from .exceptions import PredevAPIError, AuthenticationError, RateLimitError

__version__ = "0.8.0"
__all__ = ["PredevAPI", "PredevAPIError",
           "AuthenticationError", "RateLimitError", "ZippedDocsUrl"]

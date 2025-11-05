"""
Mercator Python SDK

A drop-in replacement for OpenAI/Anthropic SDKs that provides automatic LLM governance,
policy enforcement, content detection, and compliance logging through the Mercator proxy.

Example:
    >>> from mercator import MercatorClient
    >>> client = MercatorClient(
    ...     api_key="mercator-key-123",
    ...     application="my-app"
    ... )
    >>> response = client.chat.completions.create(
    ...     model="gpt-4",
    ...     messages=[{"role": "user", "content": "Hello"}]
    ... )
    >>> print(response.choices[0].message.content)
"""

from .client import MercatorClient
from .config import MercatorConfig
from .exceptions import (
    AuthenticationError,
    ContentDetectionError,
    MercatorError,
    PolicyViolationError,
    ProviderUnavailableError,
    RateLimitError,
    TimeoutError,
    ValidationError,
)
from .session import SessionContext

__version__ = "0.2.1"

__all__ = [
    # Core
    "MercatorClient",
    "MercatorConfig",
    "SessionContext",
    # Exceptions
    "MercatorError",
    "PolicyViolationError",
    "ProviderUnavailableError",
    "RateLimitError",
    "AuthenticationError",
    "TimeoutError",
    "ValidationError",
    "ContentDetectionError",
    # Version
    "__version__",
]

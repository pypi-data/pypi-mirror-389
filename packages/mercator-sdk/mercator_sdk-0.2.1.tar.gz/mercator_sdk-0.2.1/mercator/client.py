"""
Core Mercator client for governed LLM access.

This module provides the main MercatorClient class, which serves as the primary
entry point for interacting with LLM providers through the Mercator proxy.
"""

import os
from typing import Optional

from .api import Chat
from .config import MercatorConfig
from .exceptions import ValidationError
from .transport import HTTPTransport


class MercatorClient:
    """
    Mercator SDK client for governed LLM access.

    Drop-in replacement for OpenAI/Anthropic clients with automatic policy
    enforcement, content detection, and compliance logging. All LLM requests
    are routed through the Mercator proxy for governance.

    The client can operate in two modes:
    - proxy mode (default): Routes requests through Mercator for full governance
    - local mode: Bypasses proxy for local development (no governance)

    Example:
        >>> # Basic usage
        >>> from mercator import MercatorClient
        >>> client = MercatorClient(
        ...     api_key="mercator-key-123",
        ...     application="my-app",
        ...     user_id="user@example.com"
        ... )
        >>> response = client.chat.completions.create(
        ...     model="gpt-4",
        ...     messages=[{"role": "user", "content": "Hello"}]
        ... )
        >>> print(response.choices[0].message.content)

        >>> # With context manager (recommended)
        >>> with MercatorClient(api_key="mercator-key-123") as client:
        ...     response = client.chat.completions.create(...)

        >>> # From environment variables
        >>> import os
        >>> os.environ['MERCATOR_API_KEY'] = 'mercator-key-123'
        >>> client = MercatorClient.from_env()

    Attributes:
        config: Configuration instance containing all settings.
        chat: Chat completions API (OpenAI-compatible interface).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        application: Optional[str] = None,
        user_id: Optional[str] = None,
        config: Optional[MercatorConfig] = None,
        **kwargs,
    ):
        """
        Initialize Mercator client.

        Args:
            api_key: Mercator API key. If not provided, reads from MERCATOR_API_KEY env var.
            endpoint: Mercator proxy endpoint. Defaults to https://proxy.mercator.local:8443.
            application: Application identifier for tracking and policies.
            user_id: User identifier for session tracking and user-level policies.
            config: Pre-configured MercatorConfig instance. If provided, other args are ignored.
            **kwargs: Additional configuration options (timeout, max_retries, etc.).

        Raises:
            ValidationError: If required configuration is missing or invalid.

        Example:
            >>> # Minimal configuration
            >>> client = MercatorClient(api_key="mercator-key-123")

            >>> # Full configuration
            >>> client = MercatorClient(
            ...     api_key="mercator-key-123",
            ...     endpoint="https://proxy.mercator.local:8443",
            ...     application="my-app",
            ...     user_id="user@example.com",
            ...     timeout=30,
            ...     max_retries=5
            ... )

            >>> # With pre-built config
            >>> config = MercatorConfig(api_key="mercator-key-123")
            >>> client = MercatorClient(config=config)
        """
        # Build config from args or use provided config
        if config is None:
            # Get API key from argument or environment
            final_api_key = api_key or os.getenv("MERCATOR_API_KEY")
            if not final_api_key:
                raise ValidationError(
                    "api_key is required. Provide it as an argument or set MERCATOR_API_KEY "
                    "environment variable.",
                    field="api_key",
                )

            # Get endpoint from argument or environment
            final_endpoint: str = (
                endpoint
                or os.getenv("MERCATOR_ENDPOINT", "https://proxy.mercator.local:8443")
                or "https://proxy.mercator.local:8443"
            )

            # Build config
            config = MercatorConfig(
                api_key=final_api_key,
                endpoint=final_endpoint,
                application=application,
                user_id=user_id,
                **kwargs,
            )

        self.config = config
        self._validate_config()

        # Check if local mode (bypass proxy for development)
        if self.config.mode == "local":
            # Local development mode - bypass proxy
            from .local_mode import LocalModeClient

            self._local_client = LocalModeClient(self.config)  # type: ignore
            self._http_client = None  # type: ignore
            self.chat = self._local_client.chat  # type: ignore
        else:
            # Proxy mode - route through Mercator
            self._local_client = None  # type: ignore
            self._http_client = HTTPTransport(self.config)
            self.chat = Chat(self)  # type: ignore

        # Track if client has been closed
        self._closed = False

    @classmethod
    def from_env(cls) -> "MercatorClient":
        """
        Create client from environment variables.

        This is a convenience method that loads all configuration from environment
        variables using MercatorConfig.from_env().

        Returns:
            MercatorClient: Client instance configured from environment.

        Raises:
            ValidationError: If required environment variables are missing.

        Example:
            >>> import os
            >>> os.environ['MERCATOR_API_KEY'] = 'mercator-key-123'
            >>> os.environ['MERCATOR_APPLICATION'] = 'my-app'
            >>> client = MercatorClient.from_env()
        """
        config = MercatorConfig.from_env()
        return cls(config=config)

    def _validate_config(self):
        """
        Validate client configuration.

        This method performs additional validation beyond what MercatorConfig does.
        It's called during initialization.

        Raises:
            ValidationError: If configuration is invalid.
        """
        # Config validation is already done in MercatorConfig.__post_init__
        # This method is reserved for any client-specific validation that might
        # be needed in the future.

        # Example future validation:
        # if self.config.mode == "proxy" and not self.config.api_key.startswith("mercator-key-"):
        #     raise ValidationError(
        #         "api_key must start with 'mercator-key-' in proxy mode",
        #         field="api_key"
        #     )
        pass

    def session(self, user_id: Optional[str] = None, session_id: Optional[str] = None):
        """
        Create a session context for tracking related requests.

        Sessions allow you to group multiple requests together for tracking,
        analytics, and user-level policies. All requests made within the
        session context will include the user_id and session_id metadata.

        Args:
            user_id: User identifier for this session.
            session_id: Session identifier (auto-generated if not provided).

        Returns:
            SessionContext: Context manager for the session.

        Example:
            >>> client = MercatorClient(api_key="mercator-key-123")
            >>> with client.session(user_id="user@example.com", session_id="sess-123"):
            ...     # All requests in this block will include user/session metadata
            ...     response1 = client.chat.completions.create(...)
            ...     response2 = client.chat.completions.create(...)
        """
        # TODO(Task 5.3.4): Implement SessionContext
        from .session import SessionContext

        return SessionContext(self, user_id=user_id, session_id=session_id)

    def close(self):
        """
        Close the client and clean up resources.

        This method closes the underlying HTTP client and releases any resources.
        After calling close(), the client should not be used.

        It's recommended to use the client as a context manager (with statement)
        instead of calling close() manually.

        Example:
            >>> client = MercatorClient(api_key="mercator-key-123")
            >>> try:
            ...     response = client.chat.completions.create(...)
            ... finally:
            ...     client.close()

            >>> # Better: use context manager
            >>> with MercatorClient(api_key="mercator-key-123") as client:
            ...     response = client.chat.completions.create(...)
        """
        if self._closed:
            return

        # Close appropriate client based on mode
        if self._local_client is not None:
            self._local_client.close()
        elif self._http_client is not None:
            self._http_client.close()

        self._closed = True

    def __enter__(self):
        """
        Enter context manager.

        Returns:
            MercatorClient: Self reference for use in with statement.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit context manager.

        Args:
            exc_type: Exception type if an exception occurred.
            exc_val: Exception value if an exception occurred.
            exc_tb: Exception traceback if an exception occurred.
        """
        self.close()

    def __repr__(self) -> str:
        """
        Return string representation of client.

        Returns:
            str: String representation showing key configuration.
        """
        if self.config.mode == "local":
            return f"MercatorClient(mode='local', " f"provider='{self.config.fallback_provider}')"
        else:
            return (
                f"MercatorClient(endpoint='{self.config.endpoint}', "
                f"application='{self.config.application}', "
                f"mode='{self.config.mode}')"
            )

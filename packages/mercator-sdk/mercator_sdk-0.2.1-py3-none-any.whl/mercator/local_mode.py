"""
Local development mode for Mercator SDK.

This module provides a local mode client that bypasses the Mercator proxy and
routes requests directly to LLM providers (OpenAI, Anthropic). This is useful
for local development and testing without governance overhead.

WARNING: Local mode bypasses all policy enforcement, content detection, and
audit logging. Use only for development/testing, never in production.
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, List

if TYPE_CHECKING:
    from .config import MercatorConfig

logger = logging.getLogger(__name__)


class LocalModeChatCompletions:
    """
    Chat completions API for local mode.

    Provides OpenAI-compatible interface that routes directly to provider SDKs.
    """

    def __init__(self, provider_client: Any):
        """
        Initialize local mode chat completions.

        Args:
            provider_client: OpenAI or Anthropic client instance.
        """
        self._provider_client = provider_client

    def create(
        self,
        model: str,
        messages: List[Dict[str, Any]],
        stream: bool = False,
        **kwargs: Any,
    ) -> Any:
        """
        Create chat completion (bypasses Mercator proxy).

        This method forwards the request directly to the provider SDK.
        No policy enforcement, content detection, or audit logging is performed.

        Args:
            model: Model to use (e.g., "gpt-4", "claude-3-opus").
            messages: List of chat messages.
            stream: Whether to stream response.
            **kwargs: Additional parameters to pass to provider.

        Returns:
            Provider response (OpenAI or Anthropic format).

        Example:
            >>> # Same API as MercatorClient, but bypasses proxy
            >>> response = client.chat.completions.create(
            ...     model="gpt-4",
            ...     messages=[{"role": "user", "content": "Hello"}]
            ... )
        """
        logger.debug(f"Local mode: Forwarding request to provider (model={model}, stream={stream})")

        # Forward to provider SDK
        return self._provider_client.chat.completions.create(
            model=model, messages=messages, stream=stream, **kwargs
        )


class LocalModeChat:
    """
    Chat API namespace for local mode.

    Provides OpenAI-compatible structure: client.chat.completions.create()
    """

    def __init__(self, provider_client: Any):
        """
        Initialize local mode chat API.

        Args:
            provider_client: OpenAI or Anthropic client instance.
        """
        self.completions = LocalModeChatCompletions(provider_client)


class LocalModeClient:
    """
    Local development mode client (bypasses Mercator proxy).

    This client provides the same API as MercatorClient but routes requests
    directly to LLM providers without any governance, policy enforcement,
    content detection, or audit logging.

    Use this mode for:
    - Local development and testing
    - Debugging without proxy overhead
    - Quick prototyping

    DO NOT use in production - all governance features are disabled.

    Attributes:
        config: MercatorConfig instance.
        chat: Chat API namespace.

    Example:
        >>> # Create local mode client
        >>> client = MercatorClient(
        ...     mode="local",
        ...     fallback_provider="openai",
        ...     fallback_api_key="sk-..."
        ... )
        >>>
        >>> # Same API as regular client
        >>> response = client.chat.completions.create(
        ...     model="gpt-4",
        ...     messages=[{"role": "user", "content": "Hello"}]
        ... )
    """

    def __init__(self, config: "MercatorConfig"):
        """
        Initialize local mode client.

        Args:
            config: MercatorConfig with mode='local', fallback_provider, and fallback_api_key.

        Raises:
            ValueError: If provider is unsupported or config is invalid.
            ImportError: If provider SDK is not installed.
        """
        self.config = config

        logger.warning(
            "⚠️  Local mode enabled - bypassing Mercator proxy. "
            "No policy enforcement, content detection, or audit logging. "
            "Use only for development/testing."
        )

        # Initialize provider SDK
        if config.fallback_provider == "openai":
            self._provider_client = self._init_openai()
        elif config.fallback_provider == "anthropic":
            self._provider_client = self._init_anthropic()
        else:
            raise ValueError(
                f"Unsupported fallback provider: {config.fallback_provider}. "
                f"Supported providers: openai, anthropic"
            )

        # Initialize API namespaces
        self.chat = LocalModeChat(self._provider_client)

    def _init_openai(self) -> Any:
        """
        Initialize OpenAI client.

        Returns:
            OpenAI client instance.

        Raises:
            ImportError: If openai SDK is not installed.
        """
        try:
            from openai import OpenAI  # type: ignore
        except ImportError as e:
            raise ImportError("OpenAI SDK not installed. Install with: pip install openai") from e

        api_key = self.config.fallback_api_key
        if api_key:
            logger.debug(f"Initializing OpenAI client with API key: {api_key[:10]}...")
        return OpenAI(api_key=api_key)

    def _init_anthropic(self) -> Any:
        """
        Initialize Anthropic client.

        Returns:
            Anthropic client instance.

        Raises:
            ImportError: If anthropic SDK is not installed.
        """
        try:
            from anthropic import Anthropic  # type: ignore
        except ImportError as e:
            raise ImportError(
                "Anthropic SDK not installed. Install with: pip install anthropic"
            ) from e

        api_key = self.config.fallback_api_key
        if api_key:
            logger.debug(f"Initializing Anthropic client with API key: {api_key[:10]}...")
        return Anthropic(api_key=api_key)

    def close(self) -> None:
        """
        Close client and clean up resources.

        Local mode clients typically don't need explicit cleanup, but this
        method is provided for API compatibility with MercatorClient.
        """
        logger.debug("Closing local mode client")
        # Most provider SDKs don't require explicit cleanup
        # If needed in future, add provider-specific cleanup here
        pass

    def __enter__(self) -> "LocalModeClient":
        """
        Enter context manager.

        Returns:
            LocalModeClient: Self reference for use in with statement.
        """
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Exit context manager and close client.

        Args:
            exc_type: Exception type if an exception occurred.
            exc_val: Exception value if an exception occurred.
            exc_tb: Exception traceback if an exception occurred.
        """
        self.close()

    def __repr__(self) -> str:
        """
        Return string representation of local mode client.

        Returns:
            str: String representation showing mode and provider.
        """
        return f"LocalModeClient(provider='{self.config.fallback_provider}', " f"mode='local')"

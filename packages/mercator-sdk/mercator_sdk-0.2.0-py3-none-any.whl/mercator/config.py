"""
Configuration management for Mercator SDK.

This module provides the MercatorConfig class for managing SDK configuration,
including support for environment variables, validation, and programmatic configuration.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Literal, Optional


@dataclass
class MercatorConfig:
    """
    Configuration for Mercator client.

    The configuration can be provided programmatically or loaded from environment variables.
    All settings have sensible defaults except for the API key which is required.

    Example:
        >>> # Programmatic configuration
        >>> config = MercatorConfig(
        ...     api_key="mercator-key-123",
        ...     application="my-app",
        ...     user_id="user@example.com"
        ... )

        >>> # From environment variables
        >>> config = MercatorConfig.from_env()

    Attributes:
        api_key: Mercator API key (required). Must start with 'mercator-key-'.
        endpoint: Mercator proxy endpoint URL. Defaults to local proxy.
        application: Application identifier for tracking and policies.
        user_id: User identifier for session tracking and user-level policies.
        environment: Deployment environment (production, development, staging).
        timeout: Request timeout in seconds.
        max_retries: Maximum number of retry attempts for transient errors.
        retry_backoff: Initial backoff delay in seconds for exponential backoff.
        verify_ssl: Whether to verify SSL certificates.
        ssl_cert_path: Path to custom SSL certificate for self-signed certs.
        mode: Operating mode - 'proxy' routes through Mercator, 'local' bypasses for dev.
        fallback_provider: Provider to use in local mode (openai, anthropic).
        fallback_api_key: Direct provider API key for local mode.
        custom_headers: Additional HTTP headers to include in requests.
        enable_metadata: Whether to expose Mercator metadata in responses.
    """

    # Required
    api_key: str

    # Endpoint configuration
    endpoint: str = "https://proxy.mercator.local:8443"

    # Application context
    application: Optional[str] = None
    user_id: Optional[str] = None
    environment: str = "production"

    # HTTP settings
    timeout: int = 60
    max_retries: int = 3
    retry_backoff: float = 1.0

    # TLS/SSL
    verify_ssl: bool = True
    ssl_cert_path: Optional[str] = None

    # Local development mode
    mode: Literal["proxy", "local"] = "proxy"
    fallback_provider: Optional[str] = None
    fallback_api_key: Optional[str] = None

    # Advanced
    custom_headers: Optional[Dict[str, str]] = field(default_factory=dict)
    enable_metadata: bool = True

    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate()

    def _validate(self):
        """
        Validate configuration values.

        Raises:
            ValueError: If required fields are missing or invalid.
        """
        # Validate required fields
        if not self.api_key:
            raise ValueError("api_key is required")

        if not self.endpoint:
            raise ValueError("endpoint is required")

        # Validate API key format (basic check)
        if not isinstance(self.api_key, str) or len(self.api_key) < 10:
            raise ValueError("api_key must be a valid string of at least 10 characters")

        # Validate endpoint URL format
        if not self.endpoint.startswith(("http://", "https://")):
            raise ValueError("endpoint must be a valid HTTP/HTTPS URL")

        # Validate timeout
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")

        # Validate max_retries
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")

        # Validate retry_backoff
        if self.retry_backoff < 0:
            raise ValueError("retry_backoff must be non-negative")

        # Validate mode-specific requirements
        if self.mode == "local":
            if not self.fallback_provider:
                raise ValueError("fallback_provider is required when mode='local'")
            if not self.fallback_api_key:
                raise ValueError("fallback_api_key is required when mode='local'")

            # Validate fallback_provider
            valid_providers = ["openai", "anthropic"]
            if self.fallback_provider not in valid_providers:
                raise ValueError(
                    f"fallback_provider must be one of {valid_providers}, "
                    f"got '{self.fallback_provider}'"
                )

        # Validate environment
        valid_environments = ["production", "development", "staging"]
        if self.environment not in valid_environments:
            raise ValueError(
                f"environment must be one of {valid_environments}, got '{self.environment}'"
            )

        # Ensure custom_headers is not None
        if self.custom_headers is None:
            self.custom_headers = {}

    @classmethod
    def from_env(cls) -> "MercatorConfig":
        """
        Load configuration from environment variables.

        Environment variables:
            MERCATOR_API_KEY: API key (required)
            MERCATOR_ENDPOINT: Proxy endpoint URL
            MERCATOR_APPLICATION: Application identifier
            MERCATOR_USER_ID: User identifier
            MERCATOR_ENVIRONMENT: Environment (production, development, staging)
            MERCATOR_TIMEOUT: Request timeout in seconds
            MERCATOR_MAX_RETRIES: Maximum retry attempts
            MERCATOR_RETRY_BACKOFF: Initial backoff delay in seconds
            MERCATOR_VERIFY_SSL: Whether to verify SSL (true/false)
            MERCATOR_SSL_CERT_PATH: Path to custom SSL certificate
            MERCATOR_MODE: Operating mode (proxy/local)
            MERCATOR_FALLBACK_PROVIDER: Provider for local mode
            MERCATOR_FALLBACK_API_KEY: Provider API key for local mode
            MERCATOR_ENABLE_METADATA: Whether to expose metadata (true/false)

        Returns:
            MercatorConfig: Configuration instance loaded from environment.

        Raises:
            ValueError: If required environment variables are missing.

        Example:
            >>> import os
            >>> os.environ['MERCATOR_API_KEY'] = 'mercator-key-123'
            >>> config = MercatorConfig.from_env()
        """
        api_key = os.getenv("MERCATOR_API_KEY")
        if not api_key:
            raise ValueError(
                "MERCATOR_API_KEY environment variable is required. "
                "Set it with: export MERCATOR_API_KEY=mercator-key-..."
            )

        # Parse boolean values
        verify_ssl = os.getenv("MERCATOR_VERIFY_SSL", "true").lower() == "true"
        enable_metadata = os.getenv("MERCATOR_ENABLE_METADATA", "true").lower() == "true"

        # Parse numeric values with defaults
        timeout = int(os.getenv("MERCATOR_TIMEOUT", "60"))
        max_retries = int(os.getenv("MERCATOR_MAX_RETRIES", "3"))
        retry_backoff = float(os.getenv("MERCATOR_RETRY_BACKOFF", "1.0"))

        return cls(
            api_key=api_key,
            endpoint=os.getenv("MERCATOR_ENDPOINT", "https://proxy.mercator.local:8443"),
            application=os.getenv("MERCATOR_APPLICATION"),
            user_id=os.getenv("MERCATOR_USER_ID"),
            environment=os.getenv("MERCATOR_ENVIRONMENT", "production"),
            timeout=timeout,
            max_retries=max_retries,
            retry_backoff=retry_backoff,
            verify_ssl=verify_ssl,
            ssl_cert_path=os.getenv("MERCATOR_SSL_CERT_PATH"),
            mode=os.getenv("MERCATOR_MODE", "proxy"),  # type: ignore
            fallback_provider=os.getenv("MERCATOR_FALLBACK_PROVIDER"),
            fallback_api_key=os.getenv("MERCATOR_FALLBACK_API_KEY"),
            enable_metadata=enable_metadata,
        )

    def copy(self, **updates) -> "MercatorConfig":
        """
        Create a copy of this config with updated values.

        Args:
            **updates: Fields to update in the copy.

        Returns:
            MercatorConfig: New configuration instance with updates applied.

        Example:
            >>> config = MercatorConfig(api_key="test")
            >>> dev_config = config.copy(environment="development")
        """
        current_values = {
            "api_key": self.api_key,
            "endpoint": self.endpoint,
            "application": self.application,
            "user_id": self.user_id,
            "environment": self.environment,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "retry_backoff": self.retry_backoff,
            "verify_ssl": self.verify_ssl,
            "ssl_cert_path": self.ssl_cert_path,
            "mode": self.mode,
            "fallback_provider": self.fallback_provider,
            "fallback_api_key": self.fallback_api_key,
            "custom_headers": self.custom_headers.copy() if self.custom_headers else {},
            "enable_metadata": self.enable_metadata,
        }
        current_values.update(updates)
        return MercatorConfig(**current_values)  # type: ignore[arg-type]

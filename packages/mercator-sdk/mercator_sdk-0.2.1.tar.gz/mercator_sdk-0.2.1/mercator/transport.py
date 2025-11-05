"""
HTTP transport layer for Mercator SDK.

This module provides HTTP client functionality with connection pooling, retry logic,
timeout management, and error handling for communication with the Mercator proxy.
"""

import logging
import time
from typing import Any, Dict, Iterator, Optional, Union

import httpx

from .config import MercatorConfig
from .exceptions import (
    AuthenticationError,
    MercatorError,
    PolicyViolationError,
    ProviderUnavailableError,
    RateLimitError,
)
from .exceptions import (
    TimeoutError as MercatorTimeoutError,
)

logger = logging.getLogger(__name__)

# Version constant to avoid circular import
__version__ = "0.1.0"


class HTTPTransport:
    """
    HTTP transport layer with connection pooling and retry logic.

    This class handles all HTTP communication with the Mercator proxy, including:
    - Connection pooling for performance
    - Automatic retries with exponential backoff
    - Timeout management
    - Error response parsing
    - Custom header injection (X-Mercator-*)
    - SSL/TLS verification

    Example:
        >>> config = MercatorConfig(api_key="mercator-key-123")
        >>> transport = HTTPTransport(config)
        >>> response = transport.request("POST", "/v1/chat/completions", json={...})
        >>> transport.close()

    Attributes:
        config: MercatorConfig instance with settings.
        client: httpx.Client instance for HTTP requests.
    """

    def __init__(self, config: MercatorConfig):
        """
        Initialize HTTP transport.

        Args:
            config: MercatorConfig instance with endpoint, timeout, SSL settings, etc.

        Example:
            >>> config = MercatorConfig(
            ...     api_key="mercator-key-123",
            ...     timeout=30,
            ...     max_retries=5
            ... )
            >>> transport = HTTPTransport(config)
        """
        self.config = config

        # Determine SSL verification setting
        verify: Union[bool, str]
        if not config.verify_ssl:
            verify = False
        elif config.ssl_cert_path:
            verify = config.ssl_cert_path
        else:
            verify = True

        # Create httpx client with connection pooling
        self.client = httpx.Client(
            base_url=config.endpoint,
            timeout=httpx.Timeout(config.timeout),
            verify=verify,
            limits=httpx.Limits(
                max_connections=100,  # Total connection pool size
                max_keepalive_connections=20,  # Keepalive connections
            ),
            follow_redirects=True,
        )

        logger.debug(
            f"HTTPTransport initialized: endpoint={config.endpoint}, "
            f"timeout={config.timeout}s, verify_ssl={config.verify_ssl}"
        )

    def request(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> httpx.Response:
        """
        Make HTTP request with retries and error handling.

        Implements retry logic with exponential backoff for transient errors
        (timeouts, connection errors, rate limits). Non-retryable errors
        (authentication, policy violations) are raised immediately.

        Args:
            method: HTTP method (GET, POST, etc.).
            path: API path (e.g., "/v1/chat/completions").
            json: JSON request body.
            **kwargs: Additional httpx request parameters.

        Returns:
            httpx.Response: Successful response object.

        Raises:
            PolicyViolationError: Request blocked by policy (403).
            ProviderUnavailableError: Provider failed or unavailable (502).
            RateLimitError: Rate limit exceeded (429).
            AuthenticationError: Invalid API key (401).
            MercatorTimeoutError: Request timed out after retries.
            MercatorError: Other errors.

        Example:
            >>> transport = HTTPTransport(config)
            >>> response = transport.request(
            ...     "POST",
            ...     "/v1/chat/completions",
            ...     json={"model": "gpt-4", "messages": [...]}
            ... )
            >>> data = response.json()
        """
        headers = self._build_headers()
        headers.update(kwargs.pop("headers", {}))

        last_error: Optional[Exception] = None

        # Retry loop with exponential backoff
        for attempt in range(self.config.max_retries):
            try:
                logger.debug(
                    f"Request attempt {attempt + 1}/{self.config.max_retries}: {method} {path}"
                )

                response = self.client.request(
                    method=method, url=path, json=json, headers=headers, **kwargs
                )

                # Check for errors (4xx, 5xx)
                if response.status_code >= 400:
                    self._handle_error_response(response)

                logger.debug(f"Request successful: {method} {path} -> {response.status_code}")
                return response

            except httpx.TimeoutException as e:
                last_error = e
                if attempt < self.config.max_retries - 1:
                    backoff = self.config.retry_backoff * (2**attempt)
                    logger.warning(
                        f"Request timeout (attempt {attempt + 1}/{self.config.max_retries}), "
                        f"retrying in {backoff:.1f}s: {e}"
                    )
                    time.sleep(backoff)
                else:
                    logger.error(f"Request timeout after {self.config.max_retries} attempts: {e}")
                    raise MercatorTimeoutError(
                        f"Request timed out after {self.config.max_retries} attempts",
                        timeout=self.config.timeout,
                    ) from e

            except (httpx.ConnectError, httpx.NetworkError) as e:
                last_error = e
                if attempt < self.config.max_retries - 1:
                    backoff = self.config.retry_backoff * (2**attempt)
                    logger.warning(
                        f"Connection error (attempt {attempt + 1}/{self.config.max_retries}), "
                        f"retrying in {backoff:.1f}s: {e}"
                    )
                    time.sleep(backoff)
                else:
                    logger.error(f"Connection failed after {self.config.max_retries} attempts: {e}")
                    raise ProviderUnavailableError(
                        f"Failed to connect after {self.config.max_retries} attempts: {e}",
                        provider="mercator-proxy",
                    ) from e

            except RateLimitError:
                # Rate limit - retry with backoff
                if attempt < self.config.max_retries - 1:
                    backoff = self.config.retry_backoff * (2**attempt)
                    logger.warning(
                        f"Rate limited (attempt {attempt + 1}/{self.config.max_retries}), "
                        f"retrying in {backoff:.1f}s"
                    )
                    time.sleep(backoff)
                else:
                    logger.error(f"Rate limit exceeded after {self.config.max_retries} attempts")
                    raise

            except (
                PolicyViolationError,
                AuthenticationError,
                ProviderUnavailableError,
                MercatorError,
            ):
                # Non-retryable errors - raise immediately
                raise

        # Should never reach here, but just in case
        raise ProviderUnavailableError(
            f"Failed after {self.config.max_retries} attempts: {last_error}",
            provider="mercator-proxy",
        )

    def _build_headers(self) -> Dict[str, str]:
        """
        Build HTTP request headers.

        Includes authorization, content type, user agent, and Mercator-specific
        metadata headers (application, user, environment, session).

        Returns:
            Dict[str, str]: Headers dictionary.

        Example:
            >>> transport = HTTPTransport(config)
            >>> headers = transport._build_headers()
            >>> print(headers["Authorization"])
            Bearer mercator-key-123
        """
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "User-Agent": f"mercator-sdk-python/{__version__}",
        }

        # Add Mercator-specific metadata headers
        if self.config.application:
            headers["X-Mercator-Application"] = self.config.application
        if self.config.user_id:
            headers["X-Mercator-User"] = self.config.user_id
        if self.config.environment:
            headers["X-Mercator-Environment"] = self.config.environment

        # Add custom headers (includes session headers set by SessionContext)
        if self.config.custom_headers:
            headers.update(self.config.custom_headers)

        return headers

    def _handle_error_response(self, response: httpx.Response) -> None:
        """
        Parse error response and raise appropriate exception.

        Attempts to parse JSON error response from the Mercator proxy and
        raises the appropriate exception type based on status code and error type.

        Args:
            response: httpx.Response object with error status.

        Raises:
            PolicyViolationError: Policy blocked request (403).
            ProviderUnavailableError: Provider error (502).
            RateLimitError: Rate limit (429).
            AuthenticationError: Auth error (401).
            MercatorError: Other errors.

        Example:
            >>> # This is called internally when status >= 400
            >>> # response = httpx.Response(status_code=403, json={...})
            >>> # transport._handle_error_response(response)
            >>> # Raises: PolicyViolationError
        """
        # Try to parse JSON error response
        try:
            error_data = response.json()
            error = error_data.get("error", {})
            error_type = error.get("type")
            error_message = error.get("message", "Unknown error")
            details = error.get("details", {})
        except Exception:
            # Not a JSON error response - use status text
            error_type = None
            error_message = response.text or f"HTTP {response.status_code}"
            details = {}

        # Policy violation (403 or explicit type)
        if response.status_code == 403 or error_type == "policy_violation":
            raise PolicyViolationError(
                message=error_message,
                policy_id=details.get("policy_id"),
                policy_name=details.get("policy_name"),
                rule=details.get("rule"),
                reason=error_message,
                violated_value=details.get("violated_value"),
                threshold=details.get("threshold"),
                details=details,
            )

        # Provider errors (502 or explicit type)
        elif response.status_code == 502 or error_type == "provider_error":
            raise ProviderUnavailableError(
                message=error_message,
                provider=details.get("provider"),
                status_code=response.status_code,
                details=details,
            )

        # Rate limit (429)
        elif response.status_code == 429:
            retry_after = None
            if "Retry-After" in response.headers:
                try:
                    retry_after = int(response.headers["Retry-After"])
                except ValueError:
                    pass
            raise RateLimitError(
                message=error_message,
                retry_after=retry_after,
                limit_type=details.get("limit_type"),
                details=details,
            )

        # Authentication error (401)
        elif response.status_code == 401:
            raise AuthenticationError(message=error_message, details=details)

        # Timeout (408 or 504)
        elif response.status_code in (408, 504):
            raise MercatorTimeoutError(
                message=error_message, timeout=self.config.timeout, details=details
            )

        # Generic error
        else:
            raise MercatorError(
                message=f"{error_message} (HTTP {response.status_code})", details=details
            )

    def stream_request(
        self, method: str, path: str, json: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> Iterator[str]:
        """
        Make streaming HTTP request (Server-Sent Events).

        Used for streaming chat completions. Parses SSE format and yields
        JSON chunks as strings.

        Args:
            method: HTTP method (typically POST).
            path: API path (e.g., "/v1/chat/completions").
            json: JSON request body.
            **kwargs: Additional httpx request parameters.

        Yields:
            str: JSON string for each SSE chunk.

        Raises:
            PolicyViolationError: Request blocked by policy.
            ProviderUnavailableError: Provider error.
            RateLimitError: Rate limit exceeded.
            AuthenticationError: Invalid API key.
            MercatorError: Other errors.

        Example:
            >>> transport = HTTPTransport(config)
            >>> for chunk_json in transport.stream_request("POST", "/v1/chat/completions", json={...}):
            ...     chunk = json.loads(chunk_json)
            ...     print(chunk["choices"][0]["delta"]["content"], end="")
        """
        headers = self._build_headers()
        headers.update(kwargs.pop("headers", {}))

        logger.debug(f"Starting streaming request: {method} {path}")

        # Use httpx streaming context manager
        with self.client.stream(
            method=method, url=path, json=json, headers=headers, **kwargs
        ) as response:
            # Check for errors before streaming
            if response.status_code >= 400:
                # Read full response for error details
                response.read()
                self._handle_error_response(response)

            # Stream lines in SSE format
            for line in response.iter_lines():
                if line.startswith("data: "):
                    data = line[6:]  # Remove "data: " prefix
                    if data == "[DONE]":
                        logger.debug("Streaming completed: received [DONE] marker")
                        break
                    yield data

        logger.debug(f"Streaming request completed: {method} {path}")

    def close(self) -> None:
        """
        Close HTTP client and release connections.

        Should be called when done with the transport to clean up resources.
        The MercatorClient calls this automatically when used as a context manager.

        Example:
            >>> transport = HTTPTransport(config)
            >>> try:
            ...     response = transport.request("GET", "/health")
            ... finally:
            ...     transport.close()
        """
        logger.debug("Closing HTTPTransport and releasing connections")
        self.client.close()

    def __enter__(self) -> "HTTPTransport":
        """
        Enter context manager.

        Returns:
            HTTPTransport: Self reference.
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

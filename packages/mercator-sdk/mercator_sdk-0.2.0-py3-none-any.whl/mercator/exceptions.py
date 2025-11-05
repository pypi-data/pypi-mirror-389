"""
Custom exceptions for Mercator SDK.

This module defines all custom exception types that can be raised by the SDK.
Each exception provides structured information about the error to help with
debugging and error handling.
"""

from typing import Any, Dict, List, Optional


class MercatorError(Exception):
    """
    Base exception for all Mercator SDK errors.

    All Mercator-specific exceptions inherit from this class, allowing users
    to catch all SDK errors with a single except clause.

    Attributes:
        message: Human-readable error message.
        details: Additional structured error information.
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize MercatorError.

        Args:
            message: Human-readable error message.
            details: Additional structured error information.
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        """Return string representation of error."""
        if self.details:
            details_str = ", ".join(f"{k}={v}" for k, v in self.details.items())
            return f"{self.message} ({details_str})"
        return self.message


class PolicyViolationError(MercatorError):
    """
    Raised when a request is blocked by a Mercator policy.

    This exception is raised when the Mercator proxy evaluates policies and
    decides to block the request. It includes detailed information about which
    policy was violated and why.

    Attributes:
        message: Human-readable error message.
        policy_id: Unique identifier of the violated policy.
        policy_name: Human-readable name of the policy.
        rule: The specific policy rule that was violated.
        reason: Detailed explanation of why the request was blocked.
        violated_value: The value that violated the policy (if applicable).
        threshold: The policy threshold that was exceeded (if applicable).
        details: Additional structured error information.

    Example:
        >>> try:
        ...     response = client.chat.completions.create(...)
        ... except PolicyViolationError as e:
        ...     print(f"Blocked by policy: {e.policy_name}")
        ...     print(f"Reason: {e.reason}")
        ...     # Handle gracefully - show user-friendly message, retry, etc.
    """

    def __init__(
        self,
        message: str,
        policy_id: Optional[str] = None,
        policy_name: Optional[str] = None,
        rule: Optional[str] = None,
        reason: Optional[str] = None,
        violated_value: Optional[Any] = None,
        threshold: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize PolicyViolationError.

        Args:
            message: Human-readable error message.
            policy_id: Unique identifier of the violated policy.
            policy_name: Human-readable name of the policy.
            rule: The specific policy rule that was violated.
            reason: Detailed explanation of why the request was blocked.
            violated_value: The value that violated the policy.
            threshold: The policy threshold that was exceeded.
            details: Additional structured error information.
        """
        super().__init__(message, details)
        self.policy_id = policy_id
        self.policy_name = policy_name
        self.rule = rule
        self.reason = reason
        self.violated_value = violated_value
        self.threshold = threshold


class ProviderUnavailableError(MercatorError):
    """
    Raised when the LLM provider is unavailable.

    This exception is raised when the proxy cannot reach the LLM provider
    (OpenAI, Anthropic, etc.) or when the provider returns a 5xx error.

    Attributes:
        message: Human-readable error message.
        provider: Name of the unavailable provider.
        status_code: HTTP status code from the provider (if available).
        details: Additional structured error information.

    Example:
        >>> try:
        ...     response = client.chat.completions.create(...)
        ... except ProviderUnavailableError as e:
        ...     print(f"Provider {e.provider} is unavailable")
        ...     # Retry with exponential backoff or notify ops team
    """

    def __init__(
        self,
        message: str,
        provider: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize ProviderUnavailableError.

        Args:
            message: Human-readable error message.
            provider: Name of the unavailable provider.
            status_code: HTTP status code from the provider.
            details: Additional structured error information.
        """
        super().__init__(message, details)
        self.provider = provider
        self.status_code = status_code


class RateLimitError(MercatorError):
    """
    Raised when rate limit is exceeded.

    This exception is raised when either the Mercator proxy or the LLM provider
    rate limit is exceeded.

    Attributes:
        message: Human-readable error message.
        retry_after: Number of seconds to wait before retrying (if available).
        limit_type: Type of limit exceeded (e.g., 'requests_per_minute', 'tokens_per_day').
        details: Additional structured error information.

    Example:
        >>> try:
        ...     response = client.chat.completions.create(...)
        ... except RateLimitError as e:
        ...     if e.retry_after:
        ...         time.sleep(e.retry_after)
        ...         # Retry request
    """

    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        limit_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize RateLimitError.

        Args:
            message: Human-readable error message.
            retry_after: Number of seconds to wait before retrying.
            limit_type: Type of limit exceeded.
            details: Additional structured error information.
        """
        super().__init__(message, details)
        self.retry_after = retry_after
        self.limit_type = limit_type


class AuthenticationError(MercatorError):
    """
    Raised when authentication fails.

    This exception is raised when the API key is invalid, expired, or missing.

    Attributes:
        message: Human-readable error message.
        details: Additional structured error information.

    Example:
        >>> try:
        ...     client = MercatorClient(api_key="invalid-key")
        ...     response = client.chat.completions.create(...)
        ... except AuthenticationError as e:
        ...     print("Invalid API key - please check your credentials")
    """

    pass


class TimeoutError(MercatorError):
    """
    Raised when a request times out.

    This exception is raised when a request exceeds the configured timeout value.

    Attributes:
        message: Human-readable error message.
        timeout: The timeout value in seconds that was exceeded.
        details: Additional structured error information.

    Example:
        >>> try:
        ...     response = client.chat.completions.create(...)
        ... except TimeoutError as e:
        ...     print(f"Request timed out after {e.timeout} seconds")
        ...     # Retry with longer timeout or notify user
    """

    def __init__(
        self,
        message: str,
        timeout: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize TimeoutError.

        Args:
            message: Human-readable error message.
            timeout: The timeout value in seconds that was exceeded.
            details: Additional structured error information.
        """
        super().__init__(message, details)
        self.timeout = timeout


class ValidationError(MercatorError):
    """
    Raised when request validation fails.

    This exception is raised when the request parameters are invalid before
    sending to the proxy (e.g., missing required fields, invalid types).

    Attributes:
        message: Human-readable error message.
        field: The field that failed validation.
        details: Additional structured error information.

    Example:
        >>> try:
        ...     response = client.chat.completions.create(model="", messages=[])
        ... except ValidationError as e:
        ...     print(f"Invalid field: {e.field}")
        ...     print(f"Reason: {e.message}")
    """

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize ValidationError.

        Args:
            message: Human-readable error message.
            field: The field that failed validation.
            details: Additional structured error information.
        """
        super().__init__(message, details)
        self.field = field


class ContentDetectionError(MercatorError):
    """
    Raised when sensitive content is detected and blocked.

    This exception is raised when the content detection engine (F3.1) detects
    sensitive content (PHI, PII, secrets, toxic content) and the policy
    requires blocking the request.

    Attributes:
        message: Human-readable error message.
        detection_types: List of detected content types (e.g., ['PHI', 'PII']).
        detections: Detailed detection results.
        details: Additional structured error information.

    Example:
        >>> try:
        ...     response = client.chat.completions.create(...)
        ... except ContentDetectionError as e:
        ...     print(f"Sensitive content detected: {e.detection_types}")
        ...     # Handle appropriately - remove sensitive data, notify user
    """

    def __init__(
        self,
        message: str,
        detection_types: Optional[List[str]] = None,
        detections: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize ContentDetectionError.

        Args:
            message: Human-readable error message.
            detection_types: List of detected content types.
            detections: Detailed detection results.
            details: Additional structured error information.
        """
        super().__init__(message, details)
        self.detection_types = detection_types or []
        self.detections = detections or {}

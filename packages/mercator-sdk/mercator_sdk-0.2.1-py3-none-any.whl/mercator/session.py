"""
Session context management for Mercator SDK.

This module provides session context functionality for grouping related requests
and applying user-level tracking and policies.
"""

import uuid
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .client import MercatorClient


class SessionContext:
    """
    Context manager for session tracking.

    Sessions allow you to group multiple LLM requests together with shared
    user_id and session_id metadata. This enables:
    - User-level tracking and analytics
    - Session-based policies
    - Cost attribution per user/session
    - Audit trail correlation

    All requests made within the session context will automatically include
    the user_id and session_id in request headers.

    Example:
        >>> client = MercatorClient(api_key="mercator-key-123")
        >>> with client.session(user_id="user@example.com"):
        ...     # Request 1
        ...     response1 = client.chat.completions.create(
        ...         model="gpt-4",
        ...         messages=[{"role": "user", "content": "Hello"}]
        ...     )
        ...     # Request 2 - same session
        ...     response2 = client.chat.completions.create(
        ...         model="gpt-4",
        ...         messages=[{"role": "user", "content": "Follow-up question"}]
        ...     )
        >>> # Outside context, session metadata not included

    Attributes:
        client: Parent MercatorClient instance.
        user_id: User identifier for this session.
        session_id: Session identifier (auto-generated if not provided).
    """

    def __init__(
        self,
        client: "MercatorClient",
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ):
        """
        Initialize session context.

        Args:
            client: Parent MercatorClient instance.
            user_id: User identifier for this session.
            session_id: Session identifier (auto-generated if not provided).
        """
        self.client = client
        self.user_id = user_id
        self.session_id = session_id or f"sess-{uuid.uuid4().hex[:16]}"

        # Store previous values to restore on exit
        self._previous_user_id: Optional[str] = None
        self._previous_session_header: Optional[str] = None

    def __enter__(self) -> "SessionContext":
        """
        Enter session context.

        Saves current user_id/session_id and sets new values on the client config.

        Returns:
            SessionContext: Self reference for use in with statement.
        """
        # Save previous values
        self._previous_user_id = self.client.config.user_id

        # Save previous session header if it exists
        if (
            self.client.config.custom_headers
            and "X-Mercator-Session" in self.client.config.custom_headers
        ):
            self._previous_session_header = self.client.config.custom_headers["X-Mercator-Session"]
        else:
            self._previous_session_header = None

        # Set new values
        # We need to update the config, but since it's a dataclass, we need to
        # create a new instance or modify it carefully
        # For now, we'll directly modify (will be refined in Task 5.3.2 with headers)
        self.client.config.user_id = self.user_id

        # Add session header to custom_headers
        if self.client.config.custom_headers is None:
            self.client.config.custom_headers = {}
        self.client.config.custom_headers["X-Mercator-Session"] = self.session_id

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit session context.

        Restores previous user_id/session_id values.

        Args:
            exc_type: Exception type if an exception occurred.
            exc_val: Exception value if an exception occurred.
            exc_tb: Exception traceback if an exception occurred.
        """
        # Restore previous values
        self.client.config.user_id = self._previous_user_id

        # Restore previous session header
        if self._previous_session_header is not None:
            # Restore the previous session header value
            if self.client.config.custom_headers is not None:
                self.client.config.custom_headers["X-Mercator-Session"] = (
                    self._previous_session_header
                )
        else:
            # Remove session header if there was no previous value
            if (
                self.client.config.custom_headers
                and "X-Mercator-Session" in self.client.config.custom_headers
            ):
                del self.client.config.custom_headers["X-Mercator-Session"]

    def __repr__(self) -> str:
        """
        Return string representation of session context.

        Returns:
            str: String representation showing session details.
        """
        return f"SessionContext(user_id='{self.user_id}', session_id='{self.session_id}')"

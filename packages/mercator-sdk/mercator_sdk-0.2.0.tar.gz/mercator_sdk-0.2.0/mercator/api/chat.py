"""
Chat Completions API for Mercator SDK.

This module provides OpenAI-compatible chat completions API with Mercator governance
features. All requests are routed through the Mercator proxy for policy enforcement,
content detection, and audit logging.
"""

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Iterator, List, Optional, Union

import httpx

from ..exceptions import ValidationError

logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """
    Chat message in a conversation.

    Represents a single message in a chat conversation with role, content, and
    optional metadata for function calling.

    Attributes:
        role: Message role - "system", "user", "assistant", or "function".
        content: Message content text.
        name: Optional name for function messages.
        function_call: Optional function call data for assistant messages.

    Example:
        >>> msg = ChatMessage(role="user", content="Hello, how are you?")
        >>> msg = ChatMessage(role="system", content="You are a helpful assistant.")
        >>> msg = ChatMessage(
        ...     role="function",
        ...     name="get_weather",
        ...     content='{"temperature": 72}'
        ... )
    """

    role: str  # "system", "user", "assistant", "function"
    content: str
    name: Optional[str] = None  # For function messages
    function_call: Optional[Dict[str, Any]] = None  # For assistant function calls


@dataclass
class ChatCompletionChoice:
    """
    Single completion choice from chat completion response.

    Attributes:
        index: Choice index in the list of choices.
        message: The generated message.
        finish_reason: Reason completion finished - "stop", "length",
            "content_filter", "policy_violation", or "function_call".

    Example:
        >>> choice = ChatCompletionChoice(
        ...     index=0,
        ...     message=ChatMessage(role="assistant", content="Hello!"),
        ...     finish_reason="stop"
        ... )
    """

    index: int
    message: ChatMessage
    finish_reason: str  # "stop", "length", "content_filter", "policy_violation"


@dataclass
class ChatCompletionUsage:
    """
    Token usage information from chat completion.

    Attributes:
        prompt_tokens: Number of tokens in the prompt.
        completion_tokens: Number of tokens in the completion.
        total_tokens: Total tokens used (prompt + completion).

    Example:
        >>> usage = ChatCompletionUsage(
        ...     prompt_tokens=10,
        ...     completion_tokens=20,
        ...     total_tokens=30
        ... )
    """

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class MercatorMetadata:
    """
    Mercator-specific metadata from governance layer.

    This metadata provides visibility into policy decisions, content detections,
    provider routing, costs, and latency. It's extracted from X-Mercator-* response
    headers.

    Attributes:
        request_id: Unique request identifier for tracking.
        policy_id: Policy ID that was evaluated (if any).
        policy_decision: Policy decision - "ALLOW", "BLOCK", or "REDACT".
        provider_used: LLM provider used - "openai", "anthropic", etc.
        detections_count: Number of content detections (PII, PHI, secrets).
        detection_types: List of detection types found.
        actual_cost: Actual cost in USD (if available).
        latency_ms: Request latency in milliseconds.

    Example:
        >>> metadata = MercatorMetadata(
        ...     request_id="req-abc123",
        ...     policy_id="pol-default",
        ...     policy_decision="ALLOW",
        ...     provider_used="openai",
        ...     detections_count=2,
        ...     detection_types=["pii.email", "pii.phone"],
        ...     actual_cost=0.0042,
        ...     latency_ms=850
        ... )
    """

    request_id: str
    policy_id: Optional[str] = None
    policy_decision: Optional[str] = None  # "ALLOW", "BLOCK", "REDACT"
    provider_used: Optional[str] = None  # "openai", "anthropic", etc.
    detections_count: int = 0
    detection_types: List[str] = field(default_factory=list)
    actual_cost: Optional[float] = None
    latency_ms: Optional[int] = None


@dataclass
class ChatCompletion:
    """
    Chat completion response from Mercator.

    OpenAI-compatible chat completion response with additional Mercator metadata
    for governance visibility.

    Attributes:
        id: Unique completion ID.
        object: Object type, always "chat.completion".
        created: Unix timestamp of creation.
        model: Model used for completion.
        choices: List of completion choices.
        usage: Token usage information.
        mercator_metadata: Mercator-specific governance metadata.

    Example:
        >>> completion = ChatCompletion(
        ...     id="chatcmpl-abc123",
        ...     created=1234567890,
        ...     model="gpt-4",
        ...     choices=[
        ...         ChatCompletionChoice(
        ...             index=0,
        ...             message=ChatMessage(role="assistant", content="Hello!"),
        ...             finish_reason="stop"
        ...         )
        ...     ],
        ...     usage=ChatCompletionUsage(
        ...         prompt_tokens=10,
        ...         completion_tokens=5,
        ...         total_tokens=15
        ...     )
        ... )
    """

    id: str
    object: str = "chat.completion"
    created: int = field(default_factory=lambda: int(time.time()))
    model: Optional[str] = None
    choices: List[ChatCompletionChoice] = field(default_factory=list)
    usage: Optional[ChatCompletionUsage] = None

    # Mercator-specific metadata
    mercator_metadata: Optional[MercatorMetadata] = None


@dataclass
class ChatCompletionChunk:
    """
    Streaming chat completion chunk.

    Represents a single chunk from a streaming chat completion response.
    Chunks are sent via Server-Sent Events (SSE) and contain incremental
    updates to the completion.

    Attributes:
        id: Unique completion ID (same across all chunks).
        object: Object type, always "chat.completion.chunk".
        created: Unix timestamp of creation.
        model: Model used for completion.
        choices: List of choice deltas (incremental updates).

    Example:
        >>> # Typical streaming usage
        >>> stream = client.chat.completions.create(
        ...     model="gpt-4",
        ...     messages=[{"role": "user", "content": "Hello"}],
        ...     stream=True
        ... )
        >>> for chunk in stream:
        ...     delta = chunk.choices[0].get("delta", {})
        ...     if "content" in delta:
        ...         print(delta["content"], end="", flush=True)
    """

    id: str
    object: str = "chat.completion.chunk"
    created: int = field(default_factory=lambda: int(time.time()))
    model: Optional[str] = None
    choices: List[Dict[str, Any]] = field(default_factory=list)


class Chat:
    """
    Chat API namespace.

    Provides access to chat completions API. This class exists to match
    OpenAI's API structure: client.chat.completions.create()

    Attributes:
        completions: ChatCompletions API instance.

    Example:
        >>> from mercator import MercatorClient
        >>> client = MercatorClient(api_key="mercator-key-123")
        >>> response = client.chat.completions.create(
        ...     model="gpt-4",
        ...     messages=[{"role": "user", "content": "Hello!"}]
        ... )
    """

    def __init__(self, client):
        """
        Initialize chat API namespace.

        Args:
            client: Parent MercatorClient instance.
        """
        self.completions = ChatCompletions(client)


class ChatCompletions:
    """
    Chat completions API (OpenAI-compatible).

    Provides OpenAI-compatible interface for chat completions with automatic
    Mercator governance (policy enforcement, content detection, audit logging).

    This class is accessed via `client.chat.completions` and provides the
    `create()` method for generating chat completions.

    Attributes:
        client: Parent MercatorClient instance.

    Example:
        >>> from mercator import MercatorClient
        >>> client = MercatorClient(api_key="mercator-key-123")
        >>> response = client.chat.completions.create(
        ...     model="gpt-4",
        ...     messages=[{"role": "user", "content": "Hello!"}]
        ... )
        >>> print(response.choices[0].message.content)
    """

    def __init__(self, client):
        """
        Initialize chat completions API.

        Args:
            client: Parent MercatorClient instance.
        """
        self.client = client
        self._transport = client._http_client

    def create(
        self,
        model: str,
        messages: List[Union[Dict[str, str], ChatMessage]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        stop: Optional[Union[str, List[str]]] = None,
        n: Optional[int] = None,
        stream: bool = False,
        # Function calling
        functions: Optional[List[Dict[str, Any]]] = None,
        function_call: Optional[Union[str, Dict[str, str]]] = None,
        # Mercator-specific hints
        mercator_hints: Optional[Dict[str, Any]] = None,
        mercator_dry_run: bool = False,
        **kwargs: Any,
    ) -> Union[ChatCompletion, Iterator]:
        """
        Create chat completion.

        This method provides an OpenAI-compatible interface for chat completions
        with automatic Mercator governance. All requests are routed through the
        Mercator proxy for policy enforcement, content detection, and audit logging.

        Args:
            model: Model to use (e.g., "gpt-4", "claude-3-opus").
            messages: List of chat messages (dicts or ChatMessage objects).
            temperature: Sampling temperature (0-2). Higher values = more random.
            max_tokens: Maximum tokens to generate.
            top_p: Nucleus sampling parameter (0-1). Alternative to temperature.
            frequency_penalty: Frequency penalty (-2 to 2). Reduces repetition.
            presence_penalty: Presence penalty (-2 to 2). Encourages new topics.
            stop: Stop sequences - string or list of strings.
            n: Number of completions to generate (default: 1).
            stream: Whether to stream response (default: False).
            functions: Function definitions for function calling.
            function_call: Function call mode - "auto", "none", or {"name": "function_name"}.
            mercator_hints: Mercator-specific routing hints for provider selection.
            mercator_dry_run: Test policy without executing (returns policy decision).
            **kwargs: Additional parameters to pass to provider.

        Returns:
            ChatCompletion object for non-streaming, iterator for streaming.

        Raises:
            ValidationError: Invalid parameters (missing model, empty messages, etc.).
            PolicyViolationError: Request blocked by policy (403).
            ProviderUnavailableError: Provider unavailable or failed (502).
            RateLimitError: Rate limit exceeded (429).
            AuthenticationError: Invalid API key (401).
            MercatorError: Other errors.

        Example:
            >>> # Basic usage
            >>> response = client.chat.completions.create(
            ...     model="gpt-4",
            ...     messages=[{"role": "user", "content": "Hello!"}]
            ... )
            >>> print(response.choices[0].message.content)

            >>> # With parameters
            >>> response = client.chat.completions.create(
            ...     model="gpt-4",
            ...     messages=[
            ...         {"role": "system", "content": "You are a helpful assistant."},
            ...         {"role": "user", "content": "Tell me a joke."}
            ...     ],
            ...     temperature=0.7,
            ...     max_tokens=100
            ... )

            >>> # With function calling
            >>> response = client.chat.completions.create(
            ...     model="gpt-4",
            ...     messages=[{"role": "user", "content": "What's the weather?"}],
            ...     functions=[{
            ...         "name": "get_weather",
            ...         "description": "Get weather for a location",
            ...         "parameters": {...}
            ...     }]
            ... )

            >>> # Mercator dry run (test policy without executing)
            >>> response = client.chat.completions.create(
            ...     model="gpt-4",
            ...     messages=[{"role": "user", "content": "Hello"}],
            ...     mercator_dry_run=True
            ... )
            >>> print(response.mercator_metadata.policy_decision)
        """
        # Validate inputs
        self._validate_request(model, messages)

        # Normalize messages to dict format
        messages_dicts = []
        for msg in messages:
            if isinstance(msg, ChatMessage):
                msg_dict = asdict(msg)
                # Remove None values for cleaner JSON
                msg_dict = {k: v for k, v in msg_dict.items() if v is not None}
                messages_dicts.append(msg_dict)
            else:
                messages_dicts.append(msg)

        # Build request body (OpenAI-compatible)
        request_body: Dict[str, Any] = {
            "model": model,
            "messages": messages_dicts,
        }

        # Add optional parameters (only if not None)
        if temperature is not None:
            request_body["temperature"] = temperature
        if max_tokens is not None:
            request_body["max_tokens"] = max_tokens
        if top_p is not None:
            request_body["top_p"] = top_p
        if frequency_penalty is not None:
            request_body["frequency_penalty"] = frequency_penalty
        if presence_penalty is not None:
            request_body["presence_penalty"] = presence_penalty
        if stop is not None:
            request_body["stop"] = stop
        if n is not None:
            request_body["n"] = n
        if stream:
            request_body["stream"] = True
        if functions is not None:
            request_body["functions"] = functions
        if function_call is not None:
            request_body["function_call"] = function_call

        # Add Mercator-specific parameters
        if mercator_hints:
            request_body["mercator_hints"] = mercator_hints
        if mercator_dry_run:
            request_body["mercator_dry_run"] = True

        # Add any additional kwargs
        request_body.update(kwargs)

        # Handle streaming vs non-streaming
        if stream:
            return self._create_stream(request_body)
        else:
            return self._create_non_stream(request_body)

    def _validate_request(self, model: str, messages: List[Union[Dict[str, str], ChatMessage]]):
        """
        Validate chat completion request.

        Args:
            model: Model name.
            messages: List of messages.

        Raises:
            ValidationError: If validation fails.
        """
        if not model:
            raise ValidationError("model is required", field="model")

        if not messages or len(messages) == 0:
            raise ValidationError("messages must contain at least one message", field="messages")

        # Validate message structure
        for i, msg in enumerate(messages):
            if isinstance(msg, dict):
                if "role" not in msg:
                    raise ValidationError(
                        f"Message at index {i} is missing 'role' field",
                        field=f"messages[{i}].role",
                    )
                if "content" not in msg:
                    raise ValidationError(
                        f"Message at index {i} is missing 'content' field",
                        field=f"messages[{i}].content",
                    )
            elif isinstance(msg, ChatMessage):
                if not msg.role:
                    raise ValidationError(
                        f"Message at index {i} has empty role", field=f"messages[{i}].role"
                    )
                if not msg.content:
                    raise ValidationError(
                        f"Message at index {i} has empty content",
                        field=f"messages[{i}].content",
                    )
            else:
                raise ValidationError(
                    f"Message at index {i} must be a dict or ChatMessage object",
                    field=f"messages[{i}]",
                )

    def _create_non_stream(self, request_body: Dict[str, Any]) -> ChatCompletion:
        """
        Create non-streaming completion.

        Args:
            request_body: Request body to send to Mercator proxy.

        Returns:
            ChatCompletion: Parsed completion response.

        Raises:
            MercatorError: If request fails or response is invalid.
        """
        # Make HTTP request via transport
        response = self._transport.request(
            method="POST", path="/v1/chat/completions", json=request_body
        )

        # Parse response JSON
        response_data = response.json()

        # Extract Mercator metadata from headers
        mercator_metadata = self._extract_metadata(response)

        # Build ChatCompletion object
        choices = [
            ChatCompletionChoice(
                index=choice["index"],
                message=ChatMessage(**choice["message"]),
                finish_reason=choice["finish_reason"],
            )
            for choice in response_data["choices"]
        ]

        usage = None
        if "usage" in response_data:
            usage = ChatCompletionUsage(**response_data["usage"])

        return ChatCompletion(
            id=response_data["id"],
            created=response_data["created"],
            model=response_data["model"],
            choices=choices,
            usage=usage,
            mercator_metadata=mercator_metadata,
        )

    def _extract_metadata(self, response: httpx.Response) -> Optional[MercatorMetadata]:
        """
        Extract Mercator metadata from response headers.

        Mercator proxy returns governance metadata in X-Mercator-* headers.
        This method extracts those headers and builds a MercatorMetadata object.

        Args:
            response: HTTP response from Mercator proxy.

        Returns:
            MercatorMetadata object if metadata is enabled, None otherwise.
        """
        if not self.client.config.enable_metadata:
            return None

        headers = response.headers

        # Extract detection types from comma-separated string
        detection_types_str = headers.get("X-Mercator-Detection-Types", "")
        detection_types = (
            [dt.strip() for dt in detection_types_str.split(",") if dt.strip()]
            if detection_types_str
            else []
        )

        return MercatorMetadata(
            request_id=headers.get("X-Mercator-Request-Id", ""),
            policy_id=headers.get("X-Mercator-Policy-Id"),
            policy_decision=headers.get("X-Mercator-Policy-Decision"),
            provider_used=headers.get("X-Mercator-Provider-Used"),
            detections_count=int(headers.get("X-Mercator-Detections-Count", 0)),
            detection_types=detection_types,
            actual_cost=(
                float(headers.get("X-Mercator-Cost")) if headers.get("X-Mercator-Cost") else None
            ),
            latency_ms=(
                int(headers.get("X-Mercator-Latency-Ms"))
                if headers.get("X-Mercator-Latency-Ms")
                else None
            ),
        )

    def _create_stream(self, request_body: Dict[str, Any]) -> Iterator[ChatCompletionChunk]:
        """
        Create streaming completion.

        Streams chat completion chunks via Server-Sent Events (SSE). Each chunk
        contains incremental updates (deltas) to the completion. The stream ends
        when a [DONE] marker is received.

        Args:
            request_body: Request body to send to Mercator proxy.

        Yields:
            ChatCompletionChunk: Each chunk as it arrives from the stream.

        Raises:
            PolicyViolationError: Request blocked by policy (403).
            ProviderUnavailableError: Provider error (502).
            RateLimitError: Rate limit exceeded (429).
            MercatorError: Other errors.

        Example:
            >>> stream = client.chat.completions.create(
            ...     model="gpt-4",
            ...     messages=[{"role": "user", "content": "Hello"}],
            ...     stream=True
            ... )
            >>> for chunk in stream:
            ...     delta = chunk.choices[0].get("delta", {})
            ...     if "content" in delta:
            ...         print(delta["content"], end="", flush=True)
        """
        logger.debug(f"Starting streaming chat completion for model: {request_body.get('model')}")

        # Stream SSE response from transport layer
        for line in self._transport.stream_request(
            method="POST", path="/v1/chat/completions", json=request_body
        ):
            # Parse JSON chunk
            try:
                chunk_data = json.loads(line)
            except json.JSONDecodeError as e:
                # Log and skip invalid JSON
                logger.warning(f"Failed to parse streaming chunk JSON: {e}, line: {line[:100]}")
                continue

            # Build ChatCompletionChunk object
            chunk = ChatCompletionChunk(
                id=chunk_data.get("id", ""),
                created=chunk_data.get("created", int(time.time())),
                model=chunk_data.get("model"),
                choices=chunk_data.get("choices", []),
            )

            yield chunk

        logger.debug("Streaming chat completion completed")

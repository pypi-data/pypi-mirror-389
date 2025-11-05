# API Reference

Complete API reference for Mercator Python SDK.

## Table of Contents

- [MercatorClient](#mercatorclient)
- [MercatorConfig](#mercatorconfig)
- [Chat API](#chat-api)
- [Response Objects](#response-objects)
- [Exceptions](#exceptions)
- [Session Management](#session-management)

---

## MercatorClient

Main client for interacting with the Mercator proxy.

### Constructor

```python
MercatorClient(
    api_key: Optional[str] = None,
    endpoint: Optional[str] = None,
    application: Optional[str] = None,
    user_id: Optional[str] = None,
    environment: str = "production",
    timeout: int = 60,
    max_retries: int = 3,
    verify_ssl: bool = True,
    enable_metadata: bool = True,
    mode: str = "proxy",
    fallback_provider: Optional[str] = None,
    fallback_api_key: Optional[str] = None,
    custom_headers: Optional[Dict[str, str]] = None,
    config: Optional[MercatorConfig] = None
)
```

**Parameters:**

- **api_key** (`str`, optional): Mercator API key. Required for proxy mode. Can be set via `MERCATOR_API_KEY` environment variable.
- **endpoint** (`str`, optional): Mercator proxy endpoint URL. Defaults to `https://proxy.mercator.local:8443`.
- **application** (`str`, optional): Application identifier for audit logging.
- **user_id** (`str`, optional): Default user identifier for all requests.
- **environment** (`str`, default: `"production"`): Environment name (production, staging, development).
- **timeout** (`int`, default: `60`): Request timeout in seconds.
- **max_retries** (`int`, default: `3`): Maximum number of retry attempts.
- **verify_ssl** (`bool`, default: `True`): Whether to verify SSL certificates.
- **enable_metadata** (`bool`, default: `True`): Whether to extract Mercator governance metadata from responses.
- **mode** (`str`, default: `"proxy"`): Operating mode - `"proxy"` or `"local"`.
- **fallback_provider** (`str`, optional): Provider to use in local mode (`"openai"` or `"anthropic"`).
- **fallback_api_key** (`str`, optional): API key for fallback provider in local mode.
- **custom_headers** (`Dict[str, str]`, optional): Custom headers to include in all requests.
- **config** (`MercatorConfig`, optional): Configuration object (alternative to individual parameters).

**Example:**

```python
from mercator import MercatorClient

# Basic usage
client = MercatorClient(
    api_key="mercator-key-abc123",
    application="my-app",
    user_id="user@example.com"
)

# With configuration object
from mercator import MercatorConfig

config = MercatorConfig(
    api_key="mercator-key-abc123",
    endpoint="https://proxy.example.com:8443",
    timeout=120
)
client = MercatorClient(config=config)

# From environment variables
client = MercatorClient.from_env()
```

### Methods

#### `from_env()`

**Class method** - Create client from environment variables.

```python
client = MercatorClient.from_env()
```

Reads configuration from:
- `MERCATOR_API_KEY`
- `MERCATOR_ENDPOINT`
- `MERCATOR_APPLICATION`
- `MERCATOR_USER_ID`
- `MERCATOR_ENVIRONMENT`
- `MERCATOR_TIMEOUT`
- `MERCATOR_MAX_RETRIES`
- `MERCATOR_VERIFY_SSL`

#### `session(user_id: str, session_id: Optional[str] = None)`

Context manager for session tracking. All requests within the context share the same user/session metadata.

**Parameters:**
- **user_id** (`str`, required): User identifier for the session.
- **session_id** (`str`, optional): Session identifier. Auto-generated if not provided.

**Returns:** Context manager

**Example:**

```python
with client.session(user_id="user@example.com", session_id="sess-123"):
    response1 = client.chat.completions.create(...)
    response2 = client.chat.completions.create(...)
```

#### `close()`

Close the HTTP client and release resources.

```python
client.close()
```

#### Context Manager Support

The client can be used as a context manager:

```python
with MercatorClient(api_key="...") as client:
    response = client.chat.completions.create(...)
# Automatically closed
```

---

## MercatorConfig

Configuration object for MercatorClient.

### Constructor

```python
MercatorConfig(
    api_key: Optional[str] = None,
    endpoint: str = "https://proxy.mercator.local:8443",
    application: Optional[str] = None,
    user_id: Optional[str] = None,
    environment: str = "production",
    timeout: int = 60,
    max_retries: int = 3,
    verify_ssl: bool = True,
    enable_metadata: bool = True,
    custom_headers: Optional[Dict[str, str]] = None
)
```

**Example:**

```python
from mercator import MercatorConfig, MercatorClient

config = MercatorConfig(
    api_key="mercator-key-abc123",
    endpoint="https://proxy.example.com:8443",
    application="my-app",
    timeout=120,
    max_retries=5
)

client = MercatorClient(config=config)
```

### Validation

Config is validated on initialization:
- `api_key` must be at least 10 characters
- `endpoint` must be a valid URL
- `timeout` must be positive
- `max_retries` must be non-negative

---

## Chat API

### `client.chat.completions.create()`

Create a chat completion request.

```python
response = client.chat.completions.create(
    model: str,
    messages: List[Dict[str, str]],
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    top_p: Optional[float] = None,
    frequency_penalty: Optional[float] = None,
    presence_penalty: Optional[float] = None,
    stop: Optional[Union[str, List[str]]] = None,
    stream: bool = False,
    user: Optional[str] = None,
    mercator_dry_run: bool = False,
    mercator_hints: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Union[ChatCompletion, Iterator[ChatCompletionChunk]]
```

**Parameters:**

- **model** (`str`, required): Model identifier (e.g., `"gpt-4"`, `"claude-3-opus"`).
- **messages** (`List[Dict[str, str]]`, required): List of message objects with `role` and `content` keys.
- **temperature** (`float`, optional): Sampling temperature (0.0 - 2.0).
- **max_tokens** (`int`, optional): Maximum tokens to generate.
- **top_p** (`float`, optional): Nucleus sampling parameter.
- **frequency_penalty** (`float`, optional): Frequency penalty (-2.0 - 2.0).
- **presence_penalty** (`float`, optional): Presence penalty (-2.0 - 2.0).
- **stop** (`str | List[str]`, optional): Stop sequences.
- **stream** (`bool`, default: `False`): Whether to stream the response.
- **user** (`str`, optional): End-user identifier for abuse detection.
- **mercator_dry_run** (`bool`, default: `False`): Test policy without executing (Mercator-specific).
- **mercator_hints** (`Dict[str, Any]`, optional): Routing hints for Mercator (e.g., `{"prefer_provider": "anthropic"}`).
- **kwargs**: Additional provider-specific parameters.

**Returns:**
- `ChatCompletion` object if `stream=False`
- Iterator of `ChatCompletionChunk` objects if `stream=True`

**Raises:**
- `ValidationError`: Invalid request parameters
- `PolicyViolationError`: Request blocked by policy
- `RateLimitError`: Rate limit exceeded
- `AuthenticationError`: Invalid API key
- `NetworkError`: Network/connectivity issues

**Example - Non-streaming:**

```python
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"}
    ],
    temperature=0.7,
    max_tokens=100
)

print(response.choices[0].message.content)
```

**Example - Streaming:**

```python
stream = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Tell me a story"}],
    stream=True
)

for chunk in stream:
    delta = chunk.choices[0].get("delta", {})
    if "content" in delta:
        print(delta["content"], end="", flush=True)
```

**Example - Dry Run:**

```python
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Test"}],
    mercator_dry_run=True
)

print(f"Policy decision: {response.mercator_metadata.policy_decision}")
# Does not execute the request, only evaluates policy
```

---

## Response Objects

### ChatCompletion

Response object for non-streaming chat completions.

**Attributes:**

```python
class ChatCompletion:
    id: str                          # Unique completion ID
    object: str                      # Always "chat.completion"
    created: int                     # Unix timestamp
    model: str                       # Model used
    choices: List[Choice]            # List of completion choices
    usage: Optional[Usage]           # Token usage information
    mercator_metadata: Optional[MercatorMetadata]  # Governance metadata
```

**Example:**

```python
response = client.chat.completions.create(...)

print(f"ID: {response.id}")
print(f"Model: {response.model}")
print(f"Content: {response.choices[0].message.content}")
print(f"Total tokens: {response.usage.total_tokens}")
print(f"Provider: {response.mercator_metadata.provider_used}")
```

### ChatCompletionChunk

Response chunk for streaming chat completions.

**Attributes:**

```python
class ChatCompletionChunk:
    id: str                     # Unique completion ID
    object: str                 # Always "chat.completion.chunk"
    created: int                # Unix timestamp
    model: str                  # Model used
    choices: List[Dict]         # List with delta information
```

**Example:**

```python
stream = client.chat.completions.create(..., stream=True)

for chunk in stream:
    delta = chunk.choices[0].get("delta", {})
    if "content" in delta:
        print(delta["content"], end="", flush=True)
```

### Choice

Represents a single completion choice.

**Attributes:**

```python
class Choice:
    index: int                  # Choice index
    message: Message            # Complete message (non-streaming)
    delta: Dict                 # Partial message (streaming)
    finish_reason: Optional[str]  # Reason for completion end
```

### Message

Chat message object.

**Attributes:**

```python
class Message:
    role: str                   # Message role (system/user/assistant)
    content: str                # Message content
```

### Usage

Token usage information.

**Attributes:**

```python
class Usage:
    prompt_tokens: int          # Tokens in prompt
    completion_tokens: int      # Tokens in completion
    total_tokens: int           # Total tokens used
```

### MercatorMetadata

Governance metadata from Mercator proxy.

**Attributes:**

```python
class MercatorMetadata:
    request_id: str                       # Unique request ID
    policy_id: Optional[str]              # Applied policy ID
    policy_decision: Optional[str]        # ALLOW, BLOCK, or REDACT
    provider_used: Optional[str]          # Provider used (openai, anthropic, etc.)
    detections_count: int                 # Number of content detections
    detection_types: List[str]            # Types detected (e.g., pii.email)
    actual_cost: Optional[float]          # Actual cost in USD
    latency_ms: Optional[int]             # Request latency in milliseconds
```

**Example:**

```python
response = client.chat.completions.create(...)

metadata = response.mercator_metadata
print(f"Request ID: {metadata.request_id}")
print(f"Policy: {metadata.policy_decision}")
print(f"Provider: {metadata.provider_used}")
print(f"Detections: {metadata.detections_count} - {metadata.detection_types}")
print(f"Cost: ${metadata.actual_cost}")
print(f"Latency: {metadata.latency_ms}ms")
```

---

## Exceptions

All exceptions inherit from `MercatorError`.

### MercatorError

Base exception class.

```python
class MercatorError(Exception):
    pass
```

### ValidationError

Raised when request validation fails.

```python
class ValidationError(MercatorError):
    message: str
```

**Example:**

```python
from mercator import ValidationError

try:
    response = client.chat.completions.create(
        model="",  # Empty model
        messages=[{"role": "user", "content": "Hello"}]
    )
except ValidationError as e:
    print(f"Validation failed: {e.message}")
```

### PolicyViolationError

Raised when request is blocked by policy.

```python
class PolicyViolationError(MercatorError):
    message: str
    policy_id: str
    policy_name: str
    rule: str
    reason: str
```

**Example:**

```python
from mercator import PolicyViolationError

try:
    response = client.chat.completions.create(...)
except PolicyViolationError as e:
    print(f"Blocked by policy: {e.policy_name}")
    print(f"Rule: {e.rule}")
    print(f"Reason: {e.reason}")
```

### RateLimitError

Raised when rate limit is exceeded.

```python
class RateLimitError(MercatorError):
    message: str
    retry_after: Optional[int]  # Seconds until retry
```

**Example:**

```python
from mercator import RateLimitError
import time

try:
    response = client.chat.completions.create(...)
except RateLimitError as e:
    print(f"Rate limited: {e.message}")
    if e.retry_after:
        print(f"Retry after: {e.retry_after} seconds")
        time.sleep(e.retry_after)
        # Retry request
```

### AuthenticationError

Raised when API key is invalid or missing.

```python
class AuthenticationError(MercatorError):
    message: str
```

### NetworkError

Raised on network/connectivity issues.

```python
class NetworkError(MercatorError):
    message: str
    cause: Optional[Exception]
```

### ProviderError

Raised when the underlying LLM provider returns an error.

```python
class ProviderError(MercatorError):
    message: str
    provider: str
    status_code: Optional[int]
```

---

## Session Management

### Session Context Manager

The `session()` context manager groups multiple requests under the same user/session for audit tracking.

```python
with client.session(user_id: str, session_id: Optional[str] = None):
    # All requests share user_id and session_id
    ...
```

**Parameters:**
- **user_id** (`str`, required): User identifier.
- **session_id** (`str`, optional): Session identifier. Auto-generated if not provided.

**Example:**

```python
from mercator import MercatorClient

client = MercatorClient(api_key="...")

# Single session
with client.session(user_id="user@example.com", session_id="sess-123"):
    # Request 1
    response1 = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello"}]
    )

    # Request 2 - shares same session
    response2 = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Follow-up question"}]
    )

# Session ended - requests outside context use default user_id
```

**Nested Sessions:**

```python
# Outer session
with client.session(user_id="user1@example.com"):
    response1 = client.chat.completions.create(...)

    # Inner session - overrides outer session
    with client.session(user_id="user2@example.com", session_id="sess-456"):
        response2 = client.chat.completions.create(...)

    # Back to outer session
    response3 = client.chat.completions.create(...)
```

---

## Local Development Mode

For development and testing, you can bypass the Mercator proxy using local mode.

**⚠️ WARNING**: Local mode bypasses all policy enforcement, content detection, and audit logging.

### Configuration

```python
client = MercatorClient(
    mode="local",
    fallback_provider="openai",  # or "anthropic"
    fallback_api_key="sk-..."    # Provider API key
)
```

### Supported Providers

- **OpenAI**: Requires `openai` package (`pip install openai`)
- **Anthropic**: Requires `anthropic` package (`pip install anthropic`)

### Example

```python
from mercator import MercatorClient

# OpenAI local mode
client = MercatorClient(
    mode="local",
    fallback_provider="openai",
    fallback_api_key="sk-..."
)

# Same API as proxy mode
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)

print(response.choices[0].message.content)
```

### Environment-Based Mode Switching

```python
import os
from mercator import MercatorClient

# Use proxy in production, local in development
if os.getenv("ENV") == "production":
    client = MercatorClient(
        api_key=os.getenv("MERCATOR_API_KEY"),
        application="my-app"
    )
else:
    client = MercatorClient(
        mode="local",
        fallback_provider="openai",
        fallback_api_key=os.getenv("OPENAI_API_KEY")
    )

# Same code works in both modes
response = client.chat.completions.create(...)
```

---

## Best Practices

### 1. Use Context Managers

Always use context managers to ensure proper resource cleanup:

```python
# Good
with MercatorClient(api_key="...") as client:
    response = client.chat.completions.create(...)

# Also good
client = MercatorClient(api_key="...")
try:
    response = client.chat.completions.create(...)
finally:
    client.close()
```

### 2. Handle Errors Gracefully

```python
from mercator import MercatorClient, PolicyViolationError, RateLimitError

client = MercatorClient(api_key="...")

try:
    response = client.chat.completions.create(...)
except PolicyViolationError as e:
    # Handle policy violations
    logger.warning(f"Request blocked: {e.policy_name}")
except RateLimitError as e:
    # Handle rate limits
    time.sleep(e.retry_after or 60)
    # Retry
except Exception as e:
    # Handle other errors
    logger.error(f"Request failed: {e}")
```

### 3. Use Session Tracking

Group related requests for better audit trails:

```python
with client.session(user_id="user@example.com"):
    # Multi-turn conversation
    for message in conversation:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=message
        )
```

### 4. Access Governance Metadata

Monitor governance decisions and detections:

```python
response = client.chat.completions.create(...)

metadata = response.mercator_metadata
if metadata.detections_count > 0:
    logger.warning(f"Detected: {metadata.detection_types}")

logger.info(f"Cost: ${metadata.actual_cost}, Latency: {metadata.latency_ms}ms")
```

### 5. Test Policies with Dry Run

Validate requests against policies without execution:

```python
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Test"}],
    mercator_dry_run=True
)

if response.mercator_metadata.policy_decision == "BLOCK":
    print("Request would be blocked")
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MERCATOR_API_KEY` | Mercator API key (required) | - |
| `MERCATOR_ENDPOINT` | Proxy endpoint URL | `https://proxy.mercator.local:8443` |
| `MERCATOR_APPLICATION` | Application identifier | - |
| `MERCATOR_USER_ID` | Default user identifier | - |
| `MERCATOR_ENVIRONMENT` | Environment name | `production` |
| `MERCATOR_TIMEOUT` | Request timeout (seconds) | `60` |
| `MERCATOR_MAX_RETRIES` | Maximum retries | `3` |
| `MERCATOR_VERIFY_SSL` | Verify SSL certificates | `true` |

---

## Migration from OpenAI SDK

Mercator SDK is designed as a drop-in replacement for the OpenAI SDK.

### Before (OpenAI SDK)

```python
from openai import OpenAI

client = OpenAI(api_key="sk-...")

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)
```

### After (Mercator SDK)

```python
from mercator import MercatorClient

client = MercatorClient(
    api_key="mercator-key-...",  # Changed: Mercator API key
    application="my-app"          # Added: Application identifier
)

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)

# Added: Access governance metadata
print(response.mercator_metadata.policy_decision)
```

**That's it!** Only 2 lines need to change:
1. Import: `from mercator import MercatorClient`
2. Constructor: Add `application` parameter

---

## Support

- **Documentation**: https://docs.mercator.dev
- **Issues**: https://github.com/codeeater800/mercator-one/issues
- **Email**: support@mercator.dev

# Mercator Python SDK

A drop-in replacement for OpenAI/Anthropic SDKs that provides automatic LLM governance, policy enforcement, content detection, and compliance logging through the Mercator proxy.

## Features

- **Drop-in Replacement**: Change 2 lines of code to add governance to existing applications
- **Policy Enforcement**: Automatic policy evaluation for all LLM requests (F2.2)
- **Content Detection**: Built-in PHI/PII/toxic content detection (F3.1)
- **Audit Logging**: Comprehensive compliance logging (F4.1)
- **OpenAI Compatible**: Works with existing OpenAI SDK code
- **Streaming Support**: Full support for streaming responses
- **Session Tracking**: User and session-level request grouping
- **Local Development Mode**: Bypass proxy for local development

## Installation

```bash
pip install mercator-sdk
```

## Quick Start

### Basic Usage

```python
from mercator import MercatorClient

# Create client (drop-in replacement for OpenAI)
client = MercatorClient(
    api_key="mercator-key-...",
    application="my-app"
)

# Make LLM request (automatically governed)
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello, how are you?"}]
)

print(response.choices[0].message.content)
```

### With Context Manager (Recommended)

```python
from mercator import MercatorClient

with MercatorClient(api_key="mercator-key-...") as client:
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello"}]
    )
    print(response.choices[0].message.content)
```

### From Environment Variables

```bash
export MERCATOR_API_KEY=mercator-key-...
export MERCATOR_APPLICATION=my-app
export MERCATOR_USER_ID=user@example.com
```

```python
from mercator import MercatorClient

# Automatically loads from environment
client = MercatorClient.from_env()
```

### Session Tracking

```python
from mercator import MercatorClient

client = MercatorClient(api_key="mercator-key-...")

with client.session(user_id="user@example.com", session_id="sess-123"):
    # All requests in this block share the same session
    response1 = client.chat.completions.create(...)
    response2 = client.chat.completions.create(...)
```

### Streaming Responses

```python
from mercator import MercatorClient

client = MercatorClient(api_key="mercator-key-...")

# Stream chat completion
stream = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Tell me a story"}],
    stream=True
)

# Print response as it streams
for chunk in stream:
    delta = chunk.choices[0].get("delta", {})
    if "content" in delta:
        print(delta["content"], end="", flush=True)
```

**Accumulating full response:**

```python
# Accumulate full response from stream
stream = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Explain quantum physics"}],
    stream=True
)

full_response = ""
for chunk in stream:
    delta = chunk.choices[0].get("delta", {})
    if "content" in delta:
        full_response += delta["content"]

print(f"\nFull response: {full_response}")
```

## Configuration

### Programmatic Configuration

```python
from mercator import MercatorClient, MercatorConfig

config = MercatorConfig(
    api_key="mercator-key-...",
    endpoint="https://proxy.mercator.local:8443",
    application="my-app",
    user_id="user@example.com",
    timeout=60,
    max_retries=3,
    verify_ssl=True
)

client = MercatorClient(config=config)
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MERCATOR_API_KEY` | Mercator API key (required) | - |
| `MERCATOR_ENDPOINT` | Proxy endpoint URL | `https://proxy.mercator.local:8443` |
| `MERCATOR_APPLICATION` | Application identifier | - |
| `MERCATOR_USER_ID` | User identifier | - |
| `MERCATOR_ENVIRONMENT` | Environment (production/development/staging) | `production` |
| `MERCATOR_TIMEOUT` | Request timeout in seconds | `60` |
| `MERCATOR_MAX_RETRIES` | Maximum retry attempts | `3` |
| `MERCATOR_VERIFY_SSL` | Verify SSL certificates (true/false) | `true` |

## Mercator Metadata

Access governance metadata from responses:

```python
from mercator import MercatorClient

client = MercatorClient(
    api_key="mercator-key-...",
    enable_metadata=True  # Enable metadata extraction (default: True)
)

response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)

# Access Mercator governance metadata
metadata = response.mercator_metadata
print(f"Request ID: {metadata.request_id}")
print(f"Policy Decision: {metadata.policy_decision}")  # ALLOW, BLOCK, REDACT
print(f"Provider Used: {metadata.provider_used}")  # openai, anthropic, etc.
print(f"Detections Count: {metadata.detections_count}")
print(f"Detection Types: {metadata.detection_types}")  # ['pii.email', 'pii.phone']
print(f"Actual Cost: ${metadata.actual_cost}")
print(f"Latency: {metadata.latency_ms}ms")
```

### Mercator-Specific Features

```python
# Test policy without executing (dry run)
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}],
    mercator_dry_run=True
)
print(f"Policy decision: {response.mercator_metadata.policy_decision}")

# Provide routing hints to Mercator
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}],
    mercator_hints={
        "prefer_provider": "anthropic",
        "max_cost": 0.01
    }
)
```

## Error Handling

```python
from mercator import MercatorClient, PolicyViolationError, RateLimitError

client = MercatorClient(api_key="mercator-key-...")

try:
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello"}]
    )
except PolicyViolationError as e:
    # Request blocked by policy
    print(f"Policy: {e.policy_name}")
    print(f"Rule: {e.rule}")
    print(f"Reason: {e.reason}")
except RateLimitError as e:
    # Rate limit exceeded
    print(f"Rate limit exceeded. Retry after: {e.retry_after}s")
except Exception as e:
    # Other errors
    print(f"Error: {e}")
```

## Local Development Mode

For local development and testing without governance overhead, use local mode to bypass the Mercator proxy and route requests directly to LLM providers.

**⚠️ WARNING**: Local mode bypasses all policy enforcement, content detection, and audit logging. Use only for development/testing, never in production.

### Basic Local Mode

```python
from mercator import MercatorClient

# OpenAI local mode
client = MercatorClient(
    mode="local",
    fallback_provider="openai",
    fallback_api_key="sk-..."  # Your OpenAI API key
)

# Same API as proxy mode - just bypasses governance
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)
print(response.choices[0].message.content)
```

### Anthropic Local Mode

```python
# Anthropic local mode
client = MercatorClient(
    mode="local",
    fallback_provider="anthropic",
    fallback_api_key="sk-ant-..."  # Your Anthropic API key
)

response = client.chat.completions.create(
    model="claude-3-opus",
    messages=[{"role": "user", "content": "Hello"}]
)
```

### Switching Between Modes

The same code works in both proxy and local modes:

```python
import os

# Use proxy mode in production, local mode in development
mode = "proxy" if os.getenv("ENV") == "production" else "local"

client = MercatorClient(
    mode=mode,
    api_key="mercator-key-..." if mode == "proxy" else None,
    fallback_provider="openai" if mode == "local" else None,
    fallback_api_key=os.getenv("OPENAI_API_KEY") if mode == "local" else None,
)

# Same code works in both modes
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)
```

### Requirements for Local Mode

Local mode requires the provider SDK to be installed:

```bash
# For OpenAI
pip install openai

# For Anthropic
pip install anthropic
```

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/codeeater800/mercator-one.git
cd mercator-one/mercator-sdk/mercator-sdk-python

# Install dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=mercator --cov-report=html

# Run specific test file
pytest tests/test_config.py

# Run specific test
pytest tests/test_config.py::TestMercatorConfigInitialization::test_config_minimal_valid
```

### Code Quality

```bash
# Format code
black .

# Lint code
ruff check .

# Type check
mypy mercator
```

## Requirements

- Python 3.8+
- httpx >= 0.25.0

## License

MIT

## Support

- Documentation: https://www.docs.onmercator.com
- Issues: https://www.issues.onmercator.com
- Email: shreyas@onmercator.com

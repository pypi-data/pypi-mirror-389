# Getting Started with Mercator Python SDK

This guide will help you get started with the Mercator Python SDK in minutes.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Making Requests](#making-requests)
- [Streaming](#streaming)
- [Error Handling](#error-handling)
- [Session Tracking](#session-tracking)
- [Local Development](#local-development)
- [Next Steps](#next-steps)

---

## Installation

Install the Mercator SDK using pip:

```bash
pip install mercator-sdk
```

**Requirements:**
- Python 3.8 or higher
- httpx >= 0.25.0

**Optional dependencies** (for local mode):
```bash
# For OpenAI local mode
pip install openai

# For Anthropic local mode
pip install anthropic
```

---

## Quick Start

### 1. Get Your API Key

First, obtain a Mercator API key from your Mercator dashboard or administrator.

### 2. Create Your First Client

```python
from mercator import MercatorClient

# Create client
client = MercatorClient(
    api_key="mercator-key-abc123",
    application="my-first-app"
)

# Make your first request
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ]
)

# Print the response
print(response.choices[0].message.content)

# Clean up
client.close()
```

### 3. Run Your Code

```bash
python my_app.py
```

That's it! Your LLM requests are now governed by Mercator policies.

---

## Configuration

### Method 1: Direct Configuration

```python
from mercator import MercatorClient

client = MercatorClient(
    api_key="mercator-key-abc123",
    endpoint="https://proxy.mercator.local:8443",
    application="my-app",
    user_id="user@example.com",
    timeout=60,
    max_retries=3
)
```

### Method 2: Configuration Object

```python
from mercator import MercatorClient, MercatorConfig

config = MercatorConfig(
    api_key="mercator-key-abc123",
    application="my-app",
    timeout=120
)

client = MercatorClient(config=config)
```

### Method 3: Environment Variables

Set environment variables:

```bash
export MERCATOR_API_KEY=mercator-key-abc123
export MERCATOR_APPLICATION=my-app
export MERCATOR_USER_ID=user@example.com
```

Then load from environment:

```python
from mercator import MercatorClient

# Automatically loads from environment
client = MercatorClient.from_env()
```

### Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `api_key` | `str` | Required | Mercator API key |
| `endpoint` | `str` | `https://proxy.mercator.local:8443` | Proxy endpoint URL |
| `application` | `str` | `None` | Application identifier |
| `user_id` | `str` | `None` | Default user identifier |
| `environment` | `str` | `production` | Environment name |
| `timeout` | `int` | `60` | Request timeout (seconds) |
| `max_retries` | `int` | `3` | Maximum retry attempts |
| `verify_ssl` | `bool` | `True` | Verify SSL certificates |
| `enable_metadata` | `bool` | `True` | Extract governance metadata |

---

## Making Requests

### Basic Chat Completion

```python
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"}
    ]
)

print(response.choices[0].message.content)
# Output: "The capital of France is Paris."
```

### With All Parameters

```python
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "user", "content": "Tell me a joke"}
    ],
    temperature=0.7,
    max_tokens=100,
    top_p=0.9,
    frequency_penalty=0.5,
    presence_penalty=0.3,
    stop=["\n\n"]
)
```

### Multi-Turn Conversation

```python
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is Python?"},
]

# First turn
response1 = client.chat.completions.create(
    model="gpt-4",
    messages=messages
)

# Add assistant response to conversation
messages.append({
    "role": "assistant",
    "content": response1.choices[0].message.content
})

# Second turn
messages.append({
    "role": "user",
    "content": "Can you give me an example?"
})

response2 = client.chat.completions.create(
    model="gpt-4",
    messages=messages
)
```

---

## Streaming

For real-time responses, use streaming mode:

### Basic Streaming

```python
stream = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Tell me a story"}],
    stream=True
)

# Print response as it arrives
for chunk in stream:
    delta = chunk.choices[0].get("delta", {})
    if "content" in delta:
        print(delta["content"], end="", flush=True)

print()  # Newline at end
```

### Accumulate Full Response

```python
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
        print(delta["content"], end="", flush=True)

print(f"\n\nFull response length: {len(full_response)} characters")
```

### Handle Streaming Errors

```python
from mercator import PolicyViolationError

try:
    stream = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Tell me a story"}],
        stream=True
    )

    for chunk in stream:
        delta = chunk.choices[0].get("delta", {})
        if "content" in delta:
            print(delta["content"], end="", flush=True)

except PolicyViolationError as e:
    print(f"\nRequest blocked: {e.policy_name}")
except Exception as e:
    print(f"\nError: {e}")
```

---

## Error Handling

Mercator SDK raises specific exceptions for different error types:

### Policy Violations

```python
from mercator import PolicyViolationError

try:
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Sensitive content..."}]
    )
except PolicyViolationError as e:
    print(f"Policy: {e.policy_name}")
    print(f"Rule: {e.rule}")
    print(f"Reason: {e.reason}")
    # Handle gracefully - show user-friendly message
```

### Rate Limits

```python
from mercator import RateLimitError
import time

try:
    response = client.chat.completions.create(...)
except RateLimitError as e:
    print(f"Rate limited: {e.message}")
    if e.retry_after:
        print(f"Waiting {e.retry_after} seconds...")
        time.sleep(e.retry_after)
        # Retry request
        response = client.chat.completions.create(...)
```

### Validation Errors

```python
from mercator import ValidationError

try:
    response = client.chat.completions.create(
        model="",  # Invalid: empty model
        messages=[{"role": "user", "content": "Hello"}]
    )
except ValidationError as e:
    print(f"Invalid request: {e.message}")
    # Fix request and retry
```

### Comprehensive Error Handling

```python
from mercator import (
    MercatorClient,
    PolicyViolationError,
    RateLimitError,
    ValidationError,
    AuthenticationError,
    NetworkError
)

client = MercatorClient(api_key="...")

try:
    response = client.chat.completions.create(...)
    print(response.choices[0].message.content)

except ValidationError as e:
    print(f"Invalid request: {e.message}")

except PolicyViolationError as e:
    print(f"Blocked by policy '{e.policy_name}': {e.reason}")

except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s")

except AuthenticationError as e:
    print(f"Authentication failed: {e.message}")

except NetworkError as e:
    print(f"Network error: {e.message}")

except Exception as e:
    print(f"Unexpected error: {e}")

finally:
    client.close()
```

---

## Session Tracking

Group related requests for better audit trails:

### Basic Session

```python
from mercator import MercatorClient

client = MercatorClient(api_key="...")

with client.session(user_id="user@example.com", session_id="sess-123"):
    # All requests in this block share the same session
    response1 = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello"}]
    )

    response2 = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Follow-up question"}]
    )
```

### Auto-Generated Session ID

If you don't provide a session ID, one is automatically generated:

```python
with client.session(user_id="user@example.com"):
    # session_id is auto-generated
    response = client.chat.completions.create(...)
```

### Multi-User Application

```python
def handle_user_request(user_id: str, message: str):
    with client.session(user_id=user_id):
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": message}]
        )
        return response.choices[0].message.content

# Different users
answer1 = handle_user_request("alice@example.com", "What is AI?")
answer2 = handle_user_request("bob@example.com", "What is ML?")
```

---

## Local Development

For local development and testing, use local mode to bypass the proxy:

**⚠️ WARNING**: Local mode bypasses all governance. Use only for development/testing.

### OpenAI Local Mode

```python
from mercator import MercatorClient

client = MercatorClient(
    mode="local",
    fallback_provider="openai",
    fallback_api_key="sk-..."  # Your OpenAI API key
)

# Same API as proxy mode
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)
```

### Environment-Based Mode Switching

```python
import os
from mercator import MercatorClient

# Automatically use proxy in production, local in development
env = os.getenv("ENV", "development")

if env == "production":
    client = MercatorClient(
        api_key=os.getenv("MERCATOR_API_KEY"),
        application="my-app"
    )
else:
    # Local mode for development
    client = MercatorClient(
        mode="local",
        fallback_provider="openai",
        fallback_api_key=os.getenv("OPENAI_API_KEY")
    )

# Same code works in both modes
response = client.chat.completions.create(...)
```

---

## Accessing Governance Metadata

Every response includes governance metadata from Mercator:

```python
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)

# Access metadata
metadata = response.mercator_metadata

print(f"Request ID: {metadata.request_id}")
print(f"Policy Decision: {metadata.policy_decision}")  # ALLOW, BLOCK, REDACT
print(f"Provider Used: {metadata.provider_used}")     # openai, anthropic, etc.
print(f"Cost: ${metadata.actual_cost}")
print(f"Latency: {metadata.latency_ms}ms")

# Check for content detections
if metadata.detections_count > 0:
    print(f"Detected: {metadata.detection_types}")
    # e.g., ['pii.email', 'pii.phone']
```

---

## Best Practices

### 1. Always Use Context Managers

```python
# Good - automatic cleanup
with MercatorClient(api_key="...") as client:
    response = client.chat.completions.create(...)

# Also good - explicit cleanup
client = MercatorClient(api_key="...")
try:
    response = client.chat.completions.create(...)
finally:
    client.close()
```

### 2. Handle Errors Gracefully

Always catch and handle specific exceptions:

```python
from mercator import PolicyViolationError, RateLimitError

try:
    response = client.chat.completions.create(...)
except PolicyViolationError as e:
    # Show user-friendly message
    return f"Sorry, I cannot process that request: {e.reason}"
except RateLimitError:
    # Queue for later or show retry message
    return "Service is busy, please try again"
```

### 3. Use Sessions for Multi-Turn Conversations

```python
with client.session(user_id=current_user.id):
    for user_message in conversation:
        response = client.chat.completions.create(...)
        # All requests tracked under same session
```

### 4. Monitor Governance Metadata

```python
response = client.chat.completions.create(...)

# Log governance metrics
logger.info(
    "LLM request completed",
    request_id=response.mercator_metadata.request_id,
    provider=response.mercator_metadata.provider_used,
    cost=response.mercator_metadata.actual_cost,
    latency_ms=response.mercator_metadata.latency_ms
)
```

### 5. Test Policies with Dry Run

```python
# Test if request would be blocked without executing
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Test message"}],
    mercator_dry_run=True
)

if response.mercator_metadata.policy_decision == "BLOCK":
    print("Request would be blocked - adjust before sending")
```

---

## Complete Example

Here's a complete example putting it all together:

```python
import os
from mercator import MercatorClient, PolicyViolationError, RateLimitError

def main():
    # Initialize client
    client = MercatorClient.from_env()

    try:
        # Use session tracking
        with client.session(user_id="user@example.com"):
            # Make request
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "What is the capital of France?"}
                ],
                temperature=0.7,
                max_tokens=100
            )

            # Print response
            print(response.choices[0].message.content)

            # Access governance metadata
            metadata = response.mercator_metadata
            print(f"\nRequest ID: {metadata.request_id}")
            print(f"Provider: {metadata.provider_used}")
            print(f"Cost: ${metadata.actual_cost}")

            # Check for detections
            if metadata.detections_count > 0:
                print(f"Detections: {metadata.detection_types}")

    except PolicyViolationError as e:
        print(f"Request blocked by policy '{e.policy_name}': {e.reason}")

    except RateLimitError as e:
        print(f"Rate limited. Retry after {e.retry_after}s")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        client.close()

if __name__ == "__main__":
    main()
```

---

## Next Steps

Now that you've learned the basics, explore more advanced features:

- **[API Reference](api-reference.md)** - Complete API documentation
- **[Examples](../examples/)** - More code examples
- **[Migration Guide](api-reference.md#migration-from-openai-sdk)** - Migrating from OpenAI SDK
- **[Error Handling](api-reference.md#exceptions)** - Comprehensive error handling guide

---

## Troubleshooting

### Issue: "Invalid API key"

**Solution**: Verify your API key:
```python
import os
print(f"API Key: {os.getenv('MERCATOR_API_KEY')}")
```

### Issue: "Connection refused"

**Solution**: Check endpoint configuration:
```python
client = MercatorClient(
    api_key="...",
    endpoint="https://your-proxy-url:8443",  # Verify URL
    verify_ssl=False  # If using self-signed cert
)
```

### Issue: "Request blocked by policy"

**Solution**: Check policy decision:
```python
try:
    response = client.chat.completions.create(...)
except PolicyViolationError as e:
    print(f"Policy: {e.policy_name}")
    print(f"Rule: {e.rule}")
    print(f"Reason: {e.reason}")
    # Adjust request accordingly
```

---

## Support

Need help? Reach out:

- **Documentation**: https://docs.mercator.dev
- **GitHub Issues**: https://github.com/codeeater800/mercator-one/issues
- **Email**: support@mercator.dev

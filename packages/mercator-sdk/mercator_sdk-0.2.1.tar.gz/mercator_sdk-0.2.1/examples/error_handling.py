"""
Error handling example for Mercator SDK.

This example demonstrates how to handle various errors that can occur
when using the Mercator SDK, including policy violations, rate limits,
and validation errors.
"""

from mercator import (
    AuthenticationError,
    MercatorClient,
    MercatorError,
    PolicyViolationError,
    ProviderUnavailableError,
    RateLimitError,
    ValidationError,
)

client = MercatorClient(
    api_key="mercator-key-...",  # Replace with your API key
    application="error-handling-example",
)

print("=== Policy Violation Handling ===\n")

try:
    # This might be blocked by policy (e.g., content filter)
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Potentially sensitive content..."}],
    )
    print(f"Response: {response.choices[0].message.content}")

except PolicyViolationError as e:
    print("Request blocked by policy!")
    print(f"  Policy: {e.policy_name} (ID: {e.policy_id})")
    print(f"  Rule: {e.rule}")
    print(f"  Reason: {e.reason}")
    # Handle gracefully - maybe log and show user-friendly message

print("\n=== Rate Limit Handling ===\n")

try:
    # Multiple rapid requests might hit rate limit
    for i in range(100):
        response = client.chat.completions.create(
            model="gpt-4", messages=[{"role": "user", "content": f"Request {i}"}]
        )

except RateLimitError as e:
    print("Rate limit exceeded!")
    print(f"  Message: {e.message}")
    if e.retry_after:
        print(f"  Retry after: {e.retry_after} seconds")
    # Implement exponential backoff or queue for later

print("\n=== Validation Error Handling ===\n")

try:
    # Invalid request - missing model
    response = client.chat.completions.create(
        model="",  # Invalid: empty model
        messages=[{"role": "user", "content": "Hello"}],
    )

except ValidationError as e:
    print("Validation error!")
    print(f"  Message: {e.message}")
    print(f"  Field: {e.field}")
    # Fix the request and retry

print("\n=== Provider Unavailable Handling ===\n")

try:
    # Provider might be down or unreachable
    response = client.chat.completions.create(
        model="gpt-4", messages=[{"role": "user", "content": "Hello"}]
    )

except ProviderUnavailableError as e:
    print("Provider unavailable!")
    print(f"  Provider: {e.provider}")
    print(f"  Status: {e.status_code}")
    print(f"  Message: {e.message}")
    # Maybe fall back to another provider or retry later

print("\n=== Authentication Error Handling ===\n")

try:
    # Invalid API key
    bad_client = MercatorClient(api_key="invalid-key")
    response = bad_client.chat.completions.create(
        model="gpt-4", messages=[{"role": "user", "content": "Hello"}]
    )

except AuthenticationError as e:
    print("Authentication failed!")
    print(f"  Message: {e.message}")
    # Check API key, maybe prompt user to update

print("\n=== Comprehensive Error Handling ===\n")


def safe_chat_request(client, model, messages, **kwargs):
    """
    Make a chat request with comprehensive error handling.

    Returns:
        Tuple of (response, error) - one will be None
    """
    try:
        response = client.chat.completions.create(model=model, messages=messages, **kwargs)
        return response, None

    except PolicyViolationError as e:
        print(f"⚠️  Blocked by policy: {e.policy_name}")
        return None, e

    except RateLimitError as e:
        print(f"⏱  Rate limited, retry after {e.retry_after}s")
        return None, e

    except ValidationError as e:
        print(f"❌ Invalid request: {e.message}")
        return None, e

    except ProviderUnavailableError as e:
        print(f"🔌 Provider {e.provider} unavailable")
        return None, e

    except AuthenticationError as e:
        print(f"🔐 Authentication failed: {e.message}")
        return None, e

    except MercatorError as e:
        print(f"❗ Mercator error: {e.message}")
        return None, e

    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        return None, e


# Use the safe wrapper
response, error = safe_chat_request(
    client, model="gpt-4", messages=[{"role": "user", "content": "Hello"}]
)

if response:
    print(f"✅ Success: {response.choices[0].message.content}")
else:
    print(f"Failed with error: {type(error).__name__}")

# Clean up
client.close()

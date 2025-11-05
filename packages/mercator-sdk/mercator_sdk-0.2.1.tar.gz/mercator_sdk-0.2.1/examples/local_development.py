"""
Local development mode example for Mercator SDK.

This example demonstrates how to use local mode to bypass the Mercator proxy
and connect directly to LLM providers for local development and testing.

WARNING: Local mode bypasses all policy enforcement, content detection, and
audit logging. Use only for development/testing, never in production.
"""

import os

from mercator import MercatorClient

print("=== Local Mode with OpenAI ===\n")

# Create client in local mode with OpenAI
client = MercatorClient(
    mode="local",
    fallback_provider="openai",
    fallback_api_key="sk-...",  # Your OpenAI API key
)

# Same API as proxy mode - just bypasses governance
response = client.chat.completions.create(
    model="gpt-4", messages=[{"role": "user", "content": "What is 2 + 2?"}]
)

print(f"Response: {response.choices[0].message.content}")
print("No governance metadata in local mode")

client.close()

print("\n=== Local Mode with Anthropic ===\n")

# Create client in local mode with Anthropic
client = MercatorClient(
    mode="local",
    fallback_provider="anthropic",
    fallback_api_key="sk-ant-...",  # Your Anthropic API key
)

response = client.chat.completions.create(
    model="claude-3-opus", messages=[{"role": "user", "content": "Hello Claude"}]
)

print(f"Response: {response.choices[0].message.content}")

client.close()

print("\n=== Switching Between Modes ===\n")

# Use environment variable to switch between proxy and local mode
mode = "proxy" if os.getenv("ENV") == "production" else "local"

print(f"Running in mode: {mode}")

if mode == "local":
    client = MercatorClient(
        mode="local",
        fallback_provider="openai",
        fallback_api_key=os.getenv("OPENAI_API_KEY"),
    )
else:
    client = MercatorClient(
        mode="proxy", api_key=os.getenv("MERCATOR_API_KEY"), application="my-app"
    )

# Same code works in both modes!
response = client.chat.completions.create(
    model="gpt-4", messages=[{"role": "user", "content": "Hello"}]
)

print(f"Response: {response.choices[0].message.content}")

client.close()

print("\n=== Development vs Production Pattern ===\n")


def get_client():
    """Get appropriate client based on environment."""
    env = os.getenv("ENV", "development")

    if env == "production":
        # Production: Use Mercator proxy with full governance
        return MercatorClient(
            api_key=os.getenv("MERCATOR_API_KEY"),
            application="my-app",
            environment="production",
        )
    else:
        # Development: Use local mode for faster iteration
        return MercatorClient(
            mode="local",
            fallback_provider="openai",
            fallback_api_key=os.getenv("OPENAI_API_KEY"),
        )


# Use the same code in both environments
with get_client() as client:
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Tell me a joke."},
        ],
    )
    print(f"Response: {response.choices[0].message.content}")

print("\n=== Local Mode with Streaming ===\n")

# Streaming also works in local mode
client = MercatorClient(mode="local", fallback_provider="openai", fallback_api_key="sk-...")

stream = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Count to 5"}],
    stream=True,
)

print("Response: ", end="", flush=True)
for chunk in stream:
    delta = chunk.choices[0].get("delta", {})
    if "content" in delta:
        print(delta["content"], end="", flush=True)
print("\n")

client.close()

print("\n=== Testing Strategy ===\n")

# Use local mode for unit tests, proxy mode for integration tests


def test_my_feature():
    """Unit test using local mode."""
    client = MercatorClient(mode="local", fallback_provider="openai", fallback_api_key="sk-test")

    response = client.chat.completions.create(
        model="gpt-4", messages=[{"role": "user", "content": "Test"}]
    )

    assert response.choices[0].message.content
    print("✅ Test passed")

    client.close()


test_my_feature()

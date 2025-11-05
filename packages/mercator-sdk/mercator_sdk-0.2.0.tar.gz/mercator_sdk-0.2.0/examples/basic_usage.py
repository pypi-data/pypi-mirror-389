"""
Basic usage example for Mercator SDK.

This example demonstrates the fundamental usage of the Mercator SDK for
making LLM requests through the Mercator governance proxy.
"""

from mercator import MercatorClient

# Create a client with your Mercator API key
client = MercatorClient(
    api_key="mercator-key-...",  # Replace with your API key
    endpoint="https://proxy.mercator.local:8443",  # Default proxy endpoint
    application="example-app",  # Your application name
    user_id="user@example.com",  # Optional: user identifier
)

# Basic chat completion request
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"},
    ],
)

# Print the response
print("Response:", response.choices[0].message.content)

# Access governance metadata
if response.mercator_metadata:
    print("\nGovernance Metadata:")
    print(f"  Request ID: {response.mercator_metadata.request_id}")
    print(f"  Provider Used: {response.mercator_metadata.provider_used}")
    print(f"  Policy Decision: {response.mercator_metadata.policy_decision}")
    print(f"  Latency: {response.mercator_metadata.latency_ms}ms")
    if response.mercator_metadata.actual_cost:
        print(f"  Cost: ${response.mercator_metadata.actual_cost:.4f}")

# Clean up
client.close()

# Better: Use context manager
print("\n--- Using Context Manager ---")

with MercatorClient(api_key="mercator-key-...") as client:
    response = client.chat.completions.create(
        model="gpt-4", messages=[{"role": "user", "content": "Hello!"}]
    )
    print("Response:", response.choices[0].message.content)

"""
Streaming example for Mercator SDK.

This example demonstrates how to use streaming chat completions,
which allows you to receive the response incrementally as it's generated.
"""

from mercator import MercatorClient

client = MercatorClient(
    api_key="mercator-key-...",  # Replace with your API key
    application="streaming-example",
)

print("=== Basic Streaming ===\n")

# Stream a chat completion
stream = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Tell me a short story about a robot"}],
    stream=True,
)

# Print response as it streams
print("Response: ", end="", flush=True)
for chunk in stream:
    delta = chunk.choices[0].get("delta", {})
    if "content" in delta:
        print(delta["content"], end="", flush=True)
print("\n")

print("\n=== Accumulating Full Response ===\n")

# Accumulate the full response while streaming
stream = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Count to 10"}],
    stream=True,
    max_tokens=50,
)

full_response = ""
chunk_count = 0

for chunk in stream:
    chunk_count += 1
    delta = chunk.choices[0].get("delta", {})

    # Check for role (first chunk)
    if "role" in delta:
        print(f"Role: {delta['role']}")

    # Accumulate content
    if "content" in delta:
        full_response += delta["content"]

    # Check for finish reason
    finish_reason = chunk.choices[0].get("finish_reason")
    if finish_reason:
        print(f"Finish reason: {finish_reason}")

print(f"\nFull response: {full_response}")
print(f"Received {chunk_count} chunks")

print("\n=== Streaming with Parameters ===\n")

# Stream with additional parameters
stream = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a concise assistant."},
        {"role": "user", "content": "Explain quantum physics in one sentence."},
    ],
    stream=True,
    temperature=0.7,
    max_tokens=100,
)

print("Response: ", end="", flush=True)
for chunk in stream:
    delta = chunk.choices[0].get("delta", {})
    if "content" in delta:
        print(delta["content"], end="", flush=True)
print("\n")

# Clean up
client.close()

print("\n=== Using Context Manager ===\n")

# Better: Use context manager for automatic cleanup
with MercatorClient(api_key="mercator-key-...") as client:
    stream = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Say hello"}],
        stream=True,
    )

    print("Response: ", end="", flush=True)
    for chunk in stream:
        delta = chunk.choices[0].get("delta", {})
        if "content" in delta:
            print(delta["content"], end="", flush=True)
    print()

"""
Session tracking example for Mercator SDK.

This example demonstrates how to use session context to group related
requests and apply user-level tracking and policies.
"""

from mercator import MercatorClient

client = MercatorClient(
    api_key="mercator-key-...",  # Replace with your API key
    application="session-example",
)

print("=== Basic Session Tracking ===\n")

# Group related requests in a session
with client.session(user_id="user@example.com", session_id="sess-123"):
    # First request in session
    response1 = client.chat.completions.create(
        model="gpt-4", messages=[{"role": "user", "content": "What is 2 + 2?"}]
    )
    print(f"Response 1: {response1.choices[0].message.content}")

    # Second request in same session
    response2 = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "What was my previous question?"}],
    )
    print(f"Response 2: {response2.choices[0].message.content}")

    print("\nBoth requests include user_id and session_id metadata")

print("\n=== Auto-Generated Session IDs ===\n")

# Session ID is auto-generated if not provided
with client.session(user_id="user2@example.com") as session:
    print(f"Auto-generated session ID: {session.session_id}")

    response = client.chat.completions.create(
        model="gpt-4", messages=[{"role": "user", "content": "Hello"}]
    )
    print(f"Response: {response.choices[0].message.content}")

print("\n=== Nested Sessions ===\n")

# Sessions can be nested
with client.session(user_id="user3@example.com", session_id="outer-session"):
    print("In outer session")

    response1 = client.chat.completions.create(
        model="gpt-4", messages=[{"role": "user", "content": "Outer question"}]
    )

    # Inner session temporarily overrides
    with client.session(user_id="user4@example.com", session_id="inner-session"):
        print("In inner session")

        response2 = client.chat.completions.create(
            model="gpt-4", messages=[{"role": "user", "content": "Inner question"}]
        )

    print("Back to outer session")

    response3 = client.chat.completions.create(
        model="gpt-4", messages=[{"role": "user", "content": "Another outer question"}]
    )

print("\n=== Session for User Analytics ===\n")

# Track user activity across multiple interactions
user_sessions = {
    "user_123": "sess-abc",
    "user_456": "sess-def",
}

for user_id, session_id in user_sessions.items():
    with client.session(user_id=user_id, session_id=session_id):
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": f"Hello, I'm {user_id}"}],
        )

        print(f"{user_id}: {response.choices[0].message.content}")

        # Mercator tracks all requests by user and session
        if response.mercator_metadata:
            print(f"  Request ID: {response.mercator_metadata.request_id}")

# Clean up
client.close()

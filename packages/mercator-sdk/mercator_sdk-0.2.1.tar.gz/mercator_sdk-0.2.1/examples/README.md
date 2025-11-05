# Mercator SDK Examples

This directory contains example code demonstrating various features of the Mercator Python SDK.

## Examples

### [basic_usage.py](basic_usage.py)
Demonstrates fundamental SDK usage including:
- Creating a client
- Making chat completion requests
- Accessing governance metadata
- Using context managers

```bash
python examples/basic_usage.py
```

### [streaming.py](streaming.py)
Shows how to use streaming chat completions:
- Basic streaming
- Accumulating full responses
- Streaming with parameters

```bash
python examples/streaming.py
```

### [session_tracking.py](session_tracking.py)
Demonstrates session context for user tracking:
- Basic session tracking
- Auto-generated session IDs
- Nested sessions
- User analytics

```bash
python examples/session_tracking.py
```

### [error_handling.py](error_handling.py)
Comprehensive error handling examples:
- Policy violation errors
- Rate limit errors
- Validation errors
- Provider unavailable errors
- Authentication errors
- Building safe request wrappers

```bash
python examples/error_handling.py
```

### [local_development.py](local_development.py)
Local development mode for testing without governance:
- OpenAI local mode
- Anthropic local mode
- Switching between proxy and local modes
- Development vs production patterns

```bash
python examples/local_development.py
```

## Prerequisites

1. Install the Mercator SDK:
```bash
pip install mercator-sdk
```

2. Set environment variables:
```bash
export MERCATOR_API_KEY=mercator-key-...
export MERCATOR_ENDPOINT=https://proxy.mercator.local:8443  # Optional
```

3. For local mode examples, you'll also need:
```bash
export OPENAI_API_KEY=sk-...  # For OpenAI local mode
export ANTHROPIC_API_KEY=sk-ant-...  # For Anthropic local mode
```

## Running Examples

Most examples are self-contained and can be run directly:

```bash
python examples/basic_usage.py
python examples/streaming.py
python examples/session_tracking.py
```

**Note:** Examples will use mocked responses if no Mercator proxy is available. For real execution, ensure your Mercator proxy is running and environment variables are set.

## Customization

All examples use placeholder API keys. Replace them with your actual keys:
- `mercator-key-...` → Your Mercator API key
- `sk-...` → Your OpenAI API key (for local mode)
- `sk-ant-...` → Your Anthropic API key (for local mode)

## Learn More

- [SDK Documentation](../README.md)
- [Mercator Documentation](https://www.docs.onmercator.com)
- [API Reference](https://www.docs.onmercator.com/api-reference)

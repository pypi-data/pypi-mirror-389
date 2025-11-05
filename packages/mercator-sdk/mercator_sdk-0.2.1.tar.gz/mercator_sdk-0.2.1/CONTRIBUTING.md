# Contributing to Mercator Python SDK

Thank you for your interest in contributing to the Mercator Python SDK! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Submitting Changes](#submitting-changes)
- [Release Process](#release-process)

---

## Code of Conduct

This project adheres to a code of conduct. By participating, you are expected to:

- Be respectful and inclusive
- Accept constructive criticism gracefully
- Focus on what's best for the community
- Show empathy towards other community members

---

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- pip

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:

```bash
git clone https://github.com/YOUR_USERNAME/mercator-one.git
cd mercator-one/mercator-sdk/mercator-sdk-python
```

3. Add the upstream repository:

```bash
git remote add upstream https://github.com/codeeater800/mercator-one.git
```

---

## Development Setup

### 1. Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 2. Install Development Dependencies

```bash
pip install -e ".[dev]"
```

This installs:
- `mercator-sdk` in editable mode
- Development tools: pytest, black, ruff, mypy
- Testing dependencies: pytest-cov, pytest-asyncio

### 3. Verify Installation

```bash
# Run tests
pytest

# Check code quality
black --check .
ruff check .
mypy mercator
```

---

## Development Workflow

### 1. Create a Branch

Create a feature or bugfix branch:

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b bugfix/issue-123
```

Branch naming conventions:
- `feature/` - New features
- `bugfix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test additions/improvements

### 2. Make Changes

- Write code following our [Code Standards](#code-standards)
- Add tests for new functionality
- Update documentation as needed
- Ensure tests pass

### 3. Commit Changes

Write clear, descriptive commit messages:

```bash
git add .
git commit -m "feat: add support for custom headers

- Add custom_headers parameter to MercatorConfig
- Update MercatorClient to pass custom headers
- Add tests for custom header functionality
- Update documentation

Fixes #123"
```

Commit message format:
```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `test`: Adding/updating tests
- `refactor`: Code refactoring
- `chore`: Maintenance tasks

### 4. Keep Your Branch Updated

```bash
git fetch upstream
git rebase upstream/main
```

### 5. Push Changes

```bash
git push origin feature/your-feature-name
```

---

## Code Standards

### Python Style

We follow PEP 8 with these tools:

- **Black** - Code formatting (line length: 120)
- **Ruff** - Linting
- **MyPy** - Type checking

### Code Formatting

Format your code before committing:

```bash
# Format with Black
black .

# Check formatting
black --check .
```

### Linting

```bash
# Run linter
ruff check .

# Fix auto-fixable issues
ruff check --fix .
```

### Type Checking

```bash
# Run type checker
mypy mercator
```

### Docstrings

Use Google-style docstrings:

```python
def create_client(api_key: str, timeout: int = 60) -> MercatorClient:
    """Create a new Mercator client.

    Args:
        api_key: Mercator API key for authentication
        timeout: Request timeout in seconds

    Returns:
        Configured MercatorClient instance

    Raises:
        ValidationError: If api_key is invalid

    Example:
        >>> client = create_client("mercator-key-abc123")
        >>> response = client.chat.completions.create(...)
    """
    pass
```

### Type Hints

Always use type hints:

```python
from typing import Optional, Dict, List

def process_messages(
    messages: List[Dict[str, str]],
    metadata: Optional[Dict[str, str]] = None
) -> Dict[str, str]:
    """Process chat messages."""
    pass
```

### Error Handling

- Use specific exception types
- Always provide clear error messages
- Document exceptions in docstrings

```python
from mercator.exceptions import ValidationError

def validate_config(config: MercatorConfig) -> None:
    """Validate configuration.

    Args:
        config: Configuration to validate

    Raises:
        ValidationError: If configuration is invalid
    """
    if not config.api_key:
        raise ValidationError("api_key is required")
    if len(config.api_key) < 10:
        raise ValidationError("api_key must be at least 10 characters")
```

---

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_config.py

# Run specific test
pytest tests/test_config.py::TestMercatorConfig::test_config_validation

# Run with coverage
pytest --cov=mercator --cov-report=html

# Run integration tests (requires proxy)
MERCATOR_API_KEY=your-key pytest tests/integration/

# Skip integration tests
pytest -m "not integration"
```

### Writing Tests

Follow the AAA pattern (Arrange, Act, Assert):

```python
def test_client_creation():
    """Test creating a Mercator client."""
    # Arrange
    api_key = "test-key-1234567890"
    application = "test-app"

    # Act
    client = MercatorClient(api_key=api_key, application=application)

    # Assert
    assert client.config.api_key == api_key
    assert client.config.application == application

    # Cleanup
    client.close()
```

### Test Naming

Use descriptive test names:

```python
# Good
def test_chat_completion_with_valid_request_returns_response():
    pass

def test_chat_completion_with_empty_messages_raises_validation_error():
    pass

# Bad
def test_chat():
    pass

def test_error():
    pass
```

### Mocking

Use `unittest.mock` for mocking external dependencies:

```python
from unittest.mock import Mock, patch

def test_http_request_with_mocked_transport():
    """Test HTTP request with mocked transport."""
    # Arrange
    client = MercatorClient(api_key="test-key-1234567890")
    mock_response = Mock()
    mock_response.json.return_value = {"id": "chatcmpl-123"}

    # Act
    with patch.object(client._http_client, "request", return_value=mock_response):
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "Hello"}]
        )

    # Assert
    assert response.id == "chatcmpl-123"

    client.close()
```

### Coverage Goals

Maintain high test coverage:

- Overall coverage: >85%
- Core modules (client, config, transport): >90%
- New features: >90%

Check coverage:

```bash
pytest --cov=mercator --cov-report=term-missing
```

---

## Documentation

### Docstrings

Every public function, class, and method must have a docstring:

```python
class MercatorClient:
    """Client for interacting with Mercator proxy.

    Provides a drop-in replacement for OpenAI SDK with automatic
    governance, policy enforcement, and audit logging.

    Attributes:
        config: Configuration for the client
        chat: Chat completions API

    Example:
        >>> client = MercatorClient(api_key="mercator-key-...")
        >>> response = client.chat.completions.create(...)
        >>> print(response.choices[0].message.content)
    """
    pass
```

### README Updates

Update README.md when:
- Adding new features
- Changing public APIs
- Adding new configuration options
- Fixing significant bugs

### API Documentation

Update `docs/api-reference.md` when:
- Adding new classes or functions
- Changing function signatures
- Adding new exceptions
- Modifying behavior

### Examples

Add examples in `examples/` when:
- Adding significant new features
- Implementing common use cases
- Demonstrating best practices

Example structure:

```python
"""
Example: Using custom headers with Mercator SDK

This example demonstrates how to pass custom headers with requests.
"""

from mercator import MercatorClient

# Create client with custom headers
client = MercatorClient(
    api_key="mercator-key-...",
    custom_headers={
        "X-Custom-Header": "value"
    }
)

# Make request
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)

print(response.choices[0].message.content)

# Cleanup
client.close()
```

---

## Submitting Changes

### 1. Ensure Quality

Before submitting, verify:

```bash
# Format code
black .

# Lint code
ruff check .

# Type check
mypy mercator

# Run tests
pytest

# Check coverage
pytest --cov=mercator
```

### 2. Update CHANGELOG.md

Add an entry under "Unreleased":

```markdown
## [Unreleased]

### Added
- Support for custom headers in MercatorClient (#123)

### Fixed
- Bug in session tracking with nested contexts (#124)
```

### 3. Create Pull Request

1. Push your branch to GitHub
2. Open a Pull Request against `main`
3. Fill out the PR template:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] All tests pass
- [ ] Added new tests
- [ ] Updated documentation

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings
- [ ] Tests added/updated
- [ ] All tests pass
- [ ] CHANGELOG.md updated
```

### 4. Code Review

- Address review feedback promptly
- Keep discussions professional
- Push updates to the same branch
- Request re-review after updates

### 5. Merge

Once approved:
- Squash and merge (preferred)
- Update commit message if needed
- Delete branch after merge

---

## Release Process

(For maintainers)

### 1. Prepare Release

```bash
# Update version in setup.py and mercator/__init__.py
# Update CHANGELOG.md - move Unreleased to new version

git add .
git commit -m "chore: prepare release v0.2.0"
git push
```

### 2. Create Tag

```bash
git tag -a v0.2.0 -m "Release v0.2.0"
git push origin v0.2.0
```

### 3. Build Package

```bash
# Clean old builds
rm -rf dist/ build/ *.egg-info

# Build
python -m build

# Verify
twine check dist/*
```

### 4. Upload to PyPI

```bash
# Test PyPI (optional)
twine upload --repository-url https://test.pypi.org/legacy/ dist/*

# Production PyPI
twine upload dist/*
```

### 5. Create GitHub Release

1. Go to GitHub releases
2. Create release from tag
3. Add release notes from CHANGELOG.md
4. Attach wheel and tarball

---

## Project Structure

```
mercator-sdk-python/
├── mercator/              # Source code
│   ├── __init__.py       # Package init, version
│   ├── client.py         # MercatorClient
│   ├── config.py         # MercatorConfig
│   ├── transport.py      # HTTP transport
│   ├── exceptions.py     # Exception classes
│   ├── session.py        # Session management
│   ├── local_mode.py     # Local mode implementation
│   └── api/              # API implementations
│       └── chat.py       # Chat completions
├── tests/                # Tests
│   ├── test_client.py
│   ├── test_config.py
│   ├── api/
│   │   └── test_chat.py
│   └── integration/
│       └── test_end_to_end.py
├── examples/             # Example code
│   └── basic_usage.py
├── docs/                 # Documentation
│   ├── api-reference.md
│   └── getting-started.md
├── setup.py              # Package setup
├── pyproject.toml        # Build config
├── README.md             # Main readme
├── CONTRIBUTING.md       # This file
├── CHANGELOG.md          # Version history
└── LICENSE               # License file
```

---

## Getting Help

### Questions

- **GitHub Discussions**: Ask questions
- **GitHub Issues**: Report bugs or request features
- **Email**: shreyas@onmercator.com

### Resources

- **Documentation**: https://www.docs.onmercator.com
- **API Reference**: [docs/api-reference.md](docs/api-reference.md)
- **Examples**: [examples/](examples/)

---

## Recognition

Contributors are recognized in:
- CHANGELOG.md (for each release)
- GitHub contributors page
- Release notes

Thank you for contributing to Mercator! 🎉

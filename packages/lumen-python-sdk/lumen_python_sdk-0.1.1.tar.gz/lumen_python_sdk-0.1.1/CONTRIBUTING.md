# Contributing to Lumen Python SDK

Thank you for your interest in contributing to the Lumen Python SDK! This document provides guidelines and instructions for contributing.

## Development Setup

1. **Clone the repository**

```bash
git clone https://github.com/getlumen/lumen-python-sdk.git
cd lumen-python-sdk
```

2. **Create a virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install development dependencies**

```bash
make dev
# or
pip install -e ".[dev,flask,fastapi,django]"
```

4. **Set up your API key for testing**

```bash
export LUMEN_API_KEY="your_test_api_key"
```

## Development Workflow

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test file
pytest tests/test_events.py -v
```

### Code Quality

```bash
# Format code
make format

# Run linters
make lint

# Both format and lint
make format lint
```

### Type Checking

```bash
mypy lumen
```

## Code Style

- We use **Black** for code formatting (100 character line length)
- We use **Ruff** for linting
- We use **mypy** for type checking
- All code must have type hints
- All public functions must have docstrings

## Writing Tests

- Place tests in the `tests/` directory
- Name test files as `test_*.py`
- Use pytest fixtures for common setup
- Mock external API calls
- Aim for high test coverage

Example test:

```python
import pytest
from lumen import send_event

@pytest.mark.asyncio
async def test_send_event():
    """Test sending an event."""
    # Your test code here
    pass
```

## Commit Messages

Use clear, descriptive commit messages:

- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `test:` for test additions/changes
- `refactor:` for code refactoring
- `chore:` for maintenance tasks

Example:

```
feat: add support for custom metadata in seat operations
fix: handle timeout errors gracefully in send_event
docs: update README with FastAPI example
```

## Pull Request Process

1. Create a new branch for your changes

```bash
git checkout -b feature/your-feature-name
```

2. Make your changes and commit them

```bash
git add .
git commit -m "feat: your feature description"
```

3. Run tests and linters

```bash
make test lint
```

4. Push to your fork and create a pull request

```bash
git push origin feature/your-feature-name
```

5. Ensure CI passes and address any review comments

## Pull Request Checklist

Before submitting a pull request, ensure:

- [ ] Code follows the project's style guidelines
- [ ] All tests pass
- [ ] New code has tests
- [ ] Documentation is updated (if applicable)
- [ ] Type hints are added for new code
- [ ] Commit messages are clear and descriptive
- [ ] No unnecessary dependencies added

## Adding New Features

When adding new features:

1. **Discuss first** - Open an issue to discuss major changes
2. **Update types** - Add type definitions in `lumen/types.py`
3. **Write tests** - Add comprehensive tests
4. **Update docs** - Update README and docstrings
5. **Add examples** - Include usage examples if appropriate

## Documentation

- Use Google-style docstrings
- Include type hints in function signatures
- Provide examples in docstrings for complex functions
- Keep README.md up to date

Example docstring:

```python
async def my_function(
    user_id: str,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Brief description of the function.

    More detailed description if needed, explaining the purpose,
    behavior, and any important considerations.

    Args:
        user_id: Description of the user_id parameter
        api_key: Optional API key override

    Returns:
        Dictionary containing the result

    Example:
        >>> result = await my_function(user_id="user_123")
        >>> print(result)
    """
```

## Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create a git tag
4. Build and publish to PyPI

## Questions?

Feel free to open an issue or reach out:

- 📧 Email: hello@getlumen.dev
- 💬 Discord: [Join our community](https://discord.gg/lumen)

Thank you for contributing! 🎉

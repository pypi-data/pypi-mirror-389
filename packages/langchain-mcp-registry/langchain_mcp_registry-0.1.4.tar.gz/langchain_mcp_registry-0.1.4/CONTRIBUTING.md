# Contributing to langchain-mcp-registry

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Development Setup

### Prerequisites
- Python 3.11 or higher
- pip and virtualenv

### Setup

1. Clone the repository:
```bash
git clone https://github.com/foresee-ai/langchain-mcp-registry.git
cd langchain-mcp-registry
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:
```bash
pip install -e ".[dev]"
```

4. Install pre-commit hooks:
```bash
pre-commit install
```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=langchain_mcp_registry --cov-report=html

# Run specific test file
pytest tests/test_client.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Format code with black
black src/ tests/

# Lint with ruff
ruff check src/ tests/

# Type checking with mypy
mypy src/
```

### Testing CLI

```bash
# Search for servers
mcp-registry search weather

# Get server info
mcp-registry info @modelcontextprotocol/server-brave-search

# Generate configuration
mcp-registry config server-github
```

## Project Structure

```
langchain-mcp-registry/
├── src/langchain_mcp_registry/
│   ├── __init__.py          # Package exports
│   ├── client.py            # Registry HTTP client
│   ├── converter.py         # Config converter
│   ├── loader.py            # Tool loader
│   ├── models.py            # Pydantic models
│   ├── exceptions.py        # Custom exceptions
│   └── cli.py               # CLI commands
├── tests/                   # Test files
├── examples/                # Usage examples
├── docs/                    # Documentation
└── pyproject.toml          # Project configuration
```

## Contribution Guidelines

### Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Write tests for new functionality
5. Ensure all tests pass: `pytest`
6. Format code: `black src/ tests/`
7. Run linter: `ruff check src/ tests/`
8. Commit changes: `git commit -m "Add feature: ..."`
9. Push to your fork: `git push origin feature/your-feature`
10. Create a Pull Request

### Commit Messages

Follow the conventional commits format:

```
feat: add new feature
fix: fix bug
docs: update documentation
test: add tests
refactor: refactor code
chore: update dependencies
```

### Code Style

- Follow PEP 8 style guide
- Use type hints for all functions
- Write docstrings for public APIs
- Keep functions focused and small
- Use meaningful variable names

### Testing

- Write tests for all new features
- Maintain or improve code coverage
- Use descriptive test names
- Test edge cases and error conditions

## Adding New Features

### Adding a New Registry Client Method

1. Add method to `MCPRegistryClient` class in `client.py`
2. Add corresponding model in `models.py` if needed
3. Write tests in `tests/test_client.py`
4. Update documentation

### Adding a New CLI Command

1. Add command function in `cli.py`
2. Follow existing command patterns
3. Add help text and examples
4. Test manually and add integration tests

### Adding a New Exception

1. Add exception class in `exceptions.py`
2. Inherit from `MCPRegistryError`
3. Add descriptive error messages
4. Use in appropriate locations

## Documentation

- Update README.md for user-facing changes
- Add docstrings to all public functions
- Include usage examples
- Update CHANGELOG.md

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for questions or ideas
- Contact maintainers: dev@foresee.ai

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

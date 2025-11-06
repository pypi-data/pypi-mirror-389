# Test Suite

Complete automated test suite for langchain-mcp-registry.

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=langchain_mcp_registry --cov-report=html
```

## Test Categories

### Unit Tests
```bash
pytest tests/ -m "unit"
```

Tests for individual components:
- MCPRegistryClient (15 tests)
- RegistryToMCPConverter (11 tests)
- MCPToolLoader (5 tests)
- Pydantic Models (16 tests)

### Integration Tests
```bash
pytest tests/ -m "integration"
```

Tests for complete workflows combining multiple components (10 tests).

### Agent Tests
```bash
pytest tests/ -m "agent"
```

Tests for LangChain agent integration with OpenAI (7 tests).

**Note**: Agent tests require OpenAI API key (already configured in conftest.py).

## Test Files

| File | Tests | Purpose |
|------|-------|---------|
| `test_client.py` | 15 | MCPRegistryClient unit tests |
| `test_converter.py` | 11 | RegistryToMCPConverter unit tests |
| `test_loader.py` | 6 | MCPToolLoader unit tests |
| `test_models.py` | 16 | Pydantic models unit tests |
| `test_integration.py` | 10 | Integration tests |
| `test_agent.py` | 7 | LangChain Agent tests |
| `test_agent_real_mcp.py` | 4 | Real MCP server integration tests |
| `test_runtime_types.py` | 12 | All runtime types (npx, npm, python, python3, docker, node) |
| `test_transport_types.py` | 13 | All transport types (stdio, http, sse) |
| `conftest.py` | - | Pytest fixtures and configuration |

## Test Results

**Latest Run**: 2025-10-21
**Status**: ✅ 92 passed, 2 skipped
**Coverage**: 47%

See `PYTEST_SUMMARY.md` for detailed results.

## Key Features Tested

✅ **Real API Integration**
- MCP Registry API calls
- OpenAI GPT-4o-mini integration
- Real MCP server loading

✅ **Core Functionality**
- Server search and discovery
- Config conversion (npm, pypi, docker)
- Tool loading
- Error handling

✅ **LangChain Agent**
- Agent creation with real LLM
- Tool usage by AI
- Question answering

## Coverage Report

```
Name                                       Cover
--------------------------------------------------------------
src/langchain_mcp_registry/__init__.py     100%
src/langchain_mcp_registry/models.py       100%
src/langchain_mcp_registry/converter.py     62%
src/langchain_mcp_registry/exceptions.py    62%
src/langchain_mcp_registry/client.py        57%
src/langchain_mcp_registry/loader.py        35%
src/langchain_mcp_registry/cli.py            0%
--------------------------------------------------------------
TOTAL                                       47%
```

View detailed coverage: `htmlcov/index.html` (after running with `--cov-report=html`)

## Continuous Integration

Tests are designed to:
- ✅ Run in any environment with internet access
- ✅ Use real APIs (MCP Registry, OpenAI)
- ✅ Execute in <1 minute
- ✅ Have no flaky tests
- ✅ Be fully isolated

## Troubleshooting

### Tests Fail with Network Error
- Check internet connection
- Verify `registry.modelcontextprotocol.io` is accessible
- Check firewall settings

### Agent Tests Fail
- Verify OpenAI API key is valid
- Check OpenAI API quota
- Ensure `langchain-openai` and `langgraph` are installed

### Coverage Not Generated
- Install pytest-cov: `pip install pytest-cov`
- Run with `--cov` flag

## Development

### Adding New Tests

1. Create test file in `tests/` directory
2. Use pytest fixtures from `conftest.py`
3. Mark tests appropriately (`@pytest.mark.unit`, etc.)
4. Follow existing test patterns

Example:
```python
import pytest
from langchain_mcp_registry import MCPRegistryClient

@pytest.mark.unit
async def test_new_feature(registry_client):
    """Test description"""
    result = await registry_client.some_method()
    assert result is not None
```

### Running Specific Tests

```bash
# Single file
pytest tests/test_client.py

# Single class
pytest tests/test_client.py::TestMCPRegistryClient

# Single test
pytest tests/test_client.py::TestMCPRegistryClient::test_search_servers_basic

# Pattern matching
pytest tests/ -k "search"
```

### Debug Mode

```bash
# Show print statements
pytest tests/ -s

# Show full traceback
pytest tests/ --tb=long

# Stop on first failure
pytest tests/ -x

# Drop into debugger on failure
pytest tests/ --pdb
```

## CI/CD Integration

Example GitHub Actions workflow:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -e ".[dev]"
      - run: pytest tests/ --cov --cov-report=xml
      - uses: codecov/codecov-action@v2
```

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [PYTEST_SUMMARY.md](../PYTEST_SUMMARY.md) - Detailed test results

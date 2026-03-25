# Test Suite Documentation

## Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=scripts --cov-report=html

# Run specific test file
pytest tests/unit/test_week2_rpc.py

# Run tests matching pattern
pytest -k "wallet"

# Run with verbose output
pytest -v

# Skip slow integration tests
pytest -m "not integration"
```

## Test Structure
```
tests/
├── unit/           # Fast, isolated tests
├── integration/    # Slower, real connections
├── fixtures/       # Test data
└── conftest.py     # Shared fixtures
```

## Writing New Tests

1. Create test file: `test_<module>.py`
2. Write test functions: `def test_<feature>():`
3. Use fixtures for common setup
4. Mock external dependencies
5. Run and verify coverage

## Coverage Goals

- Overall: 70%+
- Critical paths: 90%+
- Utility functions: 100%

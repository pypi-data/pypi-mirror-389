# Flux Framework Test Suite

Comprehensive test suite for the Flux agentic framework, organized by functionality.

## Test Structure

```
tests/
├── __init__.py              # Test package initialization
├── run_all_tests.py         # Master test runner
├── test_node.py             # Node class functionality (8 tests)
├── test_parallel.py         # Parallel execution (8 tests)
├── test_pipeline.py         # Pipeline composition (9 tests)
├── test_persistence.py      # Persistence & state (15 tests)
└── test_edge_cases.py       # Edge cases & errors (18 tests)
```

## Running Tests

### Run All Tests
```bash
cd tests
python3 run_all_tests.py
```

### Run Individual Test Modules
```bash
cd tests
python3 test_node.py
python3 test_parallel.py
python3 test_pipeline.py
python3 test_persistence.py
python3 test_edge_cases.py
```

### Run with Pytest (if installed)
```bash
pytest tests/ -v
```

### Check Coverage (if coverage.py installed)
```bash
coverage run -m pytest tests/
coverage report
coverage html  # Generate HTML report
```

## Test Coverage

**Total: 58 tests** covering all framework functionality

### test_node.py (8 tests)
- ✓ Single node sync execution
- ✓ Single node async execution
- ✓ Node name attribute capture
- ✓ Shared parameter detection
- ✓ Persistence parameter detection
- ✓ Multiple arguments support
- ✓ Keyword arguments support
- ✓ Async vs sync detection

### test_parallel.py (8 tests)
- ✓ Two branch parallel execution
- ✓ Three branch parallel execution
- ✓ Async functions in parallel
- ✓ Shared state in parallel
- ✓ Parallel name attribute
- ✓ Parallel is_async flag
- ✓ Single branch parallel
- ✓ Result order preservation

### test_pipeline.py (9 tests)
- ✓ Two-node sequential pipeline
- ✓ Three-node sequential pipeline
- ✓ Sequential → Parallel flow
- ✓ Parallel → Sequential flow
- ✓ Complex nested pipelines
- ✓ Shared state propagation
- ✓ Pipeline name attribute
- ✓ Multiple parallel stages
- ✓ Keyword arguments handling

### test_persistence.py (15 tests)
- ✓ Automatic persistence creation
- ✓ Save and get operations
- ✓ Unique run_id generation
- ✓ Automatic history tracking
- ✓ Persistence in parallel branches
- ✓ Global run tracking
- ✓ Get specific run data
- ✓ List all runs
- ✓ Delete operation
- ✓ Get with default value
- ✓ Mark run as complete
- ✓ Mark run as failed
- ✓ Custom storage backend
- ✓ Observability hooks
- ✓ Persistence propagation through pipeline

### test_edge_cases.py (18 tests)
- ✓ Empty/None input
- ✓ Numeric data processing
- ✓ List input processing
- ✓ Dict input processing
- ✓ Zero value handling
- ✓ Empty string handling
- ✓ Boolean values
- ✓ Exception propagation
- ✓ Exception marks persistence as failed
- ✓ Large parallel execution (10 branches)
- ✓ Deep pipeline (20 steps)
- ✓ Node without return value
- ✓ Parallel with different return types
- ✓ Node with varargs
- ✓ Shared and persistence together
- ✓ Unicode strings
- ✓ Very long strings (100k chars)
- ✓ Nested data structures

## Coverage Goals

The test suite aims for 100% code coverage of:

- ✅ Node class initialization and execution
- ✅ Parallel class initialization and execution
- ✅ Persistence class all methods
- ✅ Pipeline composition (`|` operator)
- ✅ Shared state management
- ✅ Persistence state management
- ✅ History tracking
- ✅ Global run tracking
- ✅ Error handling
- ✅ Edge cases

## Test Principles

1. **Isolation**: Each test is independent and can run in any order
2. **Clarity**: Test names clearly describe what is being tested
3. **Coverage**: Tests cover normal operation, edge cases, and error conditions
4. **Async**: All tests properly use asyncio for async operations
5. **Assertions**: Clear assertions with descriptive error messages

## Adding New Tests

When adding new tests:

1. Add to appropriate test module based on functionality
2. Follow naming convention: `test_<feature_description>`
3. Add docstring explaining what is tested
4. Include assertion with clear failure message
5. Add test to module's `run_all()` function
6. Print success message: `print("✓ test_name")`

Example:
```python
async def test_new_feature():
    """Test description of what this tests"""
    @Node
    def my_node(x):
        return x * 2
    
    result = await my_node(5)
    assert result == 10, f"Expected 10, got {result}"
    print("✓ test_new_feature")
```

## CI/CD Integration

To integrate with CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Run Tests
  run: |
    cd tests
    python3 run_all_tests.py

# Or with pytest
- name: Run Tests with Coverage
  run: |
    pip install pytest pytest-asyncio coverage
    coverage run -m pytest tests/
    coverage report --fail-under=90
```

## Maintenance

- Run full test suite before committing changes
- Update tests when adding new features
- Keep test execution fast (current: < 5 seconds total)
- Review test failures before modifying code

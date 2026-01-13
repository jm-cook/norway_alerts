# Running Tests Locally

## Quick Start

1. **Install test dependencies:**
   ```bash
   pip install -r requirements_test.txt
   ```

2. **Run all tests:**
   ```bash
   pytest
   ```

## Detailed Commands

### Run all tests with verbose output:
```bash
pytest -v
```

### Run tests with coverage report:
```bash
pytest --cov=custom_components/norway_alerts --cov-report=term
```

### Run tests with HTML coverage report:
```bash
pytest --cov=custom_components/norway_alerts --cov-report=html
# Open htmlcov/index.html in your browser
```

### Run specific test file:
```bash
pytest tests/test_api.py
```

### Run specific test class:
```bash
pytest tests/test_api.py::TestLandslideAPI
```

### Run specific test:
```bash
pytest tests/test_api.py::TestLandslideAPI::test_fetch_warnings_success
```

### Run tests matching a pattern:
```bash
pytest -k "landslide"
```

### Run tests and stop on first failure:
```bash
pytest -x
```

### Run tests with detailed output on failures:
```bash
pytest -vv --tb=long
```

## Using VS Code

If you're using VS Code, install the Python Test Explorer:

1. Install "Python Test Explorer for Visual Studio Code" extension
2. Open the Testing sidebar (beaker icon)
3. Click "Configure Python Tests"
4. Select "pytest"
5. Select "tests" as the test directory
6. Tests will appear in the sidebar, click to run individual tests

## Watch Mode (auto-run on file changes)

Install pytest-watch:
```bash
pip install pytest-watch
```

Run in watch mode:
```bash
ptw
```

## Common Issues

### Import errors
Make sure you're in the repository root directory when running tests:
```bash
cd /path/to/norway_alerts
pytest
```

### Missing dependencies
Install all test dependencies:
```bash
pip install -r requirements_test.txt
```

### Async test issues
The tests use pytest-asyncio. Make sure it's installed:
```bash
pip install pytest-asyncio
```

## Test Structure

- `tests/test_api.py` - API client tests (mocked HTTP calls)
- `tests/test_config_flow.py` - Configuration flow tests
- `tests/test_sensor.py` - Sensor entity tests
- `tests/conftest.py` - Shared fixtures and configuration
- `tests/manual_*.py` - Manual scripts (not run by pytest)

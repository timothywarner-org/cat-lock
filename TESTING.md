# PawGate Testing Guide

Comprehensive testing documentation for both Python and Rust implementations.

## Table of Contents

- [Quick Start](#quick-start)
- [Python Tests](#python-tests)
- [Rust Tests](#rust-tests)
- [Test Categories](#test-categories)
- [Writing New Tests](#writing-new-tests)
- [CI/CD Integration](#cicd-integration)

---

## Quick Start

### Python Tests

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=html

# Run specific test category
pytest -m smoke      # Quick sanity checks
pytest -m unit       # Isolated unit tests
pytest -m integration  # Tests with mocked OS interaction
```

### Rust Tests

```bash
cd pawgate-rs

# Run all tests
cargo test

# Run with output displayed
cargo test -- --nocapture

# Run specific test
cargo test test_default_config

# Run only config tests
cargo test config::tests
```

---

## Python Tests

### Directory Structure

```
tests/
├── conftest.py           # Shared fixtures
├── smoke/
│   └── test_smoke.py     # Import and initialization tests
├── unit/
│   ├── test_config.py          # Configuration management
│   ├── test_lockfile_handler.py  # Single instance lockfile
│   ├── test_hotkey_listener.py   # Hotkey registration
│   ├── test_path_util.py         # Path resolution
│   └── test_notifications.py     # Toast notifications
└── integration/
    └── test_keyboard_controller.py  # Keyboard blocking
```

### Running Tests

```bash
# Full test suite with coverage
pytest

# Verbose output
pytest -v

# Stop on first failure
pytest -x

# Run tests matching pattern
pytest -k "config"

# Show print statements
pytest -s

# Generate HTML coverage report
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

### Test Markers

Tests are categorized with pytest markers:

| Marker | Description | Example |
|--------|-------------|---------|
| `smoke` | Quick sanity checks (<1s) | Import tests |
| `unit` | Isolated tests with mocks | Config parsing |
| `integration` | Tests with mocked OS interaction | Keyboard blocking |
| `slow` | Tests taking >3 seconds | Full pipeline |

```bash
# Run only smoke tests
pytest -m smoke

# Skip slow tests
pytest -m "not slow"

# Run unit and integration
pytest -m "unit or integration"
```

### Key Fixtures

Fixtures in `conftest.py` provide test isolation:

| Fixture | Purpose |
|---------|---------|
| `mock_keyboard` | Prevents real keyboard hook registration |
| `mock_tray` | Prevents system tray icon creation |
| `mock_overlay_window` | Prevents Tkinter window creation |
| `mock_config_path` | Redirects config to temp directory |
| `mock_lockfile_handler` | Prevents actual lockfile operations |
| `valid_config_data` | Sample valid configuration dict |

### Coverage Requirements

- **Target**: 80% line coverage
- **Critical paths**: 100% coverage required for:
  - Config loading/saving
  - Hotkey parsing
  - Keyboard lock/unlock
  - Lockfile handling

---

## Rust Tests

### Test Location

Rust tests are embedded in source files using `#[cfg(test)]`:

```
pawgate-rs/src/
├── config.rs      # Config tests at bottom of file
├── keyboard.rs    # Keyboard tests (Windows-only)
├── overlay.rs     # Window tests
└── main.rs        # Integration tests
```

### Running Tests

```bash
cd pawgate-rs

# Run all tests
cargo test

# Run tests with output
cargo test -- --nocapture

# Run only tests with "config" in name
cargo test config

# Run ignored tests too
cargo test -- --ignored

# List all tests
cargo test -- --list
```

### Test Categories

#### Unit Tests (in source files)

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_example() {
        // Test code
    }
}
```

#### Platform-Specific Tests

```rust
#[cfg(test)]
#[cfg(windows)]
mod windows_tests {
    // Only runs on Windows
}
```

### Current Test Coverage

| Module | Tests | Description |
|--------|-------|-------------|
| `config.rs` | 15+ | Default values, JSON serialization, color parsing |
| Hotkey parsing | 10+ | Simple/complex hotkeys, modifiers, special keys |

### Adding New Tests

Add tests at the bottom of the relevant source file:

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_new_feature() {
        // Arrange
        let input = "test";

        // Act
        let result = function_under_test(input);

        // Assert
        assert_eq!(result, expected);
    }

    #[test]
    #[should_panic(expected = "error message")]
    fn test_panic_case() {
        function_that_panics();
    }

    #[test]
    #[ignore]  // Skipped by default, run with --ignored
    fn test_slow_operation() {
        // Slow test
    }
}
```

---

## Test Categories

### Smoke Tests

**Purpose**: Verify basic functionality works

**Characteristics**:
- Run in <1 second total
- No external dependencies
- Catch import errors, basic instantiation

**Examples**:
- All modules import without error
- Core classes can be instantiated
- Default config values are correct

### Unit Tests

**Purpose**: Test individual functions in isolation

**Characteristics**:
- All dependencies mocked
- Fast execution
- Deterministic results

**Examples**:
- Config JSON parsing
- Hotkey string parsing
- Color hex parsing
- Path resolution

### Integration Tests

**Purpose**: Test component interaction

**Characteristics**:
- Multiple components working together
- OS interactions mocked
- May use temp files

**Examples**:
- Config load → save → reload cycle
- Keyboard lock → unlock sequence
- Lockfile create → check → remove

### Manual Tests

Some functionality requires manual testing:

| Feature | How to Test |
|---------|-------------|
| Actual keyboard blocking | Run app, press Ctrl+B, verify keys blocked |
| Overlay appearance | Visual inspection on all monitors |
| Tray icon | Right-click menu works |
| Settings dialog | All controls functional |

---

## Writing New Tests

### Python Test Template

```python
"""
Unit tests for [module name].

WHY: [Explain why these tests are important]
"""

import pytest
from unittest.mock import Mock, patch

class TestFeatureName:
    """
    Tests for [feature description].

    WHY: [Explain the importance]
    """

    @pytest.fixture
    def setup_fixture(self):
        """Provide test data."""
        return {"key": "value"}

    def test_happy_path(self, setup_fixture):
        """
        Verify [expected behavior] when [conditions].

        WHY: [Explain why this case matters]
        """
        # Arrange
        input_data = setup_fixture

        # Act
        result = function_under_test(input_data)

        # Assert
        assert result == expected

    def test_edge_case(self):
        """
        Verify graceful handling of [edge case].

        WHY: [Explain the edge case]
        """
        # Test edge case handling

    def test_error_handling(self):
        """
        Verify [error type] is handled gracefully.

        WHY: [Explain why error handling matters]
        """
        with pytest.raises(ExpectedError):
            function_that_raises()
```

### Rust Test Template

```rust
#[cfg(test)]
mod tests {
    use super::*;

    /// WHY: [Explain test purpose]
    #[test]
    fn test_feature_happy_path() {
        // Arrange
        let input = create_test_input();

        // Act
        let result = function_under_test(input);

        // Assert
        assert_eq!(result, expected, "Descriptive message");
    }

    /// WHY: Edge case handling
    #[test]
    fn test_feature_edge_case() {
        let result = function_under_test(edge_input);
        assert!(result.is_ok(), "Should handle edge case");
    }

    /// WHY: Error handling verification
    #[test]
    #[should_panic(expected = "specific error")]
    fn test_feature_panics_on_invalid() {
        function_under_test(invalid_input);
    }
}
```

---

## CI/CD Integration

### GitHub Actions - Python

```yaml
# .github/workflows/python-test.yml
name: Python Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run tests
        run: pytest --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### GitHub Actions - Rust

```yaml
# .github/workflows/rust-ci.yml (already created)
- name: Run tests
  working-directory: pawgate-rs
  run: cargo test --all
```

### Local Pre-Commit

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest -m smoke
        language: system
        types: [python]
        pass_filenames: false

      - id: cargo-test
        name: cargo test
        entry: bash -c 'cd pawgate-rs && cargo test'
        language: system
        types: [rust]
        pass_filenames: false
```

---

## Troubleshooting

### Python Tests

**"Module not found" errors**:
```bash
# Ensure you're in the project root
cd /path/to/pawgate
export PYTHONPATH=.
pytest
```

**Fixture not found**:
```bash
# Check conftest.py is in tests/ directory
ls tests/conftest.py
```

**Tests hang**:
```bash
# Add timeout
pytest --timeout=10
```

### Rust Tests

**"Can't find crate" errors**:
```bash
# Ensure dependencies are built
cargo build
cargo test
```

**Windows-only tests skip on Linux**:
This is expected. Windows-specific tests use `#[cfg(windows)]`.

**Tests fail with "permission denied"**:
```bash
# Run as administrator (Windows)
# Or check file permissions (Linux)
```

---

## Best Practices

1. **Write tests first** (TDD) for new features
2. **One assertion per test** when possible
3. **Use descriptive test names** that explain the scenario
4. **Include WHY comments** explaining test importance
5. **Mock external dependencies** (keyboard, filesystem, network)
6. **Test edge cases** (empty input, invalid data, boundaries)
7. **Keep tests fast** (<100ms per unit test)
8. **Don't test implementation details** - test behavior
9. **Run tests before committing** (`pytest -m smoke`)
10. **Maintain test coverage** - don't let it drop

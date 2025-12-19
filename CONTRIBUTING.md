# Contributing to PawGate

Thank you for your interest in contributing to PawGate! This guide will help you get started.

## Table of Contents
- [Development Setup](#development-setup)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing Instructions](#testing-instructions)
- [Pull Request Process](#pull-request-process)
- [Project Structure](#project-structure)

---

## Development Setup

### Prerequisites

- **Python 3.11+** (3.12 recommended)
- **Windows OS** (required - PawGate uses Windows-specific keyboard APIs)
- **Git** for version control
- **Visual Studio Code** (recommended, config included)

### Initial Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/pawgate.git
   cd pawgate
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   ```

3. **Activate the virtual environment**
   ```bash
   # Windows Command Prompt
   .venv\Scripts\activate

   # Windows PowerShell
   .venv\Scripts\Activate.ps1

   # Git Bash / MSYS2
   source .venv/Scripts/activate
   ```

4. **Install dependencies**
   ```bash
   # Runtime dependencies
   pip install -r requirements.txt

   # Development dependencies (testing, linting)
   pip install -r requirements-dev.txt
   ```

5. **Verify installation**
   ```bash
   python src/main.py
   ```

   You should see the PawGate icon appear in your system tray.

### Running in Development Mode

**WHY development mode?** Use the `PAWGATE_DEV` environment variable to reset configuration to defaults on every launch. This prevents your personal config from interfering with testing.

```bash
# Windows Command Prompt
set PAWGATE_DEV=1
python src/main.py

# Windows PowerShell
$env:PAWGATE_DEV=1
python src/main.py

# Git Bash
PAWGATE_DEV=1 python src/main.py
```

Or use the `--reset-config` flag:
```bash
python src/main.py --reset-config
```

### Building Locally

Use the provided build script to create an executable:

```bash
build.bat
```

Output will be in `dist/PawGate.exe`.

**Manual build:**
```bash
pip install pyinstaller
pyinstaller PawGate.spec
```

---

## Code Style Guidelines

### Documentation Requirements

**EVERY function must include:**

1. **Docstring** with clear description
2. **WHY comment** explaining design decisions
3. **Args** section with type hints
4. **Returns** section
5. **Raises** section (if applicable)

**Example:**

```python
def lock_keyboard(self) -> None:
    """Block all keyboard input using full scan code range.

    WHY: We block scan codes 0-255 instead of named keys because:
    1. Covers multimedia keys (volume, brightness) not in standard keymaps
    2. Handles F13-F24 keys found on extended keyboards
    3. Supports international keyboard layouts with regional keys

    Additionally, we block critical keys by name as a reliability layer
    since some scan codes may not map consistently across keyboards.

    Returns:
        None. Modifies self.blocked_keys as a side effect.

    Raises:
        None. Silently ignores unmapped scan codes.
    """
    # Implementation...
```

### Type Hints (Mandatory)

All functions must have type hints:

```python
from typing import Optional, List, Dict
import numpy as np
from dataclasses import dataclass

@dataclass
class DetectionResult:
    is_detected: bool
    confidence: float
    bounding_box: Optional[tuple[int, int, int, int]] = None

def process_frame(frame: np.ndarray) -> DetectionResult:
    """Process a frame and return detection results."""
    pass
```

### Error Handling Pattern

Always use defensive programming with graceful degradation:

```python
try:
    # Attempt operation
    result = risky_operation()
except SpecificException as e:
    # WHY: Explain why this failure is acceptable and how we handle it
    logger.warning(f"Operation failed gracefully: {e}")
    return safe_default_value()
```

**Anti-pattern (don't do this):**
```python
try:
    result = risky_operation()
except:  # Too broad, hides bugs
    pass  # No logging, silent failure
```

### Logging Standard

Use Python's `logging` module with appropriate levels:

```python
import logging

logger = logging.getLogger(__name__)

logger.debug("Verbose info for developers")
logger.info("Normal operation milestone")
logger.warning("Recoverable issue occurred")
logger.error("Serious problem but app continues")
logger.critical("Fatal error, app cannot continue")
```

### Code Organization

**File Structure Conventions:**

- Keep files focused and single-purpose
- Maximum ~300 lines per file (split if larger)
- Group related functionality in modules
- Use `__init__.py` to expose public API

**Import Order:**

```python
# 1. Standard library
import os
import sys
from pathlib import Path

# 2. Third-party packages
import keyboard
import pystray
from PIL import Image

# 3. Local modules
from src.config.config import Config
from src.util.path_util import get_packaged_path
```

### Naming Conventions

- **Classes:** `PascalCase` (e.g., `PawGateCore`, `HotkeyListener`)
- **Functions/methods:** `snake_case` (e.g., `lock_keyboard`, `send_hotkey_signal`)
- **Constants:** `UPPER_SNAKE_CASE` (e.g., `DEFAULT_HOTKEY`, `LOCKFILE_PATH`)
- **Private members:** `_leading_underscore` (e.g., `_internal_helper`)

### Comments

**WHY over WHAT:**

```python
# GOOD: Explains the reasoning
# WHY: Right Ctrl remapped to Left Ctrl as workaround for sticky key issue
# where Right Ctrl events persist after Windows lock/unlock, causing the
# hotkey listener to malfunction.
keyboard.remap_key('right ctrl', 'left ctrl')

# BAD: Just describes what the code does (obvious from reading it)
# Remap right ctrl to left ctrl
keyboard.remap_key('right ctrl', 'left ctrl')
```

---

## Testing Instructions

### Test Structure

Tests are organized by scope:

```
tests/
├── unit/           # Fast, isolated tests with mocked dependencies
├── integration/    # Tests with real OS/hardware interaction
├── smoke/          # Quick sanity checks (<1 second each)
└── conftest.py     # Shared fixtures and test configuration
```

### Running Tests

**All tests:**
```bash
pytest
```

**Specific test category:**
```bash
pytest -m smoke          # Quick sanity checks only
pytest -m unit           # Unit tests only
pytest -m integration    # Integration tests (requires Windows)
pytest -m "not slow"     # Skip slow tests
```

**Specific test file:**
```bash
pytest tests/unit/test_config.py
```

**Specific test function:**
```bash
pytest tests/unit/test_config.py::test_load_default_config
```

**With coverage report:**
```bash
pytest --cov=src --cov-report=html
```

View coverage report: Open `htmlcov/index.html`

### Writing Tests

**Use pytest fixtures from conftest.py:**

```python
def test_config_loads_defaults(mock_config_file):
    """Test that Config loads default values when file is missing."""
    config = Config()
    assert config.hotkey == "ctrl+b"
    assert config.opacity == 0.3
```

**Use markers to categorize tests:**

```python
import pytest

@pytest.mark.smoke
def test_import_main_module():
    """Quick smoke test - can we import the main module?"""
    from src import main
    assert main is not None

@pytest.mark.unit
def test_config_save(tmp_path):
    """Unit test with mocked file system."""
    config = Config()
    config.opacity = 0.5
    config.save()
    # Assert file was written correctly

@pytest.mark.integration
def test_keyboard_lock_actually_blocks():
    """Integration test requiring real keyboard library."""
    # This test actually blocks keyboard input
    # Use sparingly and ensure cleanup
```

**Test naming convention:**

- `test_<function_name>_<scenario>_<expected_result>`
- Examples:
  - `test_lock_keyboard_blocks_all_keys()`
  - `test_config_save_creates_file_when_missing()`
  - `test_hotkey_listener_ignores_invalid_combo()`

### Mocking Guidelines

**Mock external dependencies:**

```python
from unittest.mock import Mock, patch

def test_tray_icon_creation(mocker):
    """Use pytest-mock's mocker fixture for cleaner mocking."""
    # WHY: We mock pystray.Icon because it requires a GUI environment
    mock_icon = mocker.patch('src.os_controller.tray_icon.Icon')

    tray = TrayIcon(mock_main)
    tray.open()

    mock_icon.assert_called_once()
```

**Don't mock what you're testing:**

```python
# GOOD: Test actual Config logic, mock only file system
def test_config_loads_defaults(mocker):
    mocker.patch('os.path.exists', return_value=False)
    config = Config()
    assert config.hotkey == "ctrl+b"

# BAD: Mocking the thing we're testing makes test useless
def test_config_loads_defaults(mocker):
    mock_config = mocker.patch('src.config.config.Config')
    mock_config.return_value.hotkey = "ctrl+b"
    config = Config()
    assert config.hotkey == "ctrl+b"  # This tests nothing!
```

### Test Cleanup

**Always clean up resources:**

```python
def test_lockfile_created_and_removed(tmp_path):
    """Test lockfile lifecycle."""
    lockfile = tmp_path / "test.lock"

    try:
        # Test logic that creates lockfile
        create_lockfile(lockfile)
        assert lockfile.exists()
    finally:
        # Ensure cleanup even if test fails
        if lockfile.exists():
            lockfile.unlink()
```

**Or use pytest fixtures for automatic cleanup:**

```python
@pytest.fixture
def temp_lockfile(tmp_path):
    """Fixture that automatically cleans up lockfile."""
    lockfile = tmp_path / "test.lock"
    yield lockfile
    if lockfile.exists():
        lockfile.unlink()

def test_something(temp_lockfile):
    create_lockfile(temp_lockfile)
    assert temp_lockfile.exists()
    # No manual cleanup needed!
```

---

## Pull Request Process

### Before Submitting

1. **Run tests locally:**
   ```bash
   pytest
   ```

2. **Check code coverage** (aim for >80%):
   ```bash
   pytest --cov=src --cov-report=term-missing
   ```

3. **Manual testing:**
   - Build and run the executable: `build.bat`
    - Test the hotkey (Ctrl+B)
   - Verify system tray menu works
   - Test config changes persist
   - Unlock with mouse click

4. **Check for debug code:**
   - Remove any `print()` statements (use `logging` instead)
   - Remove commented-out code
   - Remove any `import pdb; pdb.set_trace()` debugger calls

### PR Title Format

Use conventional commit format:

```
type(scope): Brief description

Examples:
feat(detection): Add YOLOv8 cat detection support
fix(hotkey): Resolve sticky Right Ctrl key issue
docs(readme): Update installation instructions
refactor(config): Extract config loading into separate module
test(unit): Add tests for keyboard blocking
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code restructuring (no behavior change)
- `test`: Adding or updating tests
- `build`: Build system or dependencies
- `ci`: CI/CD pipeline changes

### PR Description Template

```markdown
## Summary
Brief description of what this PR does and why.

## Changes
- Added X functionality to Y module
- Fixed Z bug in A component
- Updated B documentation

## Testing
- [ ] All existing tests pass
- [ ] Added new tests for new functionality
- [ ] Manually tested the executable
- [ ] Verified on fresh Windows install (if applicable)

## Screenshots (if UI changes)
[Include screenshots of any UI changes]

## Related Issues
Fixes #123
Relates to #456
```

### Review Process

1. **Automated checks must pass:**
   - GitHub Actions CI/CD pipeline
   - All tests pass
   - No linting errors

2. **Code review by maintainer:**
   - Code follows style guidelines
   - Adequate test coverage
   - Documentation is complete
   - No breaking changes (or properly documented)

3. **Address feedback:**
   - Make requested changes
   - Push updates to your PR branch
   - Respond to review comments

4. **Squash and merge:**
   - PRs will be squashed into a single commit on merge
   - Ensure your PR title is clear (becomes the commit message)

---

## Project Structure

Understanding the codebase organization:

```
pawgate/
├── src/
│   ├── main.py                      # Entry point, PawGateCore class
│   ├── config/
│   │   ├── __init__.py
│   │   └── config.py                # JSON config management
│   ├── keyboard_controller/
│   │   ├── __init__.py
│   │   ├── hotkey_listener.py       # Hotkey registration
│   │   └── pressed_events_handler.py # Keyboard library bug workaround
│   ├── os_controller/
│   │   ├── __init__.py
│   │   ├── tray_icon.py             # System tray icon/menu
│   │   └── notifications.py         # Windows toast notifications
│   ├── ui/
│   │   ├── __init__.py
│   │   └── overlay_window.py        # Tkinter full-screen overlay
│   └── util/
│       ├── __init__.py
│       ├── lockfile_handler.py      # Single-instance enforcement
│       ├── path_util.py             # PyInstaller resource paths
│       └── web_browser_util.py      # Open help/about URLs
├── tests/
│   ├── conftest.py                  # Shared pytest fixtures
│   ├── unit/                        # Fast, isolated tests
│   ├── integration/                 # OS/hardware interaction tests
│   └── smoke/                       # Quick sanity checks
├── resources/
│   ├── img/
│   │   ├── icon.ico                 # Windows icon
│   │   └── icon.png                 # Tray icon image
│   └── config/
│       └── config.json              # Default configuration
├── build.bat                        # Windows build script
├── PawGate.spec                     # PyInstaller configuration
├── requirements.txt                 # Runtime dependencies
├── requirements-dev.txt             # Development dependencies
└── pytest.ini                       # Test configuration
```

---

## Getting Help

- **Questions about contributing?** Open a GitHub Discussion
- **Found a bug?** Open a GitHub Issue
- **Want to propose a feature?** Open a GitHub Issue with the "enhancement" label
- **Need development help?** Check existing Issues and Discussions

---

## Code of Conduct

- Be respectful and professional
- Provide constructive feedback
- Focus on the code, not the person
- Welcome newcomers and help them learn

---

## License

By contributing to PawGate, you agree that your contributions will be licensed under the same license as the project (see LICENSE file).

---

**Thank you for contributing to PawGate!**

Remember: Good code is code that's easy to understand, maintain, and extend. When in doubt, prioritize clarity over cleverness.

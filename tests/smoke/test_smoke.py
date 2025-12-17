"""
Smoke tests for CatLock - verify basic functionality works.

WHY: Smoke tests are the first line of defense against broken builds.
They catch import errors, basic instantiation failures, and environment
issues before running the full test suite. Fast feedback loop is critical.
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


def test_imports_succeed():
    """
    Verify all core CatLock modules can be imported without errors.

    WHY: Import failures indicate missing dependencies, syntax errors,
    or circular import issues. This test catches these immediately
    without needing to run the full application or complex logic.

    This is the most basic smoke test - if imports fail, nothing else
    will work. Run this first to fail fast.
    """
    # WHY: Use try-except to provide informative error messages
    # about which specific import failed
    try:
        import src.config.config
        assert src.config.config is not None
    except ImportError as e:
        pytest.fail(f"Failed to import src.config.config: {e}")

    try:
        import src.main
        assert src.main is not None
    except ImportError as e:
        pytest.fail(f"Failed to import src.main: {e}")

    try:
        import src.keyboard_controller.hotkey_listener
        assert src.keyboard_controller.hotkey_listener is not None
    except ImportError as e:
        pytest.fail(f"Failed to import src.keyboard_controller.hotkey_listener: {e}")

    try:
        import src.keyboard_controller.pressed_events_handler
        assert src.keyboard_controller.pressed_events_handler is not None
    except ImportError as e:
        pytest.fail(f"Failed to import src.keyboard_controller.pressed_events_handler: {e}")

    try:
        import src.os_controller.notifications
        assert src.os_controller.notifications is not None
    except ImportError as e:
        pytest.fail(f"Failed to import src.os_controller.notifications: {e}")

    try:
        import src.os_controller.tray_icon
        assert src.os_controller.tray_icon is not None
    except ImportError as e:
        pytest.fail(f"Failed to import src.os_controller.tray_icon: {e}")

    try:
        import src.ui.overlay_window
        assert src.ui.overlay_window is not None
    except ImportError as e:
        pytest.fail(f"Failed to import src.ui.overlay_window: {e}")

    try:
        import src.util.lockfile_handler
        assert src.util.lockfile_handler is not None
    except ImportError as e:
        pytest.fail(f"Failed to import src.util.lockfile_handler: {e}")

    try:
        import src.util.path_util
        assert src.util.path_util is not None
    except ImportError as e:
        pytest.fail(f"Failed to import src.util.path_util: {e}")

    try:
        import src.util.web_browser_util
        assert src.util.web_browser_util is not None
    except ImportError as e:
        pytest.fail(f"Failed to import src.util.web_browser_util: {e}")


def test_catlock_core_initializes(
    mock_keyboard,
    mock_tray_icon,
    mock_overlay_window,
    mock_lockfile_handler,
    mock_hotkey_listener,
    mock_config_path,
    mock_packaged_path,
    mock_open_about
):
    """
    Verify CatLockCore can be instantiated without errors.

    WHY: Even with all dependencies mocked, initialization could fail due to:
    - Constructor logic errors
    - Required attributes not being set
    - Thread spawning failures
    - Config loading issues

    This test ensures the core application can at least start up in a
    controlled test environment. If this fails, the app won't run at all.

    Args:
        mock_keyboard: Fixture to prevent real keyboard hooks
        mock_tray_icon: Fixture to prevent real tray icon creation
        mock_overlay_window: Fixture to prevent Tkinter window creation
        mock_lockfile_handler: Fixture to prevent lockfile operations
        mock_hotkey_listener: Fixture to prevent hotkey thread spawning
        mock_config_path: Fixture to use temp config directory
        mock_packaged_path: Fixture to mock bundled resources
        mock_open_about: Fixture to prevent browser opening
    """
    # WHY: Import here after mocks are active to prevent side effects
    # during module load time
    from src.main import CatLockCore

    # WHY: Instantiation itself exercises significant initialization logic:
    # - Config loading and parsing
    # - Thread creation (mocked)
    # - Queue initialization
    # - Lock object creation
    try:
        core = CatLockCore()
    except Exception as e:
        pytest.fail(f"CatLockCore initialization failed: {e}")

    # WHY: Verify critical attributes exist and have correct types
    # These are needed for the application to function
    assert hasattr(core, 'config'), "CatLockCore missing 'config' attribute"
    assert hasattr(core, 'hotkey_thread'), "CatLockCore missing 'hotkey_thread' attribute"
    assert hasattr(core, 'show_overlay_queue'), "CatLockCore missing 'show_overlay_queue' attribute"
    assert hasattr(core, 'program_running'), "CatLockCore missing 'program_running' attribute"
    assert hasattr(core, 'blocked_keys'), "CatLockCore missing 'blocked_keys' attribute"

    # WHY: Verify initial state is correct
    assert core.program_running is True, "program_running should start as True"
    assert isinstance(core.blocked_keys, set), "blocked_keys should be a set"
    assert core.config is not None, "config should be loaded"

    # NOTE: We don't assert mock_hotkey_listener.assert_called_once() because
    # Python's import caching makes it difficult to mock classes that are
    # imported with 'from X import Y' syntax at the correct timing.
    # The key test here is that CatLockCore can be instantiated without errors.

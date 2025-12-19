"""
Shared pytest fixtures and test configuration for PawGate.

WHY: Centralize common test setup (mocks, temp files, fixtures) to avoid
duplication across test modules and ensure consistent test isolation.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, Generator
from unittest.mock import MagicMock, patch

import pytest


# =============================================================================
# Config Data Fixtures
# =============================================================================

@pytest.fixture
def valid_config_data() -> Dict[str, Any]:
    """
    Provide a valid PawGate configuration dictionary.

    WHY: Tests need known-good config data to verify loading behavior.
    """
    return {
        "hotkey": "ctrl+b",
        "opacity": 0.3,
        "notificationsEnabled": False,
    }


@pytest.fixture
def partial_config_data() -> Dict[str, Any]:
    """
    Provide a partial PawGate configuration with missing keys.

    WHY: Tests need to verify Config handles missing keys gracefully
    by falling back to defaults.
    """
    return {
        "hotkey": "ctrl+shift+l",
        # opacity and notificationsEnabled intentionally missing
    }


@pytest.fixture
def tmp_config_file() -> Generator[Path, None, None]:
    """
    Create a temporary JSON configuration file for testing.

    WHY: Tests need isolated config files to avoid polluting the user's
    actual configuration. Using tempfile ensures automatic cleanup.

    Yields:
        Path to temporary config file with default PawGate settings
    """
    default_config: Dict[str, Any] = {
        "hotkey": "ctrl+b",
        "opacity": 0.3,
        "notificationsEnabled": False,
    }

    tmp_file = tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.json',
        delete=False,
        encoding='utf-8'
    )

    try:
        json.dump(default_config, tmp_file, indent=2)
        tmp_file.close()
        yield Path(tmp_file.name)
    finally:
        try:
            Path(tmp_file.name).unlink(missing_ok=True)
        except Exception:
            pass


# =============================================================================
# Path Mocking Fixtures
# =============================================================================

@pytest.fixture
def mock_config_path(tmp_path, mocker) -> Path:
    """
    Mock get_config_path() to return a temp directory config file.

    WHY: Prevents tests from modifying the user's actual config file.
    All config operations redirect to an isolated temp directory.

    Returns:
        Path to temp config.json file
    """
    config_dir = tmp_path / ".pawgate" / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "config.json"

    # Create default config
    default_config = {
        "hotkey": "ctrl+b",
        "opacity": 0.3,
        "notificationsEnabled": False,
    }
    config_file.write_text(json.dumps(default_config))

    mocker.patch(
        'src.util.path_util.get_config_path',
        return_value=str(config_file)
    )
    mocker.patch(
        'src.config.config.get_config_path',
        return_value=str(config_file)
    )

    return config_file


@pytest.fixture
def mock_packaged_path(tmp_path, mocker) -> Path:
    """
    Mock get_packaged_path() to return temp directory for bundled resources.

    WHY: Allows tests to work without PyInstaller bundled resources.
    Creates a mock config.json in the temp resources directory.

    Returns:
        Path to temp resources directory
    """
    resources_dir = tmp_path / "resources" / "config"
    resources_dir.mkdir(parents=True, exist_ok=True)

    # Create bundled default config
    bundled_config = {
        "hotkey": "ctrl+b",
        "opacity": 0.3,
        "notificationsEnabled": False,
    }
    bundled_file = resources_dir / "config.json"
    bundled_file.write_text(json.dumps(bundled_config))

    def mock_path(path: str) -> str:
        return str(tmp_path / path)

    mocker.patch(
        'src.util.path_util.get_packaged_path',
        side_effect=mock_path
    )
    mocker.patch(
        'src.config.config.get_packaged_path',
        side_effect=mock_path
    )

    return tmp_path


# =============================================================================
# Application Component Mocks
# =============================================================================

@pytest.fixture
def mock_open_about(mocker) -> MagicMock:
    """
    Mock open_about() to prevent browser from opening during tests.

    WHY: Opening browser windows during tests is disruptive and
    causes CI/CD failures.
    """
    mock = mocker.patch('src.config.config.open_about')
    mocker.patch('src.util.web_browser_util.open_about')
    return mock


@pytest.fixture
def mock_keyboard(mocker) -> MagicMock:
    """
    Mock the keyboard library to prevent actual global hotkey registration.

    WHY: The keyboard library requires admin privileges on Windows and
    can interfere with developer workflow during testing.
    """
    mock_kb = mocker.patch('keyboard.add_hotkey', autospec=True)
    mocker.patch('keyboard.remove_hotkey', autospec=True)
    mocker.patch('keyboard.unhook_all', autospec=True)
    mocker.patch('keyboard.block_key', autospec=True)
    mocker.patch('keyboard.unblock_key', autospec=True)
    mocker.patch('keyboard.remap_key', autospec=True)
    return mock_kb


@pytest.fixture
def mock_tray(mocker) -> MagicMock:
    """
    Mock pystray to prevent actual system tray icon creation during tests.

    WHY: System tray icons require a GUI event loop and can leave orphaned
    processes if tests crash.
    """
    mock_icon = MagicMock()
    mock_icon.run.return_value = None
    mock_icon.stop.return_value = None
    mock_icon.notify.return_value = None

    mock_icon_class = mocker.patch('pystray.Icon', autospec=True)
    mock_icon_class.return_value = mock_icon

    mocker.patch('pystray.MenuItem', autospec=True)
    mocker.patch('pystray.Menu', autospec=True)

    return mock_icon


@pytest.fixture
def mock_tray_icon(mocker) -> MagicMock:
    """
    Mock TrayIcon class to prevent actual system tray operations.

    WHY: Alias for mock_tray with additional TrayIcon class mocking.
    Some tests refer to this fixture name.
    """
    mock_icon = MagicMock()
    mock_icon.open.return_value = None
    mock_icon.close.return_value = None

    mocker.patch('src.os_controller.tray_icon.TrayIcon', return_value=mock_icon)
    mocker.patch('pystray.Icon', autospec=True)
    mocker.patch('pystray.MenuItem', autospec=True)
    mocker.patch('pystray.Menu', autospec=True)

    return mock_icon


@pytest.fixture
def mock_overlay_window(mocker) -> MagicMock:
    """
    Mock OverlayWindow to prevent Tkinter window creation.

    WHY: GUI windows require a display and event loop, which
    can fail in headless CI/CD environments.
    """
    mock_window = MagicMock()
    mock_window.show.return_value = None
    mock_window.hide.return_value = None

    mocker.patch('src.ui.overlay_window.OverlayWindow', return_value=mock_window)

    return mock_window


@pytest.fixture
def mock_lockfile_handler(mocker) -> MagicMock:
    """
    Mock lockfile operations to prevent actual file creation.

    WHY: Lockfiles can persist if tests crash, causing subsequent
    runs to fail. Mocking ensures clean test isolation.
    """
    mocker.patch('src.util.lockfile_handler.check_lockfile', return_value=None)
    mocker.patch('src.util.lockfile_handler.remove_lockfile', return_value=None)

    return MagicMock()


@pytest.fixture
def mock_hotkey_listener(mocker) -> MagicMock:
    """
    Mock HotkeyListener to prevent actual hotkey thread creation.

    WHY: Hotkey listener spawns threads and registers global hotkeys,
    which can interfere with other tests and require cleanup.
    """
    mock_listener = MagicMock()
    mock_class = mocker.patch(
        'src.keyboard_controller.hotkey_listener.HotkeyListener',
        return_value=mock_listener
    )

    return mock_class


@pytest.fixture
def mock_windows_lock(mocker) -> MagicMock:
    """
    Mock Windows LockWorkStation API to prevent actual screen locking.

    WHY: Actually locking the workstation during tests would be incredibly
    annoying and break CI/CD.
    """
    mock_lock = mocker.patch(
        'ctypes.windll.user32.LockWorkStation',
        autospec=True
    )
    mock_lock.return_value = 1
    return mock_lock


@pytest.fixture
def mock_cv2_capture(mocker) -> MagicMock:
    """
    Mock OpenCV VideoCapture to prevent actual webcam access during tests.

    WHY: Real webcam access is slow, unreliable in CI/CD, and may not be
    available. Mock allows testing capture logic without hardware dependency.
    """
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True

    import numpy as np
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    mock_cap.read.return_value = (True, dummy_frame)

    mocker.patch('cv2.VideoCapture', return_value=mock_cap)

    return mock_cap


@pytest.fixture
def mock_yolo_model(mocker) -> MagicMock:
    """
    Mock YOLOv8 model to prevent actual ML inference during unit tests.

    WHY: YOLO model loading and inference is slow (~1-2s) and requires
    downloading weights on first run.
    """
    mock_model = MagicMock()
    mock_result = MagicMock()
    mock_result.boxes = MagicMock()
    mock_result.boxes.cls = []
    mock_result.boxes.conf = []
    mock_result.boxes.xyxy = []

    mock_model.return_value = [mock_result]
    mocker.patch('ultralytics.YOLO', return_value=mock_model)

    return mock_model


# =============================================================================
# Test Isolation
# =============================================================================

@pytest.fixture(autouse=True)
def reset_singletons():
    """
    Reset any singleton instances between tests to ensure isolation.

    WHY: If PawGate uses singleton patterns, state can leak between tests.
    This fixture resets them before each test.
    """
    yield
    # Add singleton reset logic here when needed

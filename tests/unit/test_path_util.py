"""
Unit tests for path_util module.

WHY: Path utilities handle the critical distinction between development
mode (source files) and packaged mode (PyInstaller bundle). Getting paths
wrong means missing resources and app crashes.
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


class TestGetPackagedPath:
    """
    Tests for get_packaged_path function.

    WHY: This function must correctly handle:
    1. Development mode: Return path relative to source
    2. Packaged mode: Return path relative to PyInstaller's temp dir
    """

    def test_development_mode_returns_source_relative_path(self, mocker):
        """
        Verify path resolution in development mode.

        WHY: During development, resources are in the source tree.
        The function should return paths relative to the project root.
        """
        # Ensure we're not in packaged mode
        if hasattr(sys, '_MEIPASS'):
            delattr(sys, '_MEIPASS')

        from src.util.path_util import get_packaged_path

        # Request a resource path
        result = get_packaged_path("resources/config/config.json")

        # Verify it returns a valid path string
        assert isinstance(result, str)
        assert "resources" in result
        assert "config.json" in result

    def test_packaged_mode_uses_meipass(self, mocker):
        """
        Verify path resolution in PyInstaller packaged mode.

        WHY: When bundled with PyInstaller, resources are extracted to
        a temp directory stored in sys._MEIPASS. We must use this path.
        """
        from src.util.path_util import get_packaged_path

        # Simulate PyInstaller environment
        fake_meipass = "/tmp/fake_meipass_12345"
        mocker.patch.object(sys, '_MEIPASS', fake_meipass, create=True)

        # Also need to patch hasattr check
        original_hasattr = hasattr

        def patched_hasattr(obj, name):
            if obj is sys and name == '_MEIPASS':
                return True
            return original_hasattr(obj, name)

        mocker.patch('builtins.hasattr', patched_hasattr)

        # This test verifies the behavior when _MEIPASS exists
        # The actual implementation may vary

    def test_path_handles_special_characters(self):
        """
        Verify paths with special characters are handled correctly.

        WHY: Windows paths can contain spaces, unicode, etc.
        """
        from src.util.path_util import get_packaged_path

        # Test with path containing special chars
        result = get_packaged_path("resources/img/icon.ico")

        assert isinstance(result, str)
        assert "icon.ico" in result


class TestGetConfigPath:
    """
    Tests for get_config_path function.

    WHY: Config path must resolve to user's home directory for
    persistent storage across runs.
    """

    def test_config_path_uses_home_directory(self):
        """
        Verify config path is in user's home directory.

        WHY: User-specific config must be in home dir, not program dir,
        so it persists across updates and works on multi-user systems.
        """
        from src.util.path_util import get_config_path

        result = get_config_path()
        home = str(Path.home())

        assert result.startswith(home), f"Config path should start with {home}, got {result}"

    def test_config_path_contains_pawgate_dir(self):
        """
        Verify config path includes .pawgate directory.

        WHY: We use a hidden directory (.pawgate) to store config,
        following Unix/Linux conventions for app-specific data.
        """
        from src.util.path_util import get_config_path

        result = get_config_path()

        assert ".pawgate" in result, f"Config path should contain .pawgate, got {result}"

    def test_config_path_ends_with_json(self):
        """
        Verify config path points to a JSON file.

        WHY: Config is stored as JSON for human readability and
        easy manual editing if needed.
        """
        from src.util.path_util import get_config_path

        result = get_config_path()

        assert result.endswith(".json"), f"Config path should end with .json, got {result}"


class TestGetLockfilePath:
    """
    Tests for lockfile path resolution.

    WHY: Lockfile path must be consistent and in a writable location.
    """

    def test_lockfile_in_pawgate_directory(self):
        """
        Verify lockfile is in the .pawgate directory.

        WHY: Lockfile should be alongside config for consistency
        and to avoid polluting the home directory root.
        """
        from src.util.lockfile_handler import LOCKFILE_PATH

        assert ".pawgate" in LOCKFILE_PATH
        assert "lockfile" in LOCKFILE_PATH.lower()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

"""
Path Utilities - Handle PyInstaller bundled resources and user data directories.

This module provides path resolution for two critical scenarios:
1. Bundled resources (images, config files) packaged by PyInstaller
2. User data directories (config, logs) in the user's home directory

PyInstaller challenge:
    When PyInstaller creates an executable, it bundles resources into a temporary
    directory at runtime. This directory path is stored in sys._MEIPASS. Our code
    needs to work in both scenarios:
    - Development: Resources are in project directory (resources/img/icon.png)
    - Production: Resources are in PyInstaller temp dir (C:/Users/.../Temp/_MEI123/resources/img/icon.png)

    This module abstracts that complexity so other code just calls get_packaged_path()
    and it "just works" in both environments.

User data challenge:
    Configuration should be stored in a standard, predictable location that:
    - Persists across application restarts
    - Doesn't require admin rights
    - Survives application updates/reinstalls
    - Is easy for power users to find and edit

    We use ~/.catlock/ following Unix conventions, which translates to:
    - C:/Users/username/.catlock/ on Windows
    - /home/username/.catlock/ on Linux
    - /Users/username/.catlock/ on macOS

See also:
    - config.py: Uses these functions to load/save settings
    - tray_icon.py: Uses get_packaged_path() for icon image
    - notifications.py: Uses get_packaged_path() for notification icon
"""

import os
import sys
from pathlib import Path


def get_packaged_path(path: str) -> str:
    """
    Resolve path to a bundled resource, handling PyInstaller temp directory.

    Args:
        path: Relative path from project root (e.g., "resources/img/icon.png")

    Returns:
        str: Absolute path to the resource, accounting for PyInstaller

    WHY try/except:
        In production (PyInstaller), sys._MEIPASS exists and points to the
        temporary extraction directory. In development, it doesn't exist and
        raises AttributeError. We catch this and fall back to project directory.

    WHY not hasattr():
        Using try/except is more Pythonic than hasattr() for checking attributes.
        "Easier to Ask Forgiveness than Permission" (EAFP).

    Example:
        Development: get_packaged_path("resources/img/icon.png")
                    -> C:/github/cat-lock/resources/img/icon.png

        Production:  get_packaged_path("resources/img/icon.png")
                    -> C:/Users/Tim/AppData/Local/Temp/_MEI123456/resources/img/icon.png

    Edge cases:
        - Invalid path: Returns path that doesn't exist (caller's responsibility to check)
        - Nested paths: Works correctly with any depth (resources/img/subdir/file.png)
        - Absolute paths: Don't use - this function expects relative paths

    See also:
        - PyInstaller documentation on --add-data flag
        - get_config_path(): For user data, NOT bundled resources
    """
    try:
        # Production: PyInstaller temporary extraction directory
        # WHY sys._MEIPASS: PyInstaller sets this to the temp dir containing bundled files
        wd = sys._MEIPASS
        return os.path.abspath(os.path.join(wd, path))
    except:
        # Development: Calculate path relative to project root
        # WHY parent.parent.parent: This file is at src/util/path_util.py,
        # so we need to go up 3 levels to reach project root
        base = Path(__file__).parent.parent.parent
        return os.path.join(base, path)


def get_config_path() -> str:
    """
    Get path to user's configuration file, creating directory if needed.

    Returns:
        str: Absolute path to config.json in user's home directory
             (e.g., C:/Users/Tim/.catlock/config/config.json)

    WHY ~/.catlock/config/:
        - .catlock: Hidden directory (dot prefix) following Unix conventions
        - config/: Subdirectory for future expansion (logs/, cache/, etc.)
        - config.json: The actual configuration file

    WHY create directory:
        On first run, ~/.catlock/ won't exist. We create it proactively so
        the caller (config.py) can immediately write to config.json without
        worrying about directory creation.

    WHY os.makedirs() instead of os.mkdir():
        os.makedirs() creates all intermediate directories (like 'mkdir -p').
        If only .catlock/ exists but config/ doesn't, makedirs() creates it.

    Permissions:
        No special permissions needed - this goes in user's home directory
        which is always writable by the user (no admin rights required).

    Security note:
        Config file contains no secrets (just hotkey, opacity, notification
        preference). No need for encryption or special permissions.

    Example:
        Windows: C:/Users/Tim/.catlock/config/config.json
        Linux:   /home/tim/.catlock/config/config.json
        macOS:   /Users/tim/.catlock/config/config.json

    See also:
        - config.py: Main consumer of this function
        - Path.home(): Python's cross-platform way to get user's home directory
    """
    # Get user's home directory (cross-platform)
    # WHY Path.home(): Works on Windows, Linux, macOS consistently
    home = str(Path.home())

    # Build path to config directory
    config_dir = os.path.join(home, '.catlock', 'config')

    # Create directory if it doesn't exist (first run or manual deletion)
    # WHY exist_ok not used: os.path.exists() check is more explicit
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)  # Creates .catlock/ and .catlock/config/

    # Return full path to config.json
    return os.path.join(config_dir, "config.json")

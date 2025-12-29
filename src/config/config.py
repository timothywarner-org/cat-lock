"""
Configuration Management - Persistent user settings with fallback defaults.

This module handles loading, saving, and validating PawGate's configuration.
Settings are stored in JSON format at ~/.pawgate/config/config.json.

Configuration architecture:
    1. Bundled defaults: resources/config/config.json (shipped with app)
    2. User config: ~/.pawgate/config/config.json (created on first run)
    3. Dev mode: --reset-config flag or PAWGATE_DEV env var forces reset

Settings managed:
    - hotkey: Global keyboard shortcut to lock (default: "ctrl+b")
    - opacity: Overlay transparency 0.0-1.0 (default: 0.3)
    - notificationsEnabled: Show toast when locked (default: True)

WHY JSON instead of Windows Registry or .ini:
    - Cross-platform portable (future Linux/Mac support)
    - Human-readable and easily editable
    - No external dependencies (json module is stdlib)
    - Git-friendly for bundled defaults

WHY ~/.pawgate instead of AppData:
    - Consistent with Unix conventions (~/.config pattern)
    - Easier to find and edit for power users
    - Works in portable/non-admin installations

See also:
    - path_util.py: Handles PyInstaller bundled resource paths
    - main.py: Uses Config instance for all settings
"""

import json
import os
import os.path
import shutil
import sys

from src.util.path_util import get_packaged_path, get_config_path
from src.util.web_browser_util import open_about

# Path to the default config bundled with the application
# WHY in resources/: PyInstaller can package this with --add-data
BUNDLED_CONFIG_FILE = os.path.join("resources", "config", "config.json")

# Default hotkey if config is missing or invalid
# WHY Ctrl+L: Easy to reach, avoids common system shortcuts (unlike Win+L),
# and maps well to "lock" in PawGate's context.
DEFAULT_HOTKEY = "ctrl+l"


def should_use_bundled_config():
    """
    Check if we should ignore local config and use bundled defaults.

    This is useful for:
    - Development: Always start with known state (PAWGATE_DEV env var)
    - User troubleshooting: Reset corrupt config (--reset-config flag)
    - Testing: Predictable configuration in CI/CD

    Returns:
        bool: True if local config should be ignored and reset to defaults

    WHY environment variable: Developers can set PAWGATE_DEV=1 in their
    environment to always use fresh config without passing command-line args.

    WHY command-line flag: Users can easily reset config without editing
    or deleting files. This is especially helpful if bad config prevents launch.
    """
    return '--reset-config' in sys.argv or os.environ.get('PAWGATE_DEV')


def load():
    """
    Load configuration from user's config file, with fallback to bundled defaults.

    Loading priority:
        1. If dev mode (--reset-config or PAWGATE_DEV): Force reset to bundled defaults
        2. If user config exists and is valid JSON: Use it
        3. If user config missing or corrupt: Copy bundled defaults and use those

    Returns:
        dict: Configuration dictionary with keys: hotkey, opacity, notificationsEnabled

    WHY this fallback chain:
        - Dev mode override: Ensures predictable state during development
        - User config first: Respects user customization
        - Auto-repair: If config is corrupt, don't fail - just reset to defaults

    WHY catch both FileNotFoundError and JSONDecodeError:
        - FileNotFoundError: First run, no config exists yet
        - JSONDecodeError: User edited config file and broke JSON syntax
        Both are recoverable - just reset to defaults

    Edge case: What if bundled config is also missing?
        This would cause a crash, but it indicates a broken installation
        (PyInstaller didn't bundle resources correctly). This is a build
        error, not a runtime error we should silently handle.

    See also:
        - get_config_path(): Returns ~/.pawgate/config/config.json
        - get_packaged_path(): Handles PyInstaller bundled resources
    """
    # Dev mode: always use bundled config for predictable behavior
    if should_use_bundled_config():
        config_path = get_config_path()

        # Remove existing user config (if any) to force fresh state
        if os.path.exists(config_path):
            os.remove(config_path)

        # Copy bundled defaults to user config location
        # WHY copy instead of just reading bundled: Keeps user config directory
        # consistent (always has a config.json file after first run)
        shutil.copy(get_packaged_path(BUNDLED_CONFIG_FILE), config_path)
        print(f"[DEV] Reset config to bundled defaults: {config_path}")

        with open(config_path, "r") as f:
            return json.load(f)

    # Try to load user config (normal operation)
    try:
        with open(get_config_path(), "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Config missing or corrupt - copy bundled defaults
        # WHY copy on error: Ensures user config directory is populated
        # so future saves have a valid starting point
        shutil.copy(get_packaged_path(BUNDLED_CONFIG_FILE), get_config_path())

        # Now load the freshly copied config
        with open(get_config_path(), "r") as f:
            return json.load(f)


class Config:
    """
    Configuration manager with persistence and validation.

    This class encapsulates all user settings and handles loading from
    and saving to disk. It provides default values for missing keys to
    ensure backward compatibility when new settings are added.

    Attributes:
        hotkey (str): Global keyboard shortcut (e.g., "ctrl+b")
        opacity (float): Overlay transparency 0.0-1.0 (e.g., 0.3 = 30% opaque)
        notifications_enabled (bool): Show Windows toast when keyboard locks

    WHY instance attributes instead of class attributes:
        Multiple Config instances could theoretically exist (testing), and
        we don't want shared state between them.

    WHY .get() with defaults:
        Forward compatibility - if we add new settings in a future version,
        old config files won't have those keys. .get() with defaults ensures
        the app still works with old configs.

    See also:
        - load(): Module-level function that handles file I/O
        - save(): Persists current settings to disk
    """

    def __init__(self) -> None:
        """
        Load configuration from disk and populate instance attributes.

        If config is completely missing (None), this is a first-run scenario.
        We open the about page in the browser and save default config to disk.

        WHY dict.get() with ternary:
            Handles the case where config is None (should never happen due to
            load()'s fallback logic, but defensive programming is good).
            Also provides defaults for any missing keys (forward compatibility).

        WHY camelCase "notificationsEnabled" in JSON but snake_case in Python:
            JSON follows JavaScript conventions (camelCase), but Python
            follows PEP 8 (snake_case). We translate at the boundary.

        WHY open about page on first run:
            Welcomes new users and explains what PawGate does. Many users
            install software and forget what it's for. The about page provides
            context and usage instructions.
        """
        config = load()

        # Load settings with fallback defaults for missing keys
        # WHY ternary check for None: Defensive programming, though load()
        # should never return None due to its fallback logic
        self.hotkey = config.get("hotkey", DEFAULT_HOTKEY) if config else DEFAULT_HOTKEY
        self.opacity = config.get("opacity", 0.3) if config else 0.3
        self.notifications_enabled = config.get("notificationsEnabled", True) if config else True

        # First run: config was None, so open about page and save defaults
        if not config:
            open_about()  # Welcome the user with browser page
            self.save()   # Create initial config file

    def save(self) -> None:
        """
        Persist current configuration to disk.

        Writes settings to ~/.pawgate/config/config.json in JSON format.
        Called whenever user changes settings via system tray menu.

        WHY print statement:
            Debug aid during development. Confirms settings are being saved
            to the correct location. Could be replaced with proper logging
            in production.

        WHY reconstruct dict:
            We could use self.__dict__, but explicit is better than implicit.
            This ensures we only save intended settings and translates Python
            snake_case back to JSON camelCase.

        WHY no error handling:
            If saving fails (disk full, permission denied), we WANT the exception
            to bubble up. Config changes are critical - if they fail silently,
            users will be confused when their changes don't persist.

        See also:
            - tray_icon.py: Calls save() when user changes opacity or notifications
        """
        print(f'saving to: {get_config_path()}')

        with open(get_config_path(), "w") as f:
            # Reconstruct config dict with camelCase keys for JSON
            # WHY camelCase: Matches JavaScript/JSON conventions
            config = {
                "hotkey": self.hotkey,
                "opacity": self.opacity,
                "notificationsEnabled": self.notifications_enabled,  # snake_case -> camelCase
            }
            # WHY no indent or formatting: Keeps file small (though we could add indent=2
            # for human readability at the cost of a few bytes)
            json.dump(config, f)

"""
System Tray Icon - User interface and menu for PawGate.

This module creates and manages the Windows system tray icon (notification area)
that serves as the primary UI for PawGate when running in the background.

The tray icon provides:
    - Visual indication that PawGate is running
    - Menu for locking keyboard manually
    - Settings: opacity, notifications on/off
    - Help/About/Support links
    - Quit button

WHY pystray instead of pywin32 or other tray libraries:
    - Pure Python implementation (easier to debug)
    - Cross-platform (Windows, Linux, macOS)
    - Simple API with declarative menu structure
    - No native DLL dependencies

WHY run in a separate thread:
    pystray.Icon.run() is blocking (runs its own event loop to process
    Windows messages). Running it in a daemon thread keeps the main thread
    free for the Tkinter event loop and hotkey signal processing.

Menu structure:
    - Lock Keyboard (immediate action)
    - Enable/Disable Notifications (toggle with checkmark)
    - Set Opacity (submenu with checkmarks)
      - 5%, 10%, 30%, 50%, 70%, 90%
    - About (submenu)
      - Help
      - About
      - Support (Buy Me a Coffee)
    - Quit

WHY these opacity options:
    - 5%: Nearly invisible (see desktop clearly, minimal indication)
    - 10%: Very subtle (preferred by many users)
    - 30%: Default, good balance of visibility and transparency
    - 50%: Medium visibility
    - 70%: Clearly visible overlay
    - 90%: Almost opaque (maximum visual indication)

    We skip 100% because fully opaque would hide the desktop entirely,
    which is disorienting and prevents users from seeing what's protected.

Icon design:
    We load icon.png and draw on it (for visual variety or animation in
    future versions). Currently just loads and displays the icon as-is.

See also:
    - main.py: Creates TrayIcon instance in daemon thread
    - config.py: Persists opacity and notification settings
    - web_browser_util.py: Opens help/about URLs
"""

import os

from PIL import Image, ImageDraw
from pystray import Icon, Menu, MenuItem

from src.util.path_util import get_packaged_path
from src.util.web_browser_util import open_about, open_buy_me_a_coffee, open_help


class TrayIcon:
    """
    System tray icon and menu for PawGate.

    This class manages the Windows notification area icon and its context menu,
    providing user access to settings and actions.

    Attributes:
        main: Reference to PawGateCore instance (for config and callbacks)

    WHY pass main instance:
        Menu callbacks need access to:
        - self.main.config: Read/write settings
        - self.main.send_hotkey_signal(): Manually trigger lock
        - self.main.quit_program(): Clean shutdown
    """

    def __init__(self, main):
        """
        Initialize tray icon with reference to main application.

        Args:
            main: PawGateCore instance that owns this tray icon
        """
        self.main = main

    def set_opacity(self, opacity: float) -> None:
        """
        Update overlay opacity setting and persist to disk.

        Args:
            opacity: New opacity value (0.0-1.0, e.g., 0.3 = 30%)

        WHY immediate save: User expects settings to persist across restarts.
        If we don't save immediately, changes would be lost on crash or
        forced termination.

        See also:
            - config.py: Handles persistence to ~/.pawgate/config/config.json
        """
        self.main.config.opacity = opacity
        self.main.config.save()

    def toggle_notifications(self) -> None:
        """
        Toggle Windows toast notifications on/off and persist to disk.

        WHY toggle instead of separate enable/disable menu items:
            Single item with checkmark is cleaner UI and less menu clutter.
            Users can see current state (checked = enabled) and toggle with
            one click.

        See also:
            - notifications.py: Sends Windows toast when keyboard locks
        """
        self.main.config.notifications_enabled = not self.main.config.notifications_enabled
        self.main.config.save()

    def is_opacity_checked(self, opacity: float) -> bool:
        """
        Check if given opacity matches current setting (for menu checkmarks).

        Args:
            opacity: Opacity value to check (e.g., 0.3)

        Returns:
            bool: True if this opacity is currently selected

        WHY separate method: pystray's checked parameter expects a callable
        that takes an item parameter. We could use lambda with closures, but
        this is cleaner and more testable.

        Used by:
            Menu checkmarks to show which opacity is currently selected.
        """
        return self.main.config.opacity == opacity

    def open(self) -> None:
        """
        Create and run the system tray icon (blocks until icon.stop() called).

        This method:
        1. Loads icon image from bundled resources
        2. Draws on the image (currently just a white rectangle for demo)
        3. Constructs menu hierarchy with callbacks and checkmarks
        4. Creates pystray.Icon instance
        5. Runs the icon's event loop (blocks until Quit)

        WHY blocking: pystray.Icon.run() must process Windows messages
        continuously. That's why we call this from a daemon thread in main.py.

        Menu implementation notes:
            - Lambda for immediate actions: set_opacity needs to pass parameter
            - Callable for dynamic checks: checked= parameter evaluated each time
              menu opens, showing current state
            - Nested Menu() for submenus (Set Opacity, About)

        WHY lambda item parameter: pystray passes MenuItem instance to checked
        callables, even though we don't use it. We need to accept it to match
        the signature.

        WHY draw white rectangle: Placeholder for potential future features
        (status indicator, animation, badge count). Currently just demonstrates
        programmatic image manipulation.

        Edge cases:
            - Icon file missing: Would crash with FileNotFoundError, indicating
              broken installation (should be caught by packaging tests)
            - Menu callback errors: Unhandled exceptions would be logged by
              pystray but wouldn't crash the icon (graceful degradation)

        See also:
            - main.create_tray_icon(): Calls this from daemon thread
            - path_util.py: get_packaged_path handles PyInstaller bundling
        """
        # Load icon image from bundled resources
        path = os.path.join("resources", "img", "icon.png")
        image = Image.open(get_packaged_path(path))

        # Draw on the icon (currently just demo white rectangle)
        # WHY: Placeholder for future features (status badges, animations)
        draw = ImageDraw.Draw(image)
        draw.rectangle((16, 16, 48, 48), fill="white")

        # Construct menu hierarchy with callbacks and dynamic checkmarks
        menu = Menu(
            # Manual lock: Trigger keyboard lock immediately
            MenuItem("Lock Keyboard", self.main.send_hotkey_signal),

            # Notifications toggle: Checkmark shows current state
            # WHY lambda item: pystray requires this signature even though we don't use item
            MenuItem(
                "Enable/Disable Notifications",
                self.toggle_notifications,
                checked=lambda item: self.main.config.notifications_enabled,
            ),

            # Opacity submenu: Checkmarks show currently selected value
            # WHY nested Menu: Cleaner than 6 top-level items
            MenuItem("Set Opacity", Menu(
                MenuItem("5%", lambda: self.set_opacity(0.05), checked=lambda item: self.is_opacity_checked(0.05)),
                MenuItem("10%", lambda: self.set_opacity(0.1), checked=lambda item: self.is_opacity_checked(0.1)),
                MenuItem("30%", lambda: self.set_opacity(0.3), checked=lambda item: self.is_opacity_checked(0.3)),
                MenuItem("50%", lambda: self.set_opacity(0.5), checked=lambda item: self.is_opacity_checked(0.5)),
                MenuItem("70%", lambda: self.set_opacity(0.7), checked=lambda item: self.is_opacity_checked(0.7)),
                MenuItem("90%", lambda: self.set_opacity(0.9), checked=lambda item: self.is_opacity_checked(0.9)),
            )),

            # Help submenu: External links to documentation and support
            MenuItem("About", Menu(
                MenuItem("Help", open_help),  # FAQ page
                MenuItem("About", open_about),  # What is PawGate page
                MenuItem("Support ☕", open_buy_me_a_coffee),  # Donation link
            )),

            # Quit: Clean shutdown
            MenuItem("Quit", self.main.quit_program),
        )

        # Create icon instance with image and menu
        # Args: name (for accessibility), image, tooltip, menu
        tray_icon = Icon("PawGate", image, "PawGate", menu)

        # Run the icon's event loop (blocks until icon.stop() called)
        # WHY blocks: Must continuously process Windows messages for icon and menu
        tray_icon.run()

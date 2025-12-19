"""
Fullscreen Overlay Window - Visual feedback with hotkey-based unlock.

This module creates a transparent Tkinter window that covers all monitors,
providing visual indication that the keyboard is locked and relaying the
unlock hotkey press back to the main application.

Design goals:
    1. Cover ALL monitors (multi-monitor support)
    2. Transparent (configurable opacity 5%-90%)
    3. Always on top (can't be hidden by other windows)
    4. No window decorations (title bar, borders, close button)
    5. Unlocks when hotkey is pressed again (consistent toggle UX)

WHY Tkinter instead of pywin32 or other GUI frameworks:
    - Tkinter is stdlib (no extra dependencies)
    - Cross-platform (future Linux/Mac support)
    - Simple API for transparent overlays
    - Small footprint (important for a utility app)

WHY screeninfo library:
    Windows doesn't expose monitor configuration easily in Tkinter alone.
    screeninfo provides a simple, cross-platform way to enumerate monitors
    and their positions/sizes. This is critical for multi-monitor setups
    where monitors might be arranged horizontally, vertically, or in grids.

Multi-monitor strategy:
    We create a SINGLE window large enough to cover ALL monitors. The window
    starts at the minimum X,Y coordinates and extends to cover the maximum
    width and height. This handles any monitor arrangement (stacked, side-by-side,
    L-shaped, etc.).

Alternative rejected: Create separate windows per monitor
    - More complex to manage (multiple mainloops or threads)
    - Race conditions with keyboard blocking
    - Gaps between windows in some configurations

See also:
    - main.py: Creates OverlayWindow instance when hotkey pressed
    - config.py: Stores opacity setting
    - notifications.py: Toast notification when overlay appears
"""

import tkinter as tk

from screeninfo import get_monitors


class OverlayWindow:
    """
    Fullscreen transparent overlay for all monitors.

    This class creates and manages a Tkinter window that covers the entire
    desktop (all monitors), providing visual feedback that the keyboard is
    locked and routes unlock requests back to the main application.

    Attributes:
        main: Reference to PawGateCore instance (for config and callbacks)

    WHY pass main instance:
        The overlay needs:
        - self.main.config.opacity: User's transparency preference
        - self.main.root: Store reference for cleanup later
        - self.main.lock_keyboard(): Trigger keyboard blocking
        - self.main.unlock_keyboard(): Cleanup when unlock hotkey pressed
    """

    def __init__(self, main):
        """
        Initialize overlay with reference to main application.

        Args:
            main: PawGateCore instance that owns this overlay
        """
        self.main = main

    def open(self) -> None:
        """
        Create, configure, and display the fullscreen overlay.

        This method:
        1. Queries all monitor configurations
        2. Calculates bounding box to cover all monitors
        3. Creates Tkinter window with transparent overlay styling
        4. Sets up polling to detect unlock hotkey
        5. Locks the keyboard
        6. Enters Tkinter mainloop (blocks until window closed)

        WHY query monitors every time:
            Users might connect/disconnect monitors between lock activations.
            Querying fresh ensures the overlay adapts to the current configuration.

        WHY sum/max/min calculations:
            In multi-monitor setups, monitors can be arranged arbitrarily:
            - Side by side: total_width = sum of widths
            - Stacked: max_height = tallest monitor
            - Offset: min_x/min_y might be negative (monitor left/above primary)

            Example: Two 1920x1080 monitors side-by-side
                Monitor 0: x=0, y=0, width=1920, height=1080
                Monitor 1: x=1920, y=0, width=1920, height=1080
                Result: total_width=3840, max_height=1080, min_x=0, min_y=0

            Example: Two monitors in L-shape (one above-left of primary)
                Monitor 0: x=-1920, y=-1080, width=1920, height=1080
                Monitor 1: x=0, y=0, width=1920, height=1080
                Result: total_width=3840, max_height=2160, min_x=-1920, min_y=-1080

        WHY overrideredirect(True):
            Removes all window decorations (title bar, borders, close button).
            This creates a clean overlay without UI chrome. Users can't accidentally
            click the close button, and the overlay looks intentionally minimal.

        WHY attributes('-topmost', True):
            Ensures the overlay stays above all other windows. Without this,
            the cat could bring another window to the front and type there.
            topmost guarantees the overlay always blocks interaction.

        WHY attributes('-alpha', ...):
            Makes the window semi-transparent so users can see their desktop
            underneath. This:
            - Provides visual confirmation of what's protected
            - Looks less jarring than a solid color
            - Allows users to see if anything important is happening (video, download)

        WHY poll unlock_event:
            The overlay runs on Tkinter's main thread. Polling allows us to
            respond to the hotkey listener (running in another thread) without
            making unsafe cross-thread Tk calls. When the unlock hotkey is
            detected, unlock_event is set, and the overlay closes itself.

        WHY lock_keyboard AFTER creating window:
            If we locked before window creation, there's a brief moment where
            keyboard is blocked but no visual feedback exists. Creating the
            window first ensures users always see the overlay when locked.

        WHY mainloop():
            Tkinter's mainloop() blocks and processes events (mouse clicks,
            keyboard input, repaints). It runs until the window is destroyed
            (via self.main.unlock_keyboard calling root.destroy()).

        Threading note:
            This method MUST be called from the main thread because Tkinter
            is not thread-safe. That's why we use a queue in main.py to signal
            from the hotkey thread to the main thread.

        See also:
            - main.start(): Main event loop that calls this method
            - main.lock_keyboard(): Blocks all keyboard input
            - main.unlock_keyboard(): Cleanup and close overlay
        """
        # Query current monitor configuration
        # WHY every time: Monitors might have changed since last lock
        monitors = get_monitors()

        # Calculate bounding box to cover all monitors (handles any arrangement)
        total_width = sum([monitor.width for monitor in monitors])
        max_height = max([monitor.height for monitor in monitors])
        min_x = min([monitor.x for monitor in monitors])
        min_y = min([monitor.y for monitor in monitors])

        # Create Tkinter root window and store in main for cleanup
        self.main.root = tk.Tk()

        # Remove window decorations (title bar, borders, close button)
        # WHY: Creates clean, minimal overlay without UI chrome
        self.main.root.overrideredirect(True)

        # Size and position window to cover all monitors
        # Format: WIDTHxHEIGHT+XOFFSET+YOFFSET
        # WHY this format: Tkinter geometry string standard
        self.main.root.geometry(f'{total_width}x{max_height}+{min_x}+{min_y}')

        # Ensure window stays on top of all other windows
        # WHY: Prevents cat from bringing other windows forward
        self.main.root.attributes('-topmost', True)

        # Set transparency level from user config (0.05 to 0.9)
        # WHY configurable: Some users want more visibility, others less
        self.main.root.attributes('-alpha', self.main.config.opacity)

        # Poll for unlock hotkey requests from the main application
        # WHY polling: Allows background hotkey thread to signal unlock via event
        self.main.root.after(50, self._wait_for_hotkey_unlock)

        # Lock the keyboard AFTER window is created (ensures visual feedback)
        # WHY order matters: Don't block keyboard without showing overlay first
        self.main.lock_keyboard()

        # Enter Tkinter event loop (blocks until window destroyed)
        # WHY blocks: Keeps window responsive to mouse clicks and repaints
        # Exits when main.unlock_keyboard() calls root.destroy()
        self.main.root.mainloop()

    def _wait_for_hotkey_unlock(self) -> None:
        """Poll unlock_event and close overlay when hotkey is pressed."""
        if not self.main.root:
            return

        if self.main.unlock_event.is_set():
            self.main.unlock_event.clear()
            self.main.unlock_keyboard()
            return

        # Reschedule polling while overlay remains active
        self.main.root.after(50, self._wait_for_hotkey_unlock)

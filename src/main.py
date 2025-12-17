"""
PawGate Main Application - Core orchestration and event loop.

This module serves as the central coordinator for PawGate, managing:
- Keyboard blocking via the `keyboard` library (boppreh/keyboard)
- Hotkey registration and lifecycle (See also: hotkey_listener.py)
- System tray icon in a separate thread (See also: tray_icon.py)
- Tkinter overlay window lifecycle (See also: overlay_window.py)
- Single-instance enforcement via lockfile (See also: lockfile_handler.py)

Architecture Overview:
    The application runs a main event loop that monitors a queue for hotkey signals.
    When triggered (via Ctrl+L by default), it:
    1. Displays a fullscreen overlay using Tkinter
    2. Blocks ALL keyboard input (scan codes 0-255)
    3. Waits for a mouse click to unlock

    WHY: This prevents cats/pets from accidentally typing, closing windows,
    or triggering Windows shortcuts (Win+D, Alt+F4, etc.) while you're away
    from your desk. The overlay provides visual feedback that the keyboard is locked.

Threading Model:
    - Main thread: Event loop monitoring hotkey signals
    - Daemon thread 1: System tray icon (pystray runs its own event loop)
    - Daemon thread 2: Hotkey listener (keyboard.add_hotkey blocks)
    - Daemon thread 3: Pressed events cleaner (workaround for keyboard lib bug)

    WHY daemon threads: They automatically terminate when main thread exits,
    ensuring clean shutdown without hanging processes.

See also:
    - overlay_window.py: Tkinter fullscreen overlay implementation
    - tray_icon.py: System tray menu and icon
    - hotkey_listener.py: Global hotkey registration
    - pressed_events_handler.py: Keyboard library bug workaround
"""

import threading
import time
from queue import Queue

import keyboard

from src.config.config import Config
from src.keyboard_controller.hotkey_listener import HotkeyListener
from src.keyboard_controller.pressed_events_handler import clear_pressed_events
from src.os_controller.notifications import send_notification_in_thread
from src.os_controller.tray_icon import TrayIcon
from src.ui.overlay_window import OverlayWindow
from src.util.lockfile_handler import check_lockfile, remove_lockfile


class PawGateCore:
    """
    Main application coordinator for PawGate.

    This class manages the lifecycle of all components and coordinates
    communication between threads via queues and shared state.

    Attributes:
        hotkey_thread: Thread running the global hotkey listener
        show_overlay_queue: Thread-safe queue for hotkey activation signals
        config: Configuration manager (loads from ~/.pawgate/config/config.json)
        root: Tkinter root window (None when not locked)
        hotkey_lock: Threading lock to prevent race conditions during hotkey changes
        listen_for_hotkey: Flag to control hotkey listener loop
        program_running: Flag to control main event loop
        blocked_keys: Set of scan codes currently blocked (for cleanup)
        changing_hotkey_queue: Queue for coordinating hotkey changes (unused currently)

    WHY we use queues instead of direct method calls:
        Queues provide thread-safe communication between the hotkey listener
        thread and the main thread. Direct calls would require careful locking
        and could cause race conditions with Tkinter (which is not thread-safe).

    See also:
        - TrayIcon: System tray interface
        - HotkeyListener: Global hotkey registration
        - OverlayWindow: Fullscreen blocking overlay
        - Config: Settings management
    """

    def __init__(self) -> None:
        """
        Initialize PawGate and start all background threads.

        WHY start threads in __init__:
            We want the tray icon and hotkey listener running immediately
            so the user sees feedback that the app is loaded. The main thread
            will handle the event loop in start().

        Raises:
            Exception: If keyboard library fails to initialize (rare, but can
                      happen if another low-level keyboard hook is active)
        """
        # Threading infrastructure
        self.hotkey_thread = None
        self.show_overlay_queue = Queue()  # Signals from hotkey to main thread

        # Configuration and state
        self.config = Config()  # Loads from ~/.pawgate/config/config.json
        self.root = None  # Tkinter window (created on-demand when locking)

        # Hotkey management
        self.hotkey_lock = threading.Lock()  # Prevents race conditions when changing hotkeys
        self.listen_for_hotkey = True  # Flag to control hotkey listener loop

        # Application lifecycle
        self.program_running = True  # Controls main event loop

        # Keyboard blocking state
        self.blocked_keys = set()  # Track which scan codes are blocked (for cleanup)

        # Unused queue - left for future hotkey change feature
        self.changing_hotkey_queue = Queue()

        # Start background threads (order matters - hotkey before tray)
        # WHY order matters: Tray icon menu callbacks reference hotkey state,
        # so hotkey listener should be initialized first
        self.start_hotkey_listener()

        # Start the keyboard library bug workaround thread
        # See pressed_events_handler.py for details on the bug
        self.clear_pressed_events_thread = threading.Thread(target=clear_pressed_events, daemon=True)
        self.clear_pressed_events_thread.start()

        # Start system tray icon (runs in its own thread with pystray event loop)
        self.tray_icon_thread = threading.Thread(target=self.create_tray_icon, daemon=True)
        self.tray_icon_thread.start()

    def create_tray_icon(self) -> None:
        """
        Create and run the system tray icon.

        This method is executed in a daemon thread and blocks until the
        icon is stopped (via quit_program).

        WHY in a separate thread: pystray.Icon.run() is blocking and runs
        its own event loop. We need the main thread free for the Tkinter
        event loop when the overlay is shown.

        See also: tray_icon.py for menu implementation
        """
        TrayIcon(main=self).open()

    def start_hotkey_listener(self) -> None:
        """
        Initialize and start the global hotkey listener thread.

        Delegates to HotkeyListener class which manages the keyboard
        library's add_hotkey functionality.

        WHY separate class: Hotkey management has complex lifecycle
        requirements (stopping, restarting, cleanup) that deserve
        their own encapsulation.

        See also: hotkey_listener.py
        """
        HotkeyListener(self).start_hotkey_listener_thread()

    def lock_keyboard(self) -> None:
        """
        Block ALL keyboard input using comprehensive scan code blocking.

        This method implements defense-in-depth keyboard blocking:
        1. Block scan codes 0-255 (covers nearly all physical keys)
        2. Block critical keys by name as a fallback

        WHY block by scan code first:
            Scan codes are hardware-level identifiers that work across
            all keyboard layouts (QWERTY, AZERTY, Dvorak, international).
            Blocking by name is layout-dependent and can miss keys.

        WHY block critical keys by name too:
            Some special keys (Windows key, media keys) may not respond
            to scan code blocking on all hardware. Redundancy ensures
            that mischievous cats can't Win+D to minimize windows or
            Alt+F4 to close applications.

        WHY range 0-255:
            PS/2 scan codes and USB HID scan codes both fit in this range.
            This covers:
            - Standard keys (A-Z, 0-9, punctuation)
            - Function keys (F1-F24)
            - Numpad keys
            - Multimedia keys (volume, play/pause, etc.)
            - Regional keys (international keyboards)

        The blocked_keys set tracks which codes were successfully blocked
        so unlock_keyboard can clean up properly.

        See also:
            - unlock_keyboard(): Cleanup counterpart
            - overlay_window.py: Visual indication of locked state
            - notifications.py: User notification when locked
        """
        self.blocked_keys.clear()

        # Block full scan code range (0-255) to cover all keyboards including
        # multimedia keys, F13-F24, and regional/international layouts
        for i in range(256):
            try:
                keyboard.block_key(i)
                self.blocked_keys.add(i)
            except Exception:
                # WHY silent exception: Some scan codes don't map to physical keys
                # on all hardware (e.g., scan code 255 may be unmapped). This is
                # expected and not an error - we just skip those codes.
                pass

        # Also block critical keys by name for reliability
        # WHY this list: These are the most dangerous keys for cats to press
        # - Windows key: Brings up Start menu or shortcuts (Win+D, Win+L, etc.)
        # - Media keys: Can disrupt music/videos in other windows
        # - Brightness: Can make screen unusable
        critical_keys = [
            'windows', 'left windows', 'right windows',
            'volume up', 'volume down', 'volume mute',
            'play/pause media', 'next track', 'previous track',
            'brightness up', 'brightness down',
        ]
        for key_name in critical_keys:
            try:
                keyboard.block_key(key_name)
            except Exception:
                # WHY silent exception: Not all keyboards have these keys
                # (e.g., desktop keyboards often lack brightness controls)
                pass

        # Notify user that keyboard is locked (if notifications enabled)
        send_notification_in_thread(self.config.notifications_enabled)

    def unlock_keyboard(self, event=None) -> None:
        """
        Unblock all keyboard input and close the overlay window.

        This is the cleanup counterpart to lock_keyboard(). It unblocks
        all scan codes that were successfully blocked, closes the Tkinter
        overlay, and calls keyboard.stash_state() to clear internal state.

        Args:
            event: Optional Tkinter event (from mouse click binding).
                   Not used, but required for Tkinter event callback signature.

        WHY event parameter: Tkinter callbacks always receive an event object
        when bound to user input (e.g., <Button-1> for mouse clicks). We
        accept it but don't use it - we just need to know the user clicked.

        WHY stash_state: The keyboard library maintains internal state about
        which keys are currently pressed. After blocking/unblocking, this
        state can become stale, causing keys to appear "stuck". stash_state()
        clears this internal state to prevent phantom key presses.

        See also:
            - lock_keyboard(): Blocking counterpart
            - overlay_window.py: Binds mouse click to this method
        """
        # Unblock all scan codes that were successfully blocked
        for key in self.blocked_keys:
            keyboard.unblock_key(key)
        self.blocked_keys.clear()

        # Close the Tkinter overlay window if it's open
        if self.root:
            self.root.destroy()  # Exits the Tkinter mainloop

        # Clear keyboard library's internal state to prevent phantom key presses
        # WHY necessary: Without this, keys pressed during lock can appear "stuck"
        # after unlock (e.g., Ctrl appears held down even after release)
        keyboard.stash_state()

    def send_hotkey_signal(self) -> None:
        """
        Signal the main thread that the hotkey was pressed.

        This method is called from the hotkey listener thread when the
        user presses the configured hotkey (default: Ctrl+L).

        WHY use a queue: The hotkey listener runs in a separate thread,
        but Tkinter is not thread-safe. We can't create the overlay window
        directly from the hotkey thread. Instead, we signal the main thread
        via a queue, and the main event loop handles window creation.

        The queue acts as a thread-safe mailbox: "Hey main thread, show the overlay!"

        See also:
            - start(): Main event loop that monitors this queue
            - hotkey_listener.py: Calls this method when hotkey pressed
        """
        self.show_overlay_queue.put(True)

    def quit_program(self, icon, item) -> None:
        """
        Gracefully shut down PawGate and clean up resources.

        This is called from the system tray "Quit" menu item.

        Args:
            icon: pystray.Icon instance (required for menu callback signature)
            item: pystray.MenuItem instance (required for menu callback signature)

        Cleanup order:
            1. Remove lockfile (allows new instance to start)
            2. Set program_running flag to False (stops main event loop)
            3. Unlock keyboard if currently locked
            4. Stop the tray icon (exits pystray event loop)

        WHY this order: We want to remove the lockfile first so a new instance
        can start immediately. Then we stop our own event loops (main and tray).

        See also:
            - lockfile_handler.py: Single-instance enforcement
            - tray_icon.py: Menu item binding
        """
        remove_lockfile()  # Allow new instance to start
        self.program_running = False  # Stop main event loop
        self.unlock_keyboard()  # Clean up keyboard blocks if active
        icon.stop()  # Stop pystray event loop (exits tray thread)

    def start(self) -> None:
        """
        Run the main event loop that monitors for hotkey signals.

        This method blocks until the program exits (program_running = False).
        It's the heart of the application - everything else runs in daemon threads.

        Event loop behavior:
            1. Check lockfile (enforce single instance)
            2. Apply keyboard workaround (right Ctrl sticking issue)
            3. Loop forever:
               - Check queue for hotkey signals
               - If signal received, create and show overlay
               - Sleep briefly to avoid busy-waiting

        WHY the right Ctrl remap:
            The keyboard library has a bug on some systems where right Ctrl
            can get "stuck" in a pressed state after blocking/unblocking.
            Remapping it to left Ctrl works around this issue. Since most
            users never use right Ctrl separately, this is an acceptable tradeoff.

            See: https://github.com/boppreh/keyboard/issues/[various]

        WHY sleep(0.1):
            Without the sleep, this loop would spin at 100% CPU checking an
            empty queue. The 0.1 second delay (100ms) is imperceptible to users
            but prevents unnecessary CPU usage. Hotkey presses are queued, so
            we won't miss any signals during the sleep.

        WHY stash_state after overlay creation:
            The overlay window creation can trigger Tkinter focus events that
            interact poorly with the keyboard library's internal state. Calling
            stash_state() after overlay creation prevents issues with phantom
            key presses when the overlay appears.

        See also:
            - send_hotkey_signal(): Puts signals in the queue
            - overlay_window.py: Creates and displays the blocking window
            - lockfile_handler.py: Single-instance enforcement
        """
        # Enforce single instance - terminates old instance if found
        check_lockfile()

        # Workaround for keyboard library bug: right Ctrl can stick
        # WHY remap works: Makes both Ctrl keys behave identically,
        # avoiding the stateful tracking bug in right Ctrl handling
        keyboard.remap_key('right ctrl', 'left ctrl')

        # Main event loop - runs until quit_program sets program_running = False
        while self.program_running:
            # Check if hotkey was pressed (signal in queue)
            if not self.show_overlay_queue.empty():
                self.show_overlay_queue.get(block=False)  # Consume signal

                # Create and show the overlay (blocks until user clicks to unlock)
                overlay = OverlayWindow(main=self)

                # Clear keyboard library state before showing overlay
                # WHY: Prevents keys pressed during overlay creation from appearing stuck
                keyboard.stash_state()

                # This blocks until user clicks (Tkinter mainloop)
                overlay.open()

            # Sleep briefly to avoid busy-waiting (100ms is imperceptible)
            time.sleep(.1)


if __name__ == "__main__":
    # Entry point: Create the PawGate core and run the main event loop
    # WHY separate __init__ and start(): Initialization starts daemon threads
    # (tray icon, hotkey listener) but start() runs the blocking event loop.
    # This separation allows for testing and alternate entry points.
    core = PawGateCore()
    core.start()

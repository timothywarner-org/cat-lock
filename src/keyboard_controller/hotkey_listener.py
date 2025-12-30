"""
Global Hotkey Listener - Register and manage system-wide keyboard shortcuts.

This module wraps the `keyboard` library's hotkey functionality with proper
lifecycle management (start, stop, restart) and thread safety.

The keyboard library (boppreh/keyboard) uses Windows low-level keyboard hooks
to intercept key events globally, even when PawGate doesn't have focus.

Threading considerations:
    - keyboard.add_hotkey() is blocking (runs its own event loop)
    - We run it in a daemon thread to avoid blocking the main thread
    - The thread loops while listen_for_hotkey is True
    - Cleanup (unhook_all_hotkeys) happens when thread exits

WHY separate class instead of methods in main.py:
    Hotkey management has complex lifecycle requirements (start, stop, restart)
    that deserve encapsulation. This makes the code easier to understand and test.

WHY threading.Lock (hotkey_lock):
    Without a lock, concurrent calls to start_hotkey_listener_thread could
    create race conditions:
    - Two threads trying to start hotkey listener simultaneously
    - Trying to stop while another thread is starting
    The lock ensures only one thread can modify hotkey state at a time.

See also:
    - main.py: Creates HotkeyListener instance in __init__
    - pressed_events_handler.py: Workaround for keyboard library bug
    - config.py: Stores the hotkey string (e.g., "ctrl+b")
"""

import threading
import time

import keyboard


class HotkeyListener:
    """
    Manages global hotkey registration and lifecycle.

    This class handles starting, stopping, and restarting the hotkey listener
    thread with proper cleanup and state management.

    Attributes:
        main: Reference to PawGateCore instance (provides access to config,
              queues, and callbacks)

    WHY pass main instance:
        The listener needs access to:
        - self.main.config.hotkey: The key combination to listen for
        - self.main.send_hotkey_signal(): Callback when hotkey is pressed
        - self.main.hotkey_lock: Thread lock for safe lifecycle management
        - self.main.listen_for_hotkey: Flag to control listener loop

        Passing the entire main instance is simpler than passing each piece
        individually (fewer parameters, easier to extend).
    """

    def __init__(self, main):
        """
        Initialize hotkey listener with reference to main application.

        Args:
            main: PawGateCore instance that owns this listener
        """
        self.main = main

    def start_hotkey_listener_thread(self) -> None:
        """
        Start (or restart) the hotkey listener in a daemon thread.

        This method:
        1. Clears stale keyboard state (prevents stuck keys)
        2. Acquires hotkey_lock to prevent race conditions
        3. Sets listen_for_hotkey flag to True
        4. Waits for existing thread to finish (if restarting)
        5. Creates and starts new daemon thread

        WHY stash_state at the start:
            The keyboard library tracks which keys are currently pressed in
            internal state. If we're restarting the listener (e.g., after
            changing the hotkey), stale state could cause issues. Calling
            stash_state() clears this, ensuring we start fresh.

        WHY check if thread is alive before joining:
            If we're starting for the first time, hotkey_thread is None, so
            we skip the join. If we're restarting, we need to wait for the
            old thread to fully exit before starting a new one. The complex
            condition ensures we only join if:
            - A thread exists (hotkey_thread is not None)
            - We're not trying to join from within that thread (deadlock prevention)
            - The thread is actually running (is_alive check)

        WHY daemon thread:
            Daemon threads automatically terminate when the main program exits.
            This ensures clean shutdown without requiring explicit thread.join()
            in every exit path.

        Thread safety:
            The hotkey_lock ensures this method is atomic. Without it, two
            concurrent calls could create multiple listener threads, causing
            undefined behavior.

        See also:
            - hotkey_listener(): The actual thread target function
            - main.py: Calls this during initialization
        """
        # Clear keyboard library's internal state to prevent stuck keys
        # WHY: Ensures fresh start when (re)starting listener
        keyboard.stash_state()

        # Acquire lock to prevent race conditions during thread lifecycle changes
        with self.main.hotkey_lock:
            # Enable the listener loop (hotkey_listener checks this flag)
            self.main.listen_for_hotkey = True

            # If an old thread exists and is running, wait for it to exit
            # WHY check current_thread: Prevent deadlock if somehow called from within hotkey thread
            if (
                self.main.hotkey_thread
                and threading.current_thread() is not self.main.hotkey_thread
                and self.main.hotkey_thread.is_alive()
            ):
                self.main.hotkey_thread.join()

            # Create and start new hotkey listener thread
            # WHY daemon=True: Thread exits automatically when main program exits
            self.main.hotkey_thread = threading.Thread(target=self.hotkey_listener, daemon=True)
            self.main.hotkey_thread.start()

    def hotkey_listener(self) -> None:
        """
        Thread target that registers the hotkey and loops until disabled.

        This function:
        1. Registers the global hotkey with keyboard.add_hotkey()
        2. Loops while listen_for_hotkey is True (sleep to avoid busy-wait)
        3. Cleans up by unhooking all hotkeys when loop exits

        WHY suppress=True:
            When the hotkey is pressed, we don't want it to reach other
            applications. For example, if the hotkey is Ctrl+B, without
                suppress=True, the Ctrl+B would also reach the browser (which
                uses Ctrl+B for bold text). With suppress=True, the
            keyboard library intercepts the key combination before it reaches
            other applications.

        WHY loop with sleep:
            keyboard.add_hotkey() registers a callback but doesn't block.
            We need to keep the thread alive so the hotkey remains registered.
            Without the sleep, this would spin at 100% CPU. The 1-second sleep
            is arbitrary - hotkeys are registered at the OS level, so the sleep
            doesn't affect responsiveness.

        WHY unhook_all_hotkeys:
            When the thread exits (listen_for_hotkey becomes False), we must
            unregister the hotkey. Otherwise, pressing the hotkey after the
            listener "stops" would still trigger the callback, causing errors
            (attempting to signal a stopped application).

        Cleanup:
            This method ensures proper cleanup when the listener is stopped.
            The loop exits when listen_for_hotkey is False, and unhook_all_hotkeys()
            ensures no dangling keyboard hooks remain.

        See also:
            - start_hotkey_listener_thread(): Starts this thread
            - main.send_hotkey_signal(): Callback invoked when hotkey is pressed
        """
        # Register the global hotkey with the keyboard library
        # WHY suppress=True: Prevent hotkey from reaching other applications
        keyboard.add_hotkey(self.main.config.hotkey, self.main.send_hotkey_signal, suppress=True)

        # Register a built-in emergency unlock hotkey so users are never stuck
        emergency_hotkey = getattr(self.main, "emergency_hotkey", None)
        if emergency_hotkey and emergency_hotkey != self.main.config.hotkey:
            keyboard.add_hotkey(emergency_hotkey, self.main.send_hotkey_signal, suppress=True)

        # Keep thread alive while hotkey should be registered
        # WHY loop: add_hotkey() doesn't block, but we need thread alive for hook to persist
        while self.main.listen_for_hotkey:
            time.sleep(1)  # Sleep to avoid busy-waiting (CPU-friendly)

        # Cleanup: Unregister all hotkeys when thread is stopping
        # WHY necessary: Prevents dangling keyboard hooks that could cause errors
        keyboard.unhook_all_hotkeys()

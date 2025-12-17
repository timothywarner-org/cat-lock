"""
Keyboard Library Bug Workaround - Prevent stuck key state after Windows lock.

This module contains a workaround for a known bug in the boppreh/keyboard library
where hotkeys stop working after Windows locks and unlocks the session.

The Bug:
    When Windows locks (Win+L or automatic lock), the keyboard library's internal
    state tracking (_pressed_events dict) can become corrupted. Keys that were
    pressed during the lock remain marked as "pressed" even after release. This
    causes hotkeys to stop working because the library thinks keys are still held.

    See: https://github.com/boppreh/keyboard/issues/223

The Workaround:
    We periodically scan the _pressed_events dictionary and delete stale entries
    (keys pressed more than 2 seconds ago). This prevents the stuck key state
    from accumulating and breaking hotkey detection.

WHY access private members (_pressed_events, _pressed_events_lock):
    This is normally bad practice, but:
    1. The bug is in the library, not our code
    2. The library doesn't provide a public API to fix this
    3. The alternative is to fork and maintain the entire keyboard library
    4. This workaround is isolated to one function for easy removal when fixed

WHY run in a daemon thread:
    This cleanup needs to run continuously in the background. A daemon thread
    ensures it doesn't prevent application shutdown.

WHY 2-second threshold:
    - Normal key presses are brief (< 1 second typically)
    - Holding a key for 2+ seconds is unusual in normal use
    - 2 seconds is long enough to avoid false positives but short enough
      to catch stuck keys before they cause issues

Future:
    If the keyboard library fixes this bug, we can remove this entire module.
    Track: https://github.com/boppreh/keyboard/issues/223

See also:
    - main.py: Starts this thread in __init__
    - hotkey_listener.py: Benefits from this workaround (hotkeys keep working)
"""

import time

import keyboard


def clear_pressed_events() -> None:
    """
    Continuously clean up stale key press events from keyboard library's state.

    This function runs in an infinite loop (daemon thread) and periodically
    removes keys from the keyboard library's internal _pressed_events dict
    if they've been "pressed" for more than 2 seconds.

    WHY infinite loop:
        This cleanup must run for the entire application lifetime. The loop
        only exits when the application terminates (daemon thread behavior).

    WHY 2-second threshold:
        Keys held for 2+ seconds are either:
        1. Stuck due to the Windows lock bug (need cleanup)
        2. Deliberately held (rare, but cleanup won't hurt)

        Most normal key presses are < 1 second. The 2-second window gives
        generous leeway for legitimate key holds (e.g., holding Ctrl while
        clicking multiple items) while still catching stuck keys quickly.

    WHY sleep(1):
        Cleanup doesn't need to be instant. Running every second:
        - Keeps CPU usage low (not spinning at 100%)
        - Still catches stuck keys within 3 seconds total (2 second threshold
          + up to 1 second sleep delay)
        - Reduces lock contention on _pressed_events_lock

    Thread safety:
        We must acquire _pressed_events_lock before accessing _pressed_events
        because the keyboard library's event handling thread also modifies it.
        Without the lock, we'd have race conditions (reading while library writes).

    WHY list(keyboard._pressed_events.keys()):
        We can't iterate over a dict while modifying it (raises RuntimeError).
        Creating a list snapshot of the keys allows us to safely delete items
        during iteration. The list() creates a copy, so deletions don't affect
        the iteration.

    Edge cases:
        - Empty dict: Loop continues, no harm done
        - Key deleted by library while we're checking: No error, our deletion
          just becomes a no-op
        - Multiple keys stuck: All get cleaned up (loop processes all keys)

    See also:
        - main.py: Starts this in a daemon thread during initialization
        - GitHub issue: https://github.com/boppreh/keyboard/issues/223
    """
    while True:
        # WHY this list: For debugging/logging if needed (currently unused)
        deleted = []

        # Acquire keyboard library's internal lock for thread-safe access
        # WHY necessary: Prevents race conditions with keyboard's event thread
        with keyboard._pressed_events_lock:
            # Create snapshot of keys to allow safe deletion during iteration
            # WHY list(): Can't modify dict while iterating over it directly
            for k in list(keyboard._pressed_events.keys()):
                item = keyboard._pressed_events[k]

                # Check if this key has been "pressed" for more than 2 seconds
                # WHY 2 seconds: Long enough to avoid false positives, short
                # enough to catch stuck keys before user notices issues
                if time.time() - item.time > 2:
                    deleted.append(item.name)  # Track for potential logging
                    del keyboard._pressed_events[k]  # Remove stale entry

        # Sleep to avoid busy-waiting and reduce CPU usage
        # WHY 1 second: Balances responsiveness vs CPU efficiency
        time.sleep(1)

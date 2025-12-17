"""
Windows Toast Notifications - User feedback when keyboard locks.

This module sends Windows 10/11 toast notifications (Action Center notifications)
to inform users that the keyboard has been locked.

Notification strategy:
    - Appears in Windows Action Center (bottom-right on most systems)
    - Shows CatLock icon for brand recognition
    - Brief message: "Keyboard Locked - Click on screen to unlock"
    - Auto-dismisses after 3 seconds (doesn't clutter Action Center)

WHY plyer library:
    - Cross-platform notification abstraction (Windows, Mac, Linux)
    - Simple API (one function call)
    - Works on Windows 10/11 without complex Win32 API calls
    - No native dependencies

WHY in a thread:
    Notification display can be slow (100-500ms) due to Windows API calls.
    Running in a thread prevents blocking the main application while the
    notification appears. The thread joins immediately to ensure the
    notification completes before continuing.

WHY timeout=3:
    Notifications that stay too long clutter the Action Center. 3 seconds
    is enough time for users to notice, but brief enough to not be annoying.

WHY app_icon:
    Branded notifications with the CatLock icon help users identify the
    source, especially if multiple apps send notifications.

Alternatives considered:
    - win10toast: Windows-only, abandoned project
    - pywin32 with COM: Complex, requires understanding Windows notification APIs
    - plyer: Winner for simplicity and cross-platform support

See also:
    - main.lock_keyboard(): Calls this when keyboard locks
    - config.py: notifications_enabled setting to disable if user wants
    - path_util.py: get_packaged_path for PyInstaller bundled icon
"""

import os
import threading
import time

import plyer

from src.util.path_util import get_packaged_path


def send_lock_notification() -> None:
    """
    Display a Windows toast notification that keyboard is locked.

    This shows a system notification with:
    - App name: "CatLock"
    - Title: "Keyboard Locked"
    - Message: "Click on screen to unlock"
    - Icon: CatLock icon (for brand recognition)
    - Timeout: 3 seconds (auto-dismiss)

    WHY brief sleep after notify:
        The plyer.notification.notify() call returns immediately, but the
        actual notification display happens asynchronously in Windows.
        A brief sleep (100ms) gives Windows time to process the notification
        request before this thread exits. Without it, rapid thread termination
        could sometimes cancel the notification before it appears.

    Edge cases:
        - Icon file missing: Notification shows without icon (not critical)
        - Windows notifications disabled: plyer fails silently (user choice)
        - Action Center full: Windows handles (oldest notifications removed)

    See also:
        - send_notification_in_thread(): Wrapper that checks if enabled
    """
    # Build path to icon file in bundled resources
    path = os.path.join("resources", "img", "icon.ico")

    # Send Windows toast notification
    # WHY .ico file: Windows notifications prefer .ico format for consistency
    plyer.notification.notify(
        app_name="CatLock",  # Shows in notification header
        title="Keyboard Locked",  # Bold text in notification
        message="Click on screen to unlock",  # Body text with unlock instructions
        app_icon=get_packaged_path(path),  # CatLock icon for branding
        timeout=3,  # Auto-dismiss after 3 seconds
    )

    # Brief pause to let Windows process notification request
    # WHY: Prevents thread exit from cancelling notification display
    time.sleep(.1)


def send_notification_in_thread(notifications_enabled: bool) -> None:
    """
    Send lock notification in a background thread (if notifications enabled).

    Args:
        notifications_enabled: Whether user has notifications enabled in settings

    WHY in a thread:
        Notification display can take 100-500ms due to Windows API calls.
        Threading prevents blocking the main application while the OS
        processes the notification request.

    WHY join immediately:
        Even though we use a thread, we join() before returning. This ensures
        the notification completes before we continue, which:
        - Maintains predictable execution order
        - Prevents race conditions if called rapidly
        - Ensures notification appears before overlay (good UX)

    WHY daemon thread:
        If the application exits while sending a notification, the daemon
        thread will terminate automatically without blocking shutdown.

    Conditional execution:
        Respects user's notification preference (configurable in tray menu).
        If disabled, this function returns immediately without creating a thread.

    See also:
        - main.lock_keyboard(): Calls this when keyboard locks
        - config.py: notifications_enabled setting
        - tray_icon.py: Toggle notifications in menu
    """
    # Only send notification if user has them enabled
    if notifications_enabled:
        # Create daemon thread to send notification (non-blocking)
        notification_thread = threading.Thread(target=send_lock_notification, daemon=True)
        notification_thread.start()

        # Wait for notification to complete (ensures proper sequencing)
        # WHY join: Guarantees notification appears before continuing
        notification_thread.join()

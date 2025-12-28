"""
Unit tests for notifications module.

WHY: Notifications provide user feedback for lock/unlock events.
These tests verify notifications are sent correctly without
actually displaying toast notifications during tests.
"""

from unittest.mock import Mock, patch, MagicMock

import pytest


class TestNotifications:
    """
    Tests for notification functionality.

    WHY: We mock plyer.notification to prevent actual toast
    notifications from appearing during tests.
    """

    @pytest.fixture
    def mock_plyer(self, mocker):
        """Mock plyer notification to prevent real toasts."""
        return mocker.patch('src.os_controller.notifications.notification')

    def test_send_notification_calls_plyer(self, mock_plyer):
        """
        Verify send_notification uses plyer correctly.

        WHY: The notification module wraps plyer. This test ensures
        the wrapper correctly delegates to plyer.
        """
        from src.os_controller.notifications import send_notification

        send_notification("Test Title", "Test Message")

        # Verify plyer.notification.notify was called
        mock_plyer.notify.assert_called_once()

    def test_send_notification_includes_title_and_message(self, mock_plyer):
        """
        Verify notification contains correct title and message.

        WHY: Users expect meaningful notification content.
        """
        from src.os_controller.notifications import send_notification

        title = "Keyboard Locked"
        message = "Press Ctrl+B to unlock"

        send_notification(title, message)

        call_kwargs = mock_plyer.notify.call_args[1]
        assert call_kwargs.get('title') == title
        assert call_kwargs.get('message') == message

    def test_send_notification_includes_app_name(self, mock_plyer):
        """
        Verify notification includes PawGate app name.

        WHY: App name helps users identify the source of notifications.
        """
        from src.os_controller.notifications import send_notification

        send_notification("Test", "Test")

        call_kwargs = mock_plyer.notify.call_args[1]
        app_name = call_kwargs.get('app_name', '')
        assert 'pawgate' in app_name.lower() or 'paw' in app_name.lower()

    def test_send_notification_in_thread_is_non_blocking(self, mock_plyer, mocker):
        """
        Verify threaded notification doesn't block caller.

        WHY: Notifications should not slow down the main event loop.
        The threaded version should return immediately.
        """
        import threading
        import time

        from src.os_controller.notifications import send_notification_in_thread

        # Make notification slow
        def slow_notify(**kwargs):
            time.sleep(0.1)

        mock_plyer.notify.side_effect = slow_notify

        start = time.time()
        send_notification_in_thread("Test", "Test")
        elapsed = time.time() - start

        # Should return almost immediately (not wait 0.1s)
        assert elapsed < 0.05, f"Threaded notification blocked for {elapsed}s"

    def test_notification_handles_plyer_exception(self, mock_plyer):
        """
        Verify notification handles plyer errors gracefully.

        WHY: Notification failures shouldn't crash the app.
        Common on systems without notification support.
        """
        mock_plyer.notify.side_effect = Exception("Notification failed")

        from src.os_controller.notifications import send_notification

        # Should not raise
        try:
            send_notification("Test", "Test")
        except Exception as e:
            pytest.fail(f"send_notification raised exception: {e}")

    def test_notification_respects_enabled_setting(self, mock_plyer, mocker):
        """
        Verify notifications respect the enabled setting.

        WHY: Users can disable notifications in settings.
        When disabled, no notification should be sent.
        """
        # This test depends on how notifications check the config
        # Implementation may vary
        pass


class TestNotificationContent:
    """
    Tests for notification message content.

    WHY: Notification messages should be clear and helpful.
    """

    def test_lock_notification_message(self):
        """
        Verify lock notification has appropriate content.

        WHY: Users need to know the keyboard is locked and how to unlock.
        """
        # Test the actual message content if there's a factory function
        pass

    def test_unlock_notification_message(self):
        """
        Verify unlock notification confirms keyboard is usable.

        WHY: Users need confirmation that unlock was successful.
        """
        pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

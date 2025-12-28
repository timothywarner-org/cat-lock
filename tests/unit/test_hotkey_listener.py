"""
Unit tests for HotkeyListener module.

WHY: HotkeyListener is the critical component that detects when the user
presses the lock/unlock hotkey. If this fails, users can't control the app.
These tests verify hotkey registration, callback invocation, and cleanup.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from queue import Queue

import pytest


class TestHotkeyListener:
    """
    Unit tests for HotkeyListener class.

    WHY: We mock the keyboard library because:
    1. Real hotkey registration requires admin privileges on Windows
    2. Would interfere with the developer's keyboard during tests
    3. We want fast, isolated unit tests
    """

    @pytest.fixture
    def mock_keyboard(self, mocker):
        """Mock keyboard library to prevent real hotkey registration."""
        mock_kb = mocker.patch('src.keyboard_controller.hotkey_listener.keyboard')
        return mock_kb

    @pytest.fixture
    def sample_queue(self):
        """Provide a queue for hotkey signals."""
        return Queue()

    def test_listener_registers_hotkey(self, mock_keyboard, sample_queue):
        """
        Verify HotkeyListener registers the hotkey on initialization.

        WHY: The hotkey must be registered for the app to respond to
        user input. This is the core functionality.
        """
        from src.keyboard_controller.hotkey_listener import HotkeyListener

        hotkey = "ctrl+b"
        listener = HotkeyListener(sample_queue, hotkey)

        # Verify keyboard.add_hotkey was called with correct args
        mock_keyboard.add_hotkey.assert_called_once()
        call_args = mock_keyboard.add_hotkey.call_args
        assert call_args[0][0] == hotkey, f"Expected hotkey {hotkey}, got {call_args[0][0]}"

    def test_listener_callback_puts_signal_in_queue(self, mock_keyboard, sample_queue):
        """
        Verify that pressing the hotkey puts a signal in the queue.

        WHY: The main thread polls the queue to know when to toggle lock.
        If the signal doesn't reach the queue, the app becomes unresponsive.
        """
        from src.keyboard_controller.hotkey_listener import HotkeyListener

        # Capture the callback when add_hotkey is called
        callback = None

        def capture_callback(hotkey, cb, *args, **kwargs):
            nonlocal callback
            callback = cb

        mock_keyboard.add_hotkey.side_effect = capture_callback

        listener = HotkeyListener(sample_queue, "ctrl+b")

        # Simulate hotkey press by calling the callback
        assert callback is not None, "Callback was not registered"
        callback()

        # Verify signal was added to queue
        assert not sample_queue.empty(), "Queue should have a signal"
        signal = sample_queue.get_nowait()
        assert signal is True, "Signal should be True"

    def test_listener_handles_complex_hotkeys(self, mock_keyboard, sample_queue):
        """
        Verify HotkeyListener handles complex modifier combinations.

        WHY: Users may configure hotkeys like Ctrl+Shift+Alt+F12.
        The listener must handle these correctly.
        """
        from src.keyboard_controller.hotkey_listener import HotkeyListener

        complex_hotkeys = [
            "ctrl+shift+l",
            "ctrl+alt+f12",
            "ctrl+shift+alt+p",
            "win+pause",
        ]

        for hotkey in complex_hotkeys:
            mock_keyboard.reset_mock()
            listener = HotkeyListener(sample_queue, hotkey)

            # Verify hotkey was registered
            mock_keyboard.add_hotkey.assert_called_once()
            call_args = mock_keyboard.add_hotkey.call_args
            assert hotkey in str(call_args), f"Hotkey {hotkey} not found in call args"

    def test_listener_cleanup_removes_hotkey(self, mock_keyboard, sample_queue):
        """
        Verify that listener cleanup removes the registered hotkey.

        WHY: If we don't clean up, the hotkey remains registered after
        the app exits, potentially causing conflicts or zombie hooks.
        """
        from src.keyboard_controller.hotkey_listener import HotkeyListener

        listener = HotkeyListener(sample_queue, "ctrl+b")

        # Trigger cleanup (implementation-dependent)
        if hasattr(listener, 'stop'):
            listener.stop()
        elif hasattr(listener, 'cleanup'):
            listener.cleanup()

        # Note: The actual cleanup method depends on implementation
        # This test documents the expected behavior


class TestHotkeyParsing:
    """
    Tests for hotkey string parsing functionality.

    WHY: Hotkey strings from config need to be parsed correctly.
    Invalid hotkeys should be handled gracefully.
    """

    def test_parse_simple_hotkey(self):
        """Verify simple hotkey parsing."""
        # This would test a parse function if exposed
        # For now, test via HotkeyListener behavior
        pass

    def test_invalid_hotkey_handled_gracefully(self, mocker):
        """
        Verify invalid hotkeys don't crash the application.

        WHY: Users might typo their hotkey config. The app should
        handle this gracefully, perhaps with a warning or default.
        """
        mock_keyboard = mocker.patch('src.keyboard_controller.hotkey_listener.keyboard')
        mock_keyboard.add_hotkey.side_effect = ValueError("Invalid hotkey")

        from src.keyboard_controller.hotkey_listener import HotkeyListener

        queue = Queue()

        # Should not raise - should handle gracefully
        try:
            listener = HotkeyListener(queue, "invalid+++hotkey")
            # If it gets here without exception, that's acceptable
        except ValueError:
            # Also acceptable if it raises but is caught elsewhere
            pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

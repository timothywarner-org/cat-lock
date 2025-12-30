"""
Integration tests for keyboard locking functionality.

WHY: These tests verify the keyboard blocking mechanism integrates
correctly with the boppreh/keyboard library. We mock keyboard.block_key
and keyboard.unblock_key to avoid actually blocking the test runner's
keyboard (which would be... problematic).

Tests cover:
- Full scan code range blocking (0-255)
- Named key blocking for critical system keys
- Proper cleanup via unblock_key
- Graceful handling of invalid scan codes
"""

import unittest
from unittest.mock import Mock, patch

from src.main import PawGateCore, EXTENDED_SCAN_CODES

# Tests intentionally touch semi-private helpers for coverage
# pylint: disable=protected-access


class TestKeyboardController(unittest.TestCase):
    """
    Integration tests for keyboard locking in PawGateCore.

    WHY: We test at the PawGateCore level (not isolated functions) because
    keyboard blocking requires coordination between state management
    (blocked_keys set) and library calls (keyboard.block_key/unblock_key).
    This is true integration testing.
    """

    def setUp(self) -> None:
        """
        Set up test fixtures with mocked dependencies.

        WHY: We patch threading, keyboard library, and external dependencies
        to prevent:
        1. Actual thread spawning (would leak threads between tests)
        2. Real keyboard hooks (would block IDE/terminal)
        3. File I/O for lockfile operations
        4. System tray creation (requires GUI context)
        """
        # Patch all external dependencies before instantiation
        self.patcher_thread = patch('src.main.threading.Thread')
        self.patcher_keyboard_lib = patch('src.main.keyboard')
        self.patcher_check_lockfile = patch('src.main.check_lockfile')
        self.patcher_config = patch('src.main.Config')
        self.patcher_hotkey_listener = patch('src.main.HotkeyListener')
        self.patcher_send_notification = patch('src.main.send_notification_in_thread')

        self.mock_thread = self.patcher_thread.start()
        self.mock_keyboard = self.patcher_keyboard_lib.start()
        self.mock_check_lockfile = self.patcher_check_lockfile.start()
        self.mock_config = self.patcher_config.start()
        self.mock_hotkey_listener = self.patcher_hotkey_listener.start()
        self.mock_send_notification = self.patcher_send_notification.start()

        # Configure mock behavior
        self.mock_thread.return_value = Mock()
        self.mock_config.return_value.notifications_enabled = True
        self.mock_config.return_value.hotkey = 'ctrl+shift+l'

        # Deterministic scan code mapping for hotkey parsing in tests
        self.mock_keyboard.key_to_scan_codes.side_effect = lambda name: {
            'ctrl': [29],
            'left ctrl': [29],
            'right ctrl': [285],
            'shift': [42],
            'left shift': [42],
            'right shift': [54],
            'alt': [56],
            'left alt': [56],
            'right alt': [312],
            'l': [38],
            'u': [22],
        }.get(name, [])

        # WHY: Create core after all patches are active to ensure
        # __init__ doesn't trigger real system interactions
        self.core = PawGateCore()

    def tearDown(self) -> None:
        """
        Clean up all patches after each test.

        WHY: unittest.mock patches must be stopped to avoid leaking
        mocks into subsequent tests. This is critical for test isolation.
        """
        self.patcher_thread.stop()
        self.patcher_keyboard_lib.stop()
        self.patcher_check_lockfile.stop()
        self.patcher_config.stop()
        self.patcher_hotkey_listener.stop()
        self.patcher_send_notification.stop()

    def test_lock_keyboard_blocks_all_scan_codes(self) -> None:
        """
        Verify that lock_keyboard blocks all scan codes including extended brightness keys.

        WHY: Modern keyboards (especially non-US layouts) use extended
        scan codes beyond the basic ASCII range. Testing the full 0-255
        range ensures multimedia keys, F13-F24, and international keys
        are blocked. This prevents sneaky cats from hitting Play/Pause!
        """
        # Act
        self.core.lock_keyboard()

        # Assert - verify expected scan codes were attempted (excluding unlock hotkeys)
        block_key_calls = [
            call_args for call_args in self.mock_keyboard.block_key.call_args_list
            if isinstance(call_args[0][0], int)
        ]

        blocked_scan_codes = {call_args[0][0] for call_args in block_key_calls}

        # Primary hotkey: ctrl+shift+l ; Emergency: left ctrl + right ctrl
        skipped_for_hotkeys = {29, 285, 42, 54, 38}
        attempted_codes = (set(range(256)) - skipped_for_hotkeys) | set(EXTENDED_SCAN_CODES)

        self.assertEqual(
            attempted_codes,
            blocked_scan_codes,
            f"Expected {len(attempted_codes)} scan codes, got {len(blocked_scan_codes)}",
        )

    def test_lock_keyboard_blocks_critical_keys_by_name(self) -> None:
        """
        Verify that lock_keyboard blocks critical system keys by name.

        WHY: Some keys (Windows key, media controls) are more reliably
        blocked by name than scan code due to driver/OS variations.
        This test ensures we use the belt-and-suspenders approach.

        Real-world impact: Prevents cats from:
        - Opening Start menu (Windows key)
        - Changing volume/brightness
        - Playing/pausing media (Spotify interruption during standups!)
        """
        # Act
        self.core.lock_keyboard()

        # Assert - verify named keys were blocked
        # WHY: Filter to string arguments to isolate named key calls
        named_key_calls = [
            call_args[0][0] for call_args in self.mock_keyboard.block_key.call_args_list
            if isinstance(call_args[0][0], str)
        ]

        # WHY: These are the exact keys from the implementation that
        # are most dangerous for cats to press
        expected_critical_keys = [
            'windows', 'left windows', 'right windows',
            'volume up', 'volume down', 'volume mute',
            'play/pause media', 'next track', 'previous track',
            'brightness up', 'brightness down',
        ]

        for critical_key in expected_critical_keys:
            self.assertIn(
                critical_key,
                named_key_calls,
                f"Critical key '{critical_key}' was not blocked"
            )

    def test_unlock_keyboard_clears_blocked_keys(self) -> None:
        """
        Verify that unlock_keyboard properly cleans up all blocked keys.

        WHY: Failing to unblock keys would leave the keyboard in a broken
        state after the program exits. This is a catastrophic failure mode
        that requires a reboot to fix. We MUST test this!

        Test approach:
        1. Lock keyboard (populates blocked_keys set)
        2. Unlock keyboard
        3. Verify unblock_key called for each blocked key
        4. Verify blocked_keys set is cleared
        """
        # Arrange - simulate successful blocking of some keys
        # WHY: Only keys that were successfully blocked get added to
        # blocked_keys set, so we simulate this behavior
        test_scan_codes = [1, 2, 3, 28, 57]  # Representative sample
        self.core.blocked_keys = set(test_scan_codes)

        # Act
        self.core.unlock_keyboard()

        # Assert - verify each key was unblocked
        # WHY: We must call unblock_key for each key that was blocked,
        # otherwise those keys remain hooked by the keyboard library
        unblock_calls = [
            call_args[0][0] for call_args in self.mock_keyboard.unblock_key.call_args_list
        ]

        for scan_code in test_scan_codes:
            self.assertIn(
                scan_code,
                unblock_calls,
                f"Scan code {scan_code} was not unblocked"
            )

        # Assert - verify blocked_keys set was cleared
        # WHY: Cleared set indicates clean state for potential re-lock
        self.assertEqual(
            len(self.core.blocked_keys),
            0,
            "blocked_keys set should be empty after unlock"
        )

        # Assert - verify keyboard.stash_state() was called
        # WHY: stash_state() clears any lingering key press events in the
        # keyboard library's internal state. Without this, pressed keys
        # can "stick" after unlock (see GitHub issue #223)
        self.mock_keyboard.stash_state.assert_called_once()

    def test_lock_handles_invalid_scan_codes(self) -> None:
        """
        Verify that lock_keyboard gracefully handles keyboard.block_key exceptions.

        WHY: Not all scan codes map to physical keys on all keyboards.
        block_key(177) might work on a Logitech keyboard but throw on
        a Microsoft keyboard. We MUST handle this gracefully via try/except,
        otherwise the entire lock operation fails.

        Test approach:
        - Simulate keyboard.block_key raising exception for some scan codes
        - Verify lock_keyboard completes without crashing
        - Verify successful blocks are recorded in blocked_keys
        """
        # Arrange - simulate block_key failing for certain scan codes
        # WHY: Real keyboards have gaps in their scan code mappings
        failing_scan_codes = {100, 150, 200}

        def block_key_side_effect(key):
            """Simulate intermittent block_key failures."""
            if isinstance(key, int) and key in failing_scan_codes:
                raise KeyError(f"Invalid scan code: {key}")
            # Otherwise succeed silently
            return None

        self.mock_keyboard.block_key.side_effect = block_key_side_effect

        # Act - should NOT raise exception
        try:
            self.core.lock_keyboard()
        except Exception as exc:  # pylint: disable=broad-exception-caught
            self.fail(f"lock_keyboard raised exception: {exc}")

        # Assert - verify successful blocks were recorded
        # WHY: Can't directly compare sets because named keys also get blocked
        # Just verify the failing codes are NOT in blocked_keys
        for failing_code in failing_scan_codes:
            self.assertNotIn(
                failing_code,
                self.core.blocked_keys,
                f"Failing scan code {failing_code} should not be in blocked_keys"
            )

        # Assert - verify some keys WERE successfully blocked
        # WHY: We want to confirm the function didn't just silently fail
        self.assertGreater(
            len(self.core.blocked_keys),
            0,
            "Some keys should have been successfully blocked"
        )

    def test_get_hotkey_keys_parses_simple_hotkey(self) -> None:
        """
        Verify that _get_hotkey_keys correctly parses a simple hotkey.

        WHY: The hotkey must be parsed to determine which keys to unblock
        after blocking all keyboard input. If parsing fails, the unlock
        hotkey won't work and the user gets locked out.
        """
        # Arrange - set a simple hotkey
        self.core.config.hotkey = 'ctrl+b'

        # Act
        keys = self.core._get_hotkey_keys()

        # Assert - should include ctrl variants and b
        self.assertIn('b', keys)
        self.assertIn('ctrl', keys)
        self.assertIn('left ctrl', keys)
        self.assertIn('right ctrl', keys)

    def test_get_hotkey_keys_expands_all_modifiers(self) -> None:
        """
        Verify that _get_hotkey_keys expands all modifier variants.

        WHY: When the hotkey is "ctrl+shift+alt+f12", the user might press
        left Ctrl OR right Ctrl, left Shift OR right Shift, etc. We must
        unblock ALL variants to ensure the hotkey works regardless of which
        physical key the user presses.
        """
        # Arrange - set a complex hotkey with multiple modifiers
        self.core.config.hotkey = 'ctrl+shift+alt+f12'

        # Act
        keys = self.core._get_hotkey_keys()

        # Assert - should include all modifier variants
        expected_keys = [
            'ctrl', 'left ctrl', 'right ctrl',
            'shift', 'left shift', 'right shift',
            'alt', 'left alt', 'right alt',
            'f12'
        ]
        for expected_key in expected_keys:
            self.assertIn(
                expected_key,
                keys,
                f"Expected key '{expected_key}' not found in parsed hotkey"
            )

    def test_lock_keyboard_unblocks_hotkey_keys(self) -> None:
        """
        Verify that lock_keyboard unblocks hotkey keys after blocking all.

        WHY: This is the critical fix for the lockout bug. If we block ALL
        keys (scan codes 0-255) without unblocking the hotkey keys, the user
        cannot press Ctrl+B to unlock. This test ensures the fix works.

        Real-world impact: Without this fix, users had to reboot their
        machine to regain keyboard control. That's a TERRIBLE user experience.
        """
        # Arrange - set a known hotkey
        self.core.config.hotkey = 'ctrl+b'

        # Act
        self.core.lock_keyboard()

        # Assert - verify unblock_key was called for hotkey keys
        unblock_calls = [
            call_args[0][0] for call_args in self.mock_keyboard.unblock_key.call_args_list
        ]

        # WHY: These are the keys that MUST be unblocked for Ctrl+B to work
        required_unblocked = ['ctrl', 'left ctrl', 'right ctrl', 'b']
        for key in required_unblocked:
            self.assertIn(
                key,
                unblock_calls,
                f"Hotkey key '{key}' was not unblocked - user would be locked out!"
            )

    def test_lock_keyboard_unblocks_emergency_hotkey(self) -> None:
        """Verify the built-in emergency hotkey keys are also unblocked."""
        # Arrange - use defaults configured in setUp

        # Act
        self.core.lock_keyboard()

        # Assert - emergency combo keys should be unblocked
        unblock_calls = [
            call_args[0][0] for call_args in self.mock_keyboard.unblock_key.call_args_list
        ]

        emergency_keys = ['left ctrl', 'right ctrl']
        for key in emergency_keys:
            self.assertIn(
                key,
                unblock_calls,
                f"Emergency hotkey key '{key}' was not unblocked"
            )


if __name__ == '__main__':
    unittest.main()

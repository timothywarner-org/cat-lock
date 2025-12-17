"""
Unit tests for lockfile_handler module.

WHY: Lockfile handling prevents multiple instances of PawGate from running
simultaneously (which would cause keyboard hook conflicts). These tests
verify the lifecycle: create lockfile, detect stale processes, cleanup.

Critical behaviors tested:
- Lockfile creation with current PID
- Killing stale processes from previous runs
- Cleanup on normal exit
- Graceful handling of missing files (edge case)
"""

import unittest
from unittest.mock import patch, mock_open, call, MagicMock
import os
import signal
from pathlib import Path

from src.util.lockfile_handler import (
    check_lockfile,
    remove_lockfile,
    LOCKFILE_PATH
)


class TestLockfileHandler(unittest.TestCase):
    """
    Unit tests for lockfile operations.

    WHY: We use extensive mocking because:
    1. Actual file I/O would pollute the filesystem
    2. We need to test edge cases (missing files, permission errors)
    3. os.kill() would terminate real processes (BAD in tests!)
    4. os.getpid() returns unpredictable values
    """

    @patch('src.util.lockfile_handler.os.getpid')
    @patch('src.util.lockfile_handler.os.path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_check_lockfile_creates_file(
        self,
        mock_file: MagicMock,
        mock_exists: MagicMock,
        mock_getpid: MagicMock
    ) -> None:
        """
        Verify check_lockfile creates lockfile with current PID when no existing file.

        WHY: On first run, no lockfile exists. We must create one containing
        our PID so future runs can detect us. This is the "happy path" for
        a fresh installation.

        Test approach:
        1. Simulate no existing lockfile (exists returns False)
        2. Call check_lockfile()
        3. Verify file opened in write mode
        4. Verify current PID written to file
        """
        # Arrange
        # WHY: exists=False simulates first run or cleaned-up state
        mock_exists.return_value = False
        current_pid = 12345
        mock_getpid.return_value = current_pid

        # Act
        check_lockfile()

        # Assert - verify file was opened in write mode
        # WHY: We expect exactly one write operation to create the lockfile
        # The call signature should be open(LOCKFILE_PATH, 'w')
        mock_file.assert_called_once_with(LOCKFILE_PATH, 'w')

        # Assert - verify current PID was written
        # WHY: The lockfile must contain our PID as a string so other
        # processes can read it and detect we're running
        handle = mock_file()
        handle.write.assert_called_once_with(str(current_pid))

    @patch('src.util.lockfile_handler.os.kill')
    @patch('src.util.lockfile_handler.os.getpid')
    @patch('src.util.lockfile_handler.os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='9999')
    def test_check_lockfile_kills_stale_process(
        self,
        mock_file: MagicMock,
        mock_exists: MagicMock,
        mock_getpid: MagicMock,
        mock_kill: MagicMock
    ) -> None:
        """
        Verify check_lockfile terminates old process when lockfile exists.

        WHY: If PawGate crashed previously, its lockfile persists with a
        stale PID. We must kill that old process (if still running) before
        starting our new instance. This prevents zombie processes and
        keyboard hook conflicts.

        Real-world scenario: User force-closes PawGate via Task Manager.
        The lockfile remains with PID 9999. Next launch must clean this up.

        Test approach:
        1. Simulate existing lockfile containing PID 9999
        2. Call check_lockfile()
        3. Verify os.kill(9999, SIGTERM) was called
        4. Verify new lockfile written with current PID
        """
        # Arrange
        # WHY: exists=True simulates leftover lockfile from previous run
        mock_exists.return_value = True
        old_pid = 9999  # From read_data='9999'
        current_pid = 12345
        mock_getpid.return_value = current_pid

        # Act
        check_lockfile()

        # Assert - verify old process was terminated
        # WHY: SIGTERM (15) allows graceful shutdown. We don't use SIGKILL
        # because the old process might need to clean up resources.
        mock_kill.assert_called_once_with(old_pid, signal.SIGTERM)

        # Assert - verify file was read to get old PID
        # WHY: We need TWO open operations: one read (get old PID), one write (set new PID)
        calls = mock_file.call_args_list
        self.assertEqual(len(calls), 2, "Expected two file operations: read then write")

        # WHY: First call should be read mode to get the stale PID
        first_call = calls[0]
        self.assertEqual(first_call[0][0], LOCKFILE_PATH)
        self.assertEqual(first_call[0][1], 'r')

        # WHY: Second call should be write mode to store current PID
        second_call = calls[1]
        self.assertEqual(second_call[0][0], LOCKFILE_PATH)
        self.assertEqual(second_call[0][1], 'w')

        # Assert - verify current PID was written
        handle = mock_file()
        handle.write.assert_called_once_with(str(current_pid))

    @patch('src.util.lockfile_handler.os.kill')
    @patch('src.util.lockfile_handler.os.getpid')
    @patch('src.util.lockfile_handler.os.path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='9999')
    def test_check_lockfile_handles_process_not_found(
        self,
        mock_file: MagicMock,
        mock_exists: MagicMock,
        mock_getpid: MagicMock,
        mock_kill: MagicMock
    ) -> None:
        """
        Verify check_lockfile continues gracefully if old process already dead.

        WHY: The stale PID in the lockfile might reference a process that's
        already terminated. os.kill() will raise ProcessLookupError (or similar).
        We MUST catch this and continue, because the goal is just to ensure
        no old instance is running.

        Real-world scenario: PawGate crashed, Windows cleaned up the process,
        but the lockfile persists. os.kill(9999) will fail, but that's fine -
        the old process is already gone!

        Test approach:
        1. Simulate existing lockfile with PID 9999
        2. Simulate os.kill() raising Exception (process not found)
        3. Verify check_lockfile completes without crashing
        4. Verify new lockfile is still created
        """
        # Arrange
        mock_exists.return_value = True
        current_pid = 12345
        mock_getpid.return_value = current_pid

        # WHY: Simulate process already dead - os.kill raises exception
        mock_kill.side_effect = ProcessLookupError("No such process")

        # Act - should NOT raise exception
        try:
            check_lockfile()
            exception_raised = False
        except Exception as e:
            exception_raised = True
            self.fail(f"check_lockfile raised exception: {e}")

        # Assert - verify function completed without error
        self.assertFalse(exception_raised)

        # Assert - verify new lockfile was still created
        # WHY: Even if old process kill failed, we must create our lockfile
        handle = mock_file()
        handle.write.assert_called_with(str(current_pid))

    @patch('src.util.lockfile_handler.os.remove')
    @patch('src.util.lockfile_handler.os.path.exists')
    def test_remove_lockfile_deletes_file(
        self,
        mock_exists: MagicMock,
        mock_remove: MagicMock
    ) -> None:
        """
        Verify remove_lockfile deletes the lockfile when it exists.

        WHY: On clean shutdown, we must remove our lockfile to signal
        we're no longer running. Otherwise, the next launch will try
        to kill our (now defunct) PID.

        This is called from quit_program() in the main event loop.

        Test approach:
        1. Simulate existing lockfile
        2. Call remove_lockfile()
        3. Verify os.remove() called with correct path
        """
        # Arrange
        # WHY: exists=True simulates our lockfile is present
        mock_exists.return_value = True

        # Act
        remove_lockfile()

        # Assert - verify file was deleted
        # WHY: os.remove() is the OS call to delete a file
        mock_remove.assert_called_once_with(LOCKFILE_PATH)

    @patch('src.util.lockfile_handler.os.remove')
    @patch('src.util.lockfile_handler.os.path.exists')
    def test_remove_lockfile_handles_missing(
        self,
        mock_exists: MagicMock,
        mock_remove: MagicMock
    ) -> None:
        """
        Verify remove_lockfile handles missing file gracefully.

        WHY: Edge case testing! What if remove_lockfile() is called when
        no lockfile exists? This could happen if:
        1. User manually deleted it
        2. Another process cleaned it up
        3. Filesystem corruption

        We MUST NOT crash - just silently succeed since the end state
        (no lockfile) is what we want anyway.

        Test approach:
        1. Simulate no existing lockfile
        2. Call remove_lockfile()
        3. Verify os.remove() NOT called
        4. Verify no exception raised
        """
        # Arrange
        # WHY: exists=False simulates lockfile already gone
        mock_exists.return_value = False

        # Act - should NOT raise exception
        try:
            remove_lockfile()
            exception_raised = False
        except Exception as e:
            exception_raised = True
            self.fail(f"remove_lockfile raised exception: {e}")

        # Assert - verify no exception occurred
        self.assertFalse(exception_raised)

        # Assert - verify os.remove was NOT called
        # WHY: Attempting to remove a non-existent file would raise FileNotFoundError
        # The exists() check prevents this
        mock_remove.assert_not_called()

    def test_lockfile_path_uses_home_directory(self) -> None:
        """
        Verify LOCKFILE_PATH is constructed using user's home directory.

        WHY: The lockfile must be in a user-writable location. Using
        Path.home() ensures cross-user compatibility on multi-user systems.

        This test verifies the path structure matches the expected pattern:
        <home_dir>/.pawgate/lockfile.lock

        Note: We avoid module reload with mock which causes test pollution.
        """
        from src.util.lockfile_handler import LOCKFILE_PATH

        # Assert - verify path contains expected components
        self.assertIn('.pawgate', LOCKFILE_PATH)
        self.assertIn('lockfile.lock', LOCKFILE_PATH)

        # Verify it uses home directory
        home = str(Path.home())
        self.assertTrue(
            LOCKFILE_PATH.startswith(home),
            f"LOCKFILE_PATH should start with home directory {home}, got {LOCKFILE_PATH}"
        )


if __name__ == '__main__':
    unittest.main()

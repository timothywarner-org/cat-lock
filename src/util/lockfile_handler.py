"""
Lockfile Handler - Enforce single instance of CatLock.

This module ensures only one instance of CatLock runs at a time by using a
lockfile that stores the process ID (PID) of the running instance.

Single instance enforcement strategy:
    1. On startup: Check if lockfile exists
    2. If exists: Read PID, try to terminate that process, create new lockfile
    3. If doesn't exist: Create lockfile with current PID
    4. On shutdown: Remove lockfile

WHY single instance:
    - Multiple instances would register duplicate keyboard hooks (conflicts)
    - Multiple system tray icons confuse users ("which one is running?")
    - Config changes in one instance wouldn't reflect in others
    - Wasted system resources (memory, CPU for duplicate event loops)

Lockfile location:
    ~/.catlock/lockfile.lock (same directory as config)

WHY store PID in lockfile:
    If an old CatLock instance crashed without cleanup, the lockfile remains.
    We try to terminate the old process (gracefully) before starting. If the
    PID is stale (process doesn't exist), we just overwrite the lockfile.

Alternative approaches rejected:
    - Windows mutex: Platform-specific, harder to debug
    - Socket binding: Overkill for this use case
    - Registry key: Doesn't survive crashes cleanly

Edge cases:
    - Lockfile exists but process is dead: We overwrite (stale lockfile)
    - Permission denied: Would crash (rare, indicates system issues)
    - Rapid restart: Old process terminates, new process starts cleanly

See also:
    - main.start(): Calls check_lockfile() at startup
    - main.quit_program(): Calls remove_lockfile() at shutdown
"""

import os
import signal
from pathlib import Path

# Lockfile path in user's home directory
# WHY same directory as config: Keeps all CatLock user data together
home = str(Path.home())
LOCKFILE_PATH = os.path.join(home, '.catlock', 'lockfile.lock')


def check_lockfile():
    """
    Check for existing CatLock instance and create lockfile for current instance.

    This function:
    1. Checks if lockfile exists (indicates another instance is/was running)
    2. If exists, reads PID and attempts to terminate that process
    3. Creates new lockfile with current process's PID

    WHY SIGTERM (graceful termination):
        Gives the old process a chance to clean up (remove keyboard hooks,
        close tray icon, etc.) before exiting. SIGKILL would force immediate
        termination without cleanup, potentially leaving keyboard hooks active.

    WHY silent exception handling:
        If os.kill() fails, the process is likely already dead (stale lockfile).
        This is expected and not an error - we just overwrite the lockfile.
        Possible failure reasons:
        - ProcessLookupError: PID doesn't exist (stale lockfile)
        - PermissionError: PID belongs to different user (rare)
        - Other OSError: System-level issues

    Thread safety:
        Not thread-safe, but called only once from main thread at startup.

    Race condition:
        If two instances start simultaneously, both might read no lockfile
        and both create one. Last writer wins. This is acceptable because:
        - Extremely rare (requires ~1ms timing coincidence)
        - Both instances would still function (keyboard library handles multiple hooks)
        - Worst case: User sees two tray icons briefly, quits one manually

    See also:
        - remove_lockfile(): Cleanup counterpart
        - main.start(): Calls this at startup
    """
    # Check if another instance is (or was) running
    if os.path.exists(LOCKFILE_PATH):
        with open(LOCKFILE_PATH, 'r') as f:
            pid = int(f.read().strip())
            try:
                # Attempt graceful termination of old process
                # WHY SIGTERM: Allows old process to cleanup (unlike SIGKILL)
                os.kill(pid, signal.SIGTERM)
            except Exception as e:
                # Process not found or can't be terminated
                # WHY silent: This is expected if process already exited or crashed
                # Common causes:
                # - Process already terminated normally
                # - Process crashed without cleaning up lockfile
                # - PID reused by different process (very rare)
                pass

    # Create (or overwrite) lockfile with current process ID
    # WHY overwrite: Even if old lockfile exists, we're the new instance now
    with open(LOCKFILE_PATH, 'w') as f:
        f.write(str(os.getpid()))


def remove_lockfile():
    """
    Remove lockfile on clean shutdown.

    Called by quit_program() to allow new instances to start cleanly.

    WHY check existence:
        Defensive programming - avoid FileNotFoundError if lockfile was
        manually deleted or cleanup was already called. Silent no-op is
        better than crashing during shutdown.

    Thread safety:
        Not thread-safe, but only called from main thread during shutdown.

    Edge cases:
        - Lockfile already removed: Silent no-op (exists check prevents error)
        - Permission denied: Would raise PermissionError (rare, indicates system issues)
        - Lockfile locked by another process: Would block or fail (extremely rare)

    See also:
        - check_lockfile(): Startup counterpart
        - main.quit_program(): Calls this during shutdown
    """
    # Remove lockfile if it exists (allow new instances to start)
    # WHY check exists: Defensive programming to avoid FileNotFoundError
    if os.path.exists(LOCKFILE_PATH):
        os.remove(LOCKFILE_PATH)

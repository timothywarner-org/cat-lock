# PawGate Architecture

This document provides a technical deep-dive into PawGate's architecture, threading model, data flow, and key design decisions.

## Table of Contents
- [System Overview](#system-overview)
- [Component Diagram](#component-diagram)
- [Threading Model](#threading-model)
- [Data Flow](#data-flow)
- [Key Design Decisions](#key-design-decisions)
- [Dependencies](#dependencies)
- [Configuration System](#configuration-system)
- [Build and Packaging](#build-and-packaging)

---

## System Overview

PawGate is a Windows-only keyboard locking utility built in Python. It runs as a background system tray application that blocks all keyboard input on demand via a configurable hotkey (default: Ctrl+L).

**Core Capabilities:**
- Global hotkey registration (monitors system-wide key presses)
- Full keyboard input blocking (scan codes 0-255 + named keys)
- Multi-monitor overlay window (Tkinter-based)
- System tray integration (pystray)
- Configuration persistence (JSON file in user directory)
- Single-instance enforcement (lockfile-based)

**Platform Requirements:**
- **Windows only** - Relies on `keyboard` library which uses Windows API hooks
- **Python 3.11+** - Uses modern type hints and standard library features
- **No administrator privileges required** - Uses user-level APIs only

---

## Component Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                           PawGate Application                        │
└─────────────────────────────────────────────────────────────────────┘
         │
         │ Spawns 4 concurrent threads
         ▼
┌────────────────────────────────────────────────────────────────────┐
│  Main Thread (Event Loop)                                          │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │ while program_running:                                       │ │
│  │     if show_overlay_queue not empty:                         │ │
│  │         create OverlayWindow()                               │ │
│  │         overlay.open() → blocks here until unlock            │ │
│  │     sleep(0.1)                                               │ │
│  └──────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────┘
         │                                       ▲
         │ spawns                                │ puts signals
         ▼                                       │
┌─────────────────────┐              ┌───────────────────────────┐
│ Hotkey Thread       │              │ show_overlay_queue        │
│ ─────────────       │              │ (Queue)                   │
│ Listens for hotkey  │──────────────│ Signal: True = show       │
│ (Ctrl+L by default) │   put(True)  │         overlay           │
│                     │              └───────────────────────────┘
│ Uses keyboard lib   │
│ add_hotkey()        │
└─────────────────────┘

         │ spawns
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ Tray Icon Thread (pystray)                                      │
│ ──────────────────                                              │
│ System tray icon with menu:                                     │
│  • Lock Keyboard → puts signal in queue                         │
│  • Enable/Disable Notifications → updates config               │
│  • Set Opacity (5%-90%) → updates config                        │
│  • About → opens browser                                        │
│  • Quit → cleanup and exit                                      │
└─────────────────────────────────────────────────────────────────┘

         │ spawns
         ▼
┌─────────────────────────────────────────────────────────────────┐
│ Pressed Events Handler Thread                                   │
│ ─────────────────────────────────                               │
│ WHY: Workaround for keyboard library bug #223                   │
│ Periodically clears stale pressed key events that persist       │
│ after Windows lock/unlock, which can cause hotkey malfunction   │
│                                                                  │
│ Every 5 seconds: keyboard.stash_state()                         │
└─────────────────────────────────────────────────────────────────┘

Data Flow on Hotkey Press:
───────────────────────────

User presses Ctrl+L
      │
      ▼
Hotkey Thread detects via keyboard.add_hotkey()
      │
      ▼
send_hotkey_signal() → show_overlay_queue.put(True)
      │
      ▼
Main Thread detects queue not empty
      │
      ▼
Creates OverlayWindow(main=self)
      │
      ▼
overlay.open():
  ├─ Calculates geometry across all monitors (screeninfo)
  ├─ Creates Tkinter fullscreen window
  ├─ Calls main.lock_keyboard()
  │    └─ Blocks scan codes 0-255 via keyboard.block_key(i)
  │    └─ Blocks critical named keys (Windows, multimedia)
  │    └─ Sends notification (if enabled)
  ├─ Enters Tkinter mainloop (BLOCKS main thread)
  └─ User clicks mouse → unlock_keyboard() → destroy window → mainloop exits
      │
      ▼
Main thread resumes event loop polling
```

---

## Threading Model

PawGate uses a multi-threaded architecture to handle concurrent concerns:

### Thread 1: Main Thread (Event Loop)

**Purpose:** Application lifecycle management and overlay window spawning.

**Lifecycle:**
1. Initialize configuration, lockfile, threads
2. Enter event loop:
   ```python
   while program_running:
       if not show_overlay_queue.empty():
           show_overlay_queue.get(block=False)
           overlay = OverlayWindow(main=self)
           keyboard.stash_state()
           overlay.open()  # Blocks here until unlocked
       time.sleep(0.1)
   ```
3. Overlay window blocks main thread in Tkinter mainloop
4. When unlocked, window destroyed, loop resumes

**WHY this design?**
- Tkinter requires the main thread (cannot run in daemon thread)
- Polling queue allows responsive hotkey detection
- 0.1s sleep prevents CPU spinning while idle
- Blocking on overlay.open() is intentional - prevents overlapping overlays

### Thread 2: Hotkey Listener Thread (Daemon)

**Purpose:** Monitor global hotkey presses.

**Implementation:**
```python
def hotkey_listener(self) -> None:
    keyboard.add_hotkey(self.main.config.hotkey, self.main.send_hotkey_signal, suppress=True)
    while self.main.listen_for_hotkey:
        time.sleep(1)
    keyboard.unhook_all_hotkeys()
```

**Key Points:**
- Daemon thread (exits when main thread exits)
- Uses `keyboard` library's Windows API hooks
- `suppress=True` prevents hotkey from reaching other apps
- Communicates via queue to decouple from main thread

**WHY daemon thread?**
- Prevents app from hanging if hotkey thread deadlocks
- Automatically cleaned up on process termination
- No need for explicit thread shutdown in most cases

### Thread 3: Tray Icon Thread (Daemon)

**Purpose:** System tray icon and menu.

**Implementation:**
```python
def create_tray_icon(self) -> None:
    TrayIcon(main=self).open()  # Blocks in pystray.Icon.run()
```

**Key Points:**
- Daemon thread (pystray requires its own event loop)
- Menu items use lambdas for dynamic state (checkmarks)
- Direct reference to main thread for callbacks
- Runs `pystray.Icon.run()` which blocks indefinitely

**WHY separate thread?**
- pystray has its own event loop (conflicts with Tkinter's)
- Allows tray menu to respond while overlay is shown
- Keeps main thread free for Tkinter operations

### Thread 4: Pressed Events Handler Thread (Daemon)

**Purpose:** Workaround for keyboard library bug #223.

**Implementation:**
```python
def clear_pressed_events():
    while True:
        time.sleep(5)
        keyboard.stash_state()
```

**WHY this exists?**
The `keyboard` library sometimes retains "pressed" state for keys after Windows lock/unlock events. This causes hotkey detection to fail because the library thinks Ctrl is already pressed. `keyboard.stash_state()` clears this stale state.

**Alternative considered:** Detecting Windows lock events and clearing state only then. Rejected because:
1. Detecting lock events requires additional Windows API hooks
2. Periodic clearing (every 5s) is simpler and reliable
3. Performance impact is negligible

---

## Data Flow

### Lock Sequence (Hotkey → Overlay → Lock)

```
┌───────────────────────────────────────────────────────────────┐
│ 1. User Action: Press Ctrl+L                                 │
└───────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌───────────────────────────────────────────────────────────────┐
│ 2. Hotkey Thread (keyboard library hook)                     │
│    keyboard.add_hotkey('ctrl+l', send_hotkey_signal)          │
└───────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌───────────────────────────────────────────────────────────────┐
│ 3. Signal Transmission                                        │
│    show_overlay_queue.put(True)                               │
└───────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌───────────────────────────────────────────────────────────────┐
│ 4. Main Thread Event Loop                                    │
│    Detects queue not empty, calls:                            │
│    overlay = OverlayWindow(main=self)                         │
│    overlay.open()                                             │
└───────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌───────────────────────────────────────────────────────────────┐
│ 5. Overlay Window Creation (Tkinter)                         │
│    • Query all monitors via screeninfo.get_monitors()         │
│    • Calculate combined geometry (span all displays)          │
│    • Create fullscreen Tk window:                             │
│      - overrideredirect=True (no window border)               │
│      - attributes('-topmost', True) (always on top)           │
│      - attributes('-alpha', opacity) (transparency)           │
│      - bind('<Button-1>', unlock_keyboard) (click to unlock)  │
└───────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌───────────────────────────────────────────────────────────────┐
│ 6. Keyboard Blocking (BEFORE mainloop)                       │
│    lock_keyboard():                                           │
│      for i in range(256):                                     │
│          keyboard.block_key(i)  # Block scan code             │
│      for key_name in critical_keys:                           │
│          keyboard.block_key(key_name)  # Block by name        │
│    send_notification_in_thread(if enabled)                    │
└───────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌───────────────────────────────────────────────────────────────┐
│ 7. Enter Tkinter Mainloop                                    │
│    root.mainloop() → BLOCKS main thread                       │
│    User sees overlay, keyboard is blocked                     │
└───────────────────────────────────────────────────────────────┘
```

### Unlock Sequence (Mouse Click → Unlock)

```
┌───────────────────────────────────────────────────────────────┐
│ 1. User Action: Click anywhere on overlay                    │
└───────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌───────────────────────────────────────────────────────────────┐
│ 2. Tkinter Event Handler                                     │
│    root.bind('<Button-1>', unlock_keyboard)                   │
│    Triggers unlock_keyboard(event)                            │
└───────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌───────────────────────────────────────────────────────────────┐
│ 3. Keyboard Unblocking                                       │
│    for key in blocked_keys:                                   │
│        keyboard.unblock_key(key)                              │
│    blocked_keys.clear()                                       │
│    keyboard.stash_state()  # Clear any pressed state          │
└───────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌───────────────────────────────────────────────────────────────┐
│ 4. Destroy Overlay Window                                    │
│    root.destroy() → Exits mainloop                            │
└───────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌───────────────────────────────────────────────────────────────┐
│ 5. Main Thread Resumes                                       │
│    Event loop continues polling queue                         │
│    Ready for next lock trigger                                │
└───────────────────────────────────────────────────────────────┘
```

---

## Key Design Decisions

### 1. Why Queue-Based Communication?

**Decision:** Use `queue.Queue` to signal overlay show/hide.

**WHY:**
- Thread-safe without manual locking
- Decouples hotkey detection from overlay creation
- Prevents race conditions when multiple threads access shared state
- Standard library, no external dependencies

**Alternative considered:** Shared boolean flag with threading.Lock
- Rejected because: More boilerplate, easy to forget lock, potential deadlocks

### 2. Why Block ALL Scan Codes (0-255)?

**Decision:** Block every scan code instead of just named keys.

**WHY:**
- Multimedia keys (volume, brightness) don't have standard names
- Extended keyboards have F13-F24 which aren't in typical keymaps
- International keyboards have regional keys (e.g., IME toggle on Japanese keyboards)
- Scan code blocking is more comprehensive than named key blocking

**Implementation:**
```python
for i in range(256):
    try:
        keyboard.block_key(i)
        self.blocked_keys.add(i)
    except Exception:
        # Some scan codes may not map to physical keys - that's OK
        pass
```

**Alternative considered:** Only block named keys from a predefined list
- Rejected because: Misses multimedia and regional keys, users reported these still working

### 3. Why Remap Right Ctrl to Left Ctrl?

**Decision:** `keyboard.remap_key('right ctrl', 'left ctrl')` on startup.

**WHY:**
Windows lock/unlock events can cause Right Ctrl to "stick" in pressed state. The keyboard library doesn't properly handle this edge case. Remapping ensures consistent behavior regardless of which Ctrl key is used.

**Discovered via:** Bug report from user who experienced persistent hotkey failure after locking Windows (Win+L).

**Alternative considered:** Fix keyboard library bug upstream
- Rejected because: Library is minimally maintained, workaround is simple and effective

### 4. Why Tkinter for Overlay (Not WPF/Win32)?

**Decision:** Use Tkinter for the fullscreen overlay.

**WHY:**
- Included with Python (no additional dependencies)
- Simple API for fullscreen, transparent, topmost windows
- Cross-platform (if we port to Linux/Mac later)
- Works well with PyInstaller (WPF requires pythonnet, complex build)

**Limitations:**
- Tkinter must run on main thread (blocks during overlay)
- Limited styling capabilities (but we only need solid color + text)

**Alternative considered:** Win32 API via ctypes
- Rejected because: Much more complex, Windows-only, hard to maintain

### 5. Why pystray for System Tray (Not pywin32)?

**Decision:** Use pystray for system tray icon.

**WHY:**
- Pure Python (no C extensions to compile)
- Cross-platform (future Linux/Mac support)
- Clean API for menus with checkmarks and submenus
- Works well with PyInstaller (pywin32 has DLL bundling issues)

**Alternative considered:** pywin32 (direct Windows API access)
- Rejected because: Heavier dependency, Windows-only, harder to build

### 6. Why Single-Instance via Lockfile (Not Mutex)?

**Decision:** Use a PID lockfile at `~/.pawgate/lockfile.lock`.

**WHY:**
- Simple to implement (just file I/O)
- Works across different Python interpreters
- Easy to debug (user can inspect/delete lockfile)
- Handles crashed processes gracefully (we kill old PID on startup)

**Implementation:**
```python
if os.path.exists(LOCKFILE_PATH):
    with open(LOCKFILE_PATH, 'r') as f:
        pid = int(f.read().strip())
        try:
            os.kill(pid, signal.SIGTERM)  # Kill stale process
        except:
            pass  # Already dead
with open(LOCKFILE_PATH, 'w') as f:
    f.write(str(os.getpid()))
```

**Alternative considered:** Windows named mutex
- Rejected because: Requires ctypes/win32, platform-specific, harder to debug

### 7. Why JSON Config (Not TOML/YAML)?

**Decision:** Store config as JSON in `~/.pawgate/config/config.json`.

**WHY:**
- Standard library support (no dependencies)
- Simple structure (only 3 settings)
- Easy for users to edit manually
- Fast to parse

**Limitations:**
- No comments in JSON (but our structure is self-explanatory)
- Verbose for deeply nested data (not a concern for us)

**Alternative considered:** TOML
- Rejected because: Requires external dependency (tomli), overkill for 3 settings

### 8. Why PyInstaller (Not cx_Freeze/Nuitka)?

**Decision:** Use PyInstaller for building standalone executable.

**WHY:**
- Excellent support for bundling data files (icons, config)
- Works well with pystray, keyboard, tkinter
- Simple spec file configuration
- Active community and good documentation

**Build process:**
```bash
pyinstaller --onefile \
    --noconsole \  # No console window (GUI app)
    --icon=icon.ico \
    --add-data="resources/..." \
    --hidden-import plyer.platforms.win.notification \
    src/main.py
```

**Alternative considered:** Nuitka (compiles to C)
- Rejected because: Slower builds, compatibility issues with pystray, harder to debug

---

## Dependencies

### Runtime Dependencies (`requirements.txt`)

| Package | Version | Purpose | Why This Library? |
|---------|---------|---------|-------------------|
| `keyboard` | >=0.13.5 | Global hotkey registration and key blocking | Only library with reliable Windows low-level hooks. **Windows-only limitation.** |
| `pystray` | >=0.19.5 | System tray icon and menu | Pure Python, cross-platform, simple API for menus with checkmarks. |
| `pillow` | >=10.3.0 | Image handling for tray icon | Required by pystray, also useful for future image processing. |
| `plyer` | >=2.1.0 | Windows toast notifications | Cross-platform notification API. Works with Windows 10/11 Action Center. |
| `screeninfo` | >=0.8.1 | Multi-monitor detection | Lightweight, reliable monitor geometry detection across displays. |
| `requests` | >=2.32.3 | HTTP requests (future use) | Included for future update checking or telemetry. Currently unused. |

### Development Dependencies (`requirements-dev.txt`)

| Package | Version | Purpose |
|---------|---------|---------|
| `pytest` | >=8.0.0 | Test runner with modern fixture support |
| `pytest-mock` | >=3.12.0 | Simplified mocking with mocker fixture |
| `pytest-cov` | >=4.1.0 | Coverage reporting integrated with pytest |
| `pytest-timeout` | >=2.2.0 | Prevent hanging tests (critical for GUI/keyboard tests) |

### Build Dependencies

- `pyinstaller` (installed via build.bat, not in requirements.txt)

---

## Configuration System

### File Location

Config stored at: `%USERPROFILE%\.pawgate\config\config.json`

Example path: `C:\Users\Tim\.pawgate\config\config.json`

### Configuration Loading Logic

```python
def load():
    # 1. Check for dev mode flags
    if '--reset-config' in sys.argv or os.environ.get('PAWGATE_DEV'):
        # Delete existing config, copy from bundled defaults
        shutil.copy(bundled_config, user_config)
        return json.load(user_config)

    # 2. Try to load existing user config
    try:
        return json.load(user_config)
    except (FileNotFoundError, json.JSONDecodeError):
        # 3. Config missing or corrupt → copy bundled defaults
        shutil.copy(bundled_config, user_config)
        return json.load(user_config)
```

**WHY this order?**
1. Dev mode overrides prevent personal config from interfering with testing
2. User config takes precedence (allows customization)
3. Bundled config is fallback (always available, even in frozen exe)

### Configuration Schema

```json
{
  "hotkey": "ctrl+l",
  "opacity": 0.3,
  "notificationsEnabled": false
}
```

**Field Descriptions:**

- `hotkey` (string): Key combination in keyboard library format (e.g., "ctrl+shift+alt+f12")
  - Must use lowercase
  - Use `+` as separator
  - Available modifiers: `ctrl`, `shift`, `alt`, `windows`

- `opacity` (float): Overlay transparency (0.05 to 0.9)
  - 0.05 = Nearly transparent (5% opaque)
  - 0.9 = Nearly opaque (90% opaque)
  - Applied via Tkinter: `root.attributes('-alpha', opacity)`

- `notificationsEnabled` (boolean): Show Windows toast notification on lock
  - `true` = Show notification
  - `false` = Silent lock

### Configuration Persistence

Changes made via system tray menu are saved immediately:

```python
def set_opacity(self, opacity: float) -> None:
    self.main.config.opacity = opacity
    self.main.config.save()  # Immediately write to file
```

**WHY immediate save?**
- Prevents config loss if app crashes
- User sees changes reflected in file immediately
- No need for "Apply" button

---

## Build and Packaging

### PyInstaller Spec File

The `PawGate.spec` file controls the build:

```python
# Key options:
a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('resources/img/icon.ico', 'resources/img'),
        ('resources/img/icon.png', 'resources/img'),
        ('resources/config/config.json', 'resources/config'),
    ],
    hiddenimports=['plyer.platforms.win.notification'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PawGate',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # UPX compression (smaller exe)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['resources/img/icon.ico'],
)
```

### Resource Path Handling

**Problem:** PyInstaller extracts files to temporary folder (`sys._MEIPASS`) at runtime.

**Solution:** Utility function to handle both dev and frozen modes:

```python
def get_packaged_path(relative_path: str) -> str:
    """Resolve path to bundled resource (works in dev and frozen exe)."""
    if getattr(sys, 'frozen', False):
        # Running as PyInstaller executable
        base_path = sys._MEIPASS
    else:
        # Running as Python script
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)
```

**Usage:**
```python
icon_path = get_packaged_path("resources/img/icon.png")
image = Image.open(icon_path)
```

### Build Process

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install pyinstaller
   ```

2. **Build executable:**
   ```bash
   pyinstaller PawGate.spec
   ```

3. **Output:**
   - Executable: `dist/PawGate.exe` (~15 MB)
   - Build artifacts: `build/` (can be deleted)

4. **Testing:**
   ```bash
   dist/PawGate.exe
   ```

### Common Build Issues

**Issue 1: Missing icon in exe**
- Cause: Icon path wrong in spec file
- Fix: Verify `--add-data` paths match actual file locations

**Issue 2: plyer notifications don't work**
- Cause: Missing hidden import
- Fix: Add `--hidden-import plyer.platforms.win.notification`

**Issue 3: Exe crashes on startup**
- Cause: Missing data file (config.json, icon.png)
- Fix: Check `datas` list in spec file, ensure semicolon separator

**Issue 4: SmartScreen blocks exe**
- Cause: Unsigned executable from internet
- Fix: Build locally (SmartScreen only blocks downloads) or code-sign with certificate

---

## Future Architecture Considerations

### For YOLOv8 Cat Detection (Planned)

When adding cat detection, the architecture will need:

1. **New Thread:** Camera capture thread
   - Continuously read frames from webcam
   - Put frames in processing queue

2. **New Thread:** Detection thread
   - Read frames from queue
   - Run YOLOv8 inference
   - Signal main thread on cat detection

3. **Updated Main Thread:**
   - Listen for detection signals
   - Auto-lock when cat detected (with cooldown)

4. **New Config Options:**
   - `enableCatDetection` (boolean)
   - `detectionConfidenceThreshold` (float 0.0-1.0)
   - `lockCooldownSeconds` (int)

**Architectural Impact:**
- More complex threading (5-6 threads instead of 4)
- Need for thread-safe frame queue
- Increased memory usage (video frames are large)
- Performance tuning (YOLOv8n on CPU vs GPU)

### For PowerToys Integration (C# Port)

See `PORTING.md` for detailed C# migration guide.

**Key architectural changes needed:**
- Replace threading with async/await (C# best practice)
- Replace pystray with System.Windows.Forms.NotifyIcon
- Replace Tkinter with WPF or WinUI overlay
- Replace keyboard library with Windows low-level hooks
- Integrate with PowerToys settings UI

---

## Conclusion

PawGate's architecture prioritizes:
1. **Simplicity** - Easy to understand, maintain, and extend
2. **Reliability** - Graceful error handling, defensive programming
3. **Responsiveness** - Non-blocking UI, fast hotkey response
4. **Platform Integration** - Feels like a native Windows app

The multi-threaded design cleanly separates concerns (hotkey monitoring, tray UI, overlay display) while using thread-safe communication (queues) to prevent race conditions.

For questions or architectural discussions, see GitHub Issues or Discussions.

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PawGate is a Windows-only keyboard locking utility that prevents accidental input (e.g., from pets). It runs in the system tray and uses a hotkey (default: Ctrl+L) to toggle keyboard lock. When locked, a semi-transparent overlay appears across all monitors. Unlocking is via mouse click or pressing the hotkey again.

**Future goal**: Port to C# for potential inclusion in Microsoft PowerToys (see PORTING.md).

## Build Commands

```batch
# Build executable (uses PyInstaller)
build.bat

# Manual build
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --onefile --add-data="./resources/img/icon.ico;./resources/img/" --add-data="./resources/img/icon.png;./resources/img/" --add-data="./resources/config/config.json;./resources/config/" --icon="./resources/img/icon.ico" --hidden-import plyer.platforms.win.notification --noconsole --name="PawGate" "./src/main.py"
```

Output: `dist/PawGate.exe`

## Run During Development

```bash
python src/main.py
```

Note: Must run from repository root directory due to relative resource paths.

## Architecture

### Core Components

**PawGateCore** (`src/main.py`):
- Main application class and entry point
- Manages application lifecycle with a main event loop polling `show_overlay_queue`
- Coordinates keyboard blocking (scan codes 0-255 plus named critical keys via `keyboard.block_key()`)
- Uses lockfile (`~/.pawgate/lockfile.lock`) to ensure single instance

**Threading Model**:
- Main thread: Event loop checking queue, spawns overlay windows
- Hotkey listener thread: Monitors configured hotkey, puts signals in queue
- Pressed events handler thread: Workaround for keyboard library bug after Windows lock/unlock
- Tray icon thread: Runs pystray icon/menu

### Key Modules

| Module | Purpose |
|--------|---------|
| `src/config/config.py` | JSON config from `~/.pawgate/config/config.json`; falls back to bundled defaults |
| `src/keyboard_controller/hotkey_listener.py` | Registers hotkey with `keyboard` library |
| `src/keyboard_controller/pressed_events_handler.py` | Clears stale pressed events (fixes keyboard library issue #223) |
| `src/ui/overlay_window.py` | Tkinter full-screen transparent overlay spanning all monitors |
| `src/os_controller/tray_icon.py` | System tray with pystray; menu for settings |
| `src/os_controller/notifications.py` | Windows toast notifications via plyer |
| `src/util/path_util.py` | Handles PyInstaller's `sys._MEIPASS` for bundled resources |

### Configuration

Config stored at `~/.pawgate/config/config.json`:
```json
{"hotkey": "ctrl+l", "opacity": 0.3, "notificationsEnabled": false}
```

Default hotkey changed from Ctrl+Shift+Alt+F12 to Ctrl+L for better usability.

## Dependencies

- `keyboard`: Low-level keyboard hooks (Windows-focused)
- `pystray`: System tray icon
- `pillow`: Image handling for tray icon
- `plyer`: Cross-platform notifications
- `screeninfo`: Multi-monitor detection
- `requests`: HTTP requests (update checking removed)

## Development Environment

```bash
# Create and activate venv
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run
python src/main.py
```

## Known Limitations

- Windows only (keyboard library limitation)
- OS-bound hotkeys (e.g., Ctrl+Alt+Del) cannot be blocked
- Right Ctrl remapped to Left Ctrl as workaround for sticky key issue

## Documentation Files

- **README.md** - Project overview, installation, feature roadmap
- **USAGE.md** - End-user guide (hotkeys, troubleshooting, FAQs)
- **CONTRIBUTING.md** - Developer setup, code style, testing, PR process
- **ARCHITECTURE.md** - Technical deep-dive (threading, data flow, design decisions)
- **PORTING.md** - C# port guide for PowerToys integration
- **CLAUDE.md** - This file (quick reference for AI assistance)

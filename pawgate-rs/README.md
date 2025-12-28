# PawGate (Rust)

<p align="center">
  <img src="resources/pawgate.png" alt="PawGate Icon" width="128" height="128">
</p>

<p align="center">
  <strong>A fast, lightweight Windows keyboard locker written in Rust.</strong><br>
  Prevents accidental keyboard input from pets walking across your keyboard.
</p>

<p align="center">
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-default-keybind">Default Keybind</a> •
  <a href="#-features">Features</a> •
  <a href="#-installation">Installation</a> •
  <a href="#-usage">Usage</a>
</p>

---

## Default Keybind

| Action | Keybind |
|--------|---------|
| **Lock/Unlock Keyboard** | `Ctrl + B` |

Press `Ctrl+B` to lock. Press `Ctrl+B` again to unlock. That's it!

> The keybind is configurable via the Settings dialog (right-click tray icon → Settings)

---

## Quick Start

### Option 1: Download Pre-built Binary

Download `pawgate.exe` from the [Releases](https://github.com/timothywarner-org/pawgate/releases) page and run it.

### Option 2: Build from Source (5 minutes)

```powershell
# 1. Install Rust (if not already installed)
winget install Rustlang.Rustup

# 2. Restart your terminal, then:
git clone https://github.com/timothywarner-org/pawgate.git
cd pawgate/pawgate-rs
cargo build --release

# 3. Run it!
.\target\release\pawgate.exe
```

Look for the **paw icon** in your system tray (bottom-right, near the clock).

---

## Features

### Core Functionality
- **Single hotkey toggle** - Press `Ctrl+B` to lock/unlock (configurable)
- **Visual overlay** - Semi-transparent colored overlay when locked
- **Multi-monitor support** - Overlay spans all connected displays
- **System tray** - Runs quietly in the background

### Keyboard Blocking
When locked, PawGate blocks:
- Letters (A-Z) and numbers (0-9)
- Function keys (F1-F24)
- Numpad keys (0-9, +, -, *, /, .)
- Laptop media keys (volume, brightness, play/pause)
- Browser keys (back, forward, refresh)
- Navigation keys (arrows, Home, End, Page Up/Down)
- Special keys (Tab, Enter, Backspace, Delete, Insert)

**Cannot be blocked** (Windows security):
- `Ctrl+Alt+Del`
- `Win+L` (lock screen)

### Customization
- **Hotkey** - Any modifier+key combination
- **Opacity** - 10% to 90% transparency
- **Overlay color** - 6 colorblind-friendly presets
- **Notifications** - Optional toast notifications

### Technical Highlights
- **~2-3 MB** standalone executable (vs ~15MB Python version)
- **<100ms** startup time
- **~5 MB** RAM usage
- **No runtime dependencies** - single .exe file
- **No installer needed** - just run it

---

## Installation

### Windows (Primary Platform)

See [INSTALL.md](INSTALL.md) for detailed instructions, including:
- Step-by-step Rust installation
- Visual Studio Build Tools setup
- Troubleshooting common issues

**TL;DR:**
```powershell
winget install Rustlang.Rustup
# Restart terminal
git clone https://github.com/timothywarner-org/pawgate.git
cd pawgate/pawgate-rs
cargo build --release
```

### macOS / Linux (Cross-Compilation)

You can build the Windows executable from macOS or Linux. See [INSTALL.md](INSTALL.md) for cross-compilation instructions.

Note: PawGate only **runs** on Windows (uses Win32 APIs).

---

## Usage

### Starting PawGate

```powershell
.\pawgate.exe
```

A paw icon appears in your system tray.

### Locking the Keyboard

1. Press `Ctrl+B`
2. Screen shows semi-transparent overlay with "Keyboard Locked" message
3. All keyboard input is blocked (except the unlock hotkey)

### Unlocking the Keyboard

1. Press `Ctrl+B` again
2. Overlay disappears
3. Keyboard works normally

### System Tray Menu

Right-click the paw icon:

| Option | Description |
|--------|-------------|
| **Lock/Unlock Keyboard** | Toggle lock state |
| **Settings...** | Open configuration dialog |
| **Exit** | Close PawGate |

### Settings Dialog

Access via tray menu → Settings:

| Setting | Description | Default |
|---------|-------------|---------|
| **Hotkey** | Key combination for toggle | `ctrl+b` |
| **Opacity** | Overlay transparency (10-90%) | 30% |
| **Overlay Color** | Background color when locked | Forest Green |
| **Notifications** | Show toast notifications | Enabled |

> Note: Changing the hotkey requires restarting PawGate.

### Configuration File

Settings are stored at:
```
%USERPROFILE%\.pawgate\config.json
```

Example:
```json
{
  "hotkey": "ctrl+b",
  "opacity": 0.3,
  "notifications_enabled": true,
  "overlay_color": "#1B5E20"
}
```

---

## Hotkey Format

### Modifiers

| Modifier | Aliases |
|----------|---------|
| Control | `ctrl`, `control` |
| Alt | `alt` |
| Shift | `shift` |
| Windows | `win`, `windows` |

### Keys

| Type | Examples |
|------|----------|
| Letters | `a` through `z` |
| Numbers | `0` through `9` |
| Function | `f1` through `f24` |
| Special | `space`, `enter`, `escape`, `tab`, `backspace` |
| Navigation | `home`, `end`, `pageup`, `pagedown`, `up`, `down`, `left`, `right` |
| Other | `insert`, `delete`, `pause`, `printscreen`, `numlock`, `scrolllock` |

### Examples

| Hotkey String | Keys to Press |
|---------------|---------------|
| `ctrl+b` | Ctrl + B |
| `ctrl+shift+l` | Ctrl + Shift + L |
| `alt+f12` | Alt + F12 |
| `ctrl+alt+p` | Ctrl + Alt + P |
| `win+pause` | Windows + Pause |

---

## Project Structure

```
pawgate-rs/
├── src/
│   ├── main.rs              # Entry point, app lifecycle
│   ├── config.rs            # JSON config, hotkey parsing
│   ├── keyboard.rs          # Win32 low-level keyboard hook
│   ├── overlay.rs           # Transparent fullscreen window
│   ├── tray.rs              # System tray icon and menu
│   └── settings_dialog.rs   # Native Windows settings dialog
├── resources/
│   ├── pawgate.ico          # Multi-resolution Windows icon
│   ├── pawgate.png          # PNG version (256x256)
│   ├── pawgate.rc           # Windows resource script
│   ├── pawgate.manifest     # DPI awareness, modern controls
│   └── generate_icon.py     # Python script to regenerate icon
├── Cargo.toml               # Dependencies and build config
├── build.rs                 # Embeds Windows resources
├── build.bat                # Windows build helper script
├── README.md                # This file
├── INSTALL.md               # Detailed installation guide
├── DEVELOPMENT.md           # Contributor guide
└── ROADMAP.md               # Planned features
```

---

## Dependencies

| Crate | Purpose |
|-------|---------|
| `windows` | Official Microsoft Win32 API bindings |
| `tray-icon` | Cross-platform system tray |
| `muda` | Menu abstractions |
| `serde` / `serde_json` | Configuration serialization |
| `single-instance` | Prevent multiple instances |
| `dirs` | Cross-platform home directory |
| `log` / `env_logger` | Logging (debug builds) |
| `image` | Icon handling |

---

## Comparison: Rust vs Python

| Metric | Python Version | Rust Version |
|--------|----------------|--------------|
| Binary size | ~15 MB | ~2-3 MB |
| Startup time | ~2 seconds | <100 ms |
| Memory usage | ~50 MB | ~5 MB |
| Runtime deps | Python + packages | None |
| Build tool | PyInstaller | cargo |
| Build time | ~30 seconds | ~60 seconds (first) |

---

## Known Limitations

| Limitation | Reason |
|------------|--------|
| Windows only | Uses Win32 keyboard hooks |
| Can't block `Ctrl+Alt+Del` | Windows security feature |
| Can't block `Win+L` | Windows security feature |
| Hotkey change needs restart | Hook registered at startup |

---

## Auto-Start on Windows Boot

### Method 1: Startup Folder

1. Press `Win+R`
2. Type `shell:startup` and press Enter
3. Copy `pawgate.exe` or create a shortcut here

### Method 2: PowerShell Script

```powershell
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\PawGate.lnk")
$Shortcut.TargetPath = "C:\Path\To\pawgate.exe"
$Shortcut.Save()
```

### Method 3: Task Scheduler

1. Open Task Scheduler
2. Create Basic Task → Name: "PawGate"
3. Trigger: "When I log on"
4. Action: "Start a program" → Browse to `pawgate.exe`
5. Finish

---

## License

MIT License - See [LICENSE](../LICENSE) file

---

## Credits

- Rust implementation by PawGate Contributors
- Original Python version: [PawGate](https://github.com/timothywarner-org/pawgate)
- Colorblind-friendly color scheme based on accessibility research

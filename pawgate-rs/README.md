# PawGate (Rust)

A fast, lightweight Windows keyboard locker written in Rust. Prevents accidental keyboard input from pets walking across your keyboard.

## Features

- **Single hotkey toggle** - Press `Ctrl+B` (configurable) to lock/unlock
- **Full keyboard blocking** - Blocks all keys including:
  - Standard alphanumeric keys
  - Function keys (F1-F24)
  - Numpad keys
  - Laptop media/function keys
  - Browser navigation keys
- **Visual overlay** - Semi-transparent overlay across all monitors when locked
- **System tray** - Minimal footprint, runs in background
- **Settings dialog** - Configure hotkey, opacity, overlay color
- **Colorblind-friendly** - High-contrast blue/orange icon visible to all color vision types
- **Small binary** - ~2-3MB standalone executable
- **No runtime dependencies** - Single .exe, no installers needed

## Requirements

- Windows 10 or later (Windows 7/8.1 supported but not tested)
- 64-bit system recommended

## Building

### Prerequisites

1. Install Rust: https://rustup.rs
2. Windows SDK (comes with Visual Studio Build Tools)

### Build

```batch
# Debug build
cargo build

# Release build (optimized, smaller)
cargo build --release
```

Or use the build script:
```batch
build.bat
```

Output: `target/release/pawgate.exe`

### Regenerating the Icon

If you need to regenerate the icon:
```batch
cd resources
python generate_icon.py
```

Requires Python with Pillow: `pip install pillow`

## Usage

1. Run `pawgate.exe`
2. Look for the paw icon in your system tray
3. Press `Ctrl+B` to lock the keyboard
4. A semi-transparent overlay appears showing "Keyboard Locked"
5. Press `Ctrl+B` again to unlock

### System Tray Menu

Right-click the tray icon for:
- **Lock/Unlock Keyboard** - Toggle lock state
- **Settings** - Open configuration dialog
- **Exit** - Close PawGate

### Settings

- **Hotkey** - Key combination to toggle lock (e.g., `ctrl+b`, `ctrl+shift+l`)
- **Opacity** - Overlay transparency (10-90%)
- **Overlay Color** - Choose from colorblind-friendly presets
- **Notifications** - Enable/disable toast notifications

Configuration stored at: `~/.pawgate/config.json`

## Hotkey Format

Hotkeys are specified as modifier+key combinations:

**Modifiers:**
- `ctrl` or `control`
- `alt`
- `shift`
- `win` or `windows`

**Keys:**
- Letters: `a` through `z`
- Numbers: `0` through `9`
- Function keys: `f1` through `f24`
- Special: `space`, `enter`, `escape`, `tab`, `backspace`, etc.

**Examples:**
- `ctrl+b` - Control + B
- `ctrl+shift+l` - Control + Shift + L
- `alt+f12` - Alt + F12
- `ctrl+alt+p` - Control + Alt + P

## Architecture

```
pawgate-rs/
├── src/
│   ├── main.rs              # Application entry point
│   ├── config.rs            # Configuration management
│   ├── keyboard.rs          # Low-level keyboard hook
│   ├── overlay.rs           # Transparent overlay window
│   ├── tray.rs              # System tray icon/menu
│   └── settings_dialog.rs   # Settings configuration dialog
├── resources/
│   ├── pawgate.ico          # Application icon
│   ├── pawgate.rc           # Windows resources
│   ├── pawgate.manifest     # Application manifest
│   └── generate_icon.py     # Icon generator script
├── Cargo.toml               # Rust dependencies
├── build.rs                 # Build script for resources
└── build.bat                # Windows build helper
```

## Key Dependencies

- `windows` - Official Microsoft Windows API bindings
- `tray-icon` - Cross-platform system tray
- `muda` - Menu abstractions
- `serde`/`serde_json` - Configuration serialization
- `single-instance` - Prevent multiple instances

## Comparison with Python Version

| Feature | Python | Rust |
|---------|--------|------|
| Binary size | ~15MB | ~2-3MB |
| Startup time | ~2s | <100ms |
| Memory usage | ~50MB | ~5MB |
| Runtime deps | Python, packages | None |
| Build complexity | PyInstaller | cargo build |

## Known Limitations

- **Windows only** - Uses Win32 keyboard hooks
- **OS-level keys** - Cannot block `Ctrl+Alt+Del`, `Win+L`
- **Hotkey restart** - Changing hotkey requires restart

## License

MIT License - See LICENSE file

## Credits

Rust implementation inspired by the original Python PawGate project.

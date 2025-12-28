# PawGate Rust - Development Guide

Guide for contributors and developers who want to modify or extend PawGate.

## Table of Contents

- [Development Setup](#development-setup)
- [Project Architecture](#project-architecture)
- [Key Concepts](#key-concepts)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Debugging](#debugging)
- [Code Style](#code-style)
- [Contributing](#contributing)

---

## Development Setup

### Prerequisites

1. **Rust toolchain** (stable)
   ```powershell
   winget install Rustlang.Rustup
   rustup default stable
   ```

2. **Visual Studio Build Tools** with "Desktop development with C++"

3. **Git** for version control

4. **VS Code** (recommended) with extensions:
   - rust-analyzer
   - CodeLLDB (for debugging)
   - Even Better TOML

### Clone and Build

```powershell
git clone https://github.com/timothywarner-org/pawgate.git
cd pawgate/pawgate-rs

# Debug build (faster compile, includes debug symbols)
cargo build

# Check for errors without building
cargo check

# Run in debug mode
cargo run
```

### IDE Setup (VS Code)

Create `.vscode/settings.json`:
```json
{
    "rust-analyzer.cargo.features": "all",
    "rust-analyzer.checkOnSave.command": "clippy"
}
```

Create `.vscode/launch.json` for debugging:
```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "type": "lldb",
            "request": "launch",
            "name": "Debug PawGate",
            "cargo": {
                "args": ["build", "--bin=pawgate"],
                "filter": {
                    "name": "pawgate",
                    "kind": "bin"
                }
            },
            "args": [],
            "cwd": "${workspaceFolder}"
        }
    ]
}
```

---

## Project Architecture

### Module Overview

```
src/
├── main.rs           # Entry point, AppState, thread coordination
├── config.rs         # Configuration loading/saving, hotkey parsing
├── keyboard.rs       # Low-level keyboard hook (WH_KEYBOARD_LL)
├── overlay.rs        # Transparent overlay window (Win32)
├── tray.rs           # System tray icon and menu
└── settings_dialog.rs # Native Windows settings dialog
```

### Data Flow

```
┌─────────────────┐     ┌─────────────────┐
│  Keyboard Hook  │────→│   AppState      │
│    Thread       │     │  (AtomicBool)   │
└─────────────────┘     └────────┬────────┘
                                 │
                                 ↓
┌─────────────────┐     ┌─────────────────┐
│   Tray Icon     │←────│   Main Thread   │
│    Thread       │     │  (Event Loop)   │
└─────────────────┘     └────────┬────────┘
                                 │
                                 ↓
                        ┌─────────────────┐
                        │ Overlay Window  │
                        └─────────────────┘
```

### Threading Model

| Thread | Purpose | Location |
|--------|---------|----------|
| Main | Tray icon, overlay management, Windows messages | `tray.rs` |
| Keyboard | Low-level keyboard hook message loop | `keyboard.rs` |

### Shared State

The `AppState` struct uses atomics for thread-safe state sharing:

```rust
pub struct AppState {
    pub locked: AtomicBool,      // Is keyboard locked?
    pub should_quit: AtomicBool, // Signal to exit
    pub show_settings: AtomicBool, // Open settings dialog
}
```

---

## Key Concepts

### Low-Level Keyboard Hook

PawGate uses `SetWindowsHookExW` with `WH_KEYBOARD_LL` to intercept keyboard events:

```rust
// keyboard.rs
SetWindowsHookExW(WH_KEYBOARD_LL, Some(keyboard_hook_proc), None, 0)
```

The hook callback receives all keyboard events before they reach applications:

```rust
unsafe extern "system" fn keyboard_hook_proc(
    code: i32,
    wparam: WPARAM,   // WM_KEYDOWN, WM_KEYUP, etc.
    lparam: LPARAM,   // Pointer to KBDLLHOOKSTRUCT
) -> LRESULT {
    // Return LRESULT(1) to block the key
    // Call CallNextHookEx to pass it through
}
```

### Layered Windows

The overlay uses layered windows for transparency:

```rust
// overlay.rs
CreateWindowExW(
    WS_EX_LAYERED | WS_EX_TOPMOST | WS_EX_TOOLWINDOW | WS_EX_TRANSPARENT,
    // ...
);

SetLayeredWindowAttributes(hwnd, COLORREF(0), opacity, LWA_ALPHA);
```

### Thread-Local Storage

Hook callbacks can't capture closures, so we use thread-local storage:

```rust
thread_local! {
    static HOOK_STATE: RefCell<Option<HookState>> = RefCell::new(None);
}
```

---

## Making Changes

### Adding a New Setting

1. **Add field to Config** (`config.rs`):
   ```rust
   pub struct Config {
       pub hotkey: String,
       pub opacity: f32,
       pub new_setting: bool,  // Add here
   }
   ```

2. **Update Default** (`config.rs`):
   ```rust
   impl Default for Config {
       fn default() -> Self {
           Self {
               // ...
               new_setting: false,
           }
       }
   }
   ```

3. **Add UI control** (`settings_dialog.rs`):
   - Add control ID constant
   - Create control in `create_dialog_controls()`
   - Read value in `gather_dialog_values()`

### Adding a New Hotkey Action

1. **Add state flag** (`main.rs`):
   ```rust
   pub struct AppState {
       pub new_action: AtomicBool,
   }
   ```

2. **Detect in hook** (`keyboard.rs`):
   ```rust
   if is_new_hotkey_pressed {
       hook_state.state.new_action.store(true, Ordering::SeqCst);
   }
   ```

3. **Handle in main loop** (`tray.rs`):
   ```rust
   if state.new_action.load(Ordering::SeqCst) {
       // Perform action
       state.new_action.store(false, Ordering::SeqCst);
   }
   ```

### Modifying the Overlay

The overlay is a simple Win32 window. To change appearance:

1. **Color/opacity**: Modify `Config` and `SetLayeredWindowAttributes`
2. **Text**: Modify `WM_PAINT` handler in `overlay.rs`
3. **Shape**: Modify window creation flags or add regions

---

## Testing

### Manual Testing

```powershell
# Run debug build with logging
$env:RUST_LOG = "debug"
cargo run
```

### Test Checklist

- [ ] Hotkey locks keyboard
- [ ] Hotkey unlocks keyboard
- [ ] Overlay appears on all monitors
- [ ] Tray icon appears
- [ ] Tray menu works
- [ ] Settings dialog opens
- [ ] Settings save correctly
- [ ] Only one instance runs
- [ ] All key types blocked (letters, numpad, function keys)
- [ ] Modifier keys allow hotkey to work

### Unit Tests (Future)

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_hotkey() {
        assert_eq!(parse_hotkey("ctrl+b"), Some((MOD_CONTROL, 'B' as u32)));
        assert_eq!(parse_hotkey("ctrl+shift+f12"), Some((MOD_CONTROL | MOD_SHIFT, VK_F12)));
    }

    #[test]
    fn test_config_default() {
        let config = Config::default();
        assert_eq!(config.hotkey, "ctrl+b");
        assert_eq!(config.opacity, 0.3);
    }
}
```

Run tests:
```powershell
cargo test
```

---

## Debugging

### Enable Logging

```powershell
# PowerShell
$env:RUST_LOG = "debug"
cargo run

# Or trace level for verbose output
$env:RUST_LOG = "trace"
cargo run
```

### Debug in VS Code

1. Install CodeLLDB extension
2. Set breakpoints in code
3. Press F5 to start debugging

### Common Issues

**Hook not receiving events:**
- Ensure message loop is running (`GetMessageW` or `PeekMessageW`)
- Check hook was installed successfully

**Overlay not appearing:**
- Check `ShowWindow` is called
- Verify window position spans monitors correctly
- Check `WS_EX_LAYERED` flag is set

**Settings not saving:**
- Check file permissions for `~/.pawgate/`
- Verify JSON serialization is correct

---

## Code Style

### Rust Guidelines

- Use `rustfmt` for formatting: `cargo fmt`
- Use `clippy` for lints: `cargo clippy`
- Follow Rust naming conventions (snake_case for functions, CamelCase for types)

### Documentation

- Add `///` doc comments to public functions
- Explain "why" not just "what"
- Include examples for complex functions

### Error Handling

- Use `Result` for fallible operations
- Provide context with error messages
- Don't panic in library code

### Safety

- Minimize `unsafe` blocks
- Document safety requirements
- Use safe abstractions where possible

---

## Contributing

### Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make changes
4. Run checks: `cargo fmt && cargo clippy && cargo test`
5. Commit with descriptive message
6. Push and create PR

### Commit Messages

```
Add feature X for Y purpose

- Detailed description of changes
- Why this approach was chosen
- Any breaking changes
```

### Pull Request Guidelines

- One feature/fix per PR
- Include tests if applicable
- Update documentation
- Ensure CI passes

---

## Useful Resources

### Rust

- [The Rust Book](https://doc.rust-lang.org/book/)
- [Rust by Example](https://doc.rust-lang.org/rust-by-example/)
- [Rustlings](https://github.com/rust-lang/rustlings) (exercises)

### Windows API

- [windows-rs documentation](https://microsoft.github.io/windows-docs-rs/)
- [Win32 API docs](https://learn.microsoft.com/en-us/windows/win32/)
- [Keyboard hooks](https://learn.microsoft.com/en-us/windows/win32/winmsg/about-hooks)

### Crates

- [tray-icon](https://docs.rs/tray-icon)
- [muda](https://docs.rs/muda)
- [serde](https://serde.rs/)

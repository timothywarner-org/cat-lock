# PawGate Rust - Roadmap

What's implemented, what's missing, and what would make this awesome.

---

## Current Status: v1.0 (MVP)

### Implemented

| Feature | Status | Notes |
|---------|--------|-------|
| Hotkey toggle (Ctrl+B) | Done | Configurable |
| Keyboard blocking | Done | All keys including numpad, F-keys, media |
| Visual overlay | Done | Semi-transparent, multi-monitor |
| System tray icon | Done | Colorblind-friendly |
| Tray context menu | Done | Lock/Settings/Exit |
| Settings dialog | Done | Hotkey, opacity, color, notifications |
| Configuration persistence | Done | JSON at ~/.pawgate/ |
| Single instance | Done | Prevents duplicates |
| DPI awareness | Done | Manifest configured |

---

## What's Missing (To Make This Awesome)

### Priority 1: Essential Improvements

| Feature | Difficulty | Impact | Description |
|---------|------------|--------|-------------|
| **Hot-reload hotkey** | Medium | High | Change hotkey without restart |
| **Toast notifications** | Easy | Medium | Show "Locked"/"Unlocked" toasts |
| **Sound feedback** | Easy | Medium | Optional beep on lock/unlock |
| **Animated tray icon** | Medium | Low | Different icon when locked vs unlocked |
| **Mouse blocking option** | Medium | Medium | Optionally block mouse clicks too |

### Priority 2: Quality of Life

| Feature | Difficulty | Impact | Description |
|---------|------------|--------|-------------|
| **Installer (MSI/MSIX)** | Medium | High | Professional installation experience |
| **Auto-update** | Hard | High | Check for updates, download new version |
| **Hotkey recording** | Medium | High | Press keys to set hotkey instead of typing |
| **Multiple profiles** | Medium | Medium | Different settings for different situations |
| **Scheduled lock** | Medium | Low | Auto-lock after X minutes idle |
| **Password unlock** | Medium | Medium | Require password instead of hotkey |

### Priority 3: Advanced Features

| Feature | Difficulty | Impact | Description |
|---------|------------|--------|-------------|
| **Application whitelist** | Hard | Medium | Don't block in specific apps |
| **Emergency unlock** | Medium | High | Backup unlock method if hotkey fails |
| **Remote unlock** | Hard | Low | Unlock from phone/web |
| **Statistics** | Easy | Low | Track how many keys blocked |
| **Custom overlay image** | Easy | Low | Use custom image as overlay |
| **Overlay animations** | Medium | Low | Fade in/out effects |

### Priority 4: Developer Experience

| Feature | Difficulty | Impact | Description |
|---------|------------|--------|-------------|
| **GitHub Actions CI** | Easy | High | Automated builds on push |
| **Automated releases** | Medium | High | Build and publish releases |
| **Unit tests** | Medium | High | Test hotkey parsing, config |
| **Integration tests** | Hard | Medium | Test actual keyboard blocking |
| **Code coverage** | Easy | Low | Track test coverage |
| **Benchmarks** | Medium | Low | Performance testing |

---

## Feature Details

### Hot-Reload Hotkey

Currently, changing the hotkey requires restarting PawGate because the hook is registered at startup.

**Solution:**
1. Add hotkey change detection in tray event loop
2. Signal keyboard thread to re-register hook
3. Use channel to communicate new hotkey

```rust
// In tray.rs - after settings save
if config.hotkey != old_config.hotkey {
    hotkey_sender.send(config.hotkey.clone())?;
}

// In keyboard.rs - check channel periodically
if let Ok(new_hotkey) = hotkey_receiver.try_recv() {
    // Re-parse and update thread-local state
}
```

### Toast Notifications

Windows 10+ supports toast notifications. Could use `winrt` or `windows` crate:

```rust
use windows::UI::Notifications::*;

fn show_notification(title: &str, body: &str) {
    // Use ToastNotificationManager
}
```

Or simpler: use `notify-rust` crate.

### Sound Feedback

Simple beep using Windows API:

```rust
use windows::Win32::System::SystemServices::Beep;

fn play_lock_sound() {
    unsafe { Beep(800, 100); }  // 800 Hz for 100ms
}
```

Or play a WAV file with `PlaySoundW`.

### Animated Tray Icon

Switch icon based on lock state:

```rust
// In tray.rs
if current_locked != prev_locked {
    let new_icon = if current_locked {
        create_locked_icon()   // Red paw
    } else {
        create_unlocked_icon() // Blue paw
    };
    tray_icon.set_icon(Some(new_icon))?;
}
```

### Mouse Blocking

Add low-level mouse hook alongside keyboard hook:

```rust
SetWindowsHookExW(WH_MOUSE_LL, Some(mouse_hook_proc), None, 0)

unsafe extern "system" fn mouse_hook_proc(...) -> LRESULT {
    if is_locked && config.block_mouse {
        return LRESULT(1);  // Block
    }
    CallNextHookEx(None, code, wparam, lparam)
}
```

### Hotkey Recording

Replace text input with a button that captures keystrokes:

1. Add "Record" button next to hotkey field
2. When clicked, capture next key combination
3. Display captured hotkey in text field

```rust
// In settings_dialog.rs
static RECORDING: AtomicBool = AtomicBool::new(false);

// On "Record" button click:
RECORDING.store(true, Ordering::SeqCst);

// In temporary keyboard hook:
if RECORDING.load(Ordering::SeqCst) {
    captured_hotkey = format_hotkey(modifiers, vk);
    RECORDING.store(false, Ordering::SeqCst);
}
```

### Emergency Unlock

Backup unlock method in case hotkey stops working:

**Option 1: Physical key sequence**
- Press Escape 5 times rapidly to unlock

**Option 2: Time-based**
- Auto-unlock after 30 seconds of continuous hotkey attempts

**Option 3: Mouse gesture**
- Click corners in sequence: top-left, top-right, bottom-right, bottom-left

---

## GitHub Actions Workflow

### CI (Continuous Integration)

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
      - run: cargo build --release
      - run: cargo test
      - run: cargo clippy -- -D warnings

  fmt:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
        with:
          components: rustfmt
      - run: cargo fmt --check
```

### Release Automation

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags: ['v*']

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
      - run: cargo build --release

      - name: Upload Release
        uses: softprops/action-gh-release@v1
        with:
          files: target/release/pawgate.exe
```

---

## Comparison with Competitors

| Feature | PawGate (Rust) | KeyFreeze | Toddler Keys | Child Lock |
|---------|----------------|-----------|--------------|------------|
| Free | Yes | Yes | Trial | Yes |
| Open Source | Yes | No | No | No |
| Size | ~2 MB | ~5 MB | ~10 MB | ~3 MB |
| Portable | Yes | No | No | No |
| Customizable | Yes | Limited | Yes | No |
| Multi-monitor | Yes | ? | Yes | ? |
| Hotkey unlock | Yes | Yes | Yes | Yes |
| Mouse blocking | Planned | Yes | Yes | Yes |
| Settings GUI | Yes | Yes | Yes | Yes |

---

## Contributing

See [DEVELOPMENT.md](DEVELOPMENT.md) for how to contribute to these features.

Priority for contributions:
1. Bug fixes
2. Priority 1 features
3. Priority 4 (developer experience)
4. Priority 2-3 features

---

## Version History

### v1.0.0 (Current)
- Initial Rust implementation
- Core keyboard locking
- Settings dialog
- Colorblind-friendly icon

### v1.1.0 (Planned)
- Toast notifications
- Sound feedback
- Animated tray icon

### v1.2.0 (Planned)
- Hot-reload hotkey
- Mouse blocking option
- Hotkey recording

### v2.0.0 (Future)
- Installer
- Auto-update
- Multiple profiles

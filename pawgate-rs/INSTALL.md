# PawGate Rust - Installation Guide

Complete guide to building PawGate from source. No prior Rust experience required!

## Table of Contents

- [Quick Start (Windows)](#quick-start-windows)
- [Detailed Setup](#detailed-setup)
  - [Windows](#windows-setup)
  - [macOS (Cross-Compile)](#macos-cross-compile)
  - [Linux (Cross-Compile)](#linux-cross-compile)
- [Troubleshooting](#troubleshooting)
- [Uninstallation](#uninstallation)

---

## Quick Start (Windows)

If you just want to run PawGate quickly:

```powershell
# 1. Install Rust (one-time setup)
winget install Rustlang.Rustup

# 2. Clone and build
git clone https://github.com/timothywarner-org/pawgate.git
cd pawgate/pawgate-rs
cargo build --release

# 3. Run
.\target\release\pawgate.exe
```

That's it! Look for the paw icon in your system tray.

---

## Detailed Setup

### Windows Setup

#### Step 1: Install Rust

**Option A: Using winget (Windows 10/11)**
```powershell
winget install Rustlang.Rustup
```

**Option B: Manual Download**
1. Go to https://rustup.rs
2. Download `rustup-init.exe`
3. Run the installer
4. Choose option 1 (default installation)
5. Restart your terminal/PowerShell

**Option C: Using Chocolatey**
```powershell
choco install rustup.install
```

#### Step 2: Verify Installation

Open a new PowerShell or Command Prompt:

```powershell
# Check Rust version
rustc --version
# Should show: rustc 1.XX.X (xxxxx 2024-XX-XX)

# Check Cargo (package manager)
cargo --version
# Should show: cargo 1.XX.X (xxxxx 2024-XX-XX)
```

#### Step 3: Install Visual Studio Build Tools

Rust on Windows requires the MSVC build tools:

**Option A: Install Visual Studio Build Tools (Smaller)**
1. Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Run the installer
3. Select "Desktop development with C++"
4. Click Install (~2-3 GB)

**Option B: Full Visual Studio (if you have it)**
- Ensure "Desktop development with C++" workload is installed

#### Step 4: Clone the Repository

```powershell
# Using Git
git clone https://github.com/timothywarner-org/pawgate.git
cd pawgate/pawgate-rs

# Or download ZIP from GitHub and extract
```

#### Step 5: Build PawGate

```powershell
# Debug build (faster compile, larger binary, includes debug info)
cargo build

# Release build (slower compile, optimized, smaller binary)
cargo build --release
```

Build output locations:
- Debug: `target/debug/pawgate.exe` (~10-15 MB)
- Release: `target/release/pawgate.exe` (~2-3 MB)

#### Step 6: Run PawGate

```powershell
# Run directly
.\target\release\pawgate.exe

# Or copy to a permanent location
copy .\target\release\pawgate.exe C:\Tools\PawGate.exe
C:\Tools\PawGate.exe
```

#### Step 7: (Optional) Add to Startup

To run PawGate automatically when Windows starts:

1. Press `Win + R`, type `shell:startup`, press Enter
2. Create a shortcut to `pawgate.exe` in this folder

Or via PowerShell:
```powershell
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\PawGate.lnk")
$Shortcut.TargetPath = "C:\Tools\PawGate.exe"
$Shortcut.Save()
```

---

### macOS Cross-Compile

PawGate only runs on Windows, but you can build it from macOS:

#### Step 1: Install Rust

```bash
# Install Rust via rustup
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Follow prompts (choose default installation)
source $HOME/.cargo/env
```

#### Step 2: Add Windows Target

```bash
# Add Windows compilation target
rustup target add x86_64-pc-windows-msvc

# For GNU toolchain (alternative, doesn't require MSVC)
rustup target add x86_64-pc-windows-gnu
```

#### Step 3: Install Cross-Compilation Tools

**For GNU toolchain (easier):**
```bash
# Install MinGW-w64
brew install mingw-w64
```

**For MSVC toolchain (better compatibility):**
This requires additional setup. Consider using Docker or a Windows VM.

#### Step 4: Build

```bash
cd pawgate-rs

# Using GNU toolchain
cargo build --release --target x86_64-pc-windows-gnu
```

Output: `target/x86_64-pc-windows-gnu/release/pawgate.exe`

Transfer this `.exe` to a Windows machine to run it.

---

### Linux Cross-Compile

#### Step 1: Install Rust

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env
```

#### Step 2: Install Cross-Compilation Tools

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install mingw-w64 gcc-mingw-w64-x86-64
```

**Fedora:**
```bash
sudo dnf install mingw64-gcc mingw64-winpthreads-static
```

**Arch Linux:**
```bash
sudo pacman -S mingw-w64-gcc
```

#### Step 3: Add Windows Target

```bash
rustup target add x86_64-pc-windows-gnu
```

#### Step 4: Configure Cargo

Create or edit `~/.cargo/config.toml`:

```toml
[target.x86_64-pc-windows-gnu]
linker = "x86_64-w64-mingw32-gcc"
ar = "x86_64-w64-mingw32-ar"
```

#### Step 5: Build

```bash
cd pawgate-rs
cargo build --release --target x86_64-pc-windows-gnu
```

Output: `target/x86_64-pc-windows-gnu/release/pawgate.exe`

---

## Understanding Cargo Commands

| Command | Description |
|---------|-------------|
| `cargo build` | Compile debug build |
| `cargo build --release` | Compile optimized release build |
| `cargo run` | Build and run (debug mode) |
| `cargo run --release` | Build and run (release mode) |
| `cargo check` | Quick syntax/type check without building |
| `cargo clean` | Delete build artifacts |
| `cargo update` | Update dependencies |
| `cargo doc --open` | Generate and view documentation |

---

## Troubleshooting

### "rustc is not recognized"

**Cause:** Rust not in PATH or terminal not restarted.

**Fix:**
```powershell
# Windows: Restart terminal, or manually add to PATH
$env:Path += ";$env:USERPROFILE\.cargo\bin"

# Permanent fix: Reinstall rustup and select "Modify PATH"
```

### "linker 'link.exe' not found"

**Cause:** Visual Studio Build Tools not installed.

**Fix:** Install Visual Studio Build Tools with "Desktop development with C++"

### "error: failed to run custom build command for windows"

**Cause:** Windows SDK not fully installed.

**Fix:**
1. Open Visual Studio Installer
2. Modify your installation
3. Ensure "Windows 10/11 SDK" is selected

### "cargo: command not found" (macOS/Linux)

**Cause:** Cargo not in PATH.

**Fix:**
```bash
source $HOME/.cargo/env
# Add to ~/.bashrc or ~/.zshrc for permanence
```

### Build is very slow

**Cause:** First build downloads and compiles dependencies.

**Fix:** This is normal for first build. Subsequent builds are faster.

**Speed up tip:**
```powershell
# Use more CPU cores (replace 8 with your core count)
$env:CARGO_BUILD_JOBS = "8"
cargo build --release
```

### Binary is too large

**Cause:** Debug symbols included.

**Fix:** Use release build:
```powershell
cargo build --release
```

The release binary should be ~2-3 MB.

---

## Uninstallation

### Remove PawGate

1. Delete `pawgate.exe` wherever you placed it
2. Remove startup shortcut if created
3. Delete config: `rmdir /s %USERPROFILE%\.pawgate`

### Remove Rust (optional)

```powershell
rustup self uninstall
```

This removes Rust, Cargo, and all toolchains.

---

## Next Steps

- Read the [README](README.md) for usage instructions
- See [DEVELOPMENT.md](DEVELOPMENT.md) for contributing
- Check [ROADMAP.md](ROADMAP.md) for planned features

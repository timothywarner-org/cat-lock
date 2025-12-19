<div align="center">
  <img src="images/logo_image.png" alt="PawGate Logo" width="250">

  # PawGate

  [![CI](https://img.shields.io/github/actions/workflow/status/timothywarner-org/pawgate/ci.yml?label=CI&logo=github)](https://github.com/timothywarner-org/pawgate/actions/workflows/ci.yml)
  [![Release](https://img.shields.io/github/actions/workflow/status/timothywarner-org/pawgate/release.yml?label=Release&logo=github)](https://github.com/timothywarner-org/pawgate/actions/workflows/release.yml)
  [![Coverage](https://img.shields.io/badge/coverage-72%25-green)](https://github.com/timothywarner-org/pawgate)
  [![Author](https://img.shields.io/badge/Author-Tim%20Warner-blue)](https://techtrainertim.com)

</div>

PawGate is a simple utility designed to prevent accidental keyboard input, particularly when your feline friend decides to grace your workspace.
Currently only supported on **Windows**.

## Attribution

PawGate is a fork of [CatLock](https://github.com/richiehowelll/cat-lock) by [@richiehowelll](https://github.com/richiehowelll). The original project provided the foundation for this utility. This fork adds documentation, testing infrastructure, CI/CD, and a rebrand while maintaining GPL v3 licensing as required.

If you appreciate the original work, please consider [supporting the original author](https://buymeacoffee.com/richiehowelll).

## Features
- Lock your keyboard with a hotkey (Ctrl+B by default)
- Semi-transparent overlay shows keyboard is locked while you monitor your screen
- Unlock by pressing the hotkey again
- System tray menu for quick access to settings:
    - Adjust overlay opacity (5% to 90%)
    - Enable/disable lock notifications
- Blocks all 256 keyboard scan codes plus multimedia keys
- Single-instance enforcement (won't run multiple copies)

## Installation

### Option 1: Build Locally (Recommended)

Building locally avoids Windows SmartScreen warnings that can block downloaded executables.

**Easy method** - Just run the build script:
```
build.bat
```

**Manual method:**
```bash
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --onefile --add-data="./resources/img/icon.ico;./resources/img/" --add-data="./resources/img/icon.png;./resources/img/" --add-data="./resources/config/config.json;./resources/config/" --icon="./resources/img/icon.ico" --hidden-import plyer.platforms.win.notification --noconsole --name="PawGate" "./src/main.py"
```

The executable will be in the `dist/` folder.

> **Note:** If Windows Defender flags your locally-built exe, add the `dist` folder to Windows Security exclusions.

### Option 2: Download Pre-built Release

Pre-built executables are available on the [Releases](../../releases) page. Note that Windows SmartScreen may warn about unsigned executables from the internet.
## Caveats
- Relies on https://github.com/boppreh/keyboard/ which only has full support for Windows
- OS bound hotkeys take precedence such as `ctrl+alt+del` (this way you don't get locked out if something goes wrong)

---

## Feature Backlog

Future enhancements planned for PawGate. Contributions welcome!

### Tier 1: Automatic Cat Detection (The Dream)
| Feature | Description | Status |
|---------|-------------|--------|
| Webcam cat detection | Use YOLOv8 to detect cat approaching keyboard | Planned |
| Auto-lock on detection | Lock keyboard automatically when cat detected | Planned |
| Configurable cooldown | Prevent lock/unlock spam with cooldown timer | Planned |
| Detection confidence threshold | Adjust sensitivity to avoid false positives | Planned |
| Screenshot on detection | Capture photographic evidence of the culprit | Planned |

### Tier 2: Quality of Life
| Feature | Description | Status |
|---------|-------------|--------|
| Run on Windows startup | Option to launch PawGate at login | Planned |
| Lock on screen saver/sleep | Auto-lock when user steps away | Planned |
| Scheduled lock times | "Lock 9am-5pm on weekdays" | Planned |
| Quick-toggle global hotkey | Enable/disable protection without menu | Planned |
| Configurable unlock method | Choose: hotkey only, click only, or both | Planned |

### Tier 3: Fun & Engagement
| Feature | Description | Status |
|---------|-------------|--------|
| Cat activity log | "Fiona attempted 47 keypresses today" | Planned |
| Statistics dashboard | Charts of cat activity over time | Planned |
| Custom sounds | Play meow on detection (or deterrent sound) | Planned |
| Desktop widget | Show cat detection status at a glance | Planned |
| Achievement system | "Blocked 1000 cat keypresses!" | Planned |

### Tier 4: PowerToys Integration (C# Port)
| Feature | Description | Status |
|---------|-------------|--------|
| Native C# implementation | Port to C# for PowerToys submission | Planned |
| Windows 11 Settings UI | Native settings page integration | Planned |
| Keyboard Manager integration | Remap keys while locked | Planned |
| FancyZones awareness | Lock specific screen zones | Planned |

---

## Support the Original Author

PawGate builds on the work of [@richiehowelll](https://github.com/richiehowelll). If you find this utility helpful, consider supporting the original creator:

<a href="https://buymeacoffee.com/richiehowelll" target="_blank"><img src="https://img.buymeacoffee.com/button-api/?text=Buy me a coffee&emoji=&slug=richiehowelll&button_colour=FFDD00&font_colour=000000&font_family=Cookie&outline_colour=000000&coffee_colour=ffffff"></a>

## Tested by:

Fiona the Cat 🐱

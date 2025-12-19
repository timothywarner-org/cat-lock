# PawGate C# Porting Guide

This document provides a comprehensive guide for porting PawGate from Python to C# for potential integration into Microsoft PowerToys.

## Table of Contents
- [Why Port to C#](#why-port-to-c)
- [Python to C# Component Mapping](#python-to-c-component-mapping)
- [Recommended C# Libraries](#recommended-c-libraries)
- [PowerToys Architecture Overview](#powertoys-architecture-overview)
- [Key Technical Challenges](#key-technical-challenges)
- [Implementation Roadmap](#implementation-roadmap)
- [Code Examples](#code-examples)

---

## Why Port to C#

**Reasons for C# Port:**

1. **PowerToys Requirement** - PowerToys is a C# codebase (.NET 8+), Python integration not feasible
2. **Performance** - Compiled C# faster than interpreted Python for hotkey monitoring
3. **Native Windows Integration** - Direct access to Win32 APIs without ctypes layer
4. **Better Distribution** - No Python runtime dependency, smaller installer
5. **Ecosystem** - Access to WinUI 3, WPF, and full .NET ecosystem
6. **Maintainability** - PowerToys community familiar with C#, easier to get contributors

**Trade-offs:**

- **Development Time** - Rewriting from scratch takes longer than iterating on Python
- **Type Safety** - C# requires more upfront design (Python's duck typing is forgiving)
- **Learning Curve** - Need to learn PowerToys' architecture and conventions
- **Testing Complexity** - Mocking Windows APIs harder in C# than with pytest-mock

---

## Python to C# Component Mapping

### Core Libraries

| Python Library | C# Equivalent | Notes |
|----------------|---------------|-------|
| `keyboard` | `WindowsInput` or `User32.dll P/Invoke` | See detailed section below |
| `pystray` | `System.Windows.Forms.NotifyIcon` | Built into .NET Framework/Windows Forms |
| `Pillow` | `System.Drawing` or `WPF BitmapImage` | Built-in image handling |
| `plyer` | `Windows.UI.Notifications` | UWP toast notifications |
| `tkinter` | WPF or WinUI 3 | See UI framework comparison |
| `screeninfo` | `System.Windows.Forms.Screen` | Built-in multi-monitor support |
| `queue.Queue` | `System.Collections.Concurrent.ConcurrentQueue<T>` | Thread-safe queue |
| `threading` | `System.Threading.Tasks` (async/await) | Modern C# uses async over threads |
| `json` | `System.Text.Json` or `Newtonsoft.Json` | Built-in JSON serialization |

### Architecture Components

| Python Component | C# Equivalent | Implementation |
|------------------|---------------|----------------|
| `PawGateCore` main class | `PawGateManager` service | Singleton service managed by PowerToys |
| Thread-based concurrency | Async/await with `Task` | C# best practice is async over explicit threads |
| `Queue` for signaling | `Channel<T>` or events | More idiomatic: use C# events or reactive extensions |
| Lockfile PID check | Named Mutex | `System.Threading.Mutex` for single instance |
| JSON config file | Settings provider | PowerToys has centralized settings system |
| PyInstaller bundling | MSBuild + ClickOnce/MSIX | Standard .NET packaging |

---

## Recommended C# Libraries

### 1. Keyboard Hooking

**Option A: WindowsInput (NuGet Package)**
```csharp
// Install-Package InputSimulator
using WindowsInput;
using WindowsInput.Native;

var simulator = new InputSimulator();
simulator.Keyboard.KeyPress(VirtualKeyCode.VK_A);
```

**Pros:**
- High-level API, easy to use
- Active maintenance
- Works with virtual keys

**Cons:**
- Doesn't support scan code blocking (only virtual keys)
- Limited low-level hook capabilities

**Option B: Low-Level Keyboard Hook (P/Invoke)**
```csharp
using System.Runtime.InteropServices;

[DllImport("user32.dll")]
static extern IntPtr SetWindowsHookEx(int idHook, LowLevelKeyboardProc callback, IntPtr hInstance, uint threadId);

[DllImport("user32.dll")]
static extern bool UnhookWindowsHookEx(IntPtr hhk);

[DllImport("user32.dll")]
static extern IntPtr CallNextHookEx(IntPtr hhk, int nCode, IntPtr wParam, IntPtr lParam);

private const int WH_KEYBOARD_LL = 13;
private delegate IntPtr LowLevelKeyboardProc(int nCode, IntPtr wParam, IntPtr lParam);
```

**Pros:**
- Full control over keyboard events
- Can block specific keys by returning 1
- Supports scan codes

**Cons:**
- More complex, requires Win32 knowledge
- Must manage unmanaged resources carefully
- Easy to introduce bugs (crashes, memory leaks)

**Recommendation:** Use low-level hooks for blocking, WindowsInput for simulation.

### 2. System Tray Icon

```csharp
using System.Windows.Forms;

NotifyIcon trayIcon = new NotifyIcon
{
    Icon = new Icon("icon.ico"),
    Visible = true,
    Text = "PawGate"
};

ContextMenuStrip menu = new ContextMenuStrip();
menu.Items.Add("Lock Keyboard", null, OnLockKeyboard);
menu.Items.Add("Settings", null, OnOpenSettings);
menu.Items.Add("Exit", null, OnExit);

trayIcon.ContextMenuStrip = menu;
```

**Note:** PowerToys has its own tray icon - PawGate would be a module within it, not standalone.

### 3. Overlay Window

**Option A: WPF (Windows Presentation Foundation)**
```csharp
using System.Windows;

public class OverlayWindow : Window
{
    public OverlayWindow()
    {
        WindowStyle = WindowStyle.None;
        WindowState = WindowState.Maximized;
        Topmost = true;
        Background = new SolidColorBrush(Color.FromArgb(76, 0, 0, 0)); // 30% opacity
        AllowsTransparency = true;

        // Span all monitors
        Left = SystemParameters.VirtualScreenLeft;
        Top = SystemParameters.VirtualScreenTop;
        Width = SystemParameters.VirtualScreenWidth;
        Height = SystemParameters.VirtualScreenHeight;
    }
}
```

**Pros:**
- Rich UI capabilities (gradients, animations)
- XAML-based declarative UI
- Mature, well-documented

**Cons:**
- Heavier than WinUI (older framework)
- Not the latest Microsoft UI technology

**Option B: WinUI 3**
```csharp
using Microsoft.UI.Xaml;

public class OverlayWindow : Window
{
    public OverlayWindow()
    {
        AppWindow.IsShownInSwitchers = false;
        AppWindow.SetPresenter(AppWindowPresenterKind.FullScreen);
        // WinUI 3 full-screen setup
    }
}
```

**Pros:**
- Modern UI framework (Windows 11 optimized)
- Better performance than WPF
- PowerToys is moving towards WinUI

**Cons:**
- Less mature than WPF
- Some APIs still in development

**Recommendation:** Use WinUI 3 to align with PowerToys' future direction.

### 4. Notifications

```csharp
using Windows.UI.Notifications;
using Windows.Data.Xml.Dom;

public void ShowToast(string message)
{
    string toastXml = $@"
        <toast>
            <visual>
                <binding template='ToastGeneric'>
                    <text>PawGate</text>
                    <text>{message}</text>
                </binding>
            </visual>
        </toast>";

    XmlDocument doc = new XmlDocument();
    doc.LoadXml(toastXml);

    ToastNotification toast = new ToastNotification(doc);
    ToastNotificationManager.CreateToastNotifier("PawGate").Show(toast);
}
```

**PowerToys Integration:** Use PowerToys' existing notification system instead of custom implementation.

### 5. Configuration

**Option A: System.Text.Json (Recommended)**
```csharp
using System.Text.Json;

public class PawGateSettings
{
    public string Hotkey { get; set; } = "Ctrl+B";
    public double Opacity { get; set; } = 0.3;
    public bool NotificationsEnabled { get; set; } = false;

    public static PawGateSettings Load(string path)
    {
        string json = File.ReadAllText(path);
        return JsonSerializer.Deserialize<PawGateSettings>(json);
    }

    public void Save(string path)
    {
        string json = JsonSerializer.Serialize(this, new JsonSerializerOptions { WriteIndented = true });
        File.WriteAllText(path, json);
    }
}
```

**PowerToys Integration:** Use PowerToys settings system (see section below).

---

## PowerToys Architecture Overview

### Project Structure

PowerToys is organized as modules under a central runner:

```
PowerToys/
├── src/
│   ├── runner/              # Main PowerToys process
│   ├── modules/
│   │   ├── FancyZones/      # Example module
│   │   ├── PowerRename/     # Example module
│   │   └── PawGate/         # New module (your port)
│   ├── settings-ui/         # Unified settings interface
│   └── common/              # Shared utilities
└── installer/               # MSI installer
```

### Module Structure

Each PowerToys module follows this structure:

```
src/modules/PawGate/
├── PawGate/
│   ├── PawGateManager.cs       # Main service (IAsyncDisposable)
│   ├── KeyboardHook.cs         # Low-level keyboard hooking
│   ├── OverlayWindow.xaml      # WinUI overlay window
│   ├── OverlayWindow.xaml.cs   # Overlay code-behind
│   └── Settings.cs             # Settings model
├── PawGateSettingsUI/
│   ├── Views/
│   │   └── SettingsPage.xaml   # Settings UI (appears in PowerToys settings)
│   └── ViewModels/
│       └── SettingsViewModel.cs
└── PawGate.Tests/
    └── UnitTests.cs
```

### Module Lifecycle

```csharp
public interface IModule
{
    string Name { get; }
    bool IsEnabled { get; }

    void Enable();
    void Disable();
    void Destroy();
}

public class PawGateModule : IModule
{
    private PawGateManager _manager;

    public string Name => "PawGate";
    public bool IsEnabled { get; private set; }

    public void Enable()
    {
        _manager = new PawGateManager();
        _manager.Start();
        IsEnabled = true;
    }

    public void Disable()
    {
        _manager?.Stop();
        IsEnabled = false;
    }

    public void Destroy()
    {
        _manager?.Dispose();
    }
}
```

### Settings Integration

PowerToys uses a centralized settings system:

```csharp
// Define settings schema
public class PawGateSettings
{
    public HotkeySettings Hotkey { get; set; }
    public int Opacity { get; set; } = 30; // 0-100 scale for UI
    public bool NotificationsEnabled { get; set; } = false;
}

// Register with settings provider
public class PawGateModule : IModule
{
    private ISettingsUtils _settingsUtils;

    public PawGateModule(ISettingsUtils settingsUtils)
    {
        _settingsUtils = settingsUtils;
    }

    public void LoadSettings()
    {
        var settings = _settingsUtils.GetSettings<PawGateSettings>(Name);
        ApplySettings(settings);
    }

    public void SaveSettings(PawGateSettings settings)
    {
        _settingsUtils.SaveSettings(settings.ToJsonString(), Name);
    }
}
```

### Settings UI (XAML)

PowerToys settings UI is WinUI 3 XAML:

```xaml
<Page
    x:Class="PawGateSettingsUI.Views.SettingsPage"
    xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"
    xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml">

    <StackPanel Spacing="8">
        <TextBlock Text="PawGate Settings" Style="{StaticResource SubtitleTextBlockStyle}" />

        <!-- Hotkey Picker -->
        <controls:HotkeySettingsCard
            Header="Lock/Unlock Hotkey"
            Keys="{x:Bind ViewModel.Hotkey, Mode=TwoWay}" />

        <!-- Opacity Slider -->
        <controls:SettingsCard Header="Overlay Opacity">
            <Slider
                Minimum="5"
                Maximum="90"
                Value="{x:Bind ViewModel.Opacity, Mode=TwoWay}"
                Width="200" />
        </controls:SettingsCard>

        <!-- Notifications Toggle -->
        <controls:SettingsCard Header="Show Notifications">
            <ToggleSwitch IsOn="{x:Bind ViewModel.NotificationsEnabled, Mode=TwoWay}" />
        </controls:SettingsCard>
    </StackPanel>
</Page>
```

---

## Key Technical Challenges

### 1. Keyboard Blocking Across All Scan Codes

**Python Implementation:**
```python
for i in range(256):
    keyboard.block_key(i)
```

**C# Challenge:**
Low-level hooks don't have a simple "block all" API. You must:
1. Set a global keyboard hook
2. Inspect each key event (scan code + virtual key)
3. Return 1 to block, or call next hook to allow

**C# Solution:**
```csharp
private static IntPtr HookCallback(int nCode, IntPtr wParam, IntPtr lParam)
{
    if (nCode >= 0 && _isKeyboardLocked)
    {
        int vkCode = Marshal.ReadInt32(lParam);
        Keys key = (Keys)vkCode;

        // Allow Ctrl+Alt+Del and Win+L (OS handles these anyway)
        if (IsOsHotkey(key))
            return CallNextHookEx(_hookID, nCode, wParam, lParam);

        // Block all other keys
        return (IntPtr)1; // Blocks the key
    }
    return CallNextHookEx(_hookID, nCode, wParam, lParam);
}

private static bool IsOsHotkey(Keys key)
{
    // OS-level hotkeys that can't/shouldn't be blocked
    bool isCtrlAltDel = Control.ModifierKeys.HasFlag(Keys.Control) &&
                        Control.ModifierKeys.HasFlag(Keys.Alt) &&
                        key == Keys.Delete;

    bool isWinL = Control.ModifierKeys.HasFlag(Keys.LWin) && key == Keys.L;

    return isCtrlAltDel || isWinL;
}
```

**Testing Note:** Be very careful testing this - it's easy to lock yourself out. Always test with Ctrl+Alt+Del escape route available.

### 2. Multi-Monitor Overlay

**Python Implementation:**
```python
monitors = get_monitors()
total_width = sum([m.width for m in monitors])
max_height = max([m.height for m in monitors])
min_x = min([m.x for m in monitors])
min_y = min([m.y for m in monitors])
```

**C# Challenge:**
WPF/WinUI expects a single window per monitor, not one giant window.

**C# Solution (Option A - Single Window):**
```csharp
public class OverlayWindow : Window
{
    public OverlayWindow()
    {
        // Get virtual screen bounds (spans all monitors)
        Left = SystemParameters.VirtualScreenLeft;
        Top = SystemParameters.VirtualScreenTop;
        Width = SystemParameters.VirtualScreenWidth;
        Height = SystemParameters.VirtualScreenHeight;

        WindowStyle = WindowStyle.None;
        WindowState = WindowState.Normal; // Not Maximized (we set dimensions manually)
        Topmost = true;
        ShowInTaskbar = false;
    }
}
```

**C# Solution (Option B - Window Per Monitor):**
```csharp
public class OverlayManager
{
    private List<OverlayWindow> _overlays = new();

    public void ShowOverlays()
    {
        foreach (var screen in System.Windows.Forms.Screen.AllScreens)
        {
            var overlay = new OverlayWindow
            {
                Left = screen.Bounds.Left,
                Top = screen.Bounds.Top,
                Width = screen.Bounds.Width,
                Height = screen.Bounds.Height
            };
            overlay.Show();
            _overlays.Add(overlay);
        }
    }

    public void HideOverlays()
    {
        foreach (var overlay in _overlays)
            overlay.Close();
        _overlays.Clear();
    }
}
```

**Recommendation:** Single window is simpler, but multiple windows gives better per-monitor DPI handling.

### 3. Async/Await vs Threading

**Python Implementation:**
```python
self.hotkey_thread = threading.Thread(target=self.hotkey_listener, daemon=True)
self.hotkey_thread.start()
```

**C# Best Practice:**
Avoid explicit threads, use async/await:

```csharp
private CancellationTokenSource _cancellationTokenSource;

public async Task StartHotkeyListenerAsync()
{
    _cancellationTokenSource = new CancellationTokenSource();
    await Task.Run(() => HotkeyListenerLoop(_cancellationTokenSource.Token));
}

private void HotkeyListenerLoop(CancellationToken token)
{
    while (!token.IsCancellationRequested)
    {
        // Monitor for hotkey
        Thread.Sleep(100); // Or use async delay in real implementation
    }
}

public void StopHotkeyListener()
{
    _cancellationTokenSource?.Cancel();
}
```

**WHY async over threads?**
- Better resource management (thread pool reuse)
- Easier cancellation (CancellationToken)
- Integrates with UI frameworks (avoid dispatcher calls)
- More idiomatic C#

### 4. PyInstaller Resource Bundling

**Python Implementation:**
```python
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(__file__)
```

**C# Solution:**
Embedded resources in .NET assembly:

```csharp
// Add icon to project as Embedded Resource
// Access it at runtime:
using (Stream stream = Assembly.GetExecutingAssembly()
    .GetManifestResourceStream("PawGate.Resources.icon.ico"))
{
    Icon icon = new Icon(stream);
}
```

Or use MSBuild content files:
```xml
<!-- PawGate.csproj -->
<ItemGroup>
  <Content Include="Resources\icon.ico">
    <CopyToOutputDirectory>PreserveNewest</CopyToOutputDirectory>
  </Content>
</ItemGroup>
```

Access via:
```csharp
string iconPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "Resources", "icon.ico");
```

---

## Implementation Roadmap

### Phase 1: Core Functionality (MVP)

1. **Set up module structure** within PowerToys solution
2. **Implement low-level keyboard hook** for blocking
3. **Create simple overlay window** (WinUI 3)
4. **Global hotkey registration** (Ctrl+B)
5. **Basic settings integration** (hardcoded values first)

**Deliverable:** Standalone module that locks keyboard with hotkey, shows overlay.

### Phase 2: PowerToys Integration

1. **Integrate with PowerToys settings UI**
2. **Add settings page** (hotkey picker, opacity slider)
3. **Follow PowerToys coding standards** (linting, tests)
4. **Add module to PowerToys runner**
5. **Test with other modules** (ensure no conflicts)

**Deliverable:** Fully integrated PowerToys module with settings UI.

### Phase 3: Advanced Features

1. **Multi-monitor optimization**
2. **Notification system integration**
3. **Localization** (multiple languages)
4. **Accessibility** (screen reader support, high contrast mode)
5. **Telemetry** (anonymous usage stats, if PowerToys has this)

**Deliverable:** Production-ready module meeting PowerToys quality standards.

### Phase 4: Cat Detection (Future)

1. **Integrate YOLO.NET or ML.NET** for object detection
2. **Webcam capture** (MediaCapture API)
3. **Background inference** (async, GPU-accelerated if available)
4. **Auto-lock on detection**

**Deliverable:** Full automatic cat detection experience.

---

## Code Examples

### Complete Keyboard Hook Example

```csharp
using System;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Windows.Forms;

public class KeyboardBlocker : IDisposable
{
    private const int WH_KEYBOARD_LL = 13;
    private const int WM_KEYDOWN = 0x0100;
    private LowLevelKeyboardProc _proc;
    private IntPtr _hookID = IntPtr.Zero;
    private bool _isBlocking = false;

    public KeyboardBlocker()
    {
        _proc = HookCallback;
    }

    public void StartBlocking()
    {
        _hookID = SetHook(_proc);
        _isBlocking = true;
    }

    public void StopBlocking()
    {
        _isBlocking = false;
        if (_hookID != IntPtr.Zero)
        {
            UnhookWindowsHookEx(_hookID);
            _hookID = IntPtr.Zero;
        }
    }

    private IntPtr SetHook(LowLevelKeyboardProc proc)
    {
        using (Process curProcess = Process.GetCurrentProcess())
        using (ProcessModule curModule = curProcess.MainModule)
        {
            return SetWindowsHookEx(WH_KEYBOARD_LL, proc,
                GetModuleHandle(curModule.ModuleName), 0);
        }
    }

    private IntPtr HookCallback(int nCode, IntPtr wParam, IntPtr lParam)
    {
        if (nCode >= 0 && wParam == (IntPtr)WM_KEYDOWN && _isBlocking)
        {
            int vkCode = Marshal.ReadInt32(lParam);

            // Allow Ctrl+Alt+Del (doesn't actually work - OS handles it)
            // Allow Ctrl+Shift+Esc (Task Manager)
            if (IsEmergencyKey(vkCode))
                return CallNextHookEx(_hookID, nCode, wParam, lParam);

            // Block all other keys
            return (IntPtr)1;
        }
        return CallNextHookEx(_hookID, nCode, wParam, lParam);
    }

    private bool IsEmergencyKey(int vkCode)
    {
        // In practice, OS handles these before we see them
        // This is just defensive coding
        return vkCode == (int)Keys.Delete &&
               Control.ModifierKeys.HasFlag(Keys.Control) &&
               Control.ModifierKeys.HasFlag(Keys.Alt);
    }

    public void Dispose()
    {
        StopBlocking();
    }

    #region Native Methods
    private delegate IntPtr LowLevelKeyboardProc(int nCode, IntPtr wParam, IntPtr lParam);

    [DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
    private static extern IntPtr SetWindowsHookEx(int idHook,
        LowLevelKeyboardProc lpfn, IntPtr hMod, uint dwThreadId);

    [DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool UnhookWindowsHookEx(IntPtr hhk);

    [DllImport("user32.dll", CharSet = CharSet.Auto, SetLastError = true)]
    private static extern IntPtr CallNextHookEx(IntPtr hhk, int nCode,
        IntPtr wParam, IntPtr lParam);

    [DllImport("kernel32.dll", CharSet = CharSet.Auto, SetLastError = true)]
    private static extern IntPtr GetModuleHandle(string lpModuleName);
    #endregion
}
```

### Complete Overlay Window Example (WPF)

```csharp
using System.Windows;
using System.Windows.Input;
using System.Windows.Media;

public class OverlayWindow : Window
{
    public event EventHandler UnlockRequested;

    public OverlayWindow(double opacity = 0.3)
    {
        // Window setup
        WindowStyle = WindowStyle.None;
        WindowState = WindowState.Normal;
        ResizeMode = ResizeMode.NoResize;
        Topmost = true;
        ShowInTaskbar = false;
        AllowsTransparency = true;

        // Span all monitors
        Left = SystemParameters.VirtualScreenLeft;
        Top = SystemParameters.VirtualScreenTop;
        Width = SystemParameters.VirtualScreenWidth;
        Height = SystemParameters.VirtualScreenHeight;

        // Appearance
        Background = new SolidColorBrush(Color.FromArgb(
            (byte)(opacity * 255), 0, 0, 0));

        // Content
        Content = CreateContent();

        // Event handlers
        KeyDown += OnKeyDown;
    }

    private UIElement CreateContent()
    {
        var textBlock = new System.Windows.Controls.TextBlock
        {
            Text = "KEYBOARD LOCKED\nPress Ctrl+B to unlock",
            FontSize = 48,
            Foreground = Brushes.White,
            HorizontalAlignment = HorizontalAlignment.Center,
            VerticalAlignment = VerticalAlignment.Center,
            TextAlignment = TextAlignment.Center
        };

        var grid = new System.Windows.Controls.Grid();
        grid.Children.Add(textBlock);
        return grid;
    }

    private void OnKeyDown(object sender, KeyEventArgs e)
    {
        // Hotkey is handled globally by KeyboardBlocker
        // This is just for completeness
    }

    protected override void OnSourceInitialized(EventArgs e)
    {
        base.OnSourceInitialized(e);
        // Make sure window gets focus to receive keyboard events
        Activate();
        Focus();
    }
}
```

### Complete Manager Service

```csharp
using System;
using System.Threading.Tasks;

public class PawGateManager : IDisposable
{
    private readonly KeyboardBlocker _keyboardBlocker;
    private OverlayWindow _overlay;
    private HotKeyManager _hotKeyManager;
    private PawGateSettings _settings;
    private bool _isLocked = false;

    public PawGateManager(PawGateSettings settings)
    {
        _settings = settings;
        _keyboardBlocker = new KeyboardBlocker();
        _hotKeyManager = new HotKeyManager();
    }

    public void Start()
    {
        // Register hotkey
        _hotKeyManager.RegisterHotKey(_settings.Hotkey, OnHotKeyPressed);
    }

    private void OnHotKeyPressed()
    {
        if (_isLocked)
            Unlock();
        else
            Lock();
    }

    public void Lock()
    {
        if (_isLocked) return;

        _isLocked = true;
        _keyboardBlocker.StartBlocking();

        _overlay = new OverlayWindow(_settings.Opacity);
        _overlay.UnlockRequested += (s, e) => Unlock();
        _overlay.Show();

        if (_settings.NotificationsEnabled)
            ShowNotification("Keyboard locked");
    }

    public void Unlock()
    {
        if (!_isLocked) return;

        _isLocked = false;
        _keyboardBlocker.StopBlocking();

        _overlay?.Close();
        _overlay = null;
    }

    private void ShowNotification(string message)
    {
        // Use PowerToys notification system or Windows toast
        // Implementation depends on PowerToys integration
    }

    public void Dispose()
    {
        Unlock();
        _keyboardBlocker?.Dispose();
        _hotKeyManager?.Dispose();
    }
}
```

---

## Next Steps

1. **Set up development environment**
   - Clone PowerToys repository
   - Install Visual Studio 2022 (Community Edition works)
   - Install .NET 8 SDK
   - Build PowerToys to ensure setup works

2. **Study existing modules**
   - FancyZones - Good example of global hooks
   - PowerRename - Good example of settings UI
   - Keyboard Manager - Relevant for key remapping logic

3. **Start small**
   - Create standalone C# console app with keyboard blocking
   - Test low-level hook behavior
   - Ensure you can block/unblock reliably

4. **Prototype overlay**
   - Create WPF/WinUI overlay in standalone app
   - Test multi-monitor spanning
   - Verify transparency and topmost behavior

5. **Integrate with PowerToys**
   - Add module to PowerToys solution
   - Follow contribution guidelines
   - Submit PR for review

---

## Resources

**PowerToys Documentation:**
- [PowerToys GitHub](https://github.com/microsoft/PowerToys)
- [Contributing Guide](https://github.com/microsoft/PowerToys/blob/main/CONTRIBUTING.md)
- [Module Development Docs](https://github.com/microsoft/PowerToys/tree/main/doc/devdocs/modules)

**C# Low-Level Keyboard Hooks:**
- [SetWindowsHookEx Documentation](https://docs.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setwindowshookexa)
- [Keyboard Input Reference](https://docs.microsoft.com/en-us/windows/win32/inputdev/keyboard-input)

**WinUI 3:**
- [WinUI 3 Documentation](https://docs.microsoft.com/en-us/windows/apps/winui/winui3/)
- [WinUI 3 Gallery (Sample App)](https://github.com/microsoft/WinUI-Gallery)

**NuGet Packages:**
- [WindowsInput](https://www.nuget.org/packages/InputSimulator/) - High-level keyboard/mouse simulation
- [GlobalHotKey](https://www.nuget.org/packages/GlobalHotKey/) - Global hotkey registration
- [Newtonsoft.Json](https://www.nuget.org/packages/Newtonsoft.Json/) - JSON serialization (if not using System.Text.Json)

---

## Conclusion

Porting PawGate to C# for PowerToys integration is a significant undertaking but achievable with careful planning. The key challenges are:

1. Replacing `keyboard` library with low-level Windows hooks
2. Adapting to async/await patterns instead of explicit threads
3. Integrating with PowerToys' module system and settings UI
4. Following PowerToys' code quality and contribution standards

Start small, test thoroughly (especially keyboard blocking - easy to lock yourself out!), and engage with the PowerToys community early for feedback.

Good luck with the port! The PowerToys team and community are welcoming to new modules that add genuine value to users.

# CatLock User Guide

## Quick Start

1. **Launch CatLock** - Double-click `CatLock.exe` or run the application
2. **Look for the system tray icon** - A small cat icon will appear in your Windows system tray (near the clock)
3. **The app runs in the background** - No visible window opens. CatLock waits for you to trigger the lock

That's it! The application is now running and ready to protect your keyboard.

---

## Locking Your Keyboard

### Default Hotkey
Press **Ctrl + L** simultaneously to lock your keyboard.

**WHY Ctrl+L?**
This 2-key combination is easy to press quickly when you see your cat approaching, while still being unlikely to trigger accidentally during normal typing. The "L" stands for "Lock" making it memorable.

### What Happens When Locked

1. **Semi-transparent overlay appears** - Your entire screen (all monitors) will be covered with a dark overlay
2. **Unlock instructions displayed** - The center of your primary monitor shows:
   ```
   KEYBOARD LOCKED
   Press CTRL + L to unlock or click anywhere
   ```
3. **All keyboard input is blocked** - Every key on your keyboard becomes inactive, including:
   - Letter and number keys
   - Function keys (F1-F24)
   - Modifier keys (Ctrl, Alt, Shift, Windows key)
   - Multimedia keys (volume, play/pause, brightness)
   - Special keys (Print Screen, etc.)

### What Still Works When Locked

- **Your mouse** - You can still move the cursor and see what's on screen through the semi-transparent overlay
- **Mouse clicks** - Clicking anywhere on the overlay UNLOCKS the keyboard (changed from earlier versions)
- **Ctrl + Alt + Del** - This OS-level hotkey ALWAYS works (see Safety section below)
- **Monitor viewing** - The overlay is transparent enough to monitor ongoing processes

---

## Unlocking Your Keyboard

### Normal Unlock Options

**Option 1: Hotkey**
Press the same hotkey again: **Ctrl + L**

**Option 2: Mouse Click**
Click anywhere on the overlay window.

The overlay will disappear immediately and all keyboard functionality returns.

### Mouse Unlock: Design Decision

Earlier versions blocked mouse clicks to prevent cats from unlocking by stepping on the mouse. However, user feedback indicated that:
1. Quick mouse unlock is more convenient for humans
2. Cats rarely click mice accidentally in practice
3. The visual overlay itself often deters cat interference

If you prefer hotkey-only unlock, this may be configurable in future versions.

---

## Emergency Unlock / Safety Features

### Never Get Locked Out

**Ctrl + Alt + Del ALWAYS works** - This is a Windows operating system feature that CANNOT be blocked by any application, including CatLock.

If you ever need to escape:

1. **Press Ctrl + Alt + Del** - This brings up the Windows security screen
2. **Choose an option:**
   - **Sign out** - Logs you out of Windows (closes CatLock)
   - **Task Manager** - End the CatLock process
   - **Lock** - Locks Windows (different from keyboard lock)
   - **Restart** - Restarts your computer
   - **Press Escape** - Returns to your locked session

### "But I Forgot the Hotkey!"

Don't panic! The hotkey is displayed in the center of your screen when locked:
```
Press CTRL + L to unlock or click anywhere
```

If you still can't unlock:
1. **Click anywhere on the screen** - The easiest unlock method
2. Use **Ctrl + Alt + Del** (see above)
3. Or right-click the **CatLock system tray icon** and select **Quit** (this unlocks automatically)

### Other OS Hotkeys That Work

These Windows shortcuts cannot be blocked (by design):
- **Ctrl + Alt + Del** - Security screen
- **Windows + L** - Lock Windows session
- **Ctrl + Shift + Esc** - Task Manager (direct)

---

## System Tray Menu

### Finding the Icon

Look in your Windows system tray (bottom-right corner, near the clock). If you don't see the CatLock icon, click the up-arrow to show hidden icons.

### Menu Options

Right-click the CatLock icon to access:

#### Lock Keyboard
Triggers the keyboard lock immediately (same as pressing the hotkey).

#### Enable/Disable Notifications
Toggle system notifications on/off. When enabled, a Windows toast notification appears each time you lock the keyboard.

- Checkmark = Notifications enabled
- No checkmark = Notifications disabled

#### Set Opacity
Adjust how dark the lock overlay appears. Options:
- **5%** - Nearly transparent (barely visible)
- **10%** - Very light (good for monitoring)
- **30%** - Light (default, balanced visibility)
- **50%** - Medium (noticeable but readable)
- **70%** - Dark (strong visual indicator)
- **90%** - Very dark (maximum cat deterrent)

**TIP:** Lower opacity (5-30%) is great when you need to monitor long-running tasks. Higher opacity (70-90%) provides a stronger visual "keyboard is locked" reminder.

#### About
- **Help** - Opens documentation
- **About** - Information about CatLock
- **Support** - Buy the developer a coffee

#### Quit
Closes CatLock completely. If the keyboard is currently locked, it will unlock automatically before quitting.

---

## Configuration

### Config File Location

CatLock stores your settings in:
```
C:\Users\YourUsername\.catlock\config\config.json
```

Where `YourUsername` is your Windows username.

### What You Can Configure

Open the `config.json` file in any text editor to customize:

```json
{
  "hotkey": "ctrl+shift+alt+f12",
  "opacity": 0.3,
  "notificationsEnabled": false
}
```

#### hotkey
The key combination to lock/unlock the keyboard.

**Format:** Use lowercase with `+` separators.

**Examples:**
- `"ctrl+l"` (default - L for Lock)
- `"ctrl+shift+l"` (more keys to prevent accidental triggers)
- `"ctrl+alt+k"` (K for Keyboard lock)
- `"ctrl+shift+alt+f12"` (previous default, very hard to trigger accidentally)

**Available modifiers:** `ctrl`, `shift`, `alt`, `windows`

**WARNING:** Avoid hotkeys that conflict with common applications:
- `Ctrl+C`, `Ctrl+V`, `Ctrl+Z` (clipboard/undo)
- `Ctrl+S` (save in most apps)
- `Alt+F4` (close window)

**NOTE:** If you find `Ctrl+L` triggers accidentally, consider adding more modifiers like `Ctrl+Shift+L`.

#### opacity
How dark the lock overlay appears (0.0 to 1.0).

**Range:** 0.05 (5% opaque) to 0.9 (90% opaque)

**Examples:**
- `0.05` - Nearly invisible
- `0.3` - Default (30% opaque)
- `0.7` - Very dark
- `0.9` - Maximum darkness

**NOTE:** You can also change this from the system tray menu without editing the file.

#### notificationsEnabled
Whether to show Windows toast notifications when locking.

**Values:**
- `true` - Show notification
- `false` - Silent lock (default)

**NOTE:** Notifications can be toggled from the system tray menu.

### Applying Configuration Changes

1. **Edit `config.json`** and save your changes
2. **Restart CatLock** - Quit from the system tray menu and launch again
3. Your new settings will be loaded

**TIP:** Most users never need to edit this file directly - the system tray menu provides easier access to common settings.

---

## Troubleshooting

### "I can't unlock the keyboard!"

**Solution 1:** Press **Ctrl + Alt + Del**
- This ALWAYS works regardless of CatLock's state
- Choose Task Manager and end the CatLock process
- Or sign out/restart

**Solution 2:** Check the on-screen instructions
- The unlock hotkey is displayed in the center of your screen
- Make sure you're pressing all keys simultaneously

**Solution 3:** Use the system tray
- Right-click the CatLock icon
- Select "Quit" (this unlocks automatically)

### "The hotkey isn't working"

**Possible causes:**

1. **Another application is using the same hotkey**
   - Try changing the hotkey in `config.json`
   - Note: `Ctrl+L` is used by browsers to focus the address bar - this conflict only matters if browser is active

2. **You're not pressing all keys simultaneously**
   - For `Ctrl+L`, press Ctrl first, then L while holding Ctrl
   - For multi-modifier combos, press modifiers first, then the letter/function key

3. **Keyboard layout issues**
   - Some non-US keyboard layouts may have different key mappings
   - Try a different hotkey combination

**Test your hotkey:**
- Launch CatLock
- Press your hotkey - the overlay should appear
- Click the overlay or press hotkey again - the overlay should disappear

### "Some keys still work when locked"

This is expected behavior for OS-level hotkeys that Windows reserves:

**Keys that cannot be blocked:**
- **Ctrl + Alt + Del** - Security screen (intentional safety feature)
- **Windows + L** - Lock session (OS-level)
- **Ctrl + Shift + Esc** - Task Manager

**Why?** Windows prevents ANY application from blocking these hotkeys. This is a safety feature that ensures you can always regain control of your system.

**Keys that ARE blocked:**
- All letter, number, and symbol keys
- Function keys (F1-F24)
- Windows key (when pressed alone)
- Multimedia keys
- Arrow keys, Page Up/Down, etc.

### "CatLock won't start" or "Multiple instances running"

CatLock prevents multiple copies from running simultaneously using a lockfile.

**Solution:**
1. Check Task Manager (Ctrl + Shift + Esc)
2. Look for any running CatLock processes
3. End them
4. Delete the lockfile: `C:\Users\YourUsername\.catlock\catlock.lock`
5. Launch CatLock again

### "Windows Defender blocked CatLock"

If you built CatLock locally or downloaded it, Windows SmartScreen may flag it as unknown.

**Solution:**
1. Open **Windows Security**
2. Go to **Virus & threat protection > Protection history**
3. Find the CatLock entry
4. Select **Allow on device**

**Alternative:** Add the `dist` folder (or wherever CatLock.exe is) to Windows Defender exclusions.

### "The overlay doesn't cover all my monitors"

CatLock automatically detects all connected monitors and spans the overlay across them.

**If this isn't working:**
1. Make sure your monitors are properly configured in Windows Display Settings
2. Restart CatLock after changing monitor configuration
3. Check for Windows updates (multi-monitor support has improved in recent versions)

### "Notifications aren't showing"

**Check Windows notification settings:**
1. Open **Windows Settings > System > Notifications**
2. Ensure notifications are enabled globally
3. Scroll down and verify notifications are allowed for CatLock

**Also check:** The CatLock system tray menu - notifications may be disabled there.

### "CatLock is using too much CPU/memory"

CatLock is designed to be extremely lightweight (< 50 MB RAM, minimal CPU when idle).

**If you're seeing high resource usage:**
1. Check Task Manager for the actual CatLock process
2. Ensure you don't have multiple instances running
3. Try restarting CatLock
4. Check for conflicts with keyboard monitoring software

---

## Tips & Best Practices

### For Cat Owners

1. **Test the hotkey before you need it** - Practice locking and unlocking a few times (both hotkey and mouse click)
2. **Use higher opacity (70-90%)** - Cats are less interested in dark screens
3. **Lock proactively** - Hit Ctrl+L when you see your cat approaching
4. **Train with treats** - Some users reward their cats for NOT jumping on the keyboard
5. **Quick unlock** - If your cat does walk on the screen, a quick mouse click unlocks without fumbling for the hotkey

### For Shared Workstations

1. **Keep notifications disabled** - Silent locking is less disruptive
2. **Use a memorable hotkey** - Consider something easier than the default if you lock frequently
3. **Explain to colleagues** - If others use your computer, show them how to unlock

### For Streamers/Content Creators

1. **Use low opacity (5-10%)** - Viewers can still see your screen
2. **Lock during breaks** - Protects your stream from accidental input
3. **Test on OBS/streaming software** - Ensure the overlay appears in your capture

### For Multi-Monitor Setups

1. **The unlock instructions always appear on your primary monitor** - Make sure you know which monitor Windows considers "primary"
2. **The overlay spans ALL monitors** - This prevents cats from attacking secondary screens
3. **Adjust opacity per your workflow** - Lower opacity lets you monitor all screens simultaneously

---

## Frequently Asked Questions

### Can I customize the overlay appearance?

Currently, the overlay is a semi-transparent black screen with centered text. Opacity is configurable, but colors and text cannot be changed without modifying the source code.

### Does CatLock work with virtual machines?

When running inside a VM, keyboard blocking works within the VM only. Host OS hotkeys (like Ctrl + Alt + Del on the host) are not affected.

### Can I use CatLock to protect against toddlers/kids?

Yes! The keyboard lock works for any accidental input. However:
- Toddlers can unlock by clicking the screen (this is by design for quick adult unlock)
- Determined older children may figure out the unlock hotkey
- The overlay shows the unlock instructions on screen
- Consider these less effective than dedicated parental control software for determined children

### Does this drain my laptop battery?

No. CatLock uses negligible CPU and battery when idle (not locked). Even when locked, resource usage is minimal.

### Can I run CatLock on startup?

Yes! Add CatLock to your Windows startup folder:
1. Press **Windows + R**
2. Type `shell:startup` and press Enter
3. Create a shortcut to CatLock.exe in this folder

### Will CatLock interfere with games or full-screen apps?

No, when CatLock is NOT locked, it has zero impact on other applications. When locked, it blocks all keyboard input including to games.

### Can CatLock lock my mouse too?

No. CatLock only blocks keyboard input. The mouse remains fully functional and clicking anywhere unlocks the keyboard. This is intentional for quick human unlock.

### Is CatLock safe?

Yes. CatLock:
- Does not collect or transmit any data
- Does not modify system files
- Uses only documented Windows APIs
- Cannot prevent Ctrl + Alt + Del (safety feature)
- Unlocks automatically when quit

**Source code is available** on GitHub for security review.

---

## Support & Feedback

- **Issues or bugs:** Report on the GitHub Issues page
- **Feature requests:** Submit on GitHub Discussions
- **Support the developer:** Use the "Support" link in the About menu

---

## Safety Reminder

**You can NEVER be locked out of your system.**

Ctrl + Alt + Del ALWAYS works, regardless of CatLock's state. This is a Windows operating system guarantee that no application can override.

If you ever feel stuck:
1. Press **Ctrl + Alt + Del**
2. Choose **Task Manager**
3. End the **CatLock** process

Your keyboard will immediately unlock.

---

*CatLock - Because Fiona doesn't understand `git commit --amend`*

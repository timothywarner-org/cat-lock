//! Low-level keyboard hook for blocking input and detecting hotkeys
//!
//! Uses Windows SetWindowsHookEx with WH_KEYBOARD_LL to intercept all keyboard events.
//! When locked, blocks all keys except the configured unlock hotkey.

use crate::config::{parse_hotkey, Config};
use crate::AppState;
use log::{debug, info};
use std::sync::atomic::Ordering;
use std::sync::Arc;
use windows::Win32::Foundation::{LPARAM, LRESULT, WPARAM};
use windows::Win32::UI::Input::KeyboardAndMouse::*;
use windows::Win32::UI::WindowsAndMessaging::*;

/// Thread-local storage for hook state
/// Required because the hook callback can't capture closures
thread_local! {
    static HOOK_STATE: std::cell::RefCell<Option<HookState>> = const { std::cell::RefCell::new(None) };
}

struct HookState {
    state: Arc<AppState>,
    hotkey_modifiers: u32,
    hotkey_vk: u32,
}

/// Virtual key codes for modifier keys
const VK_LCONTROL_U32: u32 = VK_LCONTROL.0 as u32;
const VK_RCONTROL_U32: u32 = VK_RCONTROL.0 as u32;
const VK_LSHIFT_U32: u32 = VK_LSHIFT.0 as u32;
const VK_RSHIFT_U32: u32 = VK_RSHIFT.0 as u32;
const VK_LMENU_U32: u32 = VK_LMENU.0 as u32;  // Left Alt
const VK_RMENU_U32: u32 = VK_RMENU.0 as u32;  // Right Alt
const VK_LWIN_U32: u32 = VK_LWIN.0 as u32;
const VK_RWIN_U32: u32 = VK_RWIN.0 as u32;

/// Run the keyboard hook message loop
pub fn run_keyboard_hook(state: Arc<AppState>, config: Config) {
    // Parse the hotkey configuration
    let (modifiers, vk) = parse_hotkey(&config.hotkey).unwrap_or((MOD_CONTROL.0, 'B' as u32));

    info!(
        "Keyboard hook starting with hotkey: {} (modifiers={:#x}, vk={:#x})",
        config.hotkey, modifiers, vk
    );

    // Store state in thread-local storage for the hook callback
    HOOK_STATE.with(|hs| {
        *hs.borrow_mut() = Some(HookState {
            state: Arc::clone(&state),
            hotkey_modifiers: modifiers,
            hotkey_vk: vk,
        });
    });

    // Install low-level keyboard hook
    let hook = unsafe {
        SetWindowsHookExW(WH_KEYBOARD_LL, Some(keyboard_hook_proc), None, 0)
            .expect("Failed to install keyboard hook")
    };

    info!("Keyboard hook installed");

    // Message loop - required for low-level hooks to work
    unsafe {
        let mut msg = MSG::default();
        while !state.should_quit.load(Ordering::SeqCst) {
            // Use PeekMessage with a short timeout to allow checking should_quit
            if PeekMessageW(&mut msg, None, 0, 0, PM_REMOVE).as_bool() {
                if msg.message == WM_QUIT {
                    break;
                }
                TranslateMessage(&msg);
                DispatchMessageW(&msg);
            } else {
                // Small sleep to avoid busy-waiting
                std::thread::sleep(std::time::Duration::from_millis(10));
            }
        }

        // Unhook before exiting
        let _ = UnhookWindowsHookEx(hook);
    }

    info!("Keyboard hook removed");
}

/// Check if a modifier key is currently pressed
fn is_modifier_pressed(modifier: u32) -> bool {
    unsafe {
        match modifier {
            m if m == MOD_CONTROL.0 => {
                (GetAsyncKeyState(VK_LCONTROL.0 as i32) as u16 & 0x8000) != 0
                    || (GetAsyncKeyState(VK_RCONTROL.0 as i32) as u16 & 0x8000) != 0
            }
            m if m == MOD_SHIFT.0 => {
                (GetAsyncKeyState(VK_LSHIFT.0 as i32) as u16 & 0x8000) != 0
                    || (GetAsyncKeyState(VK_RSHIFT.0 as i32) as u16 & 0x8000) != 0
            }
            m if m == MOD_ALT.0 => {
                (GetAsyncKeyState(VK_LMENU.0 as i32) as u16 & 0x8000) != 0
                    || (GetAsyncKeyState(VK_RMENU.0 as i32) as u16 & 0x8000) != 0
            }
            m if m == MOD_WIN.0 => {
                (GetAsyncKeyState(VK_LWIN.0 as i32) as u16 & 0x8000) != 0
                    || (GetAsyncKeyState(VK_RWIN.0 as i32) as u16 & 0x8000) != 0
            }
            _ => false,
        }
    }
}

/// Check if all required modifiers are pressed (and no extra ones)
fn check_modifiers(required: u32) -> bool {
    let ctrl_required = (required & MOD_CONTROL.0) != 0;
    let shift_required = (required & MOD_SHIFT.0) != 0;
    let alt_required = (required & MOD_ALT.0) != 0;
    let win_required = (required & MOD_WIN.0) != 0;

    let ctrl_pressed = is_modifier_pressed(MOD_CONTROL.0);
    let shift_pressed = is_modifier_pressed(MOD_SHIFT.0);
    let alt_pressed = is_modifier_pressed(MOD_ALT.0);
    let win_pressed = is_modifier_pressed(MOD_WIN.0);

    ctrl_required == ctrl_pressed
        && shift_required == shift_pressed
        && alt_required == alt_pressed
        && win_required == win_pressed
}

/// Check if a virtual key code is a modifier key
fn is_modifier_vk(vk: u32) -> bool {
    matches!(
        vk,
        VK_LCONTROL_U32
            | VK_RCONTROL_U32
            | VK_LSHIFT_U32
            | VK_RSHIFT_U32
            | VK_LMENU_U32
            | VK_RMENU_U32
            | VK_LWIN_U32
            | VK_RWIN_U32
            | 0x11  // VK_CONTROL
            | 0x10  // VK_SHIFT
            | 0x12  // VK_MENU (Alt)
    )
}

/// Low-level keyboard hook procedure
unsafe extern "system" fn keyboard_hook_proc(
    code: i32,
    wparam: WPARAM,
    lparam: LPARAM,
) -> LRESULT {
    if code >= 0 {
        let kb_struct = &*(lparam.0 as *const KBDLLHOOKSTRUCT);
        let vk_code = kb_struct.vkCode;
        let is_keydown = wparam.0 == WM_KEYDOWN as usize || wparam.0 == WM_SYSKEYDOWN as usize;

        HOOK_STATE.with(|hs| {
            if let Some(hook_state) = hs.borrow().as_ref() {
                let is_locked = hook_state.state.locked.load(Ordering::SeqCst);

                // Check for hotkey press (only on keydown, not modifiers themselves)
                if is_keydown && !is_modifier_vk(vk_code) {
                    if vk_code == hook_state.hotkey_vk
                        && check_modifiers(hook_state.hotkey_modifiers)
                    {
                        // Toggle lock state
                        let new_state = !is_locked;
                        hook_state.state.locked.store(new_state, Ordering::SeqCst);
                        debug!("Hotkey pressed, locked={}", new_state);

                        // Block this keypress so it doesn't pass through
                        return LRESULT(1);
                    }
                }

                // If locked, block all keys except:
                // - The unlock hotkey modifiers (so user can press the combo)
                // - Ctrl+Alt+Del (can't be blocked anyway, OS-level)
                if is_locked {
                    // Allow modifier keys through so user can build up the hotkey combo
                    if is_modifier_vk(vk_code) {
                        // Pass through modifier keys
                        return CallNextHookEx(None, code, wparam, lparam);
                    }

                    // Block everything else
                    debug!("Blocking key: vk={:#x}", vk_code);
                    return LRESULT(1);
                }
            }
        });
    }

    CallNextHookEx(None, code, wparam, lparam)
}

/// List of all virtual key codes to block when locked
/// Includes standard keys, function keys, numpad, and laptop special keys
#[allow(dead_code)]
pub const BLOCKED_KEYS: &[u16] = &[
    // Letters A-Z (0x41-0x5A)
    0x41, 0x42, 0x43, 0x44, 0x45, 0x46, 0x47, 0x48, 0x49, 0x4A, 0x4B, 0x4C, 0x4D,
    0x4E, 0x4F, 0x50, 0x51, 0x52, 0x53, 0x54, 0x55, 0x56, 0x57, 0x58, 0x59, 0x5A,
    // Numbers 0-9 (0x30-0x39)
    0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36, 0x37, 0x38, 0x39,
    // Numpad 0-9 (VK_NUMPAD0-VK_NUMPAD9)
    0x60, 0x61, 0x62, 0x63, 0x64, 0x65, 0x66, 0x67, 0x68, 0x69,
    // Numpad operators
    0x6A, // VK_MULTIPLY
    0x6B, // VK_ADD
    0x6C, // VK_SEPARATOR
    0x6D, // VK_SUBTRACT
    0x6E, // VK_DECIMAL
    0x6F, // VK_DIVIDE
    // Function keys F1-F24
    0x70, 0x71, 0x72, 0x73, 0x74, 0x75, 0x76, 0x77, 0x78, 0x79, 0x7A, 0x7B,
    0x7C, 0x7D, 0x7E, 0x7F, 0x80, 0x81, 0x82, 0x83, 0x84, 0x85, 0x86, 0x87,
    // Special keys
    0x08, // VK_BACK (Backspace)
    0x09, // VK_TAB
    0x0D, // VK_RETURN (Enter)
    0x1B, // VK_ESCAPE
    0x20, // VK_SPACE
    0x21, // VK_PRIOR (Page Up)
    0x22, // VK_NEXT (Page Down)
    0x23, // VK_END
    0x24, // VK_HOME
    0x25, // VK_LEFT
    0x26, // VK_UP
    0x27, // VK_RIGHT
    0x28, // VK_DOWN
    0x2D, // VK_INSERT
    0x2E, // VK_DELETE
    // OEM keys (symbols)
    0xBA, // VK_OEM_1 (;:)
    0xBB, // VK_OEM_PLUS (=+)
    0xBC, // VK_OEM_COMMA (,<)
    0xBD, // VK_OEM_MINUS (-_)
    0xBE, // VK_OEM_PERIOD (.>)
    0xBF, // VK_OEM_2 (/?)
    0xC0, // VK_OEM_3 (`~)
    0xDB, // VK_OEM_4 ([{)
    0xDC, // VK_OEM_5 (\|)
    0xDD, // VK_OEM_6 (]})
    0xDE, // VK_OEM_7 ('")
    // Laptop/Media keys
    0xAD, // VK_VOLUME_MUTE
    0xAE, // VK_VOLUME_DOWN
    0xAF, // VK_VOLUME_UP
    0xB0, // VK_MEDIA_NEXT_TRACK
    0xB1, // VK_MEDIA_PREV_TRACK
    0xB2, // VK_MEDIA_STOP
    0xB3, // VK_MEDIA_PLAY_PAUSE
    0xB4, // VK_LAUNCH_MAIL
    0xB5, // VK_LAUNCH_MEDIA_SELECT
    0xB6, // VK_LAUNCH_APP1
    0xB7, // VK_LAUNCH_APP2
    // Browser keys
    0xA6, // VK_BROWSER_BACK
    0xA7, // VK_BROWSER_FORWARD
    0xA8, // VK_BROWSER_REFRESH
    0xA9, // VK_BROWSER_STOP
    0xAA, // VK_BROWSER_SEARCH
    0xAB, // VK_BROWSER_FAVORITES
    0xAC, // VK_BROWSER_HOME
    // Misc
    0x90, // VK_NUMLOCK
    0x91, // VK_SCROLL
    0x13, // VK_PAUSE
    0x2C, // VK_SNAPSHOT (Print Screen)
    0x03, // VK_CANCEL (Ctrl+Break)
];

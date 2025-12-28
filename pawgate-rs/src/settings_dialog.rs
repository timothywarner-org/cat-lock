//! Settings dialog for configuring PawGate
//!
//! A native Windows dialog allowing users to configure:
//! - Hotkey combination
//! - Overlay opacity
//! - Overlay color
//! - Notification settings

use crate::config::Config;
use std::cell::RefCell;
use windows::core::{w, PCWSTR};
use windows::Win32::Foundation::*;
use windows::Win32::Graphics::Gdi::*;
use windows::Win32::System::LibraryLoader::GetModuleHandleW;
use windows::Win32::UI::Controls::*;
use windows::Win32::UI::WindowsAndMessaging::*;

// Control IDs
const ID_OK: i32 = 1;
const ID_CANCEL: i32 = 2;
const ID_HOTKEY_EDIT: i32 = 100;
const ID_OPACITY_SLIDER: i32 = 101;
const ID_OPACITY_LABEL: i32 = 102;
const ID_COLOR_COMBO: i32 = 103;
const ID_NOTIFICATIONS_CHECK: i32 = 104;

/// Thread-local storage for dialog state
thread_local! {
    static DIALOG_CONFIG: RefCell<Option<Config>> = const { RefCell::new(None) };
    static DIALOG_RESULT: RefCell<Option<Config>> = const { RefCell::new(None) };
}

/// Color presets - all colorblind-friendly
const COLOR_PRESETS: &[(&str, &str)] = &[
    ("Forest Green", "#1B5E20"),
    ("Deep Blue", "#1565C0"),
    ("Dark Purple", "#4A148C"),
    ("Charcoal Gray", "#37474F"),
    ("Dark Orange", "#E65100"),
    ("Deep Teal", "#00695C"),
];

/// Show the settings dialog and return updated config if OK was pressed
pub fn show_settings_dialog(current_config: &Config) -> Option<Config> {
    // Store current config for the dialog
    DIALOG_CONFIG.with(|c| {
        *c.borrow_mut() = Some(current_config.clone());
    });
    DIALOG_RESULT.with(|r| {
        *r.borrow_mut() = None;
    });

    unsafe {
        let hinstance = GetModuleHandleW(None).ok()?;

        // Register window class for dialog
        let class_name = w!("PawGateSettings");
        let wc = WNDCLASSEXW {
            cbSize: std::mem::size_of::<WNDCLASSEXW>() as u32,
            style: CS_HREDRAW | CS_VREDRAW,
            lpfnWndProc: Some(settings_wnd_proc),
            hInstance: hinstance.into(),
            hCursor: LoadCursorW(None, IDC_ARROW).ok(),
            hbrBackground: HBRUSH((COLOR_3DFACE.0 + 1) as *mut std::ffi::c_void),
            lpszClassName: class_name,
            ..Default::default()
        };

        RegisterClassExW(&wc);

        // Calculate center position
        let screen_width = GetSystemMetrics(SM_CXSCREEN);
        let screen_height = GetSystemMetrics(SM_CYSCREEN);
        let dialog_width = 400;
        let dialog_height = 320;
        let x = (screen_width - dialog_width) / 2;
        let y = (screen_height - dialog_height) / 2;

        // Create dialog window
        let hwnd = CreateWindowExW(
            WS_EX_DLGMODALFRAME,
            class_name,
            w!("PawGate Settings"),
            WS_OVERLAPPED | WS_CAPTION | WS_SYSMENU | WS_VISIBLE,
            x,
            y,
            dialog_width,
            dialog_height,
            None,
            None,
            Some(hinstance.into()),
            None,
        )?;

        // Create controls
        create_dialog_controls(hwnd, current_config);

        // Run modal dialog loop
        let mut msg = MSG::default();
        while GetMessageW(&mut msg, None, 0, 0).as_bool() {
            if !IsDialogMessageW(hwnd, &msg).as_bool() {
                TranslateMessage(&msg);
                DispatchMessageW(&msg);
            }

            // Check if dialog was closed
            if !IsWindow(hwnd).as_bool() {
                break;
            }
        }
    }

    // Return the result
    DIALOG_RESULT.with(|r| r.borrow_mut().take())
}

unsafe fn create_dialog_controls(hwnd: HWND, config: &Config) {
    let hinstance = GetModuleHandleW(None).ok();

    // Get default font
    let font = get_default_font();

    let mut y = 20;
    let label_width = 120;
    let control_x = 140;
    let control_width = 220;

    // Hotkey label
    let hotkey_label = CreateWindowExW(
        WINDOW_EX_STYLE(0),
        w!("STATIC"),
        w!("Hotkey:"),
        WS_CHILD | WS_VISIBLE | WINDOW_STYLE(SS_RIGHT as u32),
        20, y + 2, label_width, 20,
        Some(hwnd),
        None,
        hinstance,
        None,
    );
    if let Some(h) = hotkey_label {
        send_font_message(h, font);
    }

    // Hotkey edit box
    let hotkey_edit = CreateWindowExW(
        WS_EX_CLIENTEDGE,
        w!("EDIT"),
        PCWSTR(to_wide(&config.hotkey).as_ptr()),
        WS_CHILD | WS_VISIBLE | WS_TABSTOP | WINDOW_STYLE(ES_AUTOHSCROLL as u32),
        control_x, y, control_width, 24,
        Some(hwnd),
        HMENU(ID_HOTKEY_EDIT as *mut std::ffi::c_void),
        hinstance,
        None,
    );
    if let Some(h) = hotkey_edit {
        send_font_message(h, font);
    }

    y += 40;

    // Opacity label
    let opacity_label = CreateWindowExW(
        WINDOW_EX_STYLE(0),
        w!("STATIC"),
        w!("Opacity:"),
        WS_CHILD | WS_VISIBLE | WINDOW_STYLE(SS_RIGHT as u32),
        20, y + 2, label_width, 20,
        Some(hwnd),
        None,
        hinstance,
        None,
    );
    if let Some(h) = opacity_label {
        send_font_message(h, font);
    }

    // Opacity slider (trackbar)
    // Initialize common controls for trackbar
    let icc = INITCOMMONCONTROLSEX {
        dwSize: std::mem::size_of::<INITCOMMONCONTROLSEX>() as u32,
        dwICC: ICC_BAR_CLASSES,
    };
    InitCommonControlsEx(&icc);

    let slider = CreateWindowExW(
        WINDOW_EX_STYLE(0),
        w!("msctls_trackbar32"),
        PCWSTR::null(),
        WS_CHILD | WS_VISIBLE | WS_TABSTOP | WINDOW_STYLE(TBS_AUTOTICKS as u32),
        control_x, y, control_width - 50, 30,
        Some(hwnd),
        HMENU(ID_OPACITY_SLIDER as *mut std::ffi::c_void),
        hinstance,
        None,
    );
    if let Some(h) = slider {
        // Set range 10-90 (representing 0.1 to 0.9)
        SendMessageW(h, TBM_SETRANGE, WPARAM(1), LPARAM(((90 << 16) | 10) as isize));
        SendMessageW(h, TBM_SETPOS, WPARAM(1), LPARAM((config.opacity * 100.0) as isize));
        SendMessageW(h, TBM_SETTICFREQ, WPARAM(10), LPARAM(0));
    }

    // Opacity value label
    let opacity_value = format!("{}%", (config.opacity * 100.0) as i32);
    let opacity_value_label = CreateWindowExW(
        WINDOW_EX_STYLE(0),
        w!("STATIC"),
        PCWSTR(to_wide(&opacity_value).as_ptr()),
        WS_CHILD | WS_VISIBLE | WINDOW_STYLE(SS_LEFT as u32),
        control_x + control_width - 40, y + 5, 40, 20,
        Some(hwnd),
        HMENU(ID_OPACITY_LABEL as *mut std::ffi::c_void),
        hinstance,
        None,
    );
    if let Some(h) = opacity_value_label {
        send_font_message(h, font);
    }

    y += 50;

    // Color label
    let color_label = CreateWindowExW(
        WINDOW_EX_STYLE(0),
        w!("STATIC"),
        w!("Overlay Color:"),
        WS_CHILD | WS_VISIBLE | WINDOW_STYLE(SS_RIGHT as u32),
        20, y + 2, label_width, 20,
        Some(hwnd),
        None,
        hinstance,
        None,
    );
    if let Some(h) = color_label {
        send_font_message(h, font);
    }

    // Color combo box
    let color_combo = CreateWindowExW(
        WINDOW_EX_STYLE(0),
        w!("COMBOBOX"),
        PCWSTR::null(),
        WS_CHILD | WS_VISIBLE | WS_TABSTOP | WS_VSCROLL | WINDOW_STYLE((CBS_DROPDOWNLIST) as u32),
        control_x, y, control_width, 200,
        Some(hwnd),
        HMENU(ID_COLOR_COMBO as *mut std::ffi::c_void),
        hinstance,
        None,
    );
    if let Some(h) = color_combo {
        send_font_message(h, font);
        // Add color presets
        let mut selected_idx = 0i32;
        for (idx, (name, hex)) in COLOR_PRESETS.iter().enumerate() {
            let wide_name = to_wide(name);
            SendMessageW(h, CB_ADDSTRING, WPARAM(0), LPARAM(wide_name.as_ptr() as isize));
            if *hex == config.overlay_color {
                selected_idx = idx as i32;
            }
        }
        SendMessageW(h, CB_SETCURSEL, WPARAM(selected_idx as usize), LPARAM(0));
    }

    y += 40;

    // Notifications checkbox
    let notifications_check = CreateWindowExW(
        WINDOW_EX_STYLE(0),
        w!("BUTTON"),
        w!("Enable notifications"),
        WS_CHILD | WS_VISIBLE | WS_TABSTOP | WINDOW_STYLE(BS_AUTOCHECKBOX as u32),
        control_x, y, control_width, 24,
        Some(hwnd),
        HMENU(ID_NOTIFICATIONS_CHECK as *mut std::ffi::c_void),
        hinstance,
        None,
    );
    if let Some(h) = notifications_check {
        send_font_message(h, font);
        if config.notifications_enabled {
            SendMessageW(h, BM_SETCHECK, WPARAM(BST_CHECKED.0 as usize), LPARAM(0));
        }
    }

    y += 50;

    // Note about hotkey restart
    let note_label = CreateWindowExW(
        WINDOW_EX_STYLE(0),
        w!("STATIC"),
        w!("Note: Hotkey changes require restart"),
        WS_CHILD | WS_VISIBLE | WINDOW_STYLE((SS_CENTER) as u32),
        20, y, 360, 20,
        Some(hwnd),
        None,
        hinstance,
        None,
    );
    if let Some(h) = note_label {
        send_font_message(h, font);
    }

    y += 40;

    // OK button
    let ok_button = CreateWindowExW(
        WINDOW_EX_STYLE(0),
        w!("BUTTON"),
        w!("OK"),
        WS_CHILD | WS_VISIBLE | WS_TABSTOP | WINDOW_STYLE(BS_DEFPUSHBUTTON as u32),
        200, y, 80, 28,
        Some(hwnd),
        HMENU(ID_OK as *mut std::ffi::c_void),
        hinstance,
        None,
    );
    if let Some(h) = ok_button {
        send_font_message(h, font);
    }

    // Cancel button
    let cancel_button = CreateWindowExW(
        WINDOW_EX_STYLE(0),
        w!("BUTTON"),
        w!("Cancel"),
        WS_CHILD | WS_VISIBLE | WS_TABSTOP,
        290, y, 80, 28,
        Some(hwnd),
        HMENU(ID_CANCEL as *mut std::ffi::c_void),
        hinstance,
        None,
    );
    if let Some(h) = cancel_button {
        send_font_message(h, font);
    }
}

unsafe fn get_default_font() -> HFONT {
    let ncm = NONCLIENTMETRICSW {
        cbSize: std::mem::size_of::<NONCLIENTMETRICSW>() as u32,
        ..Default::default()
    };
    // Return a reasonable default font
    CreateFontW(
        -14, 0, 0, 0,
        FW_NORMAL.0 as i32,
        0, 0, 0,
        DEFAULT_CHARSET.0 as u32,
        OUT_DEFAULT_PRECIS.0 as u32,
        CLIP_DEFAULT_PRECIS.0 as u32,
        CLEARTYPE_QUALITY.0 as u32,
        DEFAULT_PITCH.0 as u32,
        w!("Segoe UI"),
    )
}

unsafe fn send_font_message(hwnd: HWND, font: HFONT) {
    SendMessageW(hwnd, WM_SETFONT, WPARAM(font.0 as usize), LPARAM(1));
}

fn to_wide(s: &str) -> Vec<u16> {
    s.encode_utf16().chain(std::iter::once(0)).collect()
}

fn from_wide(wide: &[u16]) -> String {
    let len = wide.iter().position(|&c| c == 0).unwrap_or(wide.len());
    String::from_utf16_lossy(&wide[..len])
}

unsafe extern "system" fn settings_wnd_proc(
    hwnd: HWND,
    msg: u32,
    wparam: WPARAM,
    lparam: LPARAM,
) -> LRESULT {
    match msg {
        WM_COMMAND => {
            let id = (wparam.0 & 0xFFFF) as i32;
            let notification = ((wparam.0 >> 16) & 0xFFFF) as u32;

            match id {
                ID_OK => {
                    // Gather values from controls and save config
                    if let Some(config) = gather_dialog_values(hwnd) {
                        DIALOG_RESULT.with(|r| {
                            *r.borrow_mut() = Some(config);
                        });
                    }
                    let _ = DestroyWindow(hwnd);
                }
                ID_CANCEL => {
                    let _ = DestroyWindow(hwnd);
                }
                _ => {}
            }
            LRESULT(0)
        }

        WM_HSCROLL => {
            // Handle slider changes
            let slider = GetDlgItem(hwnd, ID_OPACITY_SLIDER);
            if lparam.0 == slider.unwrap_or(HWND(std::ptr::null_mut())).0 as isize {
                let pos = SendMessageW(slider.unwrap(), TBM_GETPOS, WPARAM(0), LPARAM(0)).0 as i32;
                let label = GetDlgItem(hwnd, ID_OPACITY_LABEL);
                if let Some(lbl) = label {
                    let text = format!("{}%", pos);
                    SetWindowTextW(lbl, PCWSTR(to_wide(&text).as_ptr()));
                }
            }
            LRESULT(0)
        }

        WM_CLOSE => {
            let _ = DestroyWindow(hwnd);
            LRESULT(0)
        }

        WM_DESTROY => {
            PostQuitMessage(0);
            LRESULT(0)
        }

        _ => DefWindowProcW(hwnd, msg, wparam, lparam),
    }
}

unsafe fn gather_dialog_values(hwnd: HWND) -> Option<Config> {
    DIALOG_CONFIG.with(|c| {
        let mut config = c.borrow().clone()?;

        // Get hotkey
        if let Some(edit) = GetDlgItem(hwnd, ID_HOTKEY_EDIT) {
            let mut buffer = [0u16; 256];
            let len = GetWindowTextW(edit, &mut buffer) as usize;
            config.hotkey = from_wide(&buffer[..len]);
        }

        // Get opacity from slider
        if let Some(slider) = GetDlgItem(hwnd, ID_OPACITY_SLIDER) {
            let pos = SendMessageW(slider, TBM_GETPOS, WPARAM(0), LPARAM(0)).0 as f32;
            config.opacity = pos / 100.0;
        }

        // Get color from combo
        if let Some(combo) = GetDlgItem(hwnd, ID_COLOR_COMBO) {
            let idx = SendMessageW(combo, CB_GETCURSEL, WPARAM(0), LPARAM(0)).0 as usize;
            if idx < COLOR_PRESETS.len() {
                config.overlay_color = COLOR_PRESETS[idx].1.to_string();
            }
        }

        // Get notifications checkbox
        if let Some(check) = GetDlgItem(hwnd, ID_NOTIFICATIONS_CHECK) {
            let state = SendMessageW(check, BM_GETCHECK, WPARAM(0), LPARAM(0)).0;
            config.notifications_enabled = state == BST_CHECKED.0 as isize;
        }

        Some(config)
    })
}

//! Full-screen overlay window for visual feedback when keyboard is locked
//!
//! Creates a semi-transparent window that spans all monitors.
//! Uses Win32 layered windows for proper transparency.

use std::sync::atomic::Ordering;
use std::sync::Arc;
use windows::core::{PCWSTR, w};
use windows::Win32::Foundation::*;
use windows::Win32::Graphics::Gdi::*;
use windows::Win32::System::LibraryLoader::GetModuleHandleW;
use windows::Win32::UI::WindowsAndMessaging::*;

use crate::config::Config;
use crate::AppState;

const OVERLAY_CLASS_NAME: PCWSTR = w!("PawGateOverlay");

/// Thread-local state for the overlay window
thread_local! {
    static OVERLAY_STATE: std::cell::RefCell<Option<OverlayState>> = const { std::cell::RefCell::new(None) };
}

struct OverlayState {
    state: Arc<AppState>,
    color: (u8, u8, u8),
    opacity: u8,
}

/// Create and show the overlay window
/// Returns the window handle
pub fn create_overlay(state: Arc<AppState>, config: &Config) -> Option<HWND> {
    let (r, g, b) = config.parse_overlay_color();
    let opacity = (config.opacity * 255.0) as u8;

    // Store state for window procedure
    OVERLAY_STATE.with(|os| {
        *os.borrow_mut() = Some(OverlayState {
            state: Arc::clone(&state),
            color: (r, g, b),
            opacity,
        });
    });

    unsafe {
        let hinstance = GetModuleHandleW(None).ok()?;

        // Register window class
        let wc = WNDCLASSEXW {
            cbSize: std::mem::size_of::<WNDCLASSEXW>() as u32,
            style: CS_HREDRAW | CS_VREDRAW,
            lpfnWndProc: Some(overlay_wnd_proc),
            hInstance: hinstance.into(),
            hCursor: LoadCursorW(None, IDC_ARROW).ok(),
            hbrBackground: HBRUSH(0), // No background - we paint manually
            lpszClassName: OVERLAY_CLASS_NAME,
            ..Default::default()
        };

        RegisterClassExW(&wc);

        // Get virtual screen dimensions (all monitors)
        let x = GetSystemMetrics(SM_XVIRTUALSCREEN);
        let y = GetSystemMetrics(SM_YVIRTUALSCREEN);
        let width = GetSystemMetrics(SM_CXVIRTUALSCREEN);
        let height = GetSystemMetrics(SM_CYVIRTUALSCREEN);

        // Create layered window
        let hwnd = CreateWindowExW(
            WS_EX_LAYERED | WS_EX_TOPMOST | WS_EX_TOOLWINDOW | WS_EX_TRANSPARENT,
            OVERLAY_CLASS_NAME,
            w!("PawGate Overlay"),
            WS_POPUP | WS_VISIBLE,
            x,
            y,
            width,
            height,
            None,
            None,
            Some(hinstance.into()),
            None,
        )?;

        // Set layered window attributes for transparency
        SetLayeredWindowAttributes(
            hwnd,
            COLORREF(0),
            opacity,
            LWA_ALPHA,
        ).ok()?;

        // Force a repaint
        InvalidateRect(hwnd, None, true);
        UpdateWindow(hwnd);

        Some(hwnd)
    }
}

/// Hide and destroy the overlay window
pub fn destroy_overlay(hwnd: HWND) {
    unsafe {
        let _ = DestroyWindow(hwnd);
    }
}

/// Show or hide the overlay based on lock state
pub fn set_overlay_visible(hwnd: HWND, visible: bool) {
    unsafe {
        ShowWindow(hwnd, if visible { SW_SHOW } else { SW_HIDE });
        if visible {
            // Bring to top and repaint
            let _ = SetWindowPos(
                hwnd,
                HWND_TOPMOST,
                0, 0, 0, 0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW,
            );
            InvalidateRect(hwnd, None, true);
        }
    }
}

/// Window procedure for the overlay
unsafe extern "system" fn overlay_wnd_proc(
    hwnd: HWND,
    msg: u32,
    wparam: WPARAM,
    lparam: LPARAM,
) -> LRESULT {
    match msg {
        WM_PAINT => {
            OVERLAY_STATE.with(|os| {
                if let Some(state) = os.borrow().as_ref() {
                    let mut ps = PAINTSTRUCT::default();
                    let hdc = BeginPaint(hwnd, &mut ps);

                    // Get window dimensions
                    let mut rect = RECT::default();
                    let _ = GetClientRect(hwnd, &mut rect);

                    // Create brush with overlay color
                    let (r, g, b) = state.color;
                    let brush = CreateSolidBrush(COLORREF(
                        (r as u32) | ((g as u32) << 8) | ((b as u32) << 16),
                    ));

                    // Fill the window
                    FillRect(hdc, &rect, brush);
                    let _ = DeleteObject(brush);

                    // Draw centered text
                    let text = "Keyboard Locked - Press hotkey to unlock";
                    let wide_text: Vec<u16> = text.encode_utf16().chain(std::iter::once(0)).collect();

                    // Create a larger font
                    let font = CreateFontW(
                        48, 0, 0, 0,
                        FW_BOLD.0 as i32,
                        0, 0, 0,
                        DEFAULT_CHARSET.0 as u32,
                        OUT_DEFAULT_PRECIS.0 as u32,
                        CLIP_DEFAULT_PRECIS.0 as u32,
                        CLEARTYPE_QUALITY.0 as u32,
                        DEFAULT_PITCH.0 as u32 | (FF_DONTCARE.0 as u32),
                        w!("Segoe UI"),
                    );

                    let old_font = SelectObject(hdc, font);
                    SetTextColor(hdc, COLORREF(0xFFFFFF)); // White text
                    SetBkMode(hdc, TRANSPARENT);

                    // Draw text centered
                    let _ = DrawTextW(
                        hdc,
                        &mut wide_text.as_slice()[..wide_text.len()-1].to_vec(),
                        &mut rect,
                        DT_CENTER | DT_VCENTER | DT_SINGLELINE,
                    );

                    SelectObject(hdc, old_font);
                    let _ = DeleteObject(font);

                    let _ = EndPaint(hwnd, &ps);
                }
            });
            LRESULT(0)
        }

        WM_ERASEBKGND => {
            // Handled in WM_PAINT
            LRESULT(1)
        }

        WM_DESTROY => {
            OVERLAY_STATE.with(|os| {
                *os.borrow_mut() = None;
            });
            LRESULT(0)
        }

        _ => DefWindowProcW(hwnd, msg, wparam, lparam),
    }
}

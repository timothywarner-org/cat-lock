//! System tray icon and menu for PawGate
//!
//! Provides a system tray icon with a context menu for settings, lock toggle, and exit.

use crate::config::Config;
use crate::overlay::{create_overlay, destroy_overlay, set_overlay_visible};
use crate::settings_dialog;
use crate::AppState;
use log::info;
use muda::{Menu, MenuEvent, MenuItem, PredefinedMenuItem};
use std::sync::atomic::Ordering;
use std::sync::Arc;
use tray_icon::{Icon, TrayIcon, TrayIconBuilder};
use windows::Win32::Foundation::HWND;
use windows::Win32::UI::WindowsAndMessaging::*;

/// Menu item IDs
const MENU_LOCK: &str = "lock";
const MENU_SETTINGS: &str = "settings";
const MENU_EXIT: &str = "exit";

/// Create the tray icon from embedded or generated icon
fn create_tray_icon() -> Icon {
    // Generate a simple colorblind-friendly icon programmatically
    // Using high contrast blue/orange which is distinguishable by most colorblind types
    let size = 64u32;
    let mut rgba = vec![0u8; (size * size * 4) as usize];

    // Create a paw-like shape with high contrast colors
    // Background: Deep blue (#1565C0) - visible to all color vision types
    // Foreground: Bright orange (#FF6D00) - contrasts well with blue

    for y in 0..size {
        for x in 0..size {
            let idx = ((y * size + x) * 4) as usize;
            let cx = (x as f32 - size as f32 / 2.0).abs();
            let cy = (y as f32 - size as f32 / 2.0).abs();

            // Circular background
            let dist = ((cx * cx + cy * cy) as f32).sqrt();
            if dist < size as f32 / 2.0 - 2.0 {
                // Deep blue background
                rgba[idx] = 0x15;     // R
                rgba[idx + 1] = 0x65; // G
                rgba[idx + 2] = 0xC0; // B
                rgba[idx + 3] = 255;  // A

                // Draw paw pads in orange
                // Main pad (center-bottom)
                let main_pad_x = size as f32 / 2.0;
                let main_pad_y = size as f32 / 2.0 + 8.0;
                let main_dist = (((x as f32 - main_pad_x).powi(2) + (y as f32 - main_pad_y).powi(2))).sqrt();

                // Toe pads (top)
                let toe_positions = [
                    (size as f32 / 2.0 - 12.0, size as f32 / 2.0 - 10.0),
                    (size as f32 / 2.0, size as f32 / 2.0 - 14.0),
                    (size as f32 / 2.0 + 12.0, size as f32 / 2.0 - 10.0),
                ];

                let mut is_pad = main_dist < 14.0;
                for (tx, ty) in &toe_positions {
                    let toe_dist = (((x as f32 - tx).powi(2) + (y as f32 - ty).powi(2))).sqrt();
                    if toe_dist < 7.0 {
                        is_pad = true;
                    }
                }

                if is_pad {
                    // Bright orange for paw
                    rgba[idx] = 0xFF;     // R
                    rgba[idx + 1] = 0x6D; // G
                    rgba[idx + 2] = 0x00; // B
                }
            } else {
                // Transparent outside
                rgba[idx] = 0;
                rgba[idx + 1] = 0;
                rgba[idx + 2] = 0;
                rgba[idx + 3] = 0;
            }
        }
    }

    Icon::from_rgba(rgba, size, size).expect("Failed to create icon")
}

/// Run the main tray icon event loop
pub fn run_tray_loop(state: Arc<AppState>, mut config: Config) -> Result<(), Box<dyn std::error::Error>> {
    // Create menu
    let menu = Menu::new();

    let lock_item = MenuItem::with_id(MENU_LOCK, "Lock Keyboard", true, None);
    let settings_item = MenuItem::with_id(MENU_SETTINGS, "Settings...", true, None);
    let exit_item = MenuItem::with_id(MENU_EXIT, "Exit", true, None);

    menu.append(&lock_item)?;
    menu.append(&PredefinedMenuItem::separator())?;
    menu.append(&settings_item)?;
    menu.append(&PredefinedMenuItem::separator())?;
    menu.append(&exit_item)?;

    // Create tray icon
    let icon = create_tray_icon();
    let _tray_icon = TrayIconBuilder::new()
        .with_menu(Box::new(menu))
        .with_tooltip("PawGate - Keyboard Locker")
        .with_icon(icon)
        .build()?;

    info!("Tray icon created");

    // Create overlay window (initially hidden)
    let overlay_hwnd = create_overlay(Arc::clone(&state), &config);

    // Track previous lock state to detect changes
    let mut prev_locked = false;

    // Main event loop
    let menu_receiver = MenuEvent::receiver();

    loop {
        // Check for quit signal
        if state.should_quit.load(Ordering::SeqCst) {
            break;
        }

        // Handle menu events (non-blocking)
        if let Ok(event) = menu_receiver.try_recv() {
            match event.id.0.as_str() {
                MENU_LOCK => {
                    let current = state.locked.load(Ordering::SeqCst);
                    state.locked.store(!current, Ordering::SeqCst);
                    info!("Menu toggle lock: {}", !current);
                }
                MENU_SETTINGS => {
                    info!("Opening settings dialog");
                    // Show settings dialog
                    if let Some(new_config) = settings_dialog::show_settings_dialog(&config) {
                        // Save the new config
                        if let Err(e) = new_config.save() {
                            log::error!("Failed to save config: {}", e);
                        } else {
                            config = new_config;
                            info!("Settings saved");
                            // Note: Hotkey changes require restart to take effect
                            // We could signal the keyboard thread to reload, but simpler to restart
                        }
                    }
                }
                MENU_EXIT => {
                    info!("Exit requested");
                    state.should_quit.store(true, Ordering::SeqCst);
                    break;
                }
                _ => {}
            }
        }

        // Check for lock state changes
        let current_locked = state.locked.load(Ordering::SeqCst);
        if current_locked != prev_locked {
            if let Some(hwnd) = overlay_hwnd {
                set_overlay_visible(hwnd, current_locked);

                // Update menu item text
                let new_text = if current_locked {
                    "Unlock Keyboard"
                } else {
                    "Lock Keyboard"
                };
                lock_item.set_text(new_text);
            }
            prev_locked = current_locked;
        }

        // Process Windows messages for proper event handling
        unsafe {
            let mut msg = MSG::default();
            while PeekMessageW(&mut msg, HWND(std::ptr::null_mut()), 0, 0, PM_REMOVE).as_bool() {
                if msg.message == WM_QUIT {
                    state.should_quit.store(true, Ordering::SeqCst);
                    break;
                }
                TranslateMessage(&msg);
                DispatchMessageW(&msg);
            }
        }

        // Small sleep to avoid busy-waiting
        std::thread::sleep(std::time::Duration::from_millis(16)); // ~60fps
    }

    // Cleanup
    if let Some(hwnd) = overlay_hwnd {
        destroy_overlay(hwnd);
    }

    Ok(())
}
